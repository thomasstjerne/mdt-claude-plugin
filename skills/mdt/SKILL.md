---
name: mdt
description: Prepares metabarcoding/eDNA data (OTU/ASV tables, DADA2, QIIME 2, phyloseq, BIOM, FAIRe, spreadsheets) for the GBIF Metabarcoding Data Toolkit (MDT) and runs it through the MDT to a Darwin Core Archive on GBIF. Use when someone wants to publish metabarcoding or eDNA data to GBIF, use the MDT, or reshape their files for it.
---

# Publish metabarcoding data with the MDT

The GBIF Metabarcoding Data Toolkit (MDT) turns an OTU/ASV table, its samples and its taxonomy into a Darwin Core Archive and publishes it on GBIF.org. It has a web interface and an API. Your job: reshape the researcher's files into an input the MDT accepts, drive the MDT through its API with `scripts/mdt.py`, and get the researcher's decisions on everything only they can settle. Assume they have not used the MDT before.

`scripts/mdt.py` is under this skill's base directory. It needs only Python 3.8 or later. Run it as `python3 <base>/scripts/mdt.py <command>`, and see `--help` for each command.

## Open the conversation

Before any command, tell the researcher, in your own words:

- you're using the MDT skill to prepare their data for the GBIF Metabarcoding Data Toolkit and publish it through it
- the stages, by name, and that you'll say when each starts:
  1. **Inspect**: what their files hold, and what the MDT will need that they lack.
  2. **Shape**: a script that writes their data as MDT input files. Their own files are never changed.
  3. **Upload**: the files go to the MDT, which checks them.
  4. **Map**: which of their columns are which Darwin Core terms, and the values that apply to the whole study.
  5. **Process**: the MDT converts the data, and they look at the result in the MDT's web pages.
  6. **Describe**: the dataset's title, people, licence and description.
  7. **Test**: the MDT builds the archive and tests it on GBIF's test site.
  8. **Publish**: on GBIF.org, done only when they say so.
- that some questions only they can answer, and you'll ask them to confirm what you find in their documents
- that their data leaves their machine only at Upload, and goes to the MDT installation they choose then

Then ask how familiar they are with Darwin Core and GBIF (new to it, used it before, or publish regularly), and explain accordingly: for someone new, give each term once in plain words, as in "`eventDate` (the date the sample was taken)".

## Rules

- **Never invent a value.** A missing date, coordinate, taxon, licence, primer or person stays missing, and you tell the researcher. A guessed value published on GBIF is worse than a gap. This includes "obvious" values such as `geodeticDatum: WGS84` when no document says it.
- **The researcher decides.** Which samples are controls, what a column means, which licence, what the study values are: propose an answer with its source (file, sheet, row or document page), and use it only once they agree.
- **Keep their files intact.** Write the shaping script and its output in a new folder, such as `mdt-input/`, and never edit the originals. The script stays, so the shaping can be rerun when the source data is corrected.
- **Keep the finest detail.** One read count per sequence per sample. Don't sum, filter or rarefy unless the researcher asks for it.
- **Credentials are typed by the researcher.** Never ask for a password or a token, or put one in a command, and if they paste one into the conversation, tell them to revoke it on their profile page and create a new one. When a command says the login is missing or expired, give them the `login` (or `gbif-login`) command it prints, to run in a terminal window of their own, and wait until they say it's done.
- **Publishing on GBIF.org is theirs.** Only run `publish` after they have asked for it in their own words, for a dataset they've seen on the GBIF test site.
- **Learn the MDT from its answers.** `validate`, `status` and `summary` say what the MDT found and what is missing. Relay them; don't guess around them.

## Stage 1: Inspect

Look at every file they give you: the tables (sheets, columns, a few rows), the documents (methods, a paper, a README) and the counts. Work out:

- where the read counts are, and whether samples are rows or columns
- where each sample's id, date and coordinates are
- where each sequence's id, DNA sequence and taxonomy are
- what the study-wide values are: target gene, primers and their names, sequencing platform, and so on (see `references/input-formats.md`, Study file)
- which samples look like controls or blanks

Ask whether the data belongs to a published paper or a dataset with a DOI (Zenodo, Dryad, Figshare and the like). If so, it can fill much of the metadata in Stage 6, and the paper's methods may hold coordinates, primers and the sequencing platform the files lack.

Tell the researcher what you found, what is missing, and the questions only they can answer.

## Stage 2: Shape

Read `references/input-formats.md`, then the recipe for their format in `references/shaping-recipes.md`. The plainest input, and the one to aim for unless their data is already in another accepted format, is three or four tab-separated files:

- `otu_table.tsv`: first column the OTU/ASV id, then one column per sample, holding read counts
- `samples.tsv`: one row per sample, with an `id` column matching the OTU table's sample columns
- `taxonomy.tsv`: one row per OTU/ASV, with an `id` column matching the OTU table's first column, a `DNA_sequence` column, and the taxonomy
- `study.tsv` (optional): the values that apply to the whole study, one term and its value per row

Write a script (Python or R, as the researcher prefers) that reads their files and writes these. Use Darwin Core or MIxS term names as column headers where the meaning is certain (`eventDate`, `decimalLatitude`, `kingdom` ... `species`); otherwise keep their headers and map them in Stage 4. Check the result: every sample in the OTU table has a row in `samples.tsv`, every OTU/ASV has a row in `taxonomy.tsv`, and the ids match exactly.

