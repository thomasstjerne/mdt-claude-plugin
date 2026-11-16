# Dataset metadata (EML)

`mdt.py metadata eml.json` saves the dataset's metadata. The MDT requires:

| Field | What |
|---|---|
| `title` | a descriptive title: what, where, when, how |
| `license` | one of `mdt.py enum license`: `CC0`, `CC-BY` or `CC-BY-NC`. GBIF publishes only these. It is the researcher's choice; explain the difference if they ask, never pick one. |
| `description` | the abstract: what was sampled, where, when, how, and what the data is for |
| `contact` | one person, with `electronicMailAddress` |
| `creator` | a list of people who created the dataset |

A person is an object:

```json
{"givenName": "Ana", "surName": "Silva", "organizationName": "Example University",
 "electronicMailAddress": "ana.silva@example.org", "userId": "0000-0002-1825-0097",
 "positionName": "", "phone": "", "deliveryPoint": "", "city": "", "administrativeArea": "", "country": "PT"}
```

`userId` is an ORCID iD, if they have one; `country` is a two-letter code. Leave a field empty rather than guess it.

A minimal `eml.json`:

```json
{
  "title": "Fish eDNA from coastal sites in ...",
  "license": "CC-BY",
  "description": "...",
  "contact": {"givenName": "...", "surName": "...", "electronicMailAddress": "..."},
  "creator": [{"givenName": "...", "surName": "...", "electronicMailAddress": "..."}]
}
```

The MDT has more fields. These can go in `eml.json` too:

| Field | What |
|---|---|
| `samplingDescription`, `studyExtent` | text |
| `keywords` | a list of strings |
| `project` | an object: `{"title": "...", "identifier": "...", "funding": "...", "description": "..."}`. The web form shows these as Project Title, Project Funding and so on, but the API takes only the object; top-level `projectTitle` or `projectFunding` are silently dropped. |
| `bibliographicReferences` | a list of `{"key": "<DOI without https://doi.org/>", "value": "<full citation>"}` |

For the others, such as method steps and associated parties, give the researcher the metadata form link (`<web>/dataset/<key>/metadata`) and let them fill them in there; it shows each field's help text. The MDT fills the geographic, temporal and taxonomic coverage from the data.

Take values from the researcher's documents where they exist, say which document, and have them confirm. Never write a person, email, ORCID iD, licence or funding source that no document gives and they haven't told you.

## From a DOI

`mdt.py doi <DOI>` looks the DOI up in CrossRef (journal articles), then DataCite (datasets on Zenodo, Dryad, Figshare and the like), and writes a draft to `eml-from-doi.json`: `title`, `description` (the abstract), `creator` (with affiliation and ORCID iD where the record has them), `project.funding`, and the publication in `bibliographicReferences`. It is a draft, not the `eml.json`:

- The title and abstract describe the publication. Propose a dataset title and description built from them, with what the dataset holds (marker, samples, place, dates), and have the researcher confirm.
- The authors of a paper are not always the creators of the dataset. Ask.
- A DOI record has no contact and no e-mail addresses, and affiliations and ORCID iDs are often missing. Ask for these rather than reading them from a web page.
- The licence it prints is the publication's, not the data's. Mention it, but the data licence is still the researcher's choice.
- The DOI record holds no methods, coordinates or study values. Those come from the paper's text, with the researcher's confirmation.
