# Breeding Objective Patterns

Use this file when the user states a practical breeding goal rather than a single gene or trait.

## Goal Decomposition

Translate the user goal into RiceMind-searchable trait phrases. State the decomposition before ranking candidates.

The search terms below are exact, case-sensitive items from `All-Traits.txt`, which contains the 5,371 traits returned by the RiceMind All Traits API. Keep capitalization variants when the API contains both forms. Do not substitute abbreviations or plausible synonyms unless they are also present in that file.

Examples:

| User goal | Possible RiceMind trait searches |
|---|---|
| insect resistance | `insect resistance`, `insect damage resistance`, `brown planthopper resistance`, `white-backed planthopper resistance`, `green leafhopper resistance`, `leafhopper resistance`, `stem borer resistance`, `resistance to Lepidopteran insect`, `pest resistance`, `insect damage response trait`, `response to insect`, `Brown planthopper damage`, `Whitebacked planthopper damage`, `Green leafhopper damage`, `Stem borer damage` |
| disease resistance | `disease resistance`, `pathogen resistance`, `blast disease resistance`, `rice blast disease response`, `Leaf blast damage`, `Panicle blast incidence`, `Panicle blast damage`, `Panicle blast severity`, `rice bacterial blight disease resistance`, `bacterial blight disease resistance`, `bacterial leaf blight resistance`, `Bacterial blight damage`, `rice bacterial leaf streak disease resistance`, `Bacterial leaf streak damage`, `sheath blight disease resistance`, `rice leaf sheath blight disease response`, `Sheath blight`, `rice seedling blight disease resistance` |
| drought tolerance | `drought`, `drought tolerance`, `Drought injury`, `drought sensitivity`, `drought susceptibility index`, `drought recovery`, `Drought recovery`, `response to water deprivation`, `regulation of response to water deprivation`, `water stress`, `water use efficiency`, `response to desiccation`, `cellular response to desiccation`, `abscisic acid-activated signaling pathway`, `abscisic acid content`, `abscisic acid sensitivity`, `abscisic acid concentration`, `response to abscisic acid`, `cellular response to abscisic acid stimulus` |
| salinity tolerance | `salt`, `salt in the soil`, `Salt injury`, `salt tolerance`, `salt sensitivity`, `salt exposure`, `response to salt`, `response to salt stress`, `cellular response to salt`, `cellular response to salt stress`, `hyperosmotic salinity response`, `ion`, `sodium content`, `sodium concentration`, `sodium uptake`, `sodium ion transport`, `sodium ion homeostasis`, `root system sodium content`, `sodium to potassium content ratio`, `regulation of sodium ion transport`, `abscisic acid-activated signaling pathway`, `abscisic acid content`, `abscisic acid sensitivity`, `abscisic acid concentration`, `response to abscisic acid`, `cellular response to abscisic acid stimulus` |
| nitrogen use efficiency | `nitrogen use efficiency`, `nitrogen utilization`, `nitrogen harvest index`, `nitrogen content`, `leaf nitrogen content`, `grain nitrogen content`, `nitrogen sensitivity`, `nitrogen deficiency`, `response to nitrogen limitation`, `cellular response to nitrogen starvation`, `nitrate`, `nitrate uptake`, `nitrate transport`, `nitrate import`, `nitrate transmembrane transport`, `nitrate assimilation`, `response to nitrate`, `nitrate content`, `nitrate reductase activity`, `ammonium`, `ammonium transmembrane transport`, `glutamine synthetase content`, `glutamine synthetase activity`, `NADH glutamate synthase content`, `glutamate synthase (NADH) activity`, `glutamate synthase (NADPH) activity` |
| yield improvement | `crop yield`, `Grain yield`, `grain yield trait`, `grain yield per plant`, `Grain yield per plant`, `grain yield per panicle`, `yield trait`, `yield component`, `yield and yield component`, `grain number`, `grain number trait`, `grain number per plant`, `filled grain number`, `unfilled grain number`, `grain weight`, `Grain weight`, `average grain weight`, `100-grain weight`, `1000-grain weight`, `100-dehulled grain weight`, `1000-dehulled grain weight`, `panicle length`, `Panicle length`, `panicle number`, `Panicle number per plant`, `panicle weight`, `panicle dry weight`, `spikelet number`, `Spikelets per panicle`, `Filled spikelets per panicle`, `spikelet fertility`, `Spikelet fertility`, `harvest index`, `Harvest index` |
| lodging resistance | `lodging resistance`, `susceptibility to lodging`, `lodging incidence`, `root lodging resistance`, `plant height`, `Plant height`, `relative plant height`, `stem strength`, `Culm strength`, `stem diameter`, `basal internode diameter`, `Culm diameter - 1st internode`, `Culm wall thickness`, `Culm length`, `Second internode length`, `stem internode`, `culm angle`, `Culm angle`, `brittle culm`, `lignin`, `lignin content`, `lignin biosynthesis trait`, `lignin biosynthetic process`, `cellulose content`, `cellulose biosynthetic process` |

These are starting points, not fixed biological themes. They cover direct phenotype, response, and major component labels for these examples, not every potentially related ontology term. Use RiceMind returned evidence to decide which terms matter.

## Analysis Pattern

1. Decompose objective into trait phrases in the file "All-Traits.txt".
2. Run trait-centered evidence scans for each phrase.
3. Merge candidate genes across traits.
4. Rank candidates by evidence strength and relevance.
5. Identify tradeoff evidence, such as yield versus resistance, growth versus stress tolerance, or plant height versus lodging.
6. Summarize mechanism themes from sentence evidence. For each theme, describe the genetic mechanisms based on the sentence evidences in detail and give the PMID citations.
7. Recommend evidence gaps for experimental or database follow-up.

## Candidate Grouping

Group candidates by evidence role when supported:

- high-confidence or curated candidates
- repeated literature/NLP candidates
- QTL or locus candidates
- breeding-use candidates
- mechanism-rich candidates
- tradeoff candidates
- exploratory candidates

## Output Style

Use decision-oriented language but keep evidence boundaries:

- "RiceMind evidence prioritizes..."
- "The sentence evidence suggests this candidate is worth follow-up because..."
- "This is a literature-evidence candidate, not a validated breeding recommendation..."

Avoid:

- final cultivar recommendation
- unsupported causal claims
- assuming a trait term has one biological mechanism

## Sidecar Files

For large analyses, place non-empty sidecars in the sibling `{report_stem}_data/` directory required by `references/output-contracts.md`. Keep:

- objective decomposition JSON or Markdown
- per-trait payload JSON
- merged candidate ranking CSV
- normalized sentence evidence CSV
- evidence-network edge CSV

Do not retain a sidecar for a failed query or an empty per-trait result.

## Figures

For a formal breeding-objective report, run `scripts/build_report_figures.py` after the merged ranking and evidence sidecars are complete. Generate every non-empty data-supported figure, especially:

- candidate targets by Tier 1 or objective-specific article support
- candidate targets by objective-context independent PMID support
- objective-support trait count versus yield/growth or other user-specified caution signals
- Tier 1 trait distribution across candidates
- publication-year, journal, evidence-code, and source distributions when those fields are available

Use the user's actual objective and tradeoff columns; do not hard-code salinity or yield labels for unrelated breeding questions. Put images in `{report_stem}_data/figures/` and insert them into the final report.
