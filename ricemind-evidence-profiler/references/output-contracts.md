# RiceMind Output Contracts

Choose the smallest output that answers the user request while preserving traceability.

## Contents

- Global Output Rules
- Output Modes
- Gene Full Report
- Trait-Centered Evidence Panorama
- Gene-Trait Pair Audit
- Breeding Objective Analysis
- Variety-Centered Evidence Profile
- Temporal and Bibliometric Analysis

## Global Output Rules

### Language and Typography

Match the report language to the user's query: all-English requests produce English reports; Chinese requests produce primarily Chinese reports while preserving original RiceMind trait labels, sentence evidence, gene symbols, PMIDs, ontology IDs, evidence codes, source names, and technical terms when provenance is clearer in English.

For styled reports, use SimSun/宋体 for Chinese text and Times New Roman for English/Latin-script text, numbers, PMIDs, URLs, gene symbols, and ontology IDs.

### Mechanism Writing

Any output that describes a biological, genetic, molecular, physiological, agronomic, or breeding mechanism must follow `references/evidence-rules.md`, especially `## Mechanism Synthesis`. This requirement applies to concise answers, Markdown, DOCX reports, candidate rankings, network interpretations, and all task-specific modules.

Do not replace the required Sentence Evidence review, PMID-level citation, evidence-derived topic induction, or review-style synthesis with a shorter preset mechanism template.

### Report and Data Layout

Keep the user-facing report and its data directory at the same directory level. Use the canonical report stem to name one sibling data directory:

```text
output_directory/
  {report_stem}.docx
  {report_stem}_data/
    {report_stem}_payload.json
    {report_stem}_normalized_evidence.csv
    {report_stem}_normalized_traits.csv
    figures/
```

Apply these rules:

- Keep DOCX, Markdown, PDF, or other primary user-facing reports in the output directory.
- Put API payloads, normalized CSV/JSON files, mechanism evidence bundles, network tables, intermediate data, and figures inside `{report_stem}_data/`.
- Put generated plots and images inside `{report_stem}_data/figures/`, unless the user explicitly requests another location.
- For a formal report, include figures when they materially clarify the current question, evidence structure, ranking, comparison, or relationship. Select a concise, nonredundant set rather than plotting every available column.
- Generate trait, breeding-objective, ranking, and bibliometric figures with `scripts/build_report_figures.py` after final normalized sidecars are available.
- For Markdown/PDF workflows, run the script with `--markdown {report}.md` before converting Markdown to PDF. For an existing DOCX, use `--docx {report}.docx`.
- The report must display or reference every retained generated figure. Do not leave images only in the data directory without connecting them to the report.
- Use one canonical report stem. Do not scatter sidecars beside the report or create `_final`, `_updated`, or duplicate data directories.
- For a data-only request, create one clearly named data directory and place all non-empty deliverables inside it; do not create an empty report placeholder.
- If the user explicitly supplies an output layout, follow it while retaining report/data separation where possible.

### Empty and Failed Retrieval Artifacts

Do not retain empty data artifacts after API retrieval, normalization, or report generation.

Treat an artifact as empty when it has no usable returned data, including:

- a zero-byte or whitespace-only file
- a CSV containing only a header and no data rows
- JSON equal to `null`, `{}`, or `[]`
- a JSON pagination/result wrapper with zero records and no substantive returned entity data
- a figure or network table with no observations, nodes, or edges

Apply this workflow:

1. Retrieve and normalize data before committing sidecars, or write them to a temporary path first.
2. Validate each candidate artifact by its structured content, not file size alone.
3. Move or write only non-empty artifacts into the final data directory.
4. Remove empty artifacts assigned to the current run, including stale canonical outputs at those exact paths.
5. Remove `figures/` and `{report_stem}_data/` if they are empty after cleanup.
6. Never delete user-provided input files or unrelated files.

If an endpoint fails or returns no usable data, state the endpoint, query, error or empty-result status, and effect on completeness in the report or final response. Do not keep an empty payload/CSV merely to represent the failure. If no report is being generated, return the failure status directly to the user.

## Output Modes

| Mode | Use when | Required contents |
|---|---|---|
| Concise answer | User asks a direct question or wants quick guidance | Answer, evidence basis, PMIDs, caveat |
| Evidence memo | User asks for interpretation but not a DOCX | Retrieval scope, ranked evidence, synthesis paragraphs, citation list |
| Candidate ranking | User asks "which genes/traits/varieties" | Ranked table, scoring criteria, top evidence PMIDs, limitations |
| DOCX report | User requests a formal report | Fixed or task-specific template, figures, sidecar files |
| CSV/JSON bundle | User asks for complete data or full traceability | Normalized CSV/JSON with compact explanation |
| Network-style summary | User asks relationships among genes, traits, varieties | Nodes, edges, evidence counts, PMIDs, confidence/source summaries |

## Visualization Workflow

Complete the report outline and normalized sidecars first. Then create a report-specific JSON figure plan and run:

```text
python scripts/build_report_figures.py --data-dir {report_stem}_data --plan {report_stem}_data/figure_plan.json --markdown {report_stem}.md
```

Each planned figure must define its data source and visual role. Supported chart types are:

