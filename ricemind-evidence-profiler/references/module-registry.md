# RiceMind Internal Module Registry

This registry keeps the integrated skill modular. Every RiceMind capability should belong to one module with a trigger, retrieval plan, output contract, and optional script.

## Current Modules

| Module | Purpose | Template/reference | Script |
|---|---|---|---|
| `gene_report` | Full single-gene mechanism and evidence DOCX report | `gene-report-template.md` | `build_gene_report.py` |
| `trait_report` | Trait-centered evidence panorama and candidate gene ranking | `trait-report-template.md` | `build_trait_report.py` |
| `gene_trait_audit` | Focused evidence assessment for a gene-trait pair | `output-contracts.md` | `ricemind_api_client.py`, `normalize_ricemind_payload.py` |
| `breeding_objective` | Decompose breeding goals into trait scans and candidate prioritization | `breeding-question-patterns.md` | `build_trait_report.py`, `build_evidence_network.py` |
| `variety_profile` | Variety-gene-trait co-occurrence profile | `output-contracts.md` | `ricemind_api_client.py`, `build_evidence_network.py` |
| `literature_trend` | Year, journal, PMID, and hotspot-term analysis | `output-contracts.md` | `normalize_ricemind_payload.py` |
| `evidence_network` | Node/edge tables for gene-trait-variety evidence | `output-contracts.md` | `build_evidence_network.py` |
| `data_export` | Complete paginated API payload and normalized tables | `ricemind-api.md` | `ricemind_api_client.py`, `normalize_ricemind_payload.py` |

## Module Contract

Each module must define:

1. Trigger: user wording that selects the module.
2. Retrieval macro: endpoints and pagination requirements.
3. Evidence logic: how claims are ranked or synthesized.
4. Output: user-facing artifact plus sidecar files.
5. Limits: known cases where RiceMind evidence is incomplete or ambiguous.

## Adding a New Module

Add a module only when the task is repeated or needs a stable workflow.

Required additions:

- route in `task-router.md`
- retrieval macro in `ricemind-api.md`
- output contract or task template
- script if deterministic data collection, normalization, plotting, or file generation is needed
- validation examples with at least two biologically different inputs

Do not add a new module for one-off prose preferences. Put writing rules in `evidence-rules.md` or the task template instead.

## Internal Dependency Rule

Modules can reuse scripts and references from this same skill directory. They must not require users to install another RiceMind skill.

If a module borrows design from an older standalone skill, copy the necessary script or template into this integrated skill and document the integration.
