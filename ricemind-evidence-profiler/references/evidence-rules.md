# RiceMind Evidence Rules

These rules apply to every module in this integrated skill.

## Contents

- Evidence Substrate
- Claim Strength
- PMID Citation
- Mechanism Synthesis
- Candidate Ranking
- Uncertainty
- External Knowledge Boundary
- Anti-Hard-Coding Rule

## Evidence Substrate

Use only RiceMind API responses, exported RiceMind JSON, normalized sidecar files, or sentence context retrieved from RiceMind as evidence.

Preserve provenance:

- PMID
- sentence ID
- sentence text
- year
- journal
- title
- DOI
- trait and ontology fields
- evidence code
- source database
- confidence tier
- support count

## Claim Strength

Use the GTA tier returned by the RiceMind API in `confidence_tier` or `confidence`. The API tier is authoritative and already applies the RiceMind aggregation rules correctly. Preserve and present it; do not recalculate, override, downgrade, or upgrade it from `evidence_codes`, `sources`, `article_count`, sentence count, or PMID count.

The criteria below document how RiceMind defines the tiers. They are for interpretation and user-facing explanation, not client-side classification. If a payload lacks a tier, report `Unspecified` and preserve the available metadata instead of inferring a tier.

### GTA Evidence Metadata

RiceMind GTA records may contain these `evidence_codes`:

`EXP`, `HEP`, `IBA`, `IC`, `IDA`, `IEA`, `IEP`, `IMP`, `ISS`, `Oryzabase_Curated`, `RAP-DB_Curated`, and `TAS`.

They may contain these `sources`:

`Ensembl`, `Oryzabase`, `Planteome`, `RAP-DB`, and `RiceMind_NLP`.

Apply these interpretation rules:

- Treat `Oryzabase_Curated` and `RAP-DB_Curated` as RiceMind evidence-code labels manually attached according to curated database provenance.
- Treat the abbreviated evidence codes from Ensembl and Planteome according to the code returned by the API. Do not invent code expansions or silently assign a stronger class than the API supports.
- Treat `sources` as provenance, not confidence by itself. For example, the source value `Oryzabase` is not interchangeable with the evidence code `Oryzabase_Curated`.
- Treat `RiceMind_NLP` as automatically constructed literature-extraction evidence, not expert manual review.
- Do not describe NLP extraction, sentence co-occurrence, or article-count support alone as curated, experimentally validated, or ground truth.
- Treat `article_count` as the aggregated literature count used by the RiceMind API. Do not substitute sentence count for `article_count`.

### Confidence Tiers

| API filter | Confidence tier | Evidence criteria | Primary utility |
|---|---|---|---|
| `High` | Tier 1: Curated/Experimental | For the same trait, at least one aggregated record contains `Oryzabase_Curated`, `RAP-DB_Curated`, `EXP`, `IDA`, `IMP`, `IEP`, `HEP`, or `TAS`. The presence of any one of these codes is sufficient for Tier 1. | Ground-truth retrieval and high-fidelity mechanism validation. |
| `Medium` | Tier 2: Verified Literature + Computational | No Tier 1 evidence is present, and all three conditions hold: `sources` contains `RiceMind_NLP`; `sources` contains at least one source other than `RiceMind_NLP`; and aggregated `article_count > 10`. | High-confidence discovery of novel or uncatalogued functional associations. |
| `Low` | Tier 3: Emerging/Single-source Evidence | The association has neither Tier 1 evidence nor all three Tier 2 conditions. All remaining cases belong to Tier 3. | Broad knowledge exploration and early-stage hypothesis generation. |

When explaining the API tier:

- Describe Tier 1 as evidence-code triggered at the aggregated trait level; do not require more than one qualifying code.
- Describe Tier 2 as requiring literature support, at least one non-`RiceMind_NLP` source, and aggregated `article_count > 10` simultaneously.
- Describe Tier 3 as the exhaustive fallback after Tier 1 and Tier 2.
- Do not independently execute these rules in the skill or report builders. Read the API tier and use the criteria only to explain what that returned tier means.
- If raw metadata appears inconsistent with the returned tier, preserve the API tier and flag the apparent metadata discrepancy rather than silently reclassifying the GTA.

Use the tiers to control wording:

| Evidence pattern | Use this language | Avoid |
|---|---|---|
| Tier 1 curated or experimental evidence | "RiceMind curated/experimental evidence supports..." | Claims beyond the retrieved curated, experimental, and sentence evidence |
| Tier 2 verified literature plus computational evidence | "RiceMind literature and computational evidence consistently supports/prioritizes..." | Calling the association manually curated or experimentally validated |
| Tier 3 emerging or single-source evidence | "RiceMind records an emerging/exploratory association..." | Strong mechanism, causality, or breeding recommendations |
| NLP sentence co-occurrence only | "co-reported", "mentioned together", "text-mined candidate" | "proves", "causes", "controls", or "validated" |
| Mixed or context-dependent evidence | "the RiceMind evidence appears context-dependent..." | Declaring a conflict from generic positive/negative words without reading the sentences |

## PMID Citation

