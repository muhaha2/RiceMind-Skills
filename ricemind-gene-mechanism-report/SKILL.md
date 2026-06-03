---
name: ricemind-gene-mechanism-report
description: Create multi-dimensional, evidence-grounded DOCX reports for rice gene mechanisms from RiceMind APIs, MCP tool payloads, or exported RiceMind JSON. Use when a user asks for a gene-centered RiceMind report, gene-trait association overview, mechanism synthesis, PMID-backed evidence table, confidence-tier analysis, ontology distribution, temporal hotspot evolution, bibliometrics, literature trend chart, or task-oriented workflow based on RiceMind GTA evidence.
---

# RiceMind Gene Mechanism Report

## Overview

Generate a gene-centered multi-dimensional evidence report from RiceMind evidence only. The output must be a fixed-template `.docx` with traceable gene profile data, all retrievable gene-trait associations, confidence/evidence-code summaries, ontology and sentence provenance, PMID-backed synthesized mechanism prose, temporal hotspot evolution, bibliometrics, and figures where the RiceMind payload supports them.

Do not use the LLM as an independent source of rice biology. Treat RiceMind API/MCP JSON as the canonical evidence substrate and preserve provenance fields in the report.

## Workflow

Before generating any report, read `references/report-template.md` and `references/ricemind-api.md`. Use the bundled original API documentation `references/ricemind-api-guide.docx` or extracted guide `references/ricemind-api-guide.md` when endpoint fields are unclear.

1. Resolve the target gene.
   - Accept a gene symbol, alias, RAP ID, or literature-used gene name.
   - Query `GET http://lit-evi.hzau.edu.cn/ricemind-api/gene-profile/?gene={gene}` first. Use returned RAP ID, synonyms, locus, cross-references, and external links as the normalized anchor.
   - If a RAP ID is available, optionally query `ricemind_get_gene_omics_sequence` for sequence availability and identifiers.

2. Retrieve the complete gene-trait landscape.
   - Query `GET /traits-by-gene/?gene={gene}&confidence=All&onto_type=ALL&page={page}&limit={limit}` first.
   - Use explicit `page` and `limit` and exhaust all pages. Do not stop at the first page.
   - Use `onto_type`, not `ontology_type`, for the live RiceMind REST API.
   - If `traits-by-gene` fails for an Oryzabase-only or RAP-unresolved entry, record the endpoint error in Section 1 and the payload JSON, then continue with all available `search-by-gene` evidence instead of aborting.
   - If the report needs precision-focused sections, repeat with `High`, `Medium`, and `Low` to verify tier-specific counts.
   - Preserve `Ontology_Type`, `Ontology_ID`, `Trait_Description`, `Evidence_Code`, `Source_DB`, `confidence`, support counts, earliest year, and association identifiers.

3. Retrieve sentence-level evidence.
   - For every retrieved trait, call `GET /search-by-trait-and-gene/?gene={gene}&trait={trait}&page={page}&limit={limit}` using the normalized gene and exact RiceMind trait term.
   - Exhaust all pages for each trait. Use `sentence_pagination.total_pages` when present.
   - Also call `GET /search-by-gene/?gene={gene}&page={page}&limit={limit}` to capture gene-wide sentence evidence.
   - Include full evidence in the DOCX when practical and always retain all normalized records in sidecar JSON/CSV.
   - For important or ambiguous sentences, call `GET /sentence-context/?pmid={PMID}&sent_id={sent_id}&window=2` to inspect neighboring sentences.

