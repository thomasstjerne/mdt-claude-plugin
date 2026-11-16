#!/usr/bin/env python3
"""Drive the GBIF Metabarcoding Data Toolkit (MDT) API from the command line.

Standard library only. The login token is kept in ~/.config/mdt/, never printed, and renewed
from the `token` header every authenticated response carries. The dataset being worked on is
remembered in ./mdt-dataset.json, so commands run in the same directory need no key.
"""
import argparse
import base64
import getpass
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

DEFAULT_BASE_URL = "https://mdt.gbif.org/service"
CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config", "mdt")
TOKEN_FILE = os.path.join(CONFIG_DIR, "token")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
DATASET_FILE = "mdt-dataset.json"
POLL_SECONDS = 5
SCRIPT = os.path.abspath(__file__)


class MdtError(Exception):
    pass


def read_json_file(path, default=None):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default


def write_private(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(text)


def base_url():
    url = os.environ.get("MDT_BASE_URL") or read_json_file(CONFIG_FILE, {}).get("base_url") or DEFAULT_BASE_URL
    return url.rstrip("/")


def ui_url():
    url = base_url()
    return url[: -len("/service")] if url.endswith("/service") else url


def read_token():
    try:
        with open(TOKEN_FILE, encoding="utf-8") as f:
            return f.read().strip() or None
    except FileNotFoundError:
        return None


def dataset_key(args):
    key = getattr(args, "dataset", None) or read_json_file(DATASET_FILE, {}).get("key")
    if not key:
        raise MdtError("No dataset. Upload files with `upload`, or pass --dataset KEY.")
    return key


def remember_dataset(key):
    with open(DATASET_FILE, "w", encoding="utf-8") as f:
        json.dump({"key": key, "base_url": base_url(), "ui": f"{ui_url()}/dataset/{key}"}, f, indent=2)
        f.write("\n")


def login_hint():
    return f"Log in by running this in a terminal window of your own, so the password doesn't pass through the agent:\n  python3 {SCRIPT} login"


def request(method, path, body=None, headers=None, auth=True, raw=False):
    url = path if path.startswith("http") else f"{base_url()}{path}"
    headers = dict(headers or {})
    if auth:
        token = read_token()
        if not token:
            raise MdtError("Not logged in. " + login_hint())
        headers["Authorization"] = f"Bearer {token}"
    if isinstance(body, (dict, list)):
        body = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=300) as res:
            renewed = res.headers.get("token")
            if auth and renewed:
                write_private(TOKEN_FILE, renewed)
            data = res.read()
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace").strip()
        if e.code in (401, 403):
            raise MdtError(f"{method} {path} was refused ({e.code}): the login has expired, or this account may not change the dataset. " + login_hint())
        raise MdtError(f"{method} {path} failed with {e.code}" + (f": {detail[:500]}" if detail else ""))
    except urllib.error.URLError as e:
        raise MdtError(f"Could not reach {url}: {e.reason}")
    if raw:
        return data
    text = data.decode("utf-8", "replace")
    try:
        return json.loads(text) if text else None
    except ValueError:
        return text


def multipart(files):
    boundary = uuid.uuid4().hex
    parts = []
    for path in files:
        if not os.path.isfile(path):
            raise MdtError(f"No such file: {path}")
        name = os.path.basename(path)
        ctype = mimetypes.guess_type(name)[0] or "application/octet-stream"
        with open(path, "rb") as f:
            content = f.read()
        parts.append(
            f'--{boundary}\r\nContent-Disposition: form-data; name="tables"; filename="{name}"\r\n'
            f"Content-Type: {ctype}\r\n\r\n".encode("utf-8") + content + b"\r\n"
        )
    body = b"".join(parts) + f"--{boundary}--\r\n".encode("utf-8")
    return body, {"Content-Type": f"multipart/form-data; boundary={boundary}"}


def out(args, data, lines):
    if getattr(args, "json", False):
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print("\n".join(line for line in lines if line is not None))


