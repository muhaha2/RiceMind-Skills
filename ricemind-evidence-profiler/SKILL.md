---
name: ricemind-evidence-profiler
description: Integrated RiceMind skill family for rice gene, trait, gene-trait, variety, breeding-objective, bibliometric, and evidence-network questions. Use RiceMind APIs or exported RiceMind JSON to route tasks, retrieve full paginated evidence, rank candidates, synthesize PMID-backed mechanisms, build reports, export CSV/JSON sidecars, and create evidence summaries without requiring separate RiceMind subskills.
---

# RiceMind Evidence Profiler

## Overview

This is the integrated RiceMind skill family. It keeps all RiceMind task modules, templates, shared evidence rules, and reusable scripts inside one skill directory so users do not need to install multiple RiceMind skills.

Use it for:

- single-gene full evidence reports
- trait-centered candidate gene landscapes
- gene-trait pair evidence audits
- breeding-objective candidate prioritization
- variety-gene-trait evidence profiles
- literature trend and journal/PMID summaries
- evidence-network tables or JSON
- RiceMind API/JSON data exports

Do not use the LLM as an independent source of rice biology. Treat RiceMind API responses, exported RiceMind JSON, and retrieved sentence evidence as the evidence substrate.

## Global Language and Typography

- If the user asks entirely in English, write generated reports in English.
- If the user asks in Chinese, write generated reports primarily in Chinese while preserving original RiceMind trait labels, sentence evidence, gene symbols, PMIDs, ontology IDs, evidence codes, source names, and technical terms when provenance is clearer in English.
- For styled reports, use SimSun/宋体 for Chinese text and Times New Roman for English/Latin-script text, numbers, PMIDs, URLs, gene symbols, and ontology IDs.

## Architecture

Use a single skill with modular internal layers:

1. Router layer: `references/task-router.md`
   - Classifies the user request and selects a task module.

2. API/data layer: `references/ricemind-api.md`, `scripts/ricemind_api_client.py`, `scripts/normalize_ricemind_payload.py`
   - Handles endpoint selection, full pagination, payload capture, and normalized evidence tables.

3. Evidence layer: `references/evidence-rules.md`
   - Controls claim strength(including Confidence Tiers explanation), PMID citation, uncertainty, and anti-hard-coding rules.

4. Output layer: `references/output-contracts.md` and task templates
   - Chooses concise answer, evidence memo, candidate ranking, DOCX report, CSV/JSON bundle, or evidence network.

5. Task module layer: `references/module-registry.md`
   - Defines gene report, trait report, gene-trait audit, breeding objective, variety profile, literature hotspot, and evidence-network modules.

## Workflow

1. Route the task.
   - Read `references/task-router.md`.
   - Identify whether the request is gene-centered, trait-centered, gene-trait pair, breeding-objective, variety-centered, bibliometric, network-oriented, or data-export oriented.
   - Read only the specific task template needed for the chosen module.

2. Retrieve evidence.
   - Read `references/ricemind-api.md`.
   - Follow its vocabulary policy: avoid full `/all-genes/` retrieval, use `references/All-Traits.txt` instead of `/all-traits/`, and resolve user-derived trait terms to exact stored labels before trait API calls.
   - Use explicit `page` and `limit` for every paginated endpoint.
   - Exhaust all pages for full analyses unless the user explicitly requests a quick/capped analysis.
   - Record retrieval scope, endpoint failures, caps, and completeness.

3. Normalize and preserve data.
   - Use `scripts/normalize_ricemind_payload.py` or the task-specific builder script.
   - Preserve complete raw payloads and normalized CSV/JSON sidecars for large evidence sets.
   - Treat API-returned GTA confidence tiers as authoritative. Preserve and present them; never recompute tiers from evidence codes, sources, article counts, sentences, or PMIDs.
   - Do not paste large raw evidence tables into user-facing prose or DOCX bodies.

