#!/usr/bin/env python
"""Normalize RiceMind JSON payloads into reusable CSV tables."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


RAP_RE = re.compile(r"\b(?:LOC_)?Os\d{2}g\d{7}\b", re.I)
TEXT_GENE_TOKEN_RE = re.compile(
    r"\b(?:Os[A-Z0-9][A-Za-z0-9_.-]{1,}|[A-Za-z][A-Za-z0-9_.-]*\d[A-Za-z0-9_.-]*)\b"
)
GENE_STOPWORDS = {
    "DNA", "RNA", "PCR", "QTL", "GO", "TO", "PO", "CO", "RTO", "PMID", "NLP",
    "ABA", "GA", "JA", "SA", "ROS", "WT", "DEG", "DEGS", "SNP", "SNPS", "H2O",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def walk(obj: Any) -> Iterable[Any]:
    yield obj
    if isinstance(obj, dict):
        for value in obj.values():
            yield from walk(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from walk(value)


def first_value(obj: Dict[str, Any], keys: Iterable[str]) -> str:
    for key in keys:
        value = obj.get(key)
        if value not in (None, ""):
            if isinstance(value, (list, dict)):
                return json.dumps(value, ensure_ascii=False)
            return str(value)
    return ""


def find_sentence_rows(payload: Any) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for obj in walk(payload):
        if not isinstance(obj, dict):
            continue
        text = first_value(obj, ("text", "sentence", "sentence_text"))
        pmid = first_value(obj, ("PMID", "pmid"))
        sent_id = first_value(obj, ("sent_id", "sentence_id"))
        if not text or not (pmid or sent_id):
            continue
        rows.append({
            "PMID": pmid,
            "sent_id": sent_id,
            "year": first_value(obj, ("year", "publication_year")),
            "journal": first_value(obj, ("journal",)),
            "title": first_value(obj, ("title",)),
            "doi": first_value(obj, ("doi",)),
            "text": text,
            "gene": first_value(obj, ("gene", "gene_symbol", "standard_rap_id", "rap_id")),
            "trait": first_value(obj, ("trait", "trait_name", "trait_description")),
            "ontology_id": first_value(obj, ("ontology_id", "Ontology_ID")),
            "ontology_type": first_value(obj, ("ontology_type", "Ontology_Type", "onto_type")),
            "confidence": first_value(obj, ("confidence", "confidence_tier")),
            "evidence_code": first_value(obj, ("evidence_code", "Evidence_Code", "evidence_codes")),
            "source_db": first_value(obj, ("source_db", "Source_DB", "sources")),
        })
    return dedupe_rows(rows, ("PMID", "sent_id", "text", "trait", "gene"))


def find_trait_rows(payload: Any) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for obj in walk(payload):
        if not isinstance(obj, dict):
            continue
        trait = first_value(obj, ("trait", "trait_name", "trait_description", "Trait_Description"))
        ontology = first_value(obj, ("ontology_id", "Ontology_ID"))
        if not trait or not (ontology or "article_count" in obj or "confidence_tier" in obj):
            continue
        rows.append({
            "trait": trait,
            "ontology_id": ontology,
            "ontology_type": first_value(obj, ("ontology_type", "Ontology_Type")),
            "confidence": first_value(obj, ("confidence", "confidence_tier")),
            "evidence_codes": first_value(obj, ("evidence_codes", "Evidence_Code", "evidence_code")),
            "sources": first_value(obj, ("sources", "Source_DB", "source_db")),
            "article_count": first_value(obj, ("article_count", "literature_support_count")),
            "earliest_year": first_value(obj, ("earliest_year", "first_mention_year")),
        })
    return dedupe_rows(rows, ("trait", "ontology_id", "confidence"))


def candidate_gene_rows(sentences: List[Dict[str, str]]) -> List[Dict[str, str]]:
    stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"sentences": 0, "pmids": set(), "traits": Counter(), "journals": Counter()})
    for row in sentences:
        mentions = extract_gene_mentions(row)
        for gene in mentions:
            stats[gene]["sentences"] += 1
            if row.get("PMID"):
                stats[gene]["pmids"].add(row["PMID"])
            if row.get("trait"):
                stats[gene]["traits"][row["trait"]] += 1
            if row.get("journal"):
                stats[gene]["journals"][row["journal"]] += 1

    out: List[Dict[str, str]] = []
    for gene, data in sorted(stats.items(), key=lambda item: (len(item[1]["pmids"]), item[1]["sentences"]), reverse=True):
        out.append({
            "candidate_gene": gene,
            "sentence_count": str(data["sentences"]),
            "unique_pmids": str(len(data["pmids"])),
            "top_traits": "; ".join([name for name, _ in data["traits"].most_common(5)]),
            "top_journals": "; ".join([name for name, _ in data["journals"].most_common(5)]),
            "pmids": ";".join(sorted(data["pmids"])[:20]),
        })
    return out


def extract_gene_mentions(row: Dict[str, str]) -> List[str]:
    mentions = set()
    # Explicit RiceMind entity fields are authoritative, including symbols that
    # cannot be distinguished safely from ordinary abbreviations in free text.
    for key in ("gene",):
        if row.get(key):
            mentions.add(row[key])
    text = row.get("text", "")
    mentions.update(match.group(0) for match in RAP_RE.finditer(text))
    # Free-text fallback is deliberately conservative: require an Os-prefixed
    # symbol or a token containing a digit. Pure uppercase biology abbreviations
    # such as EXP, IDA, MAPK, and NADPH are not inferred as genes.
    for match in TEXT_GENE_TOKEN_RE.finditer(text):
        token = match.group(0).strip(".,;:()[]{}")
        if token.upper() in GENE_STOPWORDS:
            continue
        if len(token) < 3:
            continue
        mentions.add(token)
    return sorted(mentions)


def dedupe_rows(rows: List[Dict[str, str]], keys: Tuple[str, ...]) -> List[Dict[str, str]]:
    seen = set()
    out = []
    for row in rows:
        marker = tuple(row.get(key, "") for key in keys)
        if marker in seen:
            continue
        seen.add(marker)
        out.append(row)
    return out


def write_csv(path: Path, rows: List[Dict[str, str]]) -> bool:
    if not rows:
        if path.is_file():
            path.unlink()
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize RiceMind payload JSON into CSV tables.")
    parser.add_argument("--input-json", type=Path, required=True)
    parser.add_argument("--out-prefix", type=Path, required=True)
    args = parser.parse_args()

    payload = load_json(args.input_json)
    sentences = find_sentence_rows(payload)
    traits = find_trait_rows(payload)
    candidates = candidate_gene_rows(sentences)

    data_dir = args.out_prefix.parent / f"{args.out_prefix.name}_data"
    write_csv(data_dir / f"{args.out_prefix.name}_sentences.csv", sentences)
    write_csv(data_dir / f"{args.out_prefix.name}_traits.csv", traits)
    write_csv(data_dir / f"{args.out_prefix.name}_candidate_genes.csv", candidates)
    if data_dir.is_dir():
        try:
            data_dir.rmdir()
        except OSError:
            pass


if __name__ == "__main__":
    main()