def cmd_config(args):
    config = read_json_file(CONFIG_FILE, {})
    if args.base_url:
        config["base_url"] = args.base_url.rstrip("/")
        write_private(CONFIG_FILE, json.dumps(config, indent=2))
    print(f"API: {base_url()}\nWeb: {ui_url()}")


def cmd_login(args):
    if not sys.stdin.isatty():
        raise MdtError("login reads the password from the keyboard. " + login_hint())
    user = args.user or input("GBIF username: ")
    password = getpass.getpass("GBIF password: ")
    basic = base64.b64encode(f"{user}:{password}".encode("utf-8")).decode("ascii")
    res = request("POST", "/auth/login", headers={"Authorization": f"Basic {basic}"}, auth=False)
    token = (res or {}).get("token") if isinstance(res, dict) else None
    if not token:
        raise MdtError("The MDT did not return a token. Check the username and password.")
    write_private(TOKEN_FILE, token)
    print(f"Logged in to {base_url()} as {res.get('userName', user)}.")


def cmd_whoami(args):
    res = request("POST", "/auth/whoami")
    datasets = res.get("datasets") or []
    out(args, res, [f"Logged in as {res.get('userName')} at {base_url()}", f"{len(datasets)} datasets"])


def cmd_upload(args):
    body, headers = multipart(args.files)
    key = request("POST", "/dataset/upload", body=body, headers=headers)
    key = key.strip() if isinstance(key, str) else key
    remember_dataset(key)
    print(f"Uploaded {len(args.files)} files as dataset {key} (saved in {DATASET_FILE}).")
    print(f"Web: {ui_url()}/dataset/{key}/upload")
    print("Next: validate")


def cmd_add(args):
    key = dataset_key(args)
    body, headers = multipart(args.files)
    request("PUT", f"/dataset/{key}/upload", body=body, headers=headers)
    print(f"Added {len(args.files)} files to {key}. Next: validate")


def cmd_delete_file(args):
    key = dataset_key(args)
    request("DELETE", f"/dataset/{key}/file/{urllib.parse.quote(args.name, safe='')}")
    print(f"Deleted {args.name} from {key}. Next: validate")


def describe_errors(errors, indent="    "):
    lines = []
    for e in errors or []:
        message = e.get("message") if isinstance(e, dict) else str(e)
        lines.append(f"{indent}- {message}")
    return lines


def cmd_validate(args):
    key = dataset_key(args)
    report = request("GET", f"/validate/{key}")
    files = report.get("files") or {}
    lines = [f"Format: {files.get('format')}"]
    for f in files.get("files") or []:
        lines.append(f"  {f.get('name')}: {f.get('type') or 'not recognised'}")
        lines += describe_errors(f.get("errors"))
    if files.get("invalidErrors"):
        lines.append("Errors:")
        lines += describe_errors(files.get("invalidErrors"), "  ")
    if "samplesAsColumns" in files:
        lines.append(f"Samples are the OTU table's {'columns' if files.get('samplesAsColumns') else 'rows'}")
    if files.get("assayNames"):
        lines.append(f"FAIRe assays: {', '.join(files['assayNames'])}; selected: {files.get('selectedAssay') or 'none, choose one with `assay`'}")
    if files.get("sequencesAsHeaders"):
        lines.append("The OTU table's headers are DNA sequences")
    for label, field in (("Sample headers", "sampleHeaders"), ("Taxon headers", "taxonHeaders"), ("Study terms", "defaultValueTerms")):
        if report.get(field):
            lines.append(f"{label}: {', '.join(map(str, report[field]))}")
    if files.get("format") == "INVALID":
        lines.append("Next: fix the files, or assign roles with `file-types`, then validate again")
    else:
        lines.append("Next: mapping show")
    out(args, report, lines)


def cmd_file_types(args):
    key = dataset_key(args)
    assignment = json.loads(args.assignment) if args.assignment.strip().startswith("{") else read_json_file(args.assignment)
    request("POST", f"/dataset/{key}/file-types", body=assignment)
    print("File roles saved. Next: validate")


def cmd_assay(args):
    key = dataset_key(args)
    request("POST", f"/dataset/{key}/assay", body={"assay": args.name})
    print(f"Assay {args.name} selected. Next: validate")


