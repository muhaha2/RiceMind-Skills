# RiceMind Task Router

Use this file first. It classifies the user request and selects one internal module of the integrated RiceMind skill.

## Routing Table

| Module | User intent examples | Read next | Script when needed |
|---|---|---|---|
| `gene_report` | "Generate a full report for sd1"; "Give me all evidence for NRT1" | `gene-report-template.md`, `ricemind-api.md`, `evidence-rules.md` | `build_gene_report.py` |
| `trait_report` | "Which genes are related to insect resistance?"; "Give me a drought tolerance overview" | `trait-report-template.md`, `ricemind-api.md`, `evidence-rules.md` | `build_trait_report.py` |
| `gene_trait_audit` | "How strong is the evidence for gene A and trait B?" | `output-contracts.md`, `ricemind-api.md`, `evidence-rules.md` | `ricemind_api_client.py`, `normalize_ricemind_payload.py` |
| `breeding_objective` | "Find genes for insect resistance with yield relevance"; "Improve nitrogen use efficiency without yield loss" | `breeding-question-patterns.md`, `trait-report-template.md` | `build_trait_report.py`, `build_evidence_network.py` |
| `variety_profile` | "Which genes and traits are linked to variety X?" | `output-contracts.md`, `ricemind-api.md` | `ricemind_api_client.py`, `build_evidence_network.py` |
| `literature_trend` | "How has BPH resistance research changed over time?" | `output-contracts.md`, `evidence-rules.md` | `normalize_ricemind_payload.py` |
| `evidence_network` | "Build a gene-trait evidence network"; "Show relationships among genes and traits" | `output-contracts.md`, `ricemind-api.md` | `build_evidence_network.py` |
| `data_export` | "Give me the full API data"; "Export normalized evidence tables" | `ricemind-api.md`, `output-contracts.md` | `ricemind_api_client.py`, `normalize_ricemind_payload.py` |

## Classification Rules

- If the user names one gene and asks for a full, complete, overview, report, or DOCX output, choose `gene_report`.
- If the user names one trait, stress, pest, disease, agronomic property, or breeding phenotype and asks which genes or evidence landscape, choose `trait_report`.
- If the user names both a gene and a trait, choose `gene_trait_audit` unless they explicitly request a full gene report.
- If the user states a practical breeding goal, choose `breeding_objective` and decompose the goal into RiceMind-searchable trait phrases.
- If the user names a variety, choose `variety_profile`.
- If the user asks about years, journals, PMIDs, research hotspots, or historical phases, choose `literature_trend`.
- If the user asks for graph, network, nodes, edges, relationship table, or gene-trait-variety map, choose `evidence_network`.
- If the user asks primarily for files or complete records, choose `data_export`.

## Broad-to-Deep Strategy

Use broad-to-deep analysis for open-ended tasks:

1. Broad scan: collect genes, traits, varieties, sentences, PMIDs, years, journals, evidence codes, confidence tiers, and ontology IDs.
2. Ranking or clustering: prioritize evidence by confidence, support count, independent PMIDs, source diversity, ontology specificity, and sentence clarity.
3. Deep evidence reading: inspect sentence text and context for top candidates or themes.
4. Output: provide the selected format and keep full records in sidecar files when the evidence set is large.

## Clarification Policy

Do not ask for clarification if a reasonable route is clear. State the interpreted route and proceed.

Ask only when:

- the same query could require very different artifacts, such as quick answer versus full DOCX;
- the target term is ambiguous and RiceMind cannot resolve it;
- the user asks for a breeding objective but no searchable trait terms can be inferred.

## Anti-Patterns

- Do not force every RiceMind question into a single-gene DOCX report.
- Do not answer trait-centered questions by listing traits only; identify candidate genes or evidence themes when the payload permits it.
- Do not infer causality from sentence co-occurrence.
- Do not reuse fixed biological paragraphs from previous genes, traits, or pests.
