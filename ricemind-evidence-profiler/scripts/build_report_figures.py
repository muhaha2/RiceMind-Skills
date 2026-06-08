#!/usr/bin/env python
"""Generate RiceMind report figures from normalized CSV sidecars."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


FIGURE_MARKER_START = "<!-- RICEMIND_FIGURES_START -->"
FIGURE_MARKER_END = "<!-- RICEMIND_FIGURES_END -->"
TARGET_FIELDS = ("target", "candidate_gene", "gene", "candidate", "symbol")
YEAR_FIELDS = ("year", "publication_year")
JOURNAL_FIELDS = ("journal",)
EVIDENCE_CODE_FIELDS = ("evidence_code", "evidence_codes", "Evidence_Code")
SOURCE_FIELDS = ("source_db", "sources", "Source_DB")


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def first_field(rows: Sequence[Dict[str, str]], candidates: Sequence[str]) -> str:
    if not rows:
        return ""
    fields = set(rows[0])
    return next((field for field in candidates if field in fields), "")


def number(value: object) -> float:
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return 0.0


def split_values(value: str) -> Iterable[str]:
    for item in re.split(r"[;,|]", value or ""):
        cleaned = item.strip().strip("[]'\"")
        if cleaned:
            yield cleaned


def humanize(field: str) -> str:
    text = field.replace("riceMind", "RiceMind").replace("_", " ").strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\btier\s*1\b", "Tier 1", text, flags=re.I)
    text = re.sub(r"\bpmids\b", "PMIDs", text, flags=re.I)
    text = re.sub(r"\bpmid\b", "PMID", text, flags=re.I)
    return text[:1].upper() + text[1:]


def _save_bar(
    labels: Sequence[str],
    values: Sequence[float],
    title: str,
    xlabel: str,
    out_path: Path,
    color: str = "#4f7cac",
) -> Optional[Path]:
    pairs = [(str(label), float(value)) for label, value in zip(labels, values) if str(label).strip() and float(value) > 0]
    if not pairs:
        if out_path.is_file():
            out_path.unlink()
        return None
    pairs = pairs[:20]
    labels = [item[0] for item in pairs][::-1]
    values = [item[1] for item in pairs][::-1]
    try:
        import matplotlib.pyplot as plt

        out_path.parent.mkdir(parents=True, exist_ok=True)
        fig, ax = plt.subplots(figsize=(8.2, max(3.8, 0.42 * len(labels) + 1.5)))
        ax.barh(labels, values, color=color)
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.grid(axis="x", alpha=0.2)
        fig.tight_layout()
        fig.savefig(out_path, dpi=180, bbox_inches="tight")
        plt.close(fig)
        return out_path
    except ImportError:
        return _save_bar_pillow(labels, values, title, xlabel, out_path, color)


def _save_bar_pillow(
    labels: Sequence[str],
    values: Sequence[float],
    title: str,
    xlabel: str,
    out_path: Path,
    color: str,
) -> Optional[Path]:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return None
    width = 1500
    row_height = 52
    height = 170 + row_height * len(labels)
    left, right, top = 390, 80, 90
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    max_value = max(values) or 1
    draw.text((left, 25), title, fill="#111827", font=font)
    draw.text((left, height - 45), xlabel, fill="#374151", font=font)
    for index, (label, value) in enumerate(zip(labels, values)):
        y = top + index * row_height
        draw.text((15, y + 8), label[:55], fill="#111827", font=font)
        bar_width = int((width - left - right) * value / max_value)
        draw.rectangle((left, y, left + bar_width, y + 30), fill=color)
        draw.text((left + bar_width + 8, y + 8), f"{value:g}", fill="#111827", font=font)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(out_path)
    return out_path


def _save_grouped_bar(
    labels: Sequence[str],
    first: Sequence[float],
    second: Sequence[float],
    title: str,
    ylabel: str,
    first_label: str,
    second_label: str,
    out_path: Path,
) -> Optional[Path]:
    rows = [
        (str(label), float(a), float(b))
        for label, a, b in zip(labels, first, second)
        if str(label).strip() and (float(a) > 0 or float(b) > 0)
    ][:20]
    if not rows:
        if out_path.is_file():
            out_path.unlink()
        return None
    try:
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        return None
    labels = [row[0] for row in rows]
    first = [row[1] for row in rows]
    second = [row[2] for row in rows]
    x = np.arange(len(labels))
    width = 0.4
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(max(8.2, len(labels) * 0.72), 5.2))
    ax.bar(x - width / 2, first, width, label=first_label, color="#2b7bba")
    ax.bar(x + width / 2, second, width, label=second_label, color="#e6812f")
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.legend()
    ax.grid(axis="y", alpha=0.2)
    fig.tight_layout()
    fig.savefig(out_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return out_path


def counter_figure(
    rows: Sequence[Dict[str, str]],
    field_candidates: Sequence[str],
    title: str,
    xlabel: str,
    out_path: Path,
    color: str = "#4f7cac",
) -> Optional[Path]:
    field = first_field(rows, field_candidates)
    if not field:
        return None
    counter: Counter = Counter()
    for row in rows:
        for value in split_values(row.get(field, "")):
            counter[value] += 1
    pairs = counter.most_common(20)
    return _save_bar([key for key, _ in pairs], [value for _, value in pairs], title, xlabel, out_path, color)


def numeric_ranking_figure(
    rows: Sequence[Dict[str, str]],
    value_field: str,
    title: str,
    xlabel: str,
    out_path: Path,
    color: str = "#4f7cac",
) -> Optional[Path]:
    target_field = first_field(rows, TARGET_FIELDS)
    if not target_field or not value_field:
        return None
    ranked = sorted(
        ((row.get(target_field, ""), number(row.get(value_field))) for row in rows),
        key=lambda item: item[1],
        reverse=True,
    )
    return _save_bar([item[0] for item in ranked], [item[1] for item in ranked], title, xlabel, out_path, color)


def publication_year_figure(rows: Sequence[Dict[str, str]], out_path: Path) -> Optional[Path]:
    field = first_field(rows, YEAR_FIELDS)
    if not field:
        return None
    counts = Counter()
    for row in rows:
        value = str(row.get(field, "")).strip()
        if re.fullmatch(r"(?:19|20)\d{2}", value):
            counts[value] += 1
    if not counts:
        return None
    ordered = sorted(counts.items())
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        return _save_bar(
            [year for year, _ in ordered],
            [count for _, count in ordered],
            "Publication-year distribution",
            "Sentence evidence records",
            out_path,
            "#6b8f3f",
        )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8.2, 4.2))
    ax.bar([year for year, _ in ordered], [count for _, count in ordered], color="#6b8f3f")
    ax.set_title("Publication-year distribution")
    ax.set_ylabel("Sentence evidence records")
    ax.tick_params(axis="x", rotation=45)
    ax.grid(axis="y", alpha=0.2)
    fig.tight_layout()
    fig.savefig(out_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return out_path


def build_trait_figures(
    sentences: Sequence[Dict[str, str]],
    candidates: Sequence[Dict[str, str]],
    fig_dir: Path,
) -> List[Dict[str, str]]:
    figures: List[Dict[str, str]] = []

    def add(path: Optional[Path], caption: str) -> None:
        if path:
            figures.append({"path": str(path), "caption": caption})

    add(
        publication_year_figure(sentences, fig_dir / "publication_year_distribution.png"),
        "Publication-year distribution of RiceMind Sentence Evidence.",
    )
    add(
        numeric_ranking_figure(
            candidates,
            first_field(candidates, ("sentence_count",)),
            "Top candidate genes by sentence evidence",
            "Sentence evidence records",
            fig_dir / "top_candidate_genes_by_sentence_count.png",
        ),
        "Top candidate genes ranked by RiceMind sentence-evidence count.",
    )
    add(
        numeric_ranking_figure(
            candidates,
            first_field(candidates, ("unique_pmids", "pmid_count")),
            "Top candidate genes by independent PMIDs",
            "Unique PMIDs",
            fig_dir / "top_candidate_genes_by_unique_pmids.png",
            "#59a14f",
        ),
        "Top candidate genes ranked by independent supporting PMIDs.",
    )
    add(
        counter_figure(
            sentences,
            JOURNAL_FIELDS,
            "Top journals in the retrieved evidence",
            "Sentence evidence records",
            fig_dir / "journal_distribution.png",
            "#9c755f",
        ),
        "Journal distribution of retrieved RiceMind Sentence Evidence.",
    )
    add(
        counter_figure(
            sentences,
            EVIDENCE_CODE_FIELDS,
            "Evidence-code distribution",
            "Records",
            fig_dir / "evidence_code_distribution.png",
            "#b07aa1",
        ),
        "Evidence-code distribution when returned by RiceMind.",
    )
    add(
        counter_figure(
            sentences,
            SOURCE_FIELDS,
            "Source database distribution",
            "Records",
            fig_dir / "source_distribution.png",
            "#76b7b2",
        ),
        "Source-database distribution when returned by RiceMind.",
    )
    return figures


def find_csv(data_dir: Path, patterns: Sequence[str]) -> Optional[Path]:
    matches: List[Path] = []
    for pattern in patterns:
        matches.extend(data_dir.glob(pattern))
    matches = [path for path in matches if path.is_file()]
    return max(matches, key=lambda path: path.stat().st_size) if matches else None


def build_figures_from_data_dir(data_dir: Path, fig_dir: Optional[Path] = None) -> List[Dict[str, str]]:
    fig_dir = fig_dir or data_dir / "figures"
    ranking_path = find_csv(data_dir, ("*candidate_ranking.csv", "*candidate_genes.csv", "*target_recommendations.csv"))
    evidence_path = find_csv(data_dir, ("*sentence_evidence.csv", "*normalized_evidence.csv"))
    trait_path = find_csv(data_dir, ("*tier1_traits.csv", "*traits_by_candidate_gene.csv", "*normalized_traits.csv"))
    ranking = read_csv(ranking_path) if ranking_path else []
    evidence = read_csv(evidence_path) if evidence_path else []
    traits = read_csv(trait_path) if trait_path else []
    figures = build_trait_figures(evidence, ranking, fig_dir)

    def add(path: Optional[Path], caption: str) -> None:
        if path and all(item["path"] != str(path) for item in figures):
            figures.append({"path": str(path), "caption": caption})

    if ranking:
        support_field = first_field(
            ranking,
            (
                "tier1_direct_salt_article_support",
                "tier1_salt_article_support",
                "tier1_article_support",
                "article_support",
                "score",
            ),
        )
        add(
            numeric_ranking_figure(
                ranking,
                support_field,
                f"{humanize(support_field)} by candidate target",
                humanize(support_field),
                fig_dir / "candidate_evidence_support.png",
            ),
            f"Candidate targets ranked by {humanize(support_field).lower()}." if support_field else "",
        )
        pmid_field = first_field(
            ranking,
            ("salt_sentence_unique_pmids", "riceMind_salt_unique_pmids", "unique_pmids", "pmid_count"),
        )
        add(
            numeric_ranking_figure(
                ranking,
                pmid_field,
                "Context-specific PMID support by candidate target",
                humanize(pmid_field),
                fig_dir / "candidate_context_pmids.png",
                "#59a14f",
            ),
            f"Candidate targets ranked by {humanize(pmid_field).lower()}." if pmid_field else "",
        )

        primary_field = first_field(
            ranking,
            ("tier1_direct_salt_trait_count", "tier1_salt_trait_count", "tier1_objective_trait_count"),
        )
        component_field = first_field(
            ranking,
            ("tier1_ion_homeostasis_trait_count", "tier1_objective_component_trait_count"),
        )
        caution_field = first_field(
            ranking,
            ("tier1_yield_or_growth_trait_count", "tier1_tradeoff_trait_count", "yield_or_growth_trait_count"),
        )
        target_field = first_field(ranking, TARGET_FIELDS)
        if target_field and primary_field and caution_field:
            ordered = sorted(ranking, key=lambda row: number(row.get(primary_field)), reverse=True)[:20]
            primary_values = [
                number(row.get(primary_field)) + (number(row.get(component_field)) if component_field else 0)
                for row in ordered
            ]
            primary_label = (
                "Tier 1 objective and component trait count"
                if component_field
                else humanize(primary_field)
            )
            add(
                _save_grouped_bar(
                    [row.get(target_field, "") for row in ordered],
                    primary_values,
                    [number(row.get(caution_field)) for row in ordered],
                    "Objective-support versus yield/growth caution signals",
                    "Tier 1 trait count",
                    primary_label,
                    humanize(caution_field),
                    fig_dir / "objective_vs_yield_growth_trait_counts.png",
                ),
                "Tier 1 objective-support traits compared with yield/growth caution signals.",
            )

    add(
        counter_figure(
            traits,
            ("trait", "trait_name", "trait_description"),
            "Most frequent Tier 1 traits across candidate targets",
            "Candidate-trait records",
            fig_dir / "tier1_trait_distribution.png",
            "#f28e2b",
        ),
        "Most frequent Tier 1 traits represented across candidate targets.",
    )
    return [figure for figure in figures if figure.get("caption")]


def update_markdown(path: Path, figures: Sequence[Dict[str, str]]) -> None:
    if not figures:
        return
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    if FIGURE_MARKER_START in text:
        text = text.split(FIGURE_MARKER_START, 1)[0].rstrip()
    lines = [text.rstrip(), "", FIGURE_MARKER_START, "## Evidence Figures", ""]
    for index, figure in enumerate(figures, 1):
        figure_path = Path(figure["path"])
        try:
            relative = figure_path.relative_to(path.parent)
        except ValueError:
            relative = figure_path
        lines.extend(
            [
                f"### Figure {index}",
                "",
                f"![{figure['caption']}]({relative.as_posix()})",
                "",
                figure["caption"],
                "",
            ]
        )
    lines.append(FIGURE_MARKER_END)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


def append_docx(path: Path, figures: Sequence[Dict[str, str]]) -> None:
    if not figures or not path.is_file():
        return
    try:
        from docx import Document
        from docx.shared import Inches
    except ImportError as exc:
        raise RuntimeError("python-docx is required for --docx figure embedding") from exc
    document = Document(path)
    document.add_heading("Evidence Figures", level=1)
    for index, figure in enumerate(figures, 1):
        figure_path = Path(figure["path"])
        if not figure_path.is_file():
            continue
        document.add_picture(str(figure_path), width=Inches(6.2))
        document.add_paragraph(f"Figure {index}. {figure['caption']}")
    document.save(path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--fig-dir", type=Path)
    parser.add_argument("--markdown", type=Path, help="Append or refresh the generated Evidence Figures section")
    parser.add_argument("--docx", type=Path, help="Append generated figures to an existing DOCX")
    parser.add_argument("--manifest", type=Path, help="Optional JSON manifest path")
    args = parser.parse_args()

    figures = build_figures_from_data_dir(args.data_dir, args.fig_dir)
    if args.markdown:
        update_markdown(args.markdown, figures)
    if args.docx:
        append_docx(args.docx, figures)
    manifest = args.manifest or args.data_dir / "figure_manifest.json"
    if figures:
        manifest.parent.mkdir(parents=True, exist_ok=True)
        manifest.write_text(json.dumps(figures, ensure_ascii=False, indent=2), encoding="utf-8")
    elif manifest.is_file():
        manifest.unlink()
    fig_dir = args.fig_dir or args.data_dir / "figures"
    if fig_dir.is_dir():
        try:
            fig_dir.rmdir()
        except OSError:
            pass
    print(f"Generated {len(figures)} figure(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
