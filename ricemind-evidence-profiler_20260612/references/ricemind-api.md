# RiceMind API Reference

Default base URL:

`http://lit-evi.hzau.edu.cn/ricemind-api/`

All public endpoints are `GET` endpoints. Pass parameters through the URL query string.

## Contents

- Pagination
- Vocabulary Endpoint Policy
- Endpoint Map
- Returned Fields to Preserve
- Retrieval Macros

## Pagination

Always pass explicit `page` and `limit` for paginated endpoints.

For full analyses, exhaust all pages and stop only when:

- `total_pages` is present and `current_page >= total_pages`;
- `total_count` is present and collected records reach `total_count`;
- no total is exposed and the final page returns fewer records than `limit`.

Stop immediately on an empty page, detect repeated page payloads, and apply a finite `max_pages` safety cap. Retry transient HTTP `429` and `5xx`, timeout, connection, and malformed-response failures with bounded exponential backoff. Record caps, repeated-page termination, endpoint errors, timeouts, and partial retrieval in the output.

The vocabulary-endpoint restrictions below override the general full-pagination rule. Do not interpret "full analysis" as permission to exhaust `/all-genes/` or `/all-traits/`.

## Vocabulary Endpoint Policy

### `/all-genes/`: Avoid Full Retrieval

Treat `/all-genes/` as a low-information vocabulary listing, not a default discovery endpoint. The gene list is very large and does not provide the gene-specific evidence needed for most RiceMind tasks.

Apply these rules:

- Do not retrieve all pages unless the user explicitly and specifically requests the complete RiceMind gene list.
- If the user is only curious about available genes, provide the paginated API link rather than downloading the complete list:
  `http://lit-evi.hzau.edu.cn/ricemind-api/all-genes/?page=1&limit=100`
- If the user requests a small sample, call `/all-genes/?page={page}&limit={limit}` with a limit of about 100 and clearly label the result as a sample.
- If the user already provides a gene name or identifier, use `/gene-profile/?gene={gene}` first. Use gene-specific evidence endpoints for subsequent analysis.
- Do not use `/all-genes/` as a substitute for gene-profile lookup, candidate ranking, gene-trait evidence retrieval, or mechanism analysis.
- Full pagination is permitted only for the exceptional case where the user clearly requests the complete gene vocabulary as data.

### `/all-traits/`: Use the Local Vocabulary

Do not call `/all-traits/` during normal skill execution. `references/All-Traits.txt` contains the complete RiceMind trait vocabulary needed by this skill and avoids an unnecessary API request.

Before calling any endpoint with a user-derived or decomposed `trait` parameter:

1. Search the complete `references/All-Traits.txt` file for exact matches and biologically relevant candidate labels.
2. Use keyword variants from the user's wording to search the file, but select only exact stored trait items.
3. Preserve the spelling and capitalization found in `All-Traits.txt` when sending the API query.
4. Query each selected exact trait separately when multiple labels are relevant.
5. If no suitable stored trait can be identified, explain that the requested term is not represented in the local RiceMind trait vocabulary and do not send a speculative trait query that is expected to return empty data.

Trait labels returned directly by another RiceMind endpoint are already valid API vocabulary items and can be reused without a second full-file scan. The local file must still be used to validate any trait term introduced by the user, by goal decomposition, or by model-generated query expansion.

Call `/all-traits/` only when the user explicitly requests a live refresh, comparison, or export of the API's current complete trait vocabulary. Do not call it merely to validate ordinary trait queries.

### Preset General Breeding Goals

For a general user request that clearly maps to one or more of the seven goals below, use the exact preset trait searches in `references/breeding-question-patterns.md` under `## Goal Decomposition` -> `Examples`. These presets have already been validated against `All-Traits.txt`, so a new full-vocabulary search is not required:

1. `insect resistance`
2. `disease resistance`
3. `drought tolerance`
4. `salinity tolerance`
5. `nitrogen use efficiency`
6. `yield improvement`
7. `lodging resistance`

Use this shortcut only for genuinely general requests. If the user adds a narrower organism, tissue, developmental stage, treatment, phenotype, or breeding constraint not represented by the preset row, search the complete `All-Traits.txt` file and refine the exact trait set before calling trait endpoints.

## Endpoint Map

| Endpoint | Use | Parameters |
|---|---|---|
| `/gene-profile/` | Gene identity, cross-database IDs, annotations, omics location, external links | `gene` |
| `/traits-by-gene/` | Gene-associated GTA traits | `gene`, `confidence`, `onto_type`, `page`, `limit` |
| `/search-by-gene/` | Sentence evidence by gene | `gene`, `page`, `limit` |
| `/search-by-trait/` | Sentence evidence by trait | `trait`, `page`, `limit` |
| `/search-by-trait-and-gene/` | Gene-trait GTA metadata and supporting sentences | `gene`, `trait`, `page`, `limit` |
| `/varieties-by-gene/` | Varieties co-occurring with a gene | `gene`, `page`, `limit` |
| `/search-by-variety/` | Sentence evidence by variety | `variety`, `page`, `limit` |
| `/search-by-variety-and-gene/` | Variety-gene co-occurrence sentences | `variety`, `gene`, `page`, `limit` |
| `/search-by-variety-and-trait/` | Variety-trait co-occurrence sentences | `variety`, `trait`, `page`, `limit` |
| `/sentence-context/` | Neighboring sentences and article metadata | `pmid`, `sent_id`, `window` |
| `/gene-omics-sequence/` | Genomic, cDNA, and protein sequence by RAP ID | `rap_id` |
| `/all-genes/` | Restricted-use gene vocabulary listing; avoid full retrieval unless explicitly requested | `page`, `limit` |
| `/all-traits/` | Live trait-vocabulary refresh/export only; use `references/All-Traits.txt` for normal queries | `page`, `limit` |
| `/all-varieties/` | Candidate variety vocabulary | `page`, `limit` |

