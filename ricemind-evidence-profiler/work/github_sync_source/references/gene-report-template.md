# Gene Full Evidence Report Template

Use this template for `gene_report` tasks. The integrated script is `scripts/build_gene_report.py`.

## Required Output

Default formal output is a DOCX report plus sidecars:

- `{gene}_RiceMind_gene_mechanism_report.docx`
- sibling `{gene}_RiceMind_gene_mechanism_report_data/`
- `{gene}_RiceMind_gene_mechanism_report_data/{gene}_RiceMind_gene_mechanism_report_payload.json`
- `{gene}_RiceMind_gene_mechanism_report_data/{gene}_RiceMind_gene_mechanism_report_normalized_traits.csv`
- `{gene}_RiceMind_gene_mechanism_report_data/{gene}_RiceMind_gene_mechanism_report_normalized_evidence.csv`
- optional `{gene}_RiceMind_gene_mechanism_report_data/{gene}_RiceMind_gene_mechanism_report_normalized_varieties.csv`
- optional `{gene}_RiceMind_gene_mechanism_report_data/{gene}_RiceMind_gene_mechanism_report_mechanism_evidence_bundle.json`
- optional `{gene}_RiceMind_gene_mechanism_report_data/figures/`

Use one canonical stem. Do not create `_final`, `_updated`, or duplicate sidecar versions unless explicitly requested.
Do not retain an empty, header-only, or zero-record sidecar. Report retrieval failures and empty results in the report, then remove their empty artifacts.

## Mandatory Two-Stage Build

1. Run `scripts/build_gene_report.py` with `--sidecars-only` to retrieve and normalize the complete RiceMind evidence. This writes the mechanism evidence bundle and synthesis brief when Sentence Evidence is available.
2. Inspect the complete normalized Sentence Evidence CSV and use the brief only as an evidence map. Write a personalized review-style mechanism Markdown that follows `references/evidence-rules.md`.
3. Run the builder again with `--mechanism-md {path}` to create the final DOCX. When Sentence Evidence exists, the script must not create a final DOCX without this mechanism Markdown.

## Sections

1. Data source, retrieval scope, and completeness
   - API base URL
   - endpoint summary
   - page/limit strategy
   - whether all pages were exhausted
   - total traits, sentences, PMIDs
   - endpoint failures or caps

2. Gene identity and molecular context
   - input query
   - normalized ID and RAP ID
   - primary symbol and aliases
   - genomic location
   - cross-database IDs
   - external links as hyperlinks when writing DOCX
   - compact sequence API URL(s) when RAP ID exists

3. Evidence distribution and sentence provenance
   - sentence count
   - unique PMID count
   - ontology distribution
   - representative sentences by confidence tier
   - full evidence remains in CSV

4. Full GTA landscape
   - confidence-tier counts
   - ontology-type counts
   - top traits by support
   - top 20 trait rows in report body
   - full trait table in CSV

5. Evidence codes, sources, and confidence statistics
   - evidence-code distribution
   - source database distribution
   - confidence tier summary

6. RiceMind sentence-evidence-driven mechanism synthesis
   - inspect the complete relevant sentence-evidence table, not only representative rows
   - organize by evidence-derived mechanism topic, not raw trait list or preset biological categories
   - derive preliminary clusters from sentence and title terminology; trait labels may remain metadata but must not define mechanism clusters
   - derive headings from current gene sentence evidence
   - synthesize evidence across PMIDs into detailed review-style paragraphs
   - integrate molecular identity, allele/expression, pathway, phenotype, stress/development, and breeding chains when present
   - cite supporting PMIDs immediately after each mechanistic claim
   - distinguish direct evidence, integrative inference, contradictions, context dependence, and missing links
   - avoid external mechanism knowledge not present in RiceMind payload

7. Temporal trend and hotspot evolution
   - year phases from RiceMind metadata
   - phase-specific keywords and PMIDs
   - state that phases reflect literature attention

8. Secondary bibliometrics and traceability
   - top PMIDs by evidence count
   - top journals when journal metadata exists
   - no geographic/institutional claims without affiliation metadata

9. Variety co-occurrence and omics sequence information
   - compact variety summary when available
   - direct clickable `gene-omics-sequence` API URL(s)
   - no long sequence strings in DOCX body

10. Evidence boundaries and interpretation limits
   - distinguish curated evidence, repeated NLP evidence, exploratory evidence
   - state that co-occurrence is not causality

## Figures

Include when data support them:

- confidence-tier distribution
- ontology-type distribution
- top traits by support
- evidence-code distribution
- source database distribution
- publication-year distribution
- journal distribution when journal metadata exists

## Typography for DOCX

- Chinese text: SimSun
- Latin text, numbers, PMIDs, URLs: Times New Roman
- Title: 16 pt bold
- Heading 1: 14 pt bold
- Heading 2: 12 pt bold
- Body: 10.5 pt
- Table text and captions: 9 pt