4. Synthesize from sentence evidence.
   - Read `references/evidence-rules.md`.
   - Use trait labels as indexing terms, not as substitutes for mechanism synthesis.
   - Inspect the complete relevant Sentence Evidence set, derive biological topics from the current RiceMind payload, and do not reuse fixed gene-, pest-, hormone-, pathway-, or trait-specific narratives.
   - Write mechanism sections as personalized, review-style scientific prose that connects evidence from molecular function through phenotype and breeding relevance when supported.
   - Cite every mechanism or prioritization claim with supporting PMIDs from the payload, distinguish direct evidence from integrative inference, and report contradictory or missing links.

5. Produce the output.
   - Read `references/output-contracts.md`.
   - Apply its global mechanism-writing, empty-artifact cleanup, and report/data directory rules to every module.
   - Preserve the RiceMind visualization layer. For formal trait, breeding-objective, candidate-ranking, bibliometric, or multi-gene reports, run `scripts/build_report_figures.py` after normalized sidecars and the report outline are complete and before converting Markdown to PDF or DOCX.
   - Select a small, nonredundant set of figures that directly supports the current user's question and the report's argument. For a personalized report, create a JSON figure plan that names the source table, chart type, data fields, title, caption, destination section, subsection title, placement, and display size. Do not reuse topic-specific fields, labels, or biological assumptions across unrelated reports.
   - Use automatic plotting only as a task-neutral fallback for fields that are explicit in the returned sidecars, such as year, journal, evidence code, source, confidence tier, candidate support counts, trait labels, or network edges. Automatic plotting must not infer a salinity, yield, disease, quality, or other biological scenario from column names.
   - Use `--markdown {report}.md` or `--docx {report}.docx` to place each figure beside the analysis it supports. Do not append all figures to a fixed terminal section, and do not leave a populated figures directory disconnected from the user-facing report.
   - For single-gene full DOCX reports, use the mandatory two-stage workflow in `references/gene-report-template.md`: first retrieve sidecars and the mechanism brief, then write a personalized PMID-backed mechanism Markdown from the complete Sentence Evidence, and only then build the DOCX with `--mechanism-md`.
   - Never use compact evidence-topic summaries as a substitute for the final mechanism synthesis.
   - For trait-centered candidate reports, use `scripts/build_trait_report.py` and `references/trait-report-template.md`; the builder automatically generates and links task-neutral baseline trait figures, while formal personalized reports should use a report-specific figure plan.
   - For breeding-objective questions, use `references/breeding-question-patterns.md`; combine trait scans and evidence ranking.
   - For evidence networks, use `scripts/build_evidence_network.py`.

## Bundled Resources

- `references/module-registry.md`: internal task modules, trigger conditions, scripts, templates, and extension checklist.
- `references/task-router.md`: task classification and broad-to-deep analysis strategy.
- `references/ricemind-api.md`: endpoint map, pagination rules, and retrieval macros.
- `references/evidence-rules.md`: evidence strength, citation, uncertainty, and interpretation rules.
- `references/output-contracts.md`: output modes and sidecar expectations.
- `references/gene-report-template.md`: single-gene full report template.
- `references/trait-report-template.md`: trait-centered evidence panorama template.
- `references/breeding-question-patterns.md`: breeding-objective decomposition and ranking patterns.
- `scripts/ricemind_api_client.py`: reusable RiceMind REST client and pagination helper.
- `scripts/normalize_ricemind_payload.py`: normalize RiceMind JSON into sentence, trait, candidate, and article tables.
- `scripts/build_gene_report.py`: integrated single-gene full DOCX report builder.
- `scripts/build_trait_report.py`: trait-centered evidence and candidate ranking builder.
- `scripts/build_report_figures.py`: reusable figure generator and Markdown/DOCX figure inserter for trait, breeding, ranking, and bibliometric sidecars.
- `scripts/build_evidence_network.py`: evidence-network edge/node exporter.

## Extension Rule

Add new functionality as an internal task module, not as an unstructured expansion of `SKILL.md`.

For each new module, add:

- trigger pattern in `task-router.md`
- retrieval macro in `ricemind-api.md`
- output contract or template
- script only if deterministic retrieval, normalization, plotting, or file generation is needed
- validation examples covering at least two biologically different queries

Keep `SKILL.md` as the table of contents and workflow only.