def cmd_terms(args):
    res = request("GET", f"/terms/{args.kind}", auth=False)
    print(json.dumps(res, indent=2, ensure_ascii=False))


def cmd_enum(args):
    res = request("GET", f"/enum/{args.name}", auth=False)
    print(json.dumps(res, indent=2, ensure_ascii=False))


def current_report(key):
    return request("GET", f"/dataset/{key}/process")


def cmd_mapping(args):
    key = dataset_key(args)
    report = current_report(key)
    mapping = {k: v for k, v in (report.get("mapping") or {}).items() if k not in ("createdAt", "createdBy")}
    if args.action == "show":
        print(json.dumps(mapping, indent=2, ensure_ascii=False))
        return
    update = read_json_file(args.file)
    if update is None:
        raise MdtError(f"No such file: {args.file}")
    merged = dict(mapping)
    for section in ("samples", "taxa", "defaultValues", "measurements"):
        if section in update:
            merged[section] = {**(mapping.get(section) or {}), **(update.get(section) or {})}
        else:
            merged.setdefault(section, mapping.get(section) or {})
    request("POST", f"/dataset/{key}/mapping", body=merged)
    print("Mapping saved:")
    print(json.dumps(merged, indent=2, ensure_ascii=False))
    print("Next: process --wait")


def job_steps(key, job):
    if job == "process":
        return (current_report(key) or {}).get("steps") or []
    report = request("GET", f"/dataset/{key}/{'dwc' if job == 'dwc' else 'dwc-dp'}") or {}
    return (report.get(job) or {}).get("steps") or []


def wait_for(key, job, label):
    shown = set()
    while True:
        steps = job_steps(key, job)
        for i, step in enumerate(steps):
            if step.get("name") and step.get("status") in ("processing", "finished") and (i, step.get("status")) not in shown:
                shown.add((i, step.get("status")))
                print(f"  {step.get('name')}: {step.get('status')}", flush=True)
        last = steps[-1] if steps else {}
        if last.get("status") == "failed":
            message = last.get("message")
            raise MdtError(f"{label} failed{': ' + str(message) if message else ''}. See `log`, or {base_url()}/dataset/{key}/log.txt")
        if last.get("status") == "finished" and not last.get("name"):
            return
        time.sleep(POLL_SECONDS)


def cmd_process(args):
    key = dataset_key(args)
    query = "?skipSimiliarityPlots=true" if args.skip_plots else ""
    if args.assign_taxonomy:
        query += ("&" if query else "?") + "assignTaxonomy=true"
    request("POST", f"/dataset/{key}/process{query}")
    print(f"Processing started for {key}.")
    if args.wait:
        wait_for(key, "process", "Processing")
        print_status(args, key)
    else:
        print("Next: status, until processing has finished")


def print_status(args, key):
    report = current_report(key)
    steps = report.get("steps") or []
    last = next((s for s in reversed(steps) if s.get("status") != "pending"), {})
    lines = [
        f"Dataset {key}",
        f"Format: {(report.get('files') or {}).get('format')}",
        f"Processing: {last.get('name') or ''} {last.get('status') or 'not started'}".replace("  ", " "),
        f"Mapping ready: {report.get('mappingReady')}" + (f" (missing {', '.join(report.get('mappingMissing') or [])})" if report.get("mappingMissing") else ""),
        f"Metadata ready: {report.get('metadataReady')}" + (f" (missing {', '.join(report.get('metadataMissing') or [])})" if report.get("metadataMissing") else ""),
    ]
    for f in report.get("filesAvailable") or []:
        lines.append(f"  output: {f.get('format')} {f.get('fileName')}")
    for s in steps:
        if s.get("status") == "failed" or s.get("errors"):
            lines.append(f"  {s.get('name')}: {s.get('status')} {s.get('message') or ''}".rstrip())
    lines.append(f"Review in the browser: {ui_url()}/dataset/{key}/review")
    out(args, report, lines)


def cmd_status(args):
    print_status(args, dataset_key(args))


