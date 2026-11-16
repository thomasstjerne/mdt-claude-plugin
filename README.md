# mdt-claude-plugin

A [Claude Code](https://claude.com/claude-code) plugin for the GBIF [Metabarcoding Data Toolkit](https://mdt.gbif.org) (MDT). It helps a researcher get metabarcoding or eDNA data onto [GBIF](https://www.gbif.org): Claude reshapes their files (DADA2, QIIME 2, phyloseq, BIOM, FAIRe or spreadsheets) into an input the MDT accepts, then takes the dataset through the MDT's API — upload, validation, term mapping, processing, metadata, a Darwin Core Archive and a test publication on GBIF's test site — asking the researcher at every point only they can decide.

Status: early. Expect changes.

## Install

In Claude Code:

```text
/plugin marketplace add thomasstjerne/mdt-claude-plugin
/plugin install mdt@mdt-claude-plugin
```

Then ask Claude something like "Help me publish the eDNA data in this folder to GBIF with the MDT".

You need Python 3.8 or later, and a [GBIF account](https://www.gbif.org/user/profile) to log in to the MDT. Shaping DADA2 or phyloseq data needs R.

## What it contains

- `skills/mdt/SKILL.md`: the workflow Claude follows, in eight stages, and its rules: never invent a value, the researcher decides, the original files are never changed, and publishing on GBIF.org happens only on the researcher's word.
- `skills/mdt/references/`: the MDT's input formats, recipes for reshaping common formats, the dataset metadata, and the API.
- `skills/mdt/scripts/mdt.py`: a command-line client for the MDT API, standard library only. `python3 mdt.py --help` lists its commands; it works on its own too.

## Logging in

`mdt.py login` asks for your GBIF username and password and stores the MDT's login token in `~/.config/mdt/`, one per installation. Run it in a terminal window of your own, not through Claude, so the password never enters the conversation. The token is renewed with every request; log in again when it expires.

## What leaves your machine

- Claude reads your files to reshape them. Unless you run a local model, what it reads goes to the model provider.
- `mdt.py upload` and `add` send the files you name to the MDT installation you chose: `https://mdt.gbif.org` by default, one of the national or regional installations registered with GBIF (`mdt.py installations` lists them), another installation, or a local MDT at `http://localhost:9000` when testing. The choice is kept per folder, in `mdt-dataset.json`.
- `uat`, `validator` and `publish` ask the MDT to send the archive to GBIF.

## Feedback

Report problems with the plugin in this repository's issues, and problems with the MDT itself at [gbif/metabarcoding-data-toolkit-ui](https://github.com/gbif/metabarcoding-data-toolkit-ui/issues).

## License

Apache 2.0, as the MDT. See [LICENSE](LICENSE).