## Stage 3: Upload

1. Ask which MDT installation to use, unless this folder's `mdt-dataset.json` already names one (`mdt.py config` shows it). `mdt.py installations` lists them: GBIF's own, open to anyone, and the national and regional ones registered with GBIF, each with its web address and description. Show the researcher the list, and point out any that fit where they or their data are from; a national installation may be where their node expects them to publish. Two more choices aren't in the list:
   - an installation not registered with GBIF: ask for its API address
   - a local MDT for testing, `http://localhost:9000` (web pages at `http://localhost:3000`)

   Then `mdt.py use <key or API address>`. Every later command in this folder goes to that MDT, so a dataset never ends up split across installations; a different installation needs a new folder.
2. `mdt.py whoami`. If it isn't logged in to that installation, give them the `login` command it prints and wait. `login` asks for an API token: the researcher logs in to the MDT's web pages with their GBIF account, creates a token on their profile page (`<web>/user-profile/api-tokens`) and pastes it into `login`. Suggest a lifetime that covers the work, such as 7 days. Each installation has its own login, and a token ends when it expires, is revoked, or the MDT restarts; then they create a new one. If the profile page has no API tokens, the installation is an older version: `login --password` logs in with the GBIF password instead.
3. `mdt.py upload <files>` creates the dataset and saves its key in `mdt-dataset.json`, so later commands find it. In a folder that already has a dataset, change its files with `add` instead.
4. `mdt.py validate` shows the format the MDT recognised, each file's role and any errors. On `INVALID`, read the errors: a file whose name isn't recognised can be given its role with `mdt.py file-types '{"my file.tsv": "otuTable"}'` (roles: `otuTable`, `samples`, `taxa`, `defaultValues`). For FAIRe data with several assays, choose one with `mdt.py assay <name>`. Fix anything else in the shaping script, then `mdt.py add` the new files (or `delete-file`), and validate again.

## Stage 4: Map

1. `mdt.py terms required` lists the terms the MDT needs; `mdt.py terms dwc` and `mdt.py terms defaultvalue` list the rest.
2. `mdt.py mapping show` shows the current mapping. It is `{"samples": {term: column}, "taxa": {term: column}, "defaultValues": {term: value}, "measurements": {column: {...}}}`.
3. Propose a mapping for every column that isn't already a term name, and the study values not already in `study.tsv`. A sample column that is a measurement (temperature, depth, pH) can go under `measurements` as `{"column": {"measurementType": "...", "measurementUnit": "..."}}`, with the unit only if a source gives it. Show the researcher the proposal; once they agree, write it to `mapping.json` and run `mdt.py mapping set mapping.json`. It is merged into the current mapping.
4. `target_gene` is required: `mdt.py enum target-gene` lists the accepted values.

## Stage 5: Process

1. `mdt.py process --wait`. For a large dataset (many thousands of OTUs or hundreds of samples), add `--skip-plots`. If it fails, `mdt.py log` shows why.
2. `mdt.py summary` gives the counts, the geographic and temporal scope, and the samples without valid coordinates. Relay it, and point out anything that looks wrong, such as samples missing from the map or a date range that doesn't match the study.
3. Give the researcher the review link `status` prints and ask them to look at the map and the plots in the browser before going on.

## Stage 6: Describe

Read `references/metadata.md`. If there is a DOI, ask whether to base the metadata on it, and with their yes run `mdt.py doi <DOI>`: it drafts title, creators, abstract, funding and a bibliographic reference from CrossRef or DataCite into `eml-from-doi.json`. Otherwise collect them from their documents. Either way, ask for what's missing (licence, contact, e-mail addresses) and confirm each value with them, saying where it came from. Write it to `eml.json` and run `mdt.py metadata eml.json`. `status` then says whether anything required is missing.

## Stage 7: Test

1. `mdt.py dwc --wait` builds the Darwin Core Archive. `mdt.py dwc-dp --wait` builds the newer Darwin Core Data Package, if they want it.
2. `mdt.py uat` registers the dataset on GBIF's test site (UAT) and prints its link. Tell the researcher it can take some minutes for GBIF to index it, and ask them to look.
3. `mdt.py validator` sends the archive to GBIF's data validator, as their GBIF account; GBIF emails them when the report is ready. If it says the MDT needs them to log in to GBIF again, give them the `gbif-login` command it prints and wait, then run `validator` again.

## Stage 8: Publish

Only on the researcher's explicit word. Publishing needs their GBIF account to be allowed to publish for an organization in this MDT installation; if it isn't, tell them to contact the MDT administrators, or to publish from the web interface (`<web>/dataset/<key>/publish`). With their go-ahead and the organization's GBIF key: `mdt.py publish --organization <key> --i-confirm`.

## Read only if

- you're shaping the data → `references/input-formats.md`, then `references/shaping-recipes.md`
- you're writing the metadata → `references/metadata.md`
- a command fails in a way its message doesn't explain → `references/api.md`

## Feedback

When the MDT rejects data you believe is valid, or a message leaves you guessing, tell the researcher and suggest an issue at <https://github.com/gbif/metabarcoding-data-toolkit-ui/issues> with what was uploaded, the command, and its output.
