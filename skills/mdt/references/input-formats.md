# MDT input formats

The MDT works out the format from the uploaded files; `mdt.py validate` reports it. Every format describes the same things:

- **OTU table**: read counts, one axis for samples and one for OTUs/ASVs.
- **Samples**: one row per sample, with an id matching the OTU table's sample ids.
- **Taxonomy**: one row per OTU/ASV, with an id matching the OTU table's ids, and the DNA sequence unless a fasta file supplies it.
- **Study** (optional, also called defaults): values that apply to the whole dataset, such as `target_gene` or the primers.

## How the format is chosen

Checked in this order; the first match decides:

1. **FAIRe**, if any non-`.xlsx` file name starts with a FAIRe component (`projectMetadata_`, `sampleMetadata_`, `experimentRunMetadata_`, `otuFinal_`, `taxaFinal_`, `otuRaw_`, `taxaRaw_`, `ampData_`, `stdData_`, `eLowQuantData_`), or an `.xlsx` has sheets named for FAIRe components. One such file is enough, so never name an ordinary file `sampleMetadata_x.tsv`.
2. **BIOM 2.1**, if any file is HDF5 (by content).
3. **Excel workbook**, if there are fewer than three files and one is `.xlsx`. All tables then come from the workbook; another file is ignored unless it is fasta.
4. **Text files**, if at least two files end in lower-case `.tsv`, `.csv` or `.txt`.

Anything else is `INVALID`.

## File and sheet names

A name is lower-cased, its extension dropped and everything but letters and digits removed. It must then equal one of:

| Role | Names |
|---|---|
| OTU table | `otutable`, `asvtable`, `featuretable`, `matrix`, `table` |
| Samples | `samples`, `sample`, `sampletable`, `sites`, `site`, `metadata` |
| Taxonomy | `taxonomy`, `taxa`, `taxon`, `taxontable`, `taxonomytable`, `observations`, `observation` |
| Study | `study`, `defaults`, `default`, `defaultvalues` |

`otu_table.tsv` and `ASV-table.csv` are recognised; `MyProject_ASVtable.tsv` is not. Name the files you write accordingly. A file with another name can be given its role with `mdt.py file-types`; a workbook sheet cannot, so sheets must be named this way.

## Text files

`.tsv`, `.csv` or `.txt`; tab, comma, semicolon or pipe delimited (detected per file). Use tab-separated UTF-8 when you write them. The OTU table and samples are required. The taxonomy can be its own file, columns in the OTU table next to the counts (only when samples are the columns), or come from a fasta file. The OTU table can have samples as columns or as rows; the MDT works it out from the sample ids.

When the OTU table has samples as rows, its column headers can be the DNA sequences themselves (more than 75 nucleotide letters); the MDT then makes each ASV's id from a hash of its sequence. The header row needs a field for the sample-name column.

## Excel workbook

One `.xlsx` with OTU table and samples sheets, and a taxonomy sheet unless the taxonomy is in the OTU table sheet. Samples must be the OTU table sheet's columns. A study sheet is optional. Plus an optional fasta file.

## BIOM 2.1

A BIOM 2.1 (HDF5) file with the counts. Only the matrix and its ids are read, so the samples, and the taxonomy or a fasta file, come as separate files. BIOM 1.0 (JSON) is not supported; convert with `biom convert --to-hdf5`. For a BIOM upload the taxonomy's id column can be `Feature ID`, as QIIME 2 exports it.

## FAIRe

A dataset following the FAIRe eDNA standard (https://fair-edna.github.io/), as a workbook with sheets `projectMetadata`, `sampleMetadata`, `experimentRunMetadata`, `otuFinal_<assay>_<run>`, `taxaFinal_<assay>_<run>`, or as flat files named `<component>_<project>[_<assay>_<run>].tsv`, or both. `otuFinal` is required. One assay is processed per upload; with several, the MDT asks which. If the data is already FAIRe, upload it as it is.

## Ids

The samples table should have a column named `id`; otherwise the first column is used, with a warning. The same goes for the taxonomy. Ids must match the OTU table exactly, including case and spaces.

## Fasta

`.fasta`, `.fa` or `.fas`. Each record's id is the text after `>` up to the first space, and must match an OTU/ASV id.

## Study file

A header row, then one term and its value per row:

```text
term	value
target_gene	12S rRNA
pcr_primer_forward	GTCGGTAAAACTCGTGCCAGC
pcr_primer_name_forward	MiFish-U-F
```

A term in the study file takes the place of the same column in the samples table in the archive. The same values can instead be given in the mapping's `defaultValues` (Stage 4), which overrides the study file.

## Zip

Any upload can be a `.zip`; folders are flattened, and files that aren't text, `.xlsx` or HDF5 are dropped without warning.