def cmd_summary(args):
    key = dataset_key(args)
    metrics = request("GET", f"/dataset/{key}/data/metrics", auth=False) or {}
    geo = request("GET", f"/dataset/{key}/data/geojson", auth=False) or {}
    invalid = (geo.get("metadata") or {}).get("errors") or []
    features = geo.get("features") or []
    scalar = {k: v for k, v in metrics.items() if isinstance(v, (int, float, str)) and not isinstance(v, bool)}
    lines = [f"{k}: {v}" for k, v in sorted(scalar.items())]
    for scope in ("geographicScope", "temporalScope"):
        if metrics.get(scope):
            lines.append(f"{scope}: {json.dumps(metrics[scope])}")
    lines.append(f"Samples on the map: {len(features)}; without valid coordinates: {len(invalid)}")
    if invalid:
        ids = [((i.get('properties') or {}).get('id')) if isinstance(i, dict) else i for i in invalid]
        lines.append("  " + ", ".join(map(str, ids[:30])) + (" ..." if len(ids) > 30 else ""))
    lines.append(f"Review in the browser: {ui_url()}/dataset/{key}/review")
    out(args, {"metrics": metrics, "invalidCoordinates": invalid}, lines)


def cmd_metadata(args):
    key = dataset_key(args)
    eml = read_json_file(args.file)
    if eml is None:
        raise MdtError(f"No such file: {args.file}")
    request("POST", f"/dataset/{key}/metadata", body=eml)
    print("Metadata saved.")
    print_status(args, key)


def build(args, path, job, label):
    key = dataset_key(args)
    request("POST", f"/dataset/{key}/{path}")
    print(f"{label} started for {key}.")
    if args.wait:
        wait_for(key, job, label)
        print(f"{label} finished. Download it from {ui_url()}/dataset/{key}/export")


def cmd_dwc(args):
    build(args, "dwc", "dwc", "Darwin Core Archive")


def cmd_dwc_dp(args):
    build(args, "dwc-dp", "dwcdp", "Darwin Core Data Package")


def cmd_uat(args):
    key = dataset_key(args)
    res = request("POST", f"/dataset/{key}/register-in-gbif-uat") or {}
    uat = (res.get("publishing") or {}).get("gbifUatDatasetKey")
    out(args, res, [f"Registered on the GBIF test site (UAT): https://www.gbif-uat.org/dataset/{uat}" if uat else "Registered on GBIF UAT; no dataset key in the response."])


def cmd_validator(args):
    key = dataset_key(args)
    res = request("POST", f"/dataset/{key}/data-validator") or {}
    vkey = res.get("key")
    out(args, res, [f"GBIF data validator report (ready when GBIF emails you): https://www.gbif.org/tools/data-validator/{vkey}" if vkey else "Submitted to the GBIF data validator; no key in the response."])


def cmd_publish(args):
    key = dataset_key(args)
    if not args.i_confirm:
        raise MdtError("Publishing to GBIF.org is public and is the researcher's decision. Run again with --i-confirm only after they have said so in their own words.")
    query = urllib.parse.urlencode({"organizationKey": args.organization})
    res = request("POST", f"/dataset/{key}/register-in-gbif-prod?{query}") or {}
    prod = (res.get("publishing") or {}).get("gbifProdDatasetKey")
    out(args, res, [f"Published: https://www.gbif.org/dataset/{prod}" if prod else "Submitted for publication; no dataset key in the response."])


def cmd_log(args):
    key = dataset_key(args)
    text = request("GET", f"/dataset/{key}/log.txt", auth=False, raw=True).decode("utf-8", "replace")
    print("\n".join(text.splitlines()[-args.lines:]))