4. Apply evidence discipline before writing mechanisms.
   - Separate RiceMind source evidence from interpretation.
   - Read and integrate the concrete content of the full retrieved sentence evidence; do not write a section that only restates trait associations or support counts.
   - Treat trait names as indexing terms only. The mechanism prose must be grounded primarily in `normalized_evidence.csv` sentence text, not in the trait table.
   - Derive mechanism topics from the current gene's RiceMind evidence. Do not reuse fixed biological topic inventories such as BPH resistance, sd1/GA biology, heading date, drought, or any other gene-specific template unless the current API payload explicitly supports that theme.
   - Extract sentence-derived mechanism chains such as molecular identity, allele/mutation/expression change, pathway perturbation, signaling context, phenotype endpoints, breeding-use context, stress/development context, or other chains that actually appear in the current sentence evidence.
   - Convert those RiceMind sentence-derived chains into review-style prose that explains the logic linking the gene, mechanism, phenotype and PMIDs. Avoid paragraphs that only say "sentences co-report gene X with trait Y".
   - Use strong wording only for Tier 1 curated/experimental evidence.
   - Use discovery-candidate wording for Tier 2 NLP-supported associations.
   - Use exploratory wording for Tier 3 or supplementary/uncatalogued gene evidence.
   - Cite each mechanism statement with bracket-style PMID markers, for example `[12345678, 23456789]`.
   - Never cite a PMID unless it appears in the RiceMind payload for that claim.
   - Build temporal hotspot phases from RiceMind `year` metadata and sentence keywords; do not infer historical phases from outside knowledge.
   - Report journal/PMID bibliometrics only from returned metadata. Do not invent geographic or institutional hotspots when affiliation metadata is absent.

5. Generate figures and DOCX.
   - Use `scripts/build_gene_mechanism_report.py` when REST endpoints can be called or a RiceMind JSON bundle is available.
   - Use one canonical report stem for every gene, for example `{gene}_RiceMind_gene_mechanism_report`. Do not create `_final`, `_updated`, `_no_conflict`, or other duplicate final stems unless the user explicitly asks for multiple versions.
   - First run the script with `--sidecars-only` to fetch/normalize the full data and create exactly one set of data sidecars, including `*_payload.json`, `*_normalized_traits.csv`, `*_normalized_evidence.csv`, optional `*_normalized_varieties.csv`, `*_mechanism_evidence_bundle.json`, and one figure directory.
   - Read the mechanism evidence bundle and the full `*_normalized_evidence.csv`; write a gene-specific Section 6 mechanism synthesis Markdown from the actual sentence evidence. If `--write-brief` was used for debugging, the brief may help orient this step but is not a final artifact.
   - Keep Section 6 Markdown as a temporary working file, preferably outside the final report folder or in a scratch folder. Re-run the script with `--docx-only --mechanism-md path/to/section6.md --out {canonical}.docx` to insert the personalized synthesis without rewriting duplicate sidecars.
   - Delete temporary Section 6 Markdown and optional brief files after successful DOCX generation unless the user explicitly asks to keep drafting artifacts. Without `--mechanism-md`, the script only inserts a neutral data-driven evidence-topic summary and must not invent a mechanism review.
   - Use `--write-brief` only for debugging or manual prompting. Do not keep `*_mechanism_synthesis_brief.md` as a final deliverable by default.
   - Include at minimum: confidence-tier distribution, ontology distribution, top traits by support, evidence-code distribution, source distribution, and publication-year trend if years are available.
   - Keep figures evidence-descriptive, not causal unless supported by curated or experimental evidence.
   - Format all Chinese text as SimSun/宋体 and all Latin text as Times New Roman. Use the size rules in `references/report-template.md`.
   - Do not fill the report with full raw tables. Keep full data in sidecar CSV/JSON and show concise report summaries.

## Expected Report Structure

Use the fixed template in `references/report-template.md`. The required top-level sections are:

1. Data Source, Retrieval Scope and Completeness
   - API base URL, endpoints used, page/limit strategy, completeness statement, and at most six function-level API call summaries. Do not list page-by-page URLs.

2. Gene Identity and Basic Molecular Mechanism
   - Normalized gene name/RAP ID, aliases, genomic locus, cross-references, external database links, sequence availability, and a concise consensus mechanism constrained to RiceMind profile/evidence.
   - External platform URLs, especially RAP-DB, Ensembl Plants and Gramene, must be actual DOCX hyperlinks.

3. Evidence Distribution and Sentence Provenance
   - Total sentence evidence, unique PMIDs, ontology distribution, and representative sentence evidence sampled by confidence tier. Full sentence evidence remains in `normalized_evidence.csv`.

