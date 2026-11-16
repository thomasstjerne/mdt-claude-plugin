# Shaping recipes

Each recipe writes the plain text-file input: `otu_table.tsv`, `samples.tsv`, `taxonomy.tsv` and, when there are study values, `study.tsv`, all tab-separated UTF-8. Write them into a new folder and leave the originals alone. Adapt to the actual files: these show the shape, not every case.

Whatever the source, before you upload, check:

- the OTU table's sample ids and the `samples.tsv` ids are the same set, spelled the same
- the OTU table's OTU/ASV ids and the `taxonomy.tsv` ids are the same set
- counts are whole numbers, and blanks are empty, not `NA` or `0` (unless the count is 0)
- dates are ISO 8601 (`2021-06-14`), coordinates are decimal degrees with a `.` decimal mark

## DADA2 (R)

DADA2 gives a sequence table (`seqtab`, samples as rows, sequences as column names) and, from `assignTaxonomy`/`addSpecies`, a taxonomy matrix with one row per sequence. Give each sequence a short id rather than using the sequence as the id:

```r
seqs <- colnames(seqtab.nochim)
ids <- paste0("ASV_", seq_along(seqs))

otu <- t(seqtab.nochim)                     # sequences as rows, samples as columns
rownames(otu) <- ids
write.table(data.frame(id = ids, otu, check.names = FALSE),
            "mdt-input/otu_table.tsv", sep = "\t", quote = FALSE, row.names = FALSE)

tax <- as.data.frame(taxa[seqs, , drop = FALSE])   # Kingdom, Phylum, ... from assignTaxonomy
names(tax) <- tolower(names(tax))                  # kingdom, phylum, class, order, family, genus, species
write.table(data.frame(id = ids, DNA_sequence = seqs, tax, check.names = FALSE),
            "mdt-input/taxonomy.tsv", sep = "\t", quote = FALSE, row.names = FALSE, na = "")
```

`species` from `addSpecies` is the epithet only; map it in Stage 4, or build a binomial from genus and species in the script, and say which you did. Samples come from the researcher's own sample sheet; its id column must match the sample names DADA2 used.

## QIIME 2

Export the artifacts:

```bash
qiime tools export --input-path table.qza --output-path export      # export/feature-table.biom
qiime tools export --input-path taxonomy.qza --output-path export   # export/taxonomy.tsv
qiime tools export --input-path rep-seqs.qza --output-path export   # export/dna-sequences.fasta
```

These can be uploaded as they are, as BIOM 2.1, with the sample metadata as `samples.tsv`. Two things to handle:

- QIIME 2 metadata files may have a second row starting `#q2:types`. Remove it, or the MDT reads it as a sample.
- `taxonomy.tsv` has one `Taxon` column with the whole classification (`d__Bacteria; p__Proteobacteria; ...` or `Eukaryota;Chordata;...`). The MDT doesn't split it. Map it to `verbatimIdentification`, and better, write a taxonomy file in the script with the ranks split into `kingdom` ... `species`, prefixes like `p__` removed, and the `Confidence` column kept.

Without QIIME 2 installed, a `.qza` is a zip: `data/` inside it holds the same files.

## phyloseq (R)

```r
library(phyloseq)
otu <- as(otu_table(ps), "matrix")
if (!taxa_are_rows(ps)) otu <- t(otu)
write.table(data.frame(id = rownames(otu), otu, check.names = FALSE),
            "mdt-input/otu_table.tsv", sep = "\t", quote = FALSE, row.names = FALSE)

tax <- as.data.frame(as(tax_table(ps), "matrix"))
names(tax) <- tolower(names(tax))
seqs <- if (!is.null(refseq(ps, errorIfNULL = FALSE))) as.character(refseq(ps))[rownames(tax)] else NA
write.table(data.frame(id = rownames(tax), DNA_sequence = seqs, tax, check.names = FALSE),
            "mdt-input/taxonomy.tsv", sep = "\t", quote = FALSE, row.names = FALSE, na = "")

sam <- as(sample_data(ps), "data.frame")
write.table(data.frame(id = rownames(sam), sam, check.names = FALSE),
            "mdt-input/samples.tsv", sep = "\t", quote = FALSE, row.names = FALSE, na = "")
```

If the taxa names are the sequences themselves, use them as `DNA_sequence` and give short ids as in the DADA2 recipe.

## A wide spreadsheet

A common layout is one sheet with OTU id, taxonomy, sequence and one count column per sample. Split it by column: the counts with the id go to `otu_table.tsv`; the id, sequence and taxonomy to `taxonomy.tsv`. Sample data from another sheet or file goes to `samples.tsv`. Read with pandas (`pd.read_excel(path, sheet_name=None)` gives every sheet), and keep cells as text where leading zeros or long ids matter (`dtype=str`).

Watch for: summary rows or columns (totals, "unassigned" bins) that aren't OTUs or samples; merged header cells; several markers in one sheet (one upload per marker); and controls, which stay in only if the researcher wants them published.
