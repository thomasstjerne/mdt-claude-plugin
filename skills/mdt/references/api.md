# The MDT API, as mdt.py uses it

The default installation is `https://mdt.gbif.org/service` (web: `https://mdt.gbif.org`). `mdt.py use <url>` sets the installation for the current folder, and `upload` records it in `mdt-dataset.json` with the dataset key, so every later command in that folder goes to the same MDT. A local MDT for testing is `http://localhost:9000` (web: `http://localhost:3000`). `--base-url` or `MDT_BASE_URL` override it for one command; `config --set-default <url>` changes the default for folders without one. Login tokens are kept per installation.

Authentication is a GBIF account. `login` posts the username and password once, as HTTP Basic, to `/auth/login` and stores the returned token in `~/.config/mdt/token`. Every later request sends it as `Authorization: Bearer <token>`, and each authenticated response returns a renewed token in its `token` header, which `mdt.py` stores. A 401 or 403 means the token expired (log in again), or the account may not change this dataset.

| Command | Request | Notes |
|---|---|---|
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
| `dwc` | `POST /dataset/{key}/dwc`; progress in `GET /dataset/{key}/dwc` (`.dwc.steps`) | refused while the metadata is incomplete |
| `dwc-dp` | `POST /dataset/{key}/dwc-dp`; progress in `GET /dataset/{key}/dwc-dp` (`.dwcdp.steps`) | |
| `uat` | `POST /dataset/{key}/register-in-gbif-uat` | `publishing.gbifUatDatasetKey` |
| `validator` | `POST /dataset/{key}/data-validator` | `key` of the GBIF data validator report |
| `publish` | `POST /dataset/{key}/register-in-gbif-prod?organizationKey={org}` | `publishing.gbifProdDatasetKey` |

The web pages for a dataset are `<web>/dataset/{key}/` followed by `upload`, `term-mapping`, `process`, `review`, `metadata`, `export` or `publish`. A researcher can switch between the API and the web pages at any point; they work on the same dataset.