4. Full GTA Landscape
   - All associated traits grouped by confidence tier and ontology type, with figures and a top-20 trait summary table. Preserve the complete trait table in `normalized_traits.csv`.

5. Evidence Codes, Sources and Confidence Statistics
   - Raw evidence-code distribution, source database distribution, and tier counts.

6. RiceMind Sentence-Evidence-Driven Mechanism Synthesis
   - Organize by mechanism topic rather than by trait list or confidence-tier list.
   - Write integrated review-style mechanism paragraphs based on the full retrieved sentence evidence, extracting only the pathway, mutation/expression, signaling, phenotype, breeding, stress/development or other chains visible in the current gene's RiceMind text.
   - Choose section headings from the current gene's evidence clusters. Do not hard-code traits, mechanisms, pests, hormones, pathways, or gene families into the template.
   - Explain the hidden logic among gene, molecular mechanism, trait and phenotype that is visible in RiceMind Data, while avoiding unsupported external biology.
   - Mention trait labels only when they help orient the reader; do not let trait labels substitute for sentence-evidence synthesis.
   - Use PMID bracket citations, for example `[12345678, 23456789]`.

7. Temporal Analysis and Hotspot Evolution
   - Use RiceMind year metadata to split evidence into phases and report phase-specific keywords, trait contexts and PMID counts.

8. Secondary Bibliometrics and PMID Traceability
   - Publication-year distribution, unique PMID counts, repeated-support PMID clusters, top journals when journal metadata exists, and no geographic/institutional claims unless RiceMind provides affiliation metadata.

9. Variety Co-Occurrence and Omics Sequence Information
   - Variety co-occurrence and direct clickable RiceMind `gene-omics-sequence` API URL(s). Do not paste a large omics sequence returned-summary table into the DOCX body; leave full sequence payloads in the JSON sidecar.

10. Evidence Boundaries and Interpretation Limits
   - Explicitly distinguish curated/experimental evidence, repeated NLP co-occurrence, and low-support exploratory associations.
   - Note that sentence co-occurrence alone does not establish causality.

## Bundled Resources

- `references/report-template.md`: mandatory DOCX report sections, required tables, figures and citation rules.
- `references/ricemind-api.md`: direct RiceMind REST routes, parameters, returned fields and full-pagination rules.
- `references/ricemind-api-guide.md`: extracted Markdown from the user-provided API documentation.
- `references/ricemind-api-guide.docx`: original user-provided API documentation.
- `references/evidence-and-reporting.md`: confidence-tier rules, reporting language, and DOCX section requirements.
- `scripts/build_gene_mechanism_report.py`: normalize RiceMind payloads, draw figures, export mechanism evidence bundles, insert optional personalized mechanism Markdown, and create a DOCX report.

## Script Usage

Use an existing API/MCP payload bundle:

```bash
python scripts/build_gene_mechanism_report.py --gene GSK3 --input-json payload.json --out GSK3_RiceMind_report.docx --language zh
```

Use REST endpoints when available:

```bash
python scripts/build_gene_mechanism_report.py --gene XA21 --out XA21_RiceMind_report.docx --page-limit 500
```

For a final report with a personalized mechanism section, use the generated evidence bundle and full evidence CSV to write Section 6 Markdown, then insert it:

```bash
python scripts/build_gene_mechanism_report.py --gene XA21 --out XA21_RiceMind_report.docx --page-limit 500 --sidecars-only
python scripts/build_gene_mechanism_report.py --gene XA21 --input-json XA21_RiceMind_report_payload.json --no-api --mechanism-md scratch/XA21_section6_mechanism.md --out XA21_RiceMind_report.docx --docx-only
```

The script defaults to `http://lit-evi.hzau.edu.cn/ricemind-api/`, fetches all pages for the core endpoints, writes the DOCX, saves the complete payload JSON, writes normalized CSV sidecars, exports `*_mechanism_evidence_bundle.json`, and creates figure PNGs. It writes `*_mechanism_synthesis_brief.md` only with `--write-brief`. If the live REST route names change, provide an endpoint map JSON. See `references/ricemind-api.md`.
