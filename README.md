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

Log in to the MDT's web pages with your GBIF account and create an API token on your profile page (`https://mdt.gbif.org/user-profile/api-tokens`, or the same page on another installation), with a lifetime of 1, 7 or 30 days. Then run `mdt.py login` in a terminal window of your own, not through Claude, and paste the token there, so it never enters the conversation. It is stored in `~/.config/mdt/`, one per installation. The token gives access to your datasets on that MDT only, and nothing else of your GBIF account. It ends when it expires, when you revoke it on the profile page, or when the MDT restarts; then create a new one and log in again.

The GBIF data validator runs as your GBIF account. When the MDT asks you to log in to GBIF again for it, run `mdt.py gbif-login`, also in your own terminal, and enter your GBIF password.

On an MDT installation whose profile page has no API tokens yet, `mdt.py login --password` logs in with your GBIF username and password instead.

## What leaves your machine

- Claude reads your files to reshape them. Unless you run a local model, what it reads goes to the model provider.
- `mdt.py upload` and `add` send the files you name to the MDT installation you chose: `https://mdt.gbif.org` by default, one of the national or regional installations registered with GBIF (`mdt.py installations` lists them), another installation, or a local MDT at `http://localhost:9000` when testing. The choice is kept per folder, in `mdt-dataset.json`.
- `test`, `validator` and `publish` ask the MDT to send the archive to GBIF.

## Feedback

Report problems with the plugin in this repository's issues, and problems with the MDT itself at [gbif/metabarcoding-data-toolkit-ui](https://github.com/gbif/metabarcoding-data-toolkit-ui/issues).

## License

Apache 2.0, as the MDT. See [LICENSE](LICENSE).