def main(argv=None):
    p = argparse.ArgumentParser(prog="mdt.py", description="Drive the GBIF Metabarcoding Data Toolkit API.")
    p.add_argument("--dataset", help="dataset key; defaults to the one in ./mdt-dataset.json")
    p.add_argument("--json", action="store_true", help="print the raw response")
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("config", help="show or set the MDT installation")
    s.add_argument("--base-url", help=f"the API base URL, default {DEFAULT_BASE_URL}")
    s.set_defaults(fn=cmd_config)
    s = sub.add_parser("login", help="log in with a GBIF account; run it yourself, not through the agent")
    s.add_argument("--user")
    s.set_defaults(fn=cmd_login)
    sub.add_parser("whoami", help="check the login").set_defaults(fn=cmd_whoami)

    s = sub.add_parser("upload", help="create a dataset from files")
    s.add_argument("files", nargs="+")
    s.set_defaults(fn=cmd_upload)
    s = sub.add_parser("add", help="add or replace files in the dataset")
    s.add_argument("files", nargs="+")
    s.set_defaults(fn=cmd_add)
    s = sub.add_parser("delete-file", help="delete an uploaded file")
    s.add_argument("name")
    s.set_defaults(fn=cmd_delete_file)
    sub.add_parser("validate", help="detect the format and check the files").set_defaults(fn=cmd_validate)
    s = sub.add_parser("file-types", help='assign file roles: JSON or a JSON file, {"name.tsv": "otuTable|samples|taxa|defaultValues"}')
    s.add_argument("assignment")
    s.set_defaults(fn=cmd_file_types)

    s = sub.add_parser("assay", help="choose which FAIRe assay to process")
    s.add_argument("name")
    s.set_defaults(fn=cmd_assay)

    s = sub.add_parser("terms", help="list terms the MDT knows")
    s.add_argument("kind", choices=["required", "dwc", "defaultvalue"])
    s.set_defaults(fn=cmd_terms)
    s = sub.add_parser("enum", help="list allowed values")
    s.add_argument("name", choices=["format", "file-types", "license", "target-gene", "supported-markers", "agent-roles"])
    s.set_defaults(fn=cmd_enum)
    s = sub.add_parser("mapping", help="show the term mapping, or merge a JSON file into it")
    s.add_argument("action", choices=["show", "set"])
    s.add_argument("file", nargs="?")
    s.set_defaults(fn=cmd_mapping)

    s = sub.add_parser("process", help="convert the files")
    s.add_argument("--wait", action="store_true", help="wait until processing ends")
    s.add_argument("--skip-plots", action="store_true", help="skip the ordination plots, for large datasets")
    s.add_argument("--assign-taxonomy", action="store_true", help="assign taxonomy to the sequences with the installation's BLAST service")
    s.set_defaults(fn=cmd_process)
    sub.add_parser("status", help="where the dataset is, and what is missing").set_defaults(fn=cmd_status)
    sub.add_parser("summary", help="the processed data in numbers").set_defaults(fn=cmd_summary)
    s = sub.add_parser("log", help="the end of the processing log")
    s.add_argument("--lines", type=int, default=40)
    s.set_defaults(fn=cmd_log)
    s = sub.add_parser("metadata", help="save the dataset metadata (EML) from a JSON file")
    s.add_argument("file")
    s.set_defaults(fn=cmd_metadata)

    s = sub.add_parser("dwc", help="build the Darwin Core Archive")
    s.add_argument("--wait", action="store_true")
    s.set_defaults(fn=cmd_dwc)
    s = sub.add_parser("dwc-dp", help="build the Darwin Core Data Package")
    s.add_argument("--wait", action="store_true")
    s.set_defaults(fn=cmd_dwc_dp)
    sub.add_parser("uat", help="register the archive on the GBIF test site").set_defaults(fn=cmd_uat)
    sub.add_parser("validator", help="send the archive to the GBIF data validator").set_defaults(fn=cmd_validator)
    s = sub.add_parser("publish", help="publish on GBIF.org; only on the researcher's explicit word")
    s.add_argument("--organization", required=True, help="the publishing organization's GBIF key")
    s.add_argument("--i-confirm", action="store_true", help="the researcher has asked for publication")
    s.set_defaults(fn=cmd_publish)

    args = p.parse_args(argv)
    if args.command == "mapping" and args.action == "set" and not args.file:
        p.error("mapping set needs a JSON file")
    try:
        args.fn(args)
    except MdtError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