## Returned Fields to Preserve

Preserve these fields when present:

- `PMID`, `pmid`
- `year`
- `journal`
- `title`
- `doi`
- `sent_id`
- `text`
- `gene`, `standardized_id`, `standard_rap_id`, `primary_symbol`
- `trait`, `trait_name`, `trait_description`
- `ontology_id`, `ontology_type`, `onto_type`
- `confidence_tier`, `confidence`
- `evidence_codes`, `Evidence_Code`, `evidence_code`
- `sources`, `Source_DB`, `source_db`
- `article_count`, `literature_support_count`
- `current_page`, `total_pages`, `total_count`

Treat `confidence_tier` or `confidence` as the authoritative RiceMind GTA tier. Preserve the returned tier and use `evidence_codes`, `sources`, and `article_count` to explain its evidence composition, not to recompute it. If the tier field is absent, report it as unspecified.

## Retrieval Macros

### Gene Full Report

1. `/gene-profile/?gene={gene}`
2. `/traits-by-gene/?gene={gene}&confidence=All&onto_type=ALL&page={page}&limit={limit}`
3. `/search-by-trait-and-gene/?gene={gene}&trait={trait}&page={page}&limit={limit}` for every returned trait
4. `/search-by-gene/?gene={gene}&page={page}&limit={limit}`
5. `/varieties-by-gene/?gene={gene}&page={page}&limit={limit}`
6. `/gene-omics-sequence/?rap_id={rap_id}` when profile resolves a RAP ID
7. `/sentence-context/` for ambiguous or high-value evidence

### Trait-Centered Candidate Discovery

1. Resolve the user request to exact RiceMind trait labels before calling the API.
   - For one of the seven general breeding goals, use the corresponding preset row in `references/breeding-question-patterns.md`.
   - Otherwise, search the complete `references/All-Traits.txt` vocabulary and select only exact stored items.
2. Retrieve all `/search-by-trait/?trait={exact_trait}&page={page}&limit={limit}` records for each selected trait.
3. Extract candidate genes from returned entity fields when available.
4. If entity fields are absent, extract likely gene mentions from sentence text and label them as text-mined candidates.
5. For top candidates, verify with `/gene-profile/`, `/traits-by-gene/`, and `/search-by-trait-and-gene/`.

Limitation: without a direct genes-by-trait route or explicit gene entity fields, the candidate list is a RiceMind sentence-evidence candidate list, not a complete curated trait-to-gene catalog.

### Gene-Trait Pair Audit

1. `/gene-profile/?gene={gene}`
2. Validate the user-provided trait against `references/All-Traits.txt` and preserve the exact stored label.
3. `/search-by-trait-and-gene/?gene={gene}&trait={exact_trait}&page={page}&limit={limit}`
4. `/traits-by-gene/?gene={gene}&confidence=All&onto_type=ALL&page={page}&limit={limit}`
5. `/sentence-context/` for important or ambiguous sentences

### Breeding Objective

1. Determine whether the request is a general instance of `insect resistance`, `disease resistance`, `drought tolerance`, `salinity tolerance`, `nitrogen use efficiency`, `yield improvement`, or `lodging resistance`.
2. For a matching general goal, use its preset exact traits from `references/breeding-question-patterns.md` without repeating a full `All-Traits.txt` search.
3. For any other or more specific objective, search the complete `references/All-Traits.txt` file and decompose the objective into exact stored trait labels.
4. Run trait-centered candidate discovery for each selected exact trait.
5. Merge candidates across traits.
6. Flag support patterns: high-confidence evidence, repeated NLP evidence, yield or quality terms, stress or pest context, and breeding-use terms.
7. Present candidates as RiceMind evidence-prioritized hypotheses, not final breeding recommendations.

### Variety Profile

1. `/search-by-variety/?variety={variety}&page={page}&limit={limit}`
2. Extract co-mentioned genes and traits from entity fields or sentence text.
3. Use `/search-by-variety-and-gene/` and `/search-by-variety-and-trait/` for selected pairs.
4. Use gene or trait modules for deep follow-up.

### Literature Trend

1. Retrieve the evidence set relevant to a gene, trait, pair, variety, or objective.
2. Group by `year`, `PMID`, `journal`, evidence code, and topic keywords.
3. Report phases as literature-attention changes, not biological proof.

### Evidence Network

Build edges from normalized records:

- gene -> trait direct sentence evidence
- gene -> trait same-PMID co-occurrence, stored as a separate weaker edge type
- gene -> variety
- variety -> trait
- PMID -> gene/trait/variety

Create a direct gene-trait edge only when the gene and trait occur in the same normalized Sentence Evidence row. Never promote genes and traits found in different sentences of the same PMID to a direct association.

Use edge weights from sentence count, independent PMID count, confidence, and evidence-code/source diversity.
