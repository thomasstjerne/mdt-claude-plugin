# The MDT API, as mdt.py uses it

The default installation is `https://mdt.gbif.org/service` (web: `https://mdt.gbif.org`). `mdt.py installations` lists the others registered with GBIF (`GET https://api.gbif.org/v1/installation?type=MDT_INSTALLATION`): each one's `FEED` endpoint is its RSS feed, and the API is the `/service` path of that address. `mdt.py use <url or key>` sets the installation for the current folder, and `upload` records it in `mdt-dataset.json` with the dataset key, so every later command in that folder goes to the same MDT. A local MDT for testing is `http://localhost:9000` (web: `http://localhost:3000`). `--base-url` or `MDT_BASE_URL` override it for one command; `config --set-default <url>` changes the default for folders without one. Login tokens are kept per installation.

Authentication is an API token the researcher creates on their profile page in the MDT (`<web>/user-profile/api-tokens`), with a lifetime of 1, 7 or 30 days. `login` reads it from the keyboard, checks it with `POST /auth/whoami`, and stores it in `~/.config/mdt/tokens.json`, one per installation. Every later request sends it as `Authorization: Bearer <token>`. An API token is not renewed, and ends when it expires, when it is revoked on the profile page, or when the MDT restarts. A 401 means the token is no longer valid: the researcher creates a new one and logs in again. A 403 means the account may not change this dataset.

`login --password` is for an MDT whose profile page has no API tokens (an older version): it posts the GBIF username and password once, as HTTP Basic, to `/auth/login`, and each authenticated response returns a renewed token in its `token` header, which `mdt.py` stores.

The data validator runs as the researcher's GBIF account, with the GBIF login the MDT kept from their last password login in the web interface, which lasts about 30 minutes. When it has expired, the MDT answers `401 {"error": "gbif-login-required"}`. `gbif-login` then posts the GBIF username and password as HTTP Basic to `/auth/gbif-login`, with the MDT token in `X-MDT-Token: Bearer <token>`, and the request can be repeated.

| Command | Request | Notes |
|---|---|---|
| `login` | `POST /auth/whoami` with the pasted token; with `--password`, `POST /auth/login` | |
| `gbif-login` | `POST /auth/gbif-login`, Basic auth and `X-MDT-Token` | 204; 403 when the password is wrong or the account isn't the one logged in to the MDT |
| `upload` | `POST /dataset/upload`, multipart, field `tables` per file | returns the dataset key as plain text; at most 50 files |
| `add` | `PUT /dataset/{key}/upload` | adds or replaces files |
| `delete-file` | `DELETE /dataset/{key}/file/{name}` | |
| `validate` | `GET /validate/{key}` | `files.format`, `files.files[]` with `name`, `type`, `errors`; `files.invalidErrors`; `sampleHeaders`, `taxonHeaders`, `defaultValueTerms` |
| `file-types` | `POST /dataset/{key}/file-types` | `{"file name": "otuTable" \| "samples" \| "taxa" \| "defaultValues"}` |
| `assay` | `POST /dataset/{key}/assay`, `{"assay": name}` | FAIRe only; the assays are in `validate`'s `files.assayNames` |
| `terms` | `GET /terms/required`, `/terms/dwc`, `/terms/defaultvalue` | public |
| `enum` | `GET /enum/{name}` | public: `format`, `license`, `target-gene`, `supported-markers`, ... |
| `mapping` | `GET /dataset/{key}/process` (`.mapping`), `POST /dataset/{key}/mapping` | the POST replaces the whole mapping; `mapping set` merges first |
| `process` | `POST /dataset/{key}/process[?skipSimiliarityPlots=true][&assignTaxonomy=true]` | 302 if a job is already running |
| `status` | `GET /dataset/{key}/process` | `steps[]` (the job is done when the last step is `{"status": "finished"}` without a `name`; `failed` otherwise), `mappingReady`/`mappingMissing`, `metadataReady`/`metadataMissing`, `filesAvailable` |
| `summary` | `GET /dataset/{key}/data/metrics`, `/data/geojson` | public; the geojson's `metadata.errors` are the samples without valid coordinates |
| `log` | `GET /dataset/{key}/log.txt` | |
| `metadata` | `POST /dataset/{key}/metadata` | the EML as JSON; see `metadata.md` |
| `doi` | `GET https://api.crossref.org/works/{doi}`, then `GET https://api.datacite.org/dois/{doi}` | not the MDT; public, no login. Writes a draft, sends nothing to the MDT |
| `dwc` | `POST /dataset/{key}/dwc`; progress in `GET /dataset/{key}/dwc` (`.dwc.steps`) | refused while the metadata is incomplete |
| `dwc-dp` | `POST /dataset/{key}/dwc-dp`; progress in `GET /dataset/{key}/dwc-dp` (`.dwcdp.steps`) | |
| `test` | `POST /dataset/{key}/register-in-gbif-uat` | `publishing.gbifUatDatasetKey`; the dataset is then at `https://www.gbif-test.org/dataset/{key}`. The API's names still say UAT, GBIF's former name for the test site |
| `validator` | `POST /dataset/{key}/data-validator` | `key` of the GBIF data validator report; `401 gbif-login-required` when the MDT needs `gbif-login` |
| `publish` | `POST /dataset/{key}/register-in-gbif-prod?organizationKey={org}` | `publishing.gbifProdDatasetKey` |

The web pages for a dataset are `<web>/dataset/{key}/` followed by `upload`, `term-mapping`, `process`, `review`, `metadata`, `export` or `publish`. A researcher can switch between the API and the web pages at any point; they work on the same dataset.
