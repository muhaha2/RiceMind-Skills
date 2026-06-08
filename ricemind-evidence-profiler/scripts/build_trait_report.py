#!/usr/bin/env python
"""Build a trait-centered RiceMind evidence panorama."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional

from normalize_ricemind_payload import candidate_gene_rows, find_sentence_rows, write_csv
from ricemind_api_client import DEFAULT_BASE_URL, RiceMindClient


def top_values(rows: List[Dict[str, str]], key: str, n: int = 10) -> List[str]:
    counter = Counter(row.get(key, "") for row in rows if row.get(key, ""))
    return [f"{name} ({count})" for name, count in counter.most_common(n)]


def write_markdown(
    path: Path,
    trait: str,
    payload: Dict,
    sentences: List[Dict[str, str]],
    candidates: List[Dict[str, str]],
    retrieval_error: Optional[str] = None,
) -> None:
    pmids = sorted({row.get("PMID", "") for row in sentences if row.get("PMID")})
    years = [row.get("year", "") for row in sentences if row.get("year")]
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

    lines.extend([
        "",
        "## Evidence Boundary",
        "",
        "Candidate genes are prioritized from RiceMind sentence evidence. If the API response lacks explicit gene entity fields, candidates extracted from sentence text should be treated as text-mined hypotheses rather than a complete curated trait-to-gene catalog.",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a trait-centered RiceMind evidence report.")
    parser.add_argument("--trait", required=True)
    parser.add_argument("--out-prefix", type=Path, required=True)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--limit", type=int, default=500)
    parser.add_argument("--input-json", type=Path, help="Use an existing payload instead of calling the API")
    args = parser.parse_args()

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
    if sentences:
        data_dir.mkdir(parents=True, exist_ok=True)
        payload_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    elif payload_path.is_file():
        payload_path.unlink()

    write_csv(data_dir / f"{report_path.stem}_sentence_evidence.csv", sentences)
    write_csv(data_dir / f"{report_path.stem}_candidate_genes.csv", candidates)
    write_markdown(report_path, args.trait, payload, sentences, candidates, retrieval_error)
    if data_dir.is_dir():
        try:
            data_dir.rmdir()
        except OSError:
            pass


if __name__ == "__main__":
    main()
