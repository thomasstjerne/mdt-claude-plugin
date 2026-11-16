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

The MDT has more fields, such as method steps, sampling description, study extent, keywords, project details, funding, associated parties and bibliographic references. Simple text ones (`samplingDescription`, `studyExtent`, `projectTitle`, `projectFunding`) can go in `eml.json` as strings. For the others, give the researcher the metadata form link (`<web>/dataset/<key>/metadata`) and let them fill them in there; it shows each field's help text. The MDT fills the geographic, temporal and taxonomic coverage from the data.

Take values from the researcher's documents where they exist, say which document, and have them confirm. Never write a person, email, ORCID iD, licence or funding source that no document gives and they haven't told you.