- Use bracket-style PMID citations after mechanism, evidence, or ranking statements: `[12345678, 23456789]`.
- Never cite a PMID unless it appears in the RiceMind payload for that statement.
- Do not use one PMID list to support an entire paragraph if the paragraph contains multiple distinct claims.
- If sentence context is used, distinguish target sentence evidence from retrieved neighboring context.

## Mechanism Synthesis

Apply this section to every RiceMind output that describes biological, genetic, molecular, physiological, agronomic, or breeding mechanisms. Mechanism synthesis is a primary analytical result, not a decorative summary.

### Evidence-First Workflow

1. Retrieve and inspect the complete paginated Sentence Evidence set relevant to the user's question. Use the full normalized evidence table, not only top-ranked or representative sentences.
2. Read each non-duplicate sentence in context and identify its actual claim. Record the gene or locus, allele or perturbation, expression change, molecular function, pathway or process, biological context, phenotype, direction of effect, experimental setting, and PMID when present.
3. Build mechanism themes inductively from the current evidence. Let repeated entities, processes, phenotypes, interventions, and causal relationships define the themes; do not begin from a preset pathway, hormone, stress, pest, disease, or gene-family outline.
4. Connect compatible evidence into mechanistic chains when supported:
   - molecular identity or candidate locus
   - allele, mutation, expression, biochemical, or transgenic evidence
   - molecular function, regulation, pathway, signaling, metabolism, development, or stress-response context
   - cellular, tissue, whole-plant, or environmental response
   - phenotype endpoint
   - breeding, germplasm, or agronomic implication
5. Compare evidence across PMIDs rather than summarizing papers one by one. Identify convergence, complementary steps, context dependence, disagreements, missing links, and evidence that supports alternative interpretations.
6. Create an internal evidence map for every mechanism theme, linking each material statement to its Sentence Evidence, PMID, confidence tier, evidence codes, and sources before drafting prose.
7. Account for the full evidence set. Merge true duplicates, but do not cherry-pick only convenient sentences. Discuss relevant contradictory or context-specific evidence and retain secondary evidence that changes interpretation.

### Review-Style Writing Standard

- Write detailed, connected scientific paragraphs comparable in logic and structure to a high-quality review article. Use bullet points only for planning or evidence mapping, not as the final mechanism narrative.
- Begin each mechanism subsection with an evidence-derived conclusion or organizing question, then develop the molecular-to-phenotype logic with transitions across studies.
- Synthesize what multiple sentences jointly indicate. Do not produce a sentence inventory, trait-name paraphrase, PMID list, or repeated "gene X is associated with trait Y" statements.
- Tailor the scope, headings, depth, and terminology to the user's exact gene, trait, gene-trait pair, variety, breeding objective, or evidence-network question.
- Explain why each evidence cluster matters to the user's question and, when supported, how it connects to phenotype or breeding relevance.
- Preserve biological direction and context. Distinguish activation from repression, tolerance from susceptibility, expression correlation from perturbation evidence, and observations under different tissues, stages, treatments, genotypes, or environments.

### Reasoning and Citation Boundaries

- Cite every mechanistic statement at claim level with the supporting RiceMind PMIDs. Place citations immediately after the supported statement rather than assigning one PMID list to a multi-claim paragraph.
- Use all materially relevant PMIDs for a synthesized claim. Do not cite a PMID merely because it mentions the same gene or trait.
- Distinguish direct Sentence Evidence from integrative inference. Use language such as "collectively suggests", "supports a model in which", or "is consistent with" when connecting steps not directly demonstrated in one sentence.
- Do not convert correlation, NLP co-occurrence, expression association, or computational prediction into direct causality.
- Do not use external biological knowledge to fill missing mechanistic links. External knowledge may frame a search or explicitly labeled discussion, but it is not RiceMind-supported mechanism evidence.
- If Sentence Evidence is sparse, ambiguous, contradictory, or lacks the links needed for a mechanism, state that limitation and provide an evidence-grounded hypothesis rather than a complete causal model.

The final mechanism narrative must remain auditable to the retrieved Sentence Evidence while adding genuine synthesis, organization, and question-specific scientific reasoning.

## Candidate Ranking

Rank genes, traits, varieties, or evidence clusters transparently. Useful criteria:

- confidence tier
- curated/experimental evidence
- independent PMID count
- sentence evidence count
- evidence-code diversity
- source-database diversity
- ontology specificity
- direct pair evidence
- sentence clarity
- breeding relevance terms when applicable

State that ranks reflect RiceMind evidence density and relevance, not final biological importance.

## Uncertainty

Always report:

- unresolved query terms
- endpoint failures
- capped retrieval
- incomplete pagination
- broad trait terms that mix contexts
- ambiguous gene symbols or entity names
- missing journal/year/PMID metadata

Do not smooth over weak or contradictory evidence. Explain uncertainty using the sentence evidence and metadata.

## External Knowledge Boundary

External biology may help choose search terms, but the answer must distinguish external framing from RiceMind evidence. Do not present external knowledge as RiceMind-supported unless it appears in retrieved payloads.

## Anti-Hard-Coding Rule

No task template should prescribe a fixed biological mechanism, pest, hormone, pathway, trait list, or gene family. Templates define questions and structure; RiceMind payloads determine content.
