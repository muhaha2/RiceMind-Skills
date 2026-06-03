# RiceMind API Reference for Gene Mechanism Reports

Use this reference before calling the RiceMind REST service. The original API documentation is bundled as `references/ricemind-api-guide.docx`; the extracted route guide is in `references/ricemind-api-guide.md`.

## Base URL

Default REST API base:

`http://lit-evi.hzau.edu.cn/ricemind-api/`

All public data endpoints are `GET` endpoints. Query parameters are passed in the URL query string.

## Required Gene-Report Retrieval Plan

For a gene mechanism report, retrieve data in this order:

1. `GET /gene-profile/?gene={gene}`
   - Resolve the query gene and get unified profile, cross-database IDs, annotations, omics location and external links.

2. `GET /traits-by-gene/?gene={gene}&confidence=All&onto_type=ALL&page={page}&limit={limit}`
   - Retrieve all gene-trait associations.
   - Use `confidence=All` first. Do not rely only on the default `High`.
   - Use `onto_type`, not `ontology_type`.
   - Paginate until `current_page == total_pages` or all records indicated by `total_associated_traits` have been collected.

3. `GET /search-by-trait-and-gene/?gene={gene}&trait={trait}&page={page}&limit={limit}`
   - Run for every retrieved trait unless the user explicitly asks for a reduced report.
   - Paginate until `sentence_pagination.current_page == sentence_pagination.total_pages`.
   - Preserve both `gta_metadata` and `sentence_evidence`.

4. `GET /search-by-gene/?gene={gene}&page={page}&limit={limit}`
   - Retrieve all sentences mentioning the gene. This provides gene-wide evidence outside specific trait filtering.
   - This endpoint returns `total_count` but not always `total_pages`; continue until collected rows reach `total_count` or the final page has fewer than `limit` rows.

5. `GET /varieties-by-gene/?gene={gene}&page={page}&limit={limit}`
   - Retrieve all variety co-occurrence records for the optional agronomic context section.

6. `GET /gene-omics-sequence/?rap_id={standard_rap_id}`
   - Use the standard RAP ID returned from `gene-profile`.

7. `GET /sentence-context/?pmid={PMID}&sent_id={sent_id}&window=2`
   - Use for important or ambiguous evidence sentences. Do not cite context unless it was retrieved.

## Endpoint Fields

### `/gene-profile/`

Parameters:

- `gene`: required. May be `gene_id`, `primary_symbol`, or a token in `searchable_aliases`.

Important returned fields:

- `query`
- `official_info.primary_id`
- `official_info.standard_rap_id`
- `official_info.primary_symbol`
- `official_info.all_symbols_and_synonyms`
- `official_info.cgsnl_name`
- `cross_database_ids.msu_id`
- `cross_database_ids.oryzabase_id`
- `cross_database_ids.gramene_id`
- `cross_database_ids.ensembl_id`
- `cross_database_ids.protein_id`
- `annotations.explanation`
- `annotations.trait_class`
- `omics_location.chromosome`
- `omics_location.start_pos`
- `omics_location.end_pos`
- `omics_location.strand`
- `external_platforms`

Errors:

- Missing `gene`: HTTP 400.
- Unresolved gene: HTTP 404 with `warning` and `data=null`.

### `/traits-by-gene/`

Parameters:

- `gene`: required.
- `confidence`: `High`, `Medium`, `Low`, or `All`; default is `High`.
- `onto_type`: `ALL`, `GO`, `PO`, `TO`, `CO`, or `RTO`; default is `ALL`.
- `page`: default `1`.
- `limit`: default code value is `20`; use a high explicit value such as `500` for full retrieval.

Returned fields:

