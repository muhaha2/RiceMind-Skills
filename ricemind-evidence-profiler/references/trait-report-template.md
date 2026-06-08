# Trait-Centered Evidence Panorama Template

Use this template for `trait_report` tasks, such as insect resistance, drought tolerance, disease resistance, nitrogen use efficiency, plant architecture, grain quality, yield, or other rice breeding traits.

## Required Output

Default output can be Markdown, DOCX, or sidecar data depending on user request. For formal reports, keep:

- `{report_stem}.md` or `{report_stem}.docx`
- sibling `{report_stem}_data/`
- `{report_stem}_data/{trait}_RiceMind_trait_evidence_payload.json`
- `{report_stem}_data/{trait}_RiceMind_sentence_evidence.csv`
- `{report_stem}_data/{trait}_RiceMind_candidate_genes.csv`
- optional `{report_stem}_data/{trait}_RiceMind_evidence_network_edges.csv`
- optional `{report_stem}_data/figures/`

Create only sidecars that contain usable records. Remove empty, header-only, or zero-record artifacts after failed or empty retrievals.

## Sections

1. Trait query interpretation
   - user query
   - RiceMind search term(s)
   - ontology or trait aliases if available
   - ambiguity notes

2. Retrieval scope and completeness
   - endpoints used
   - page/limit strategy
   - all-pages status
   - total sentence records
   - unique PMIDs
   - years and journals available

3. Evidence distribution
   - sentence count
   - PMID count
   - year distribution
   - journal distribution when available
   - evidence-code/source/confidence when available

4. Candidate gene ranking
   - rank genes by RiceMind evidence density and relevance
   - include gene symbol/RAP ID when resolved
   - report sentence count, independent PMIDs, top traits/contexts, representative PMIDs
   - label text-mined candidates clearly when no direct genes-by-trait route is available

5. Mechanism themes from sentence evidence
   - inspect the complete relevant sentence-evidence table, not only representative rows
   - cluster sentence evidence into topics induced from the current payload
   - synthesize evidence across PMIDs into detailed review-style paragraphs
   - discuss biological logic across genes, pathways, phenotype endpoints, and breeding contexts
   - cite supporting PMIDs immediately after each mechanistic claim
   - distinguish direct evidence, integrative inference, contradictions, context dependence, and missing links
   - avoid fixed pest or pathway narratives unless retrieved evidence supports them

6. High-confidence and curated evidence
   - highlight curated or experimental evidence when present
   - separate from NLP-only evidence

7. Breeding relevance and tradeoff signals
   - breeding, introgression, QTL, marker-assisted selection, pyramiding, yield, quality, stress, pest, disease, or agronomic terms when present
   - state that RiceMind evidence prioritizes candidates but does not replace experimental validation

8. Evidence gaps and interpretation limits
   - broad trait query limitations
   - missing gene resolver fields
   - co-occurrence versus causality
   - incomplete or capped retrieval

## Candidate Ranking Criteria

Use transparent criteria:

- direct gene-trait evidence
- independent PMID count
- sentence count
- curated/experimental evidence
- confidence tier
- evidence-code diversity
- source-database diversity
- ontology specificity
- mechanism-rich sentence evidence
- breeding relevance terms

Do not present rankings as definitive biology. Present them as RiceMind evidence-prioritized candidates.

## Recommended Figures

- publication-year distribution
- top candidate genes by sentence count
- top candidate genes by independent PMIDs
- journal distribution when available
- evidence-code/source distribution when available
- evidence network when useful