| Analytical need | Preferred chart |
|---|---|
| Ranked genes, traits, varieties, journals, sources, or evidence categories | `ranked_bar` or `category_bar` |
| Two or more evidence or decision criteria across candidates | `grouped_bar` |
| Benefit-risk, evidence-tradeoff, or two-metric prioritization | `scatter` |
| Publication or evidence evolution over time | `timeline` |
| Distribution of a continuous score or count | `histogram` |
| Candidate-by-trait, gene-by-source, or other two-dimensional evidence matrix | `heatmap` |
| Explicit normalized relationships among entities | `network` |

A minimal personalized plan has this structure:

```json
{
  "language": "zh",
  "figures": [
    {
      "id": "candidate_support",
      "type": "ranked_bar",
      "source": "*candidate_ranking.csv",
      "category": "target",
      "value": "objective_support",
      "top_n": 10,
      "title": "当前育种目标下的候选证据比较",
      "caption": "按当前目标对应的证据支持指标比较候选对象；数值表示证据密度，不直接等同于育种效应大小。",
      "section_keywords": ["优先靶点", "候选排序"],
      "subsection": "候选对象的证据比较",
      "placement": "end_of_section",
      "width_percent": 86,
      "max_height_inches": 5.2
    }
  ]
}
```

The plan may specify `section`, `section_keywords`, `subsection`, and `placement` so the figure is inserted into the part of the report whose claim it supports. Put evidence composition and temporal figures near retrieval or evidence-distribution analysis, ranking figures near candidate prioritization, tradeoff figures near the decision discussion, and relationship figures near the corresponding synthesis. Use a fallback visual-summary section only when no semantically suitable report section exists.

Titles, subsection names, legends, axes, and captions must reflect the current user question and the actual fields plotted. A caption should state what is measured, what comparison is shown, and how it should be interpreted; it must not imply unsupported causality. Topic-specific terms such as salinity, yield, disease, or quality may appear only when the current report and selected data fields support them.

For Markdown/PDF output, use the generated figure group rather than unrestricted Markdown image syntax. Default to 88% report width, never exceed 7.0 inches in width, set a suitable `max_height_inches` (normally 4.0-6.4), and keep the personalized subsection heading, image, and caption together using `break-inside: avoid`, `page-break-inside: avoid`, and heading break controls. Limit dense ranking charts to roughly 8-12 displayed categories unless a larger figure is specifically justified. Do not allow titles, labels, legends, or captions to be clipped, orphaned, or split across pages.

When no personalized plan is supplied, the script may create task-neutral summaries only from explicit sidecar fields. Use `--write-auto-plan` to inspect that detected fallback plan before rendering. Automatic mode is not a substitute for personalized figure selection in a formal report.

For single-gene DOCX reports, `scripts/build_gene_report.py` retains its integrated confidence, ontology, top-trait, evidence-code, source, and publication-year figures.

## Gene Full Report

Use the integrated `gene_report` module with `scripts/build_gene_report.py` and `references/gene-report-template.md`.

Expected deliverables:

- canonical DOCX report
- sibling `{report_stem}_data/` directory
- non-empty payload JSON, when usable API data were returned
- non-empty normalized traits CSV
- non-empty normalized evidence CSV
- optional non-empty normalized varieties CSV
- mechanism evidence bundle JSON when Sentence Evidence supports one
- optional `{report_stem}_data/figures/` directory when figures contain observations

## Trait-Centered Evidence Panorama

Use for trait-first questions such as insect resistance, drought tolerance, nitrogen use efficiency, yield quality, or disease resistance.

Recommended sections:

1. Trait query interpretation and RiceMind search terms
2. Retrieval scope and completeness
3. Evidence distribution by year, journal, PMID, and sentence count
4. Candidate genes ranked by evidence strength
5. Mechanism themes extracted from sentence evidence
6. High-confidence or curated evidence, if available
7. Breeding relevance and tradeoff terms
8. Evidence gaps and interpretation limits

Recommended sidecars:

- `{report_stem}_data/{trait}_RiceMind_trait_evidence_payload.json`
- `{report_stem}_data/{trait}_RiceMind_candidate_genes.csv`
- `{report_stem}_data/{trait}_RiceMind_sentence_evidence.csv`
- optional `{report_stem}_data/figures/` directory

Create each sidecar only when it contains usable records.

## Gene-Trait Pair Audit

Use for focused evidence strength questions.

Recommended sections:

1. Query normalization
2. GTA metadata and confidence tier
3. Sentence evidence summary
4. Representative sentences with PMIDs
5. Mechanism interpretation, if sentence evidence supports it
6. Evidence strength judgment
7. Caveats and missing data

The output can usually be Markdown unless the user requests DOCX.

## Breeding Objective Analysis

Use for practical breeding questions that combine multiple traits.

Recommended sections:

1. Objective decomposition into RiceMind-searchable traits
2. Candidate gene discovery strategy
3. Candidate groups by evidence strength and breeding relevance
4. Potential tradeoff evidence
5. Mechanism and phenotype themes
6. Recommended next evidence checks
7. Evidence boundaries

Do not present rankings as final breeding recommendations. Present them as RiceMind evidence-prioritized candidates.

## Variety-Centered Evidence Profile

Recommended sections:

1. Variety query normalization
2. Co-mentioned genes and traits
3. Evidence-supported gene-variety or trait-variety links
4. Agronomic interpretation limits
5. PMIDs and sentence evidence table

## Temporal and Bibliometric Analysis

Recommended sections:

1. Evidence set definition
2. Publication-year distribution
3. Hotspot phases by sentence keywords
4. Top journals when journal metadata exists
5. PMID clusters
6. Interpretation limits

Phrase phases as literature attention, not as proof of biological importance.