- `gene`
- `standardized_id`
- `query_context.confidence_applied`
- `query_context.onto_type_applied`
- `total_associated_traits`
- `current_page`
- `total_pages`
- `associated_traits[]`
- `associated_traits[].trait`
- `associated_traits[].ontology_id`
- `associated_traits[].confidence_tier`
- `associated_traits[].evidence_codes`
- `associated_traits[].sources`
- `associated_traits[].article_count`
- `associated_traits[].earliest_year`

Confidence rules used by the API:

- Tier 1 / High: `Oryzabase_Curated`, `RAP-DB_Curated`, `EXP`, `IDA`, `IMP`, `IEP`, `HEP`, `TAS`.
- Tier 2 / Medium: mixed RiceMind NLP and computational/database support with `article_count > 10`.
- Tier 3 / Low: all other retrieved associations.

### `/search-by-trait-and-gene/`

Parameters:

- `gene`: required.
- `trait`: required. Use the exact `associated_traits[].trait` term when possible.
- `page`: default `1`.
- `limit`: default `15`; use a high explicit value such as `500` for full retrieval.

Returned fields:

- `query_context.gene_query`
- `query_context.trait_query`
- `query_context.gene_meta.standard_rap_id`
- `query_context.gene_meta.canonical_symbol`
- `gta_metadata[]`
- `gta_metadata[].trait_info.ontology_id`
- `gta_metadata[].trait_info.ontology_type`
- `gta_metadata[].trait_info.trait_name`
- `gta_metadata[].evidence_profile.confidence_tier`
- `gta_metadata[].evidence_profile.source_databases`
- `gta_metadata[].evidence_profile.evidence_codes`
- `gta_metadata[].evidence_profile.literature_support_count`
- `sentence_pagination.total_sentences`
- `sentence_pagination.current_page`
- `sentence_pagination.total_pages`
- `sentence_evidence[]`
- `sentence_evidence[].PMID`
- `sentence_evidence[].year`
- `sentence_evidence[].sent_id`
- `sentence_evidence[].text`

### `/search-by-gene/`

Parameters:

- `gene`: required.
- `page`: default `1`.
- `limit`: default `50`; use a high explicit value such as `500`.

Returned fields:

- `total_count`
- `current_page`
- `results[].PMID`
- `results[].year`
- `results[].title`
- `results[].sent_id`
- `results[].text`

### `/varieties-by-gene/`

Parameters:

- `gene`: required.
- `page`: default `1`.
- `limit`: default `100`; use a high explicit value such as `500`.

Returned fields:

- `gene`
- `total_associated_varieties`
- `current_page`
- `total_pages`
- `varieties[]`

### `/sentence-context/`

Parameters:

- `pmid`: required.
- `sent_id`: required integer.
- `window`: optional integer; default `2`.

Returned fields:

- `PMID`
- `article_info.title`
- `article_info.authors`
- `article_info.journal`
- `article_info.year`
- `article_info.doi`
- `article_info.pubmed_url`
- `target_sent_id`
- `context_window`
- `context[].sent_id`
- `context[].is_target_sentence`
- `context[].text`

### `/gene-omics-sequence/`

Parameters:

- `rap_id`: required, for example `Os01g0883800`.

Returned fields:

- `rap_id`
- `genomic_seq`
- `transcripts[].transcript_id`
- `transcripts[].cdna_seq`
- `transcripts[].protein_seq`

## Pagination Rule

Do not report a gene as fully analyzed until all relevant paginated endpoints have been exhausted.

Use explicit `page` and `limit` on every paginated call. The report script defaults to `limit=500` and continues until one of these conditions is met:

- `total_pages` is present and `current_page >= total_pages`.
- `total_count` is present and the collected record count reaches `total_count`.
- The endpoint does not expose total pages and the final page returns fewer records than `limit`.

If a reduced retrieval is necessary for runtime reasons, state it in Section 1 of the DOCX and preserve the complete raw payload or partial-call log.

## Script Endpoint Map

`scripts/build_gene_mechanism_report.py` already includes direct route defaults. Only provide `--endpoint-map` if the live service routes change.

