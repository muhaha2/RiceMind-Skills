#!/usr/bin/env python
"""Build simple evidence-network node and edge tables from RiceMind evidence."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Set, Tuple

from normalize_ricemind_payload import extract_gene_mentions, find_sentence_rows


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: List[Dict[str, str]], fields: Iterable[str]) -> bool:
    if not rows:
        if path.is_file():
            path.unlink()
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields))
        writer.writeheader()
        writer.writerows(rows)
    return True


def build_edges(sentences: List[Dict[str, str]]) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    edge_stats: Dict[Tuple[str, str, str], Dict[str, object]] = defaultdict(lambda: {"sentences": 0, "pmids": set()})
    node_types: Dict[str, str] = {}
    genes_by_pmid: Dict[str, Set[str]] = defaultdict(set)
    traits_by_pmid: Dict[str, Set[str]] = defaultdict(set)
    direct_pmids_by_pair: Dict[Tuple[str, str], Set[str]] = defaultdict(set)

    for row in sentences:
        pmid = row.get("PMID", "")
        trait = row.get("trait", "")
        genes = set(extract_gene_mentions(row))

        if trait:
            node_types[trait] = "trait"
            if pmid:
                traits_by_pmid[pmid].add(trait)
        for g in genes:
            node_types[g] = "gene"
            if pmid:
                genes_by_pmid[pmid].add(g)
            if trait:
                key = (g, trait, "gene-trait-sentence")
                edge_stats[key]["sentences"] = int(edge_stats[key]["sentences"]) + 1
                if pmid:
                    edge_stats[key]["pmids"].add(pmid)
                    direct_pmids_by_pair[(g, trait)].add(pmid)
            if pmid:
                node_types[pmid] = "pmid"
                key = (g, pmid, "gene-pmid")
                edge_stats[key]["sentences"] = int(edge_stats[key]["sentences"]) + 1
                edge_stats[key]["pmids"].add(pmid)

    # Article-level co-occurrence is weaker than a sentence-local association.
    # Keep it as a separate edge type and never promote it to direct GTA evidence.
    for pmid, genes in genes_by_pmid.items():
        for gene in genes:
            for trait in traits_by_pmid.get(pmid, set()):
                if pmid in direct_pmids_by_pair.get((gene, trait), set()):
                    continue
                key = (gene, trait, "gene-trait-pmid-cooccurrence")
                edge_stats[key]["pmids"].add(pmid)

    nodes = [{"id": node, "type": typ} for node, typ in sorted(node_types.items(), key=lambda item: (item[1], item[0]))]
    edges = []
    for (source, target, edge_type), stats in sorted(edge_stats.items(), key=lambda item: (item[0][2], item[0][0], item[0][1])):
        pmids = sorted(stats["pmids"])
        edges.append({
            "source": source,
            "target": target,
            "edge_type": edge_type,
            "sentence_count": str(stats["sentences"]),
            "unique_pmids": str(len(pmids)),
            "pmids": ";".join(pmids[:30]),
        })
    return nodes, edges


def main() -> None:
    parser = argparse.ArgumentParser(description="Build RiceMind evidence network nodes and edges.")
    parser.add_argument("--sentences-csv", type=Path)
    parser.add_argument("--input-json", type=Path)
    parser.add_argument("--out-prefix", type=Path, required=True)
    args = parser.parse_args()

    if not args.sentences_csv and not args.input_json:
        parser.error("Provide --sentences-csv or --input-json")

    if args.sentences_csv:
        sentences = read_csv(args.sentences_csv)
    else:
        payload = json.loads(args.input_json.read_text(encoding="utf-8"))
        sentences = find_sentence_rows(payload)

    nodes, edges = build_edges(sentences)
    data_dir = args.out_prefix.parent / f"{args.out_prefix.name}_data"
    write_csv(data_dir / f"{args.out_prefix.name}_nodes.csv", nodes, ["id", "type"])
    write_csv(data_dir / f"{args.out_prefix.name}_edges.csv", edges, ["source", "target", "edge_type", "sentence_count", "unique_pmids", "pmids"])
    if data_dir.is_dir():
        try:
            data_dir.rmdir()
        except OSError:
            pass


if __name__ == "__main__":
    main()
