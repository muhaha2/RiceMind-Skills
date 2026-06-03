# Evidence and Reporting Rules

## Confidence Tiers

High / Tier 1: curated or experimental evidence. Includes expert manual curation such as `Oryzabase_Curated` or `RAP-DB_Curated`, and explicit experimental codes such as `EXP`, `IDA`, and `IMP`.

Medium / Tier 2: verified literature plus computational or repeated NLP support. Use when associations lack Tier 1 evidence but have multidimensional support or more than 10 independent supporting articles.

Low / Tier 3: emerging, single-source, or limited-support associations. Use for broad exploration and hypothesis generation.

All: bypasses confidence filtering and retrieves the full evidence spectrum.

## Evidence Codes

Preserve original `Evidence_Code` values. Common RiceMind codes include:

`EXP`, `HEP`, `IBA`, `IC`, `IDA`, `IEA`, `IEP`, `IMP`, `ISS`, `TAS`, `Oryzabase_Curated`, `RAP-DB_Curated`, `NLP_Cooccurrence`.

Do not collapse `Evidence_Code` into confidence. Confidence is derived query-time metadata; evidence code is raw provenance.

## Mechanism Writing Discipline

Use these claim strengths:

- Tier 1 curated/experimental: "RiceMind curated/experimental evidence supports..."
- Tier 2 repeated NLP/literature: "RiceMind literature evidence repeatedly associates..." or "suggests a candidate relationship..."
- Tier 3 limited support: "RiceMind records an exploratory association..."
- NLP-only sentences: "co-reported", "mentioned with", or "literature-mined evidence links"; avoid "regulates", "causes", or "controls" unless the retrieved sentence explicitly says so.

Every mechanism claim must be backed by a PMID from RiceMind payloads:

`The retrieved RiceMind evidence suggests that GENE may participate in TRAIT-related processes through MECHANISM (PMID: 12345678; PMID: 23456789).`

If sentence evidence is contradictory or mechanistically weak, say so explicitly. Do not smooth over uncertainty.

## Fixed DOCX Template

Use `references/report-template.md` as the fixed structure for every generated report. At minimum, every report must include:

- Title with gene name, report date and retrieval completeness statement.
- "Data source, retrieval scope and completeness" section stating the API base URL, endpoints, page/limit strategy and API call log.
- Gene profile table.
- Top-20 trait landscape summary table, with a note that the full table is in `normalized_traits.csv`.
- Confidence-tier figure.
- Ontology distribution figure.
- Top traits by support figure.
- Evidence-code/source figures when available.
- Publication-year trend figure when years are available.
- Mechanism synthesis section with bracket-style PMID markers such as `[12345678, 23456789]`.
- No full evidence sentence table in the DOCX body. Preserve all evidence in `normalized_evidence.csv`.
- Caveats section distinguishing curated evidence from NLP co-occurrence.

## Recommended Sidecar Files

When the report is selective, save complete normalized evidence to sidecar files:

- `<gene>_normalized_traits.csv`
- `<gene>_normalized_evidence.csv`
- `<gene>_payload.json`

This keeps the DOCX readable while preserving full RiceMind traceability.

## Full Retrieval Requirement

For gene reports, do not use a first-page-only API response. Use explicit `page` and `limit` parameters and retrieve all pages from:

- `/traits-by-gene/`
- `/search-by-trait-and-gene/` for every returned trait
- `/search-by-gene/`
- `/varieties-by-gene/`

If a user imposes a cap or an endpoint fails, record the cap or failure in the report's first section and preserve the partial payload.
