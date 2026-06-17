#!/usr/bin/env python
"""Build a trait-centered RiceMind evidence panorama.

Formal trait reports use a two-stage mechanism workflow:
1. retrieve/normalize sidecars and write a mechanism synthesis brief;
2. write a personalized PMID-backed mechanism Markdown from the complete
   sentence evidence, then rerun with --mechanism-md.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from build_report_figures import build_trait_figures, update_markdown
from normalize_ricemind_payload import candidate_gene_rows, find_sentence_rows, write_csv
from ricemind_api_client import DEFAULT_BASE_URL, RiceMindClient


REPORT_MECHANISM_TOPICS = 10
REPRESENTATIVE_SENTENCES_PER_TOPIC = 6
TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_-]{2,}")
GENERIC_STOPWORDS = {
    "about",
    "after",
    "also",
    "among",
    "analysis",
    "because",
    "been",
    "before",
    "between",
    "brown",
    "could",
    "data",
    "different",
    "during",
    "evidence",
    "from",
    "gene",
    "genes",
    "genetic",
    "have",
    "here",
    "however",
    "identified",
    "including",
    "into",
    "levels",
    "plant",
    "plants",
    "planthopper",
    "rice",
    "showed",
    "shown",
    "significant",
    "significantly",
    "study",
    "that",
    "their",
    "these",
    "this",
    "through",
    "trait",
    "traits",
    "using",
    "were",
    "with",
}


def top_values(rows: List[Dict[str, str]], key: str, n: int = 10) -> List[str]:
    counter = Counter(row.get(key, "") for row in rows if row.get(key, ""))
    return [f"{name} ({count})" for name, count in counter.most_common(n)]


def remove_output_file(path: Path) -> None:
    if path.is_file():
        path.unlink()


def write_json(path: Path, payload: Dict[str, Any]) -> bool:
    if not payload:
        remove_output_file(path)
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return True


def write_text(path: Path, text: str) -> bool:
    if not text.strip():
        remove_output_file(path)
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return True


def value(row: Dict[str, str], *keys: str) -> str:
    for key in keys:
        if row.get(key):
            return str(row.get(key, "")).strip()
    return ""


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def truncate(text: str, limit: int = 360) -> str:
    text = clean(text)
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 3)].rstrip() + "..."


def split_values(text: str) -> List[str]:
    parts = re.split(r"[;,|]\s*", text or "")
    return [part.strip() for part in parts if part.strip()]


def row_sentence(row: Dict[str, str]) -> str:
    return value(row, "sentence", "text", "evidence_sentence", "Evidence_Text")


def row_pmid(row: Dict[str, str]) -> str:
    return value(row, "PMID", "pmid", "pubmed_id", "pubmedId")


def row_sentence_id(row: Dict[str, str]) -> str:
    return value(row, "sentence_id", "Sentence_ID", "sent_id", "sentId")


def row_trait(row: Dict[str, str]) -> str:
    return value(row, "matched_trait_labels", "matched_trait_label", "trait", "query_trait")


def row_candidates(row: Dict[str, str]) -> List[str]:
    candidates = []
    for key in ("candidate_genes_text_mined", "candidate_gene", "genes", "gene"):
        candidates.extend(split_values(value(row, key)))
    seen = set()
    out = []
    for item in candidates:
        key = item.lower()
        if key not in seen:
            out.append(item)
            seen.add(key)
    return out


def normalize_keyword(token: str) -> str:
    token = token.strip(".,;:()[]{}'\"").replace("_", "-")
    if token.isupper() and len(token) <= 12:
        return token
    return token.lower()


def extract_keywords_from_text(text: str, limit: int = 12, exclude: Sequence[str] = ()) -> List[str]:
    excluded = {normalize_keyword(item) for item in exclude if item}
    counter: Counter[str] = Counter()
    for raw in TOKEN_RE.findall(text or ""):
        token = normalize_keyword(raw)
        if len(token) < 3:
            continue
        if token in GENERIC_STOPWORDS or token in excluded:
            continue
        if token.isdigit():
            continue
        counter[token] += 1
    return [term for term, _ in counter.most_common(limit)]


def row_keywords(row: Dict[str, str], exclude: Sequence[str] = ()) -> List[str]:
    return extract_keywords_from_text(
        " ".join(
            [
                row_sentence(row),
                value(row, "title", "Title", "article_title"),
                row_trait(row),
                " ".join(row_candidates(row)),
            ]
        ),
        limit=24,
        exclude=exclude,
    )


def collect_pmids(rows: Iterable[Dict[str, str]], limit: int = 12) -> List[str]:
    seen = []
    for row in rows:
        pmid = row_pmid(row)
        if pmid and pmid not in seen:
            seen.append(pmid)
        if len(seen) >= limit:
            break
    return seen


def evidence_priority(row: Dict[str, str]) -> Tuple[int, int, str]:
    has_pmid = 0 if row_pmid(row) else 1
    has_gene = 0 if row_candidates(row) else 1
    return (has_pmid, has_gene, row_sentence_id(row) or row_pmid(row) or row_sentence(row)[:80])


def representative_records(rows: List[Dict[str, str]], limit: int = REPRESENTATIVE_SENTENCES_PER_TOPIC) -> List[Dict[str, str]]:
    selected: List[Dict[str, str]] = []
    seen = set()
    for row in sorted(rows, key=evidence_priority):
        key = (row_pmid(row), row_sentence_id(row), row_sentence(row)[:100])
        if key in seen:
            continue
        seen.add(key)
        selected.append(
            {
                "PMID": row_pmid(row),
                "sentence_id": row_sentence_id(row),
                "year": value(row, "year", "Year", "publication_year"),
                "journal": value(row, "journal", "Journal"),
                "title": value(row, "title", "Title", "article_title"),
                "trait_label": row_trait(row),
                "candidate_genes": ";".join(row_candidates(row)),
                "sentence": row_sentence(row),
            }
        )
        if len(selected) >= limit:
            break
    return selected


def induce_mechanism_topics(sentences: List[Dict[str, str]], trait: str) -> List[Dict[str, Any]]:
    if not sentences:
        return []
    exclude = extract_keywords_from_text(trait, limit=20)
    term_counter: Counter[str] = Counter()
    row_terms: List[Tuple[Dict[str, str], List[str]]] = []
    for row in sentences:
        terms = row_keywords(row, exclude=exclude)
        row_terms.append((row, terms))
        term_counter.update(terms)

    topics: List[Dict[str, Any]] = []
    used_signatures: List[set] = []
    for seed, _ in term_counter.most_common(40):
        matched = [row for row, terms in row_terms if seed in terms]
        if len(matched) < 2:
            continue
        signature = {(row_pmid(row), row_sentence_id(row), row_sentence(row)[:80]) for row in matched[:80]}
        if any(signature and len(signature & prior) / max(1, len(signature)) > 0.80 for prior in used_signatures):
            continue
        used_signatures.append(signature)
        matched_ids = {id(row) for row in matched}
        co_terms = Counter(term for row, terms in row_terms if id(row) in matched_ids for term in terms if term != seed)
        genes = Counter(gene for row in matched for gene in row_candidates(row))
        traits = Counter(row_trait(row) for row in matched if row_trait(row))
        pmid_set = {row_pmid(row) for row in matched if row_pmid(row)}
        title_terms = extract_keywords_from_text(
            " ".join(value(row, "title", "Title", "article_title") for row in matched),
            limit=10,
            exclude=exclude,
        )
        topic_label = "; ".join([seed] + [term for term, _ in co_terms.most_common(2)])
        topics.append(
            {
                "topic": topic_label,
                "seed_terms": [seed] + [term for term, _ in co_terms.most_common(8)],
                "sentence_count": len(matched),
                "pmid_count": len(pmid_set),
                "top_pmids": collect_pmids(sorted(matched, key=evidence_priority), 12),
                "top_candidates": [gene for gene, _ in genes.most_common(12)],
                "top_trait_contexts": [name for name, _ in traits.most_common(8)],
                "top_title_terms": title_terms,
                "representative_sentences": representative_records(matched),
            }
        )
        if len(topics) >= REPORT_MECHANISM_TOPICS:
            break
    return topics


def build_claim_cards(topics: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    cards: List[Dict[str, str]] = []
    seen = set()
    for topic in topics:
        for item in topic.get("representative_sentences", []):
            key = (topic["topic"], item.get("PMID", ""), item.get("sentence_id", ""), item.get("sentence", "")[:100])
            if key in seen:
                continue
            seen.add(key)
            cards.append(
                {
                    "topic": topic["topic"],
                    "candidate_genes": item.get("candidate_genes", ""),
                    "trait_label": item.get("trait_label", ""),
                    "PMID": item.get("PMID", ""),
                    "sentence_id": item.get("sentence_id", ""),
                    "year": item.get("year", ""),
                    "journal": item.get("journal", ""),
                    "title": item.get("title", ""),
                    "sentence": item.get("sentence", ""),
                    "writing_use": (
                        "Use this as an evidence card. Extract the actual claim, material/context, "
                        "perturbation or association, phenotype endpoint, and evidence boundary before drafting."
                    ),
                }
            )
    return cards


def build_mechanism_evidence_bundle(
    trait: str,
    sentences: List[Dict[str, str]],
    candidates: List[Dict[str, str]],
) -> Dict[str, Any]:
    topics = induce_mechanism_topics(sentences, trait)
    return {
        "trait": trait,
        "generated": date.today().isoformat(),
        "sentence_count": len(sentences),
        "unique_pmid_count": len({row_pmid(row) for row in sentences if row_pmid(row)}),
        "candidate_count": len(candidates),
        "topics": topics,
        "claim_cards": build_claim_cards(topics),
        "instructions": (
            "Use this bundle together with the complete sentence_evidence.csv and candidate_genes.csv. "
            "For trait-centered reports, organize the mechanism synthesis around phenotype dimensions, "
            "candidate-gene groups, tissue/development/environment contexts, and breeding implications. "
            "Do not treat trait labels, keyword counts, topic labels, or representative sentences as the final mechanism. "
            "Read the full evidence table, write claim-level PMID citations, distinguish curated/experimental evidence "
            "from RiceMind_NLP co-occurrence, and state missing links or context dependence."
        ),
    }


def build_mechanism_prompt_markdown(
    trait: str,
    bundle: Dict[str, Any],
    sentence_csv_name: str,
    candidate_csv_name: str,
    language: str,
) -> str:
    is_zh = language.lower().startswith("zh")
    lines = [
        f"# RiceMind trait mechanism synthesis brief: {trait}",
        "",
    ]
    if is_zh:
        lines.extend(
            [
                "本文件不是最终机制综述。请结合完整 sentence evidence CSV 和 candidate genes CSV，写出可作为正式报告正文的 trait-centered 机制 Markdown。",
                "",
                f"- 完整句证表：`{sentence_csv_name}`",
                f"- 候选基因表：`{candidate_csv_name}`",
                f"- 句证总数：{bundle.get('sentence_count', 0)}",
                f"- PMID 数：{bundle.get('unique_pmid_count', 0)}",
                "",
                "写作要求：",
                "- 以 trait 为中心组织，不照搬 gene report 的单基因章节逻辑。",
                "- 从完整句证中归纳机制主题；主题应体现表型维度、候选基因群、组织/发育/环境和育种场景。",
                "- 每个机制判断后立即引用 RiceMind payload/CSV 中出现的 PMID。",
                "- 区分 curated/experimental evidence、数据库 evidence、RiceMind_NLP 共现和整合推断。",
                "- 不要把下面的 topic 统计、关键词或代表句当作最终机制段落。",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "This file is not the final mechanism synthesis. Use it with the complete sentence evidence CSV and candidate genes CSV to write the formal trait-centered mechanism Markdown.",
                "",
                f"- Complete sentence evidence table: `{sentence_csv_name}`",
                f"- Candidate genes table: `{candidate_csv_name}`",
                f"- Sentence records: {bundle.get('sentence_count', 0)}",
                f"- Unique PMIDs: {bundle.get('unique_pmid_count', 0)}",
                "",
                "Writing requirements:",
                "- Organize around the trait, not a single-gene report structure.",
                "- Derive mechanism themes from complete sentence evidence, including phenotype dimensions, candidate groups, tissue/development/environment contexts, and breeding scenarios.",
                "- Cite RiceMind PMIDs immediately after each mechanistic claim.",
                "- Distinguish curated/experimental evidence, database evidence, RiceMind_NLP co-occurrence, and integrative inference.",
                "- Do not treat the topic statistics, keywords, or representative sentences below as final mechanism prose.",
                "",
            ]
        )

    for idx, topic in enumerate(bundle.get("topics", []), 1):
        lines.extend(
            [
                f"## Topic {idx}: {topic.get('topic', 'NA')}",
                "",
                f"- sentence_count: {topic.get('sentence_count', 0)}",
                f"- pmid_count: {topic.get('pmid_count', 0)}",
                f"- seed_terms: {', '.join(topic.get('seed_terms', []))}",
                f"- top_candidates: {', '.join(topic.get('top_candidates', [])) or 'NA'}",
                f"- top_trait_contexts: {'; '.join(topic.get('top_trait_contexts', [])) or 'NA'}",
                f"- top_pmids: {', '.join(topic.get('top_pmids', [])) or 'NA'}",
                "- representative_sentences:",
            ]
        )
        for item in topic.get("representative_sentences", [])[:5]:
            source = ", ".join(part for part in [item.get("PMID", ""), item.get("year", ""), item.get("trait_label", "")] if part)
            genes = item.get("candidate_genes", "")
            prefix = f"  - ({source})"
            if genes:
                prefix += f" genes={genes};"
            lines.append(f"{prefix} {truncate(item.get('sentence', ''), 420)}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def read_mechanism_markdown(path: Optional[Path]) -> str:
    if not path:
        return ""
    return path.read_text(encoding="utf-8").strip()


def write_markdown(
    path: Path,
    trait: str,
    payload: Dict,
    sentences: List[Dict[str, str]],
    candidates: List[Dict[str, str]],
    retrieval_error: Optional[str] = None,
    mechanism_markdown: str = "",
    allow_summary_only: bool = False,
) -> None:
    pmids = sorted({row_pmid(row) for row in sentences if row_pmid(row)})
    years = [value(row, "year", "Year", "publication_year") for row in sentences if value(row, "year", "Year", "publication_year")]
    journals = top_values(sentences, "journal", 10)

    lines = [
        f"# RiceMind Trait Evidence Panorama: {trait}",
        "",
        "## Retrieval Scope",
        "",
        f"- Endpoint: `/search-by-trait/`",
        f"- Pages retrieved: {payload.get('pages_retrieved', 'NA')}",
        f"- Sentence records: {len(sentences)}",
        f"- Unique PMIDs: {len(pmids)}",
    ]
    if retrieval_error:
        lines.append(f"- Retrieval error: {retrieval_error}")
    elif not sentences:
        lines.append("- Retrieval result: no usable Sentence Evidence records returned")
    if years:
        lines.append(f"- Year span: {min(years)}-{max(years)}")
    if journals:
        lines.extend(["", "## Top Journals", ""])
        lines.extend([f"- {item}" for item in journals])

    lines.extend(["", "## Top Candidate Genes", ""])
    if candidates:
        for row in candidates[:20]:
            lines.append(
                f"- {row['candidate_gene']}: {row['sentence_count']} sentences, "
                f"{row['unique_pmids']} PMIDs; top contexts: {row['top_traits'] or 'NA'}; "
                f"PMIDs: [{', '.join(row['pmids'].split(';')[:5])}]"
            )
    else:
        lines.append("No candidate gene mentions were extracted from the returned RiceMind sentence evidence.")

    lines.extend(["", "## Mechanism Synthesis", ""])
    if mechanism_markdown:
        lines.append(mechanism_markdown.strip())
    elif allow_summary_only:
        lines.append(
            "Mechanism synthesis was intentionally omitted because `--allow-summary-only` was used. "
            "For formal trait reports, rerun this builder after writing a personalized PMID-backed "
            "mechanism Markdown with `--mechanism-md`."
        )
    elif not sentences:
        lines.append("No usable sentence evidence was returned, so no mechanism synthesis can be written.")

    lines.extend(
        [
            "",
            "## Evidence Boundary",
            "",
            "Candidate genes are prioritized from RiceMind sentence evidence. If the API response lacks explicit gene entity fields, candidates extracted from sentence text should be treated as text-mined hypotheses rather than a complete curated trait-to-gene catalog.",
            "RiceMind_NLP sentence co-occurrence is not curated or experimental validation. Formal mechanism and breeding statements must trace to claim-level sentence evidence, PMID, evidence code, source database, and confidence tier when available.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a trait-centered RiceMind evidence report.")
    parser.add_argument("--trait", required=True)
    parser.add_argument("--out-prefix", type=Path, required=True)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--limit", type=int, default=500)
    parser.add_argument("--input-json", type=Path, help="Use an existing payload instead of calling the API")
    parser.add_argument("--language", default="zh", choices=["en", "zh"], help="Language for the mechanism synthesis brief")
    parser.add_argument(
        "--mechanism-md",
        type=Path,
        help="Personalized PMID-backed trait mechanism synthesis Markdown generated from this run's complete evidence",
    )
    parser.add_argument("--sidecars-only", action="store_true", help="Write payload/CSV/mechanism bundle/brief only; skip report generation")
    parser.add_argument("--write-brief", action="store_true", help="Write the mechanism synthesis brief even when --mechanism-md is supplied")
    parser.add_argument(
        "--allow-summary-only",
        action="store_true",
        help="Permit the lightweight summary report without a personalized mechanism synthesis",
    )
    args = parser.parse_args()

    if args.mechanism_md and (not args.mechanism_md.is_file() or not args.mechanism_md.read_text(encoding="utf-8").strip()):
        parser.error("--mechanism-md must point to a readable, non-empty Markdown file")
    if args.sidecars_only and args.allow_summary_only:
        parser.error("Use either --sidecars-only or --allow-summary-only, not both")

    retrieval_error: Optional[str] = None
    if args.input_json:
        payload = json.loads(args.input_json.read_text(encoding="utf-8"))
    else:
        client = RiceMindClient(args.base_url)
        try:
            payload = client.fetch_all("search-by-trait", result_keys=["results", "sentence_evidence"], trait=args.trait, limit=args.limit)
        except Exception as exc:
            payload = {}
            retrieval_error = str(exc)

    sentences = find_sentence_rows(payload)
    candidates = candidate_gene_rows(sentences)

    report_path = args.out_prefix.with_name(args.out_prefix.name + "_trait_evidence_summary.md")
    data_dir = report_path.parent / f"{report_path.stem}_data"
    payload_path = data_dir / f"{report_path.stem}_payload.json"
    sentence_csv = data_dir / f"{report_path.stem}_sentence_evidence.csv"
    candidate_csv = data_dir / f"{report_path.stem}_candidate_genes.csv"
    mechanism_bundle_json = data_dir / f"{report_path.stem}_mechanism_evidence_bundle.json"
    mechanism_brief_md = data_dir / f"{report_path.stem}_mechanism_synthesis_brief.md"
    claim_cards_csv = data_dir / f"{report_path.stem}_mechanism_claim_cards.csv"

    wrote_sidecars: List[Path] = []
    if sentences:
        data_dir.mkdir(parents=True, exist_ok=True)
        payload_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        wrote_sidecars.append(payload_path)
    else:
        remove_output_file(payload_path)

    if write_csv(sentence_csv, sentences):
        wrote_sidecars.append(sentence_csv)
    if write_csv(candidate_csv, candidates):
        wrote_sidecars.append(candidate_csv)

    mechanism_bundle = build_mechanism_evidence_bundle(args.trait, sentences, candidates)
    if sentences and write_json(mechanism_bundle_json, mechanism_bundle):
        wrote_sidecars.append(mechanism_bundle_json)
    elif not sentences:
        remove_output_file(mechanism_bundle_json)

    claim_cards = mechanism_bundle.get("claim_cards", [])
    if write_csv(claim_cards_csv, claim_cards):
        wrote_sidecars.append(claim_cards_csv)

    if sentences and (args.write_brief or not args.mechanism_md):
        brief = build_mechanism_prompt_markdown(args.trait, mechanism_bundle, sentence_csv.name, candidate_csv.name, args.language)
        if write_text(mechanism_brief_md, brief):
            wrote_sidecars.append(mechanism_brief_md)
    else:
        remove_output_file(mechanism_brief_md)

    if args.sidecars_only:
        for path in wrote_sidecars:
            print(f"Wrote {path}")
        return 0

    if sentences and not args.mechanism_md and not args.allow_summary_only:
        print(
            "Trait sentence evidence is available, so a formal trait report requires a personalized --mechanism-md synthesis. "
            f"Use {mechanism_brief_md} with {sentence_csv} and {candidate_csv} to write the mechanism review, then rerun with --mechanism-md. "
            "For a quick non-mechanistic summary, rerun with --allow-summary-only.",
            file=sys.stderr,
        )
        for path in wrote_sidecars:
            print(f"Wrote {path}")
        return 3

    mechanism_markdown = read_mechanism_markdown(args.mechanism_md)
    write_markdown(
        report_path,
        args.trait,
        payload,
        sentences,
        candidates,
        retrieval_error,
        mechanism_markdown=mechanism_markdown,
        allow_summary_only=args.allow_summary_only,
    )
    figures = build_trait_figures(sentences, candidates, data_dir / "figures")
    update_markdown(report_path, figures)
    figures_dir = data_dir / "figures"
    if figures_dir.is_dir():
        try:
            figures_dir.rmdir()
        except OSError:
            pass
    if data_dir.is_dir():
        try:
            data_dir.rmdir()
        except OSError:
            pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
