#!/usr/bin/env python
"""Build normalized analysis sidecars for a RiceMind planthopper review."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Patch


PLANHOPPER_RE = re.compile(
    r"brown planthopper|nilaparvata lugens|\bBPH\b|"
    r"white.?back(?:ed)? planthopper|sogatella furcifera|\bWBPH\b|"
    r"small brown planthopper|laodelphax striatellus|\bSBPH\b|"
    r"\bplanthoppers?\b",
    re.I,
)

SPECIES_PATTERNS = {
    "BPH": re.compile(r"brown planthopper|nilaparvata lugens|\bBPH\b", re.I),
    "WBPH": re.compile(
        r"white.?back(?:ed)? planthopper|sogatella furcifera|\bWBPH\b", re.I
    ),
    "SBPH": re.compile(
        r"small brown planthopper|laodelphax striatellus|\bSBPH\b", re.I
    ),
}

GENE_PATTERNS = [
    re.compile(r"\bOs(?:miR)?[A-Za-z0-9][A-Za-z0-9_.-]{1,}\b"),
    re.compile(r"\b(?:Bph|BPH|bph)\d+[A-Za-z]?\b"),
    re.compile(r"\b(?:OM64|FJ10|JAMYB|Nl14|NlG14|GNA|ASAL|NkChit2b-1)\b", re.I),
]

GENE_ALIASES = {
    "BPH14": "Bph14",
    "BPH15": "Bph15",
    "BPH18": "Bph18",
    "BPH26": "Bph26",
    "BPH29": "Bph29",
    "BPH30": "Bph30",
    "BPH31": "Bph31",
    "BPH32": "Bph32",
    "BPH33": "Bph33",
    "BPH37": "Bph37",
    "BPH40": "Bph40",
    "BPH3": "Bph3",
    "BPH6": "Bph6",
    "BPH9": "Bph9",
    "OSMIR396": "OsmiR396",
    "OSMIR319": "OsmiR319",
    "OSGF14E": "OsGF14e",
    "OSED R1L": "OsEDR1l",
}

NOISE = {
    "BPH",
    "WBPH",
    "SBPH",
    "BPHs",
    "BPH-resistant",
    "BPH-resistance",
    "BPH-susceptible",
    "BPH-induced",
    "BPH-infested",
}

ROLE_RULES = [
    (
        "核心抗性基因/位点",
        re.compile(r"\b(?:Bph|BPH|bph)\d+[A-Za-z]?\b"),
        re.compile(
            r"resistance gene|resistance locus|conferring resistance|"
            r"map-based clon|fine map|introgress|pyramid|near-isogenic|"
            r"major gene|major QTL|dominant gene|recessive gene",
            re.I,
        ),
    ),
    (
        "功能验证的宿主调控/执行因子",
        re.compile(r"\bOs(?:miR)?[A-Za-z0-9][A-Za-z0-9_.-]{1,}\b"),
        re.compile(
            r"knockout|knock-out|knockdown|knock-down|overexpress|"
            r"loss-of-function|gain-of-function|silenc|mutant|"
            r"positively regulates|negatively regulates|confers resistance|"
            r"enhances? resistance|reduces? resistance|mediates resistance",
            re.I,
        ),
    ),
    (
        "表达/组学关联候选",
        re.compile(r"\bOs(?:miR)?[A-Za-z0-9][A-Za-z0-9_.-]{1,}\b"),
        re.compile(
            r"differentially expressed|transcriptom|proteom|metabolom|"
            r"expression profile|expression analysis|candidate gene|"
            r"associated with resistance|correlated with resistance",
            re.I,
        ),
    ),
]

THEMES = {
    "遗传定位、克隆与抗源部署": re.compile(
        r"QTL|fine map|map-based|clon|locus|introgress|pyramid|"
        r"near-isogenic|marker-assisted|MAS|resistance gene",
        re.I,
    ),
    "韧皮部取食界面与结构防御": re.compile(
        r"phloem|sieve plate|sieve tube|callose|cell wall|lignin|"
        r"honeydew|feeding behavior|electrical penetration|EPG",
        re.I,
    ),
    "激素、氧化还原与信号调控": re.compile(
        r"jasmon|JA-Ile|\bJA\b|salicylic|\bSA\b|abscisic|\bABA\b|"
        r"ethylene|reactive oxygen|H2O2|nitric oxide|MAPK|kinase",
        re.I,
    ),
    "次生代谢与挥发性防御": re.compile(
        r"flavonoid|phenylpropanoid|phenylalanine ammonia|PAL|"
        r"volatile|terpene|green leaf volatile|GLV|metabolite",
        re.I,
    ),
    "宿主免疫、肽信号与昆虫效应子": re.compile(
        r"effector|immune|immunity|elicitor|PEPR|Pep3|receptor|"
        r"salivary protein|saliva|virulence",
        re.I,
    ),
    "生长防御权衡与农艺环境": re.compile(
        r"growth-defense|growth versus defense|yield|nitrogen|"
        r"fertilizer|trade-?off|fitness cost|agronomic|field",
        re.I,
    ),
    "病毒-媒介-水稻三方互作": re.compile(
        r"virus|viral|RRSV|RGSV|SRBSDV|RBSDV|RSV|vector feeding",
        re.I,
    ),
}

MILESTONE_PATTERNS = {
    "定位/遗传资源": re.compile(r"QTL|map|locus|resistance gene", re.I),
    "克隆/分子身份": re.compile(r"clon|encodes?|identified and characterized", re.I),
    "生理机制": re.compile(r"callose|phloem|sieve plate|feeding behavior|honeydew", re.I),
    "组学/网络": re.compile(r"transcriptom|proteom|metabolom|network", re.I),
    "受体/效应子": re.compile(r"receptor|effector|elicitor|immune|salivary", re.I),
    "编辑/权衡": re.compile(
        r"CRISPR|gene edit|knockout|frameshift|growth-defense|yield stability", re.I
    ),
}

BREEDING_RE = re.compile(
    r"introgress|pyramid|marker-assisted|\bMAS\b|near-isogenic|"
    r"breeding|cultivar|variety|germplasm|field|yield",
    re.I,
)

PHASES = [
    ("遗传定位与抗源导入", 1989, 2008),
    ("核心基因克隆与身份确认", 2009, 2016),
    ("防御网络与结构机制展开", 2017, 2021),
    ("互作免疫与精准设计", 2022, 2025),
]

CURATED_MILESTONES = [
    (2002, "抗性基因分子定位", "12184487"),
    (2004, "Bph1/Bph2 标记辅助聚合", "15032948"),
    (2008, "筛板胼胝质阻断取食", "18245456"),
    (2009, "Bph14 克隆", "20018701"),
    (2014, "BPH26 克隆", "25076167"),
    (2015, "BPH29 克隆", "26136269"),
    (2016, "BPH9 等位变异与抗虫谱", "27791169"),
    (2018, "Bph6 外泌体定位机制", "29358653"),
    (2021, "Bph30 厚壁组织屏障", "34246801"),
    (2022, "OsPep3-OsPEPR 肽信号", "35068048"),
    (2023, "细胞壁葡聚糖-OsLecRK1 联动", "36952539"),
    (2025, "昆虫效应子模拟宿主免疫调节子", "39853648"),
    (2025, "OsWRKY36 多飞虱抗性与产量稳定", "40042898"),
]
DIRECT_RE = re.compile(
    r"knockout|knock-out|knockdown|knock-down|overexpress|"
    r"loss-of-function|gain-of-function|mutant|silenc|"
    r"map-based clon|fine map|confers resistance|enhances? resistance|"
    r"reduces? resistance|mediates resistance",
    re.I,
)
EFFECT_SIZE_RE = re.compile(
    r"phenotypic variance|variance explained|\bPVE\b|LOD|major[- ]effect|"
    r"minor[- ]effect|major QTL|minor QTL|\d+(?:\.\d+)?\s*%",
    re.I,
)


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [{k: (v or "").strip() for k, v in row.items()} for row in csv.DictReader(handle)]


def write_csv(path: Path, rows: Sequence[Dict[str, object]], fields: Sequence[str]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def dedupe(rows: Iterable[Dict[str, str]]) -> List[Dict[str, str]]:
    seen = set()
    out = []
    for row in rows:
        key = (row.get("PMID", ""), row.get("sent_id", ""), row.get("text", ""))
        if key in seen:
            continue
        seen.add(key)
        out.append(row)
    return out


def normalize_gene(token: str) -> str:
    token = token.strip(".,;:()[]{}")
    alias = GENE_ALIASES.get(token.upper(), token)
    if re.fullmatch(r"(?i)bph\d+[a-z]?", alias):
        return "Bph" + alias[3:]
    return alias


def extract_genes(text: str) -> List[str]:
    genes = set()
    for pattern in GENE_PATTERNS:
        for match in pattern.finditer(text):
            token = normalize_gene(match.group(0))
            if token not in NOISE and len(token) >= 3:
                genes.add(token)
    return sorted(genes)


def species_tags(text: str) -> List[str]:
    return [name for name, pattern in SPECIES_PATTERNS.items() if pattern.search(text)]


def role_for_gene(gene: str, corpus: str) -> Tuple[str, str]:
    roles = []
    for role, gene_pattern, evidence_pattern in ROLE_RULES:
        if gene_pattern.fullmatch(gene) and evidence_pattern.search(corpus):
            roles.append(role)
    if "核心抗性基因/位点" in roles:
        role = "核心抗性基因/位点"
    elif "功能验证的宿主调控/执行因子" in roles:
        role = "功能验证的宿主调控/执行因子"
    elif "表达/组学关联候选" in roles:
        role = "表达/组学关联候选"
    elif gene.startswith("Os"):
        role = "作用层级待核验的宿主基因"
    else:
        role = "其他机制或外源因子"
    if EFFECT_SIZE_RE.search(corpus):
        effect = "原句含效应量/主微效描述，需回到原文核验"
    else:
        effect = "未报告/不可由文献频次推断"
    return role, effect


def build_gene_rows(rows: Sequence[Dict[str, str]]) -> List[Dict[str, object]]:
    evidence: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    for row in rows:
        combined = " ".join((row.get("title", ""), row.get("text", "")))
        for gene in extract_genes(combined):
            evidence[gene].append(row)

    out = []
    for gene, gene_rows in evidence.items():
        pmids = sorted({row["PMID"] for row in gene_rows if row.get("PMID")})
        corpus = " ".join(" ".join((r.get("title", ""), r.get("text", ""))) for r in gene_rows)
        role, effect = role_for_gene(gene, corpus)
        species = sorted({tag for r in gene_rows for tag in species_tags(r.get("title", "") + " " + r.get("text", ""))})
        themes = [name for name, pattern in THEMES.items() if pattern.search(corpus)]
        years = [int(r["year"]) for r in gene_rows if r.get("year", "").isdigit()]
        out.append(
            {
                "gene_or_locus": gene,
                "evidence_role": role,
                "effect_size_status": effect,
                "sentence_count": len(gene_rows),
                "unique_pmids": len(pmids),
                "earliest_year": min(years) if years else "",
                "latest_year": max(years) if years else "",
                "species_context": ";".join(species),
                "direct_perturbation_or_mapping": "yes" if DIRECT_RE.search(corpus) else "not explicit",
                "breeding_context": "yes" if BREEDING_RE.search(corpus) else "not explicit",
                "mechanism_themes": ";".join(themes),
                "representative_pmids": ";".join(pmids[:12]),
            }
        )
    return sorted(
        out,
        key=lambda r: (
            {
                "核心抗性基因/位点": 0,
                "功能验证的宿主调控/执行因子": 1,
                "表达/组学关联候选": 2,
                "作用层级待核验的宿主基因": 3,
                "其他机制或外源因子": 4,
            }.get(str(r["evidence_role"]), 9),
            -int(r["unique_pmids"]),
            -int(r["sentence_count"]),
        ),
    )


def build_theme_rows(rows: Sequence[Dict[str, str]]) -> List[Dict[str, object]]:
    out = []
    for theme, pattern in THEMES.items():
        matched = [
            row
            for row in rows
            if pattern.search(row.get("title", "") + " " + row.get("text", ""))
        ]
        pmids = sorted({row["PMID"] for row in matched if row.get("PMID")})
        genes = Counter(
            gene
            for row in matched
            for gene in extract_genes(row.get("title", "") + " " + row.get("text", ""))
        )
        years = [int(row["year"]) for row in matched if row.get("year", "").isdigit()]
        out.append(
            {
                "theme": theme,
                "sentence_count": len(matched),
                "unique_pmids": len(pmids),
                "earliest_year": min(years) if years else "",
                "latest_year": max(years) if years else "",
                "top_genes": ";".join(gene for gene, _ in genes.most_common(12)),
                "representative_pmids": ";".join(pmids[-12:]),
            }
        )
    return sorted(out, key=lambda r: int(r["unique_pmids"]), reverse=True)


def build_phase_theme_rows(rows: Sequence[Dict[str, str]]) -> List[Dict[str, object]]:
    out = []
    for phase, start, end in PHASES:
        phase_rows = [
            row
            for row in rows
            if row.get("year", "").isdigit() and start <= int(row["year"]) <= end
        ]
        phase_pmids = {row["PMID"] for row in phase_rows if row.get("PMID")}
        for theme, pattern in THEMES.items():
            matched = [
                row
                for row in phase_rows
                if pattern.search(row.get("title", "") + " " + row.get("text", ""))
            ]
            theme_pmids = {row["PMID"] for row in matched if row.get("PMID")}
            out.append(
                {
                    "phase": phase,
                    "start_year": start,
                    "end_year": end,
                    "phase_unique_pmids": len(phase_pmids),
                    "theme": theme,
                    "theme_unique_pmids": len(theme_pmids),
                    "theme_share_of_phase_pmids": (
                        round(len(theme_pmids) / len(phase_pmids), 4) if phase_pmids else 0
                    ),
                }
            )
    return out


def build_article_rows(rows: Sequence[Dict[str, str]]) -> List[Dict[str, object]]:
    articles: Dict[str, Dict[str, object]] = {}
    for row in rows:
        pmid = row.get("PMID", "")
        if not pmid:
            continue
        article = articles.setdefault(
            pmid,
            {
                "PMID": pmid,
                "year": row.get("year", ""),
                "journal": row.get("journal", ""),
                "title": row.get("title", ""),
                "sentence_count": 0,
                "species_context": set(),
                "genes": Counter(),
                "themes": set(),
            },
        )
        article["sentence_count"] = int(article["sentence_count"]) + 1
        text = row.get("title", "") + " " + row.get("text", "")
        article["species_context"].update(species_tags(text))
        article["genes"].update(extract_genes(text))
        for theme, pattern in THEMES.items():
            if pattern.search(text):
                article["themes"].add(theme)
    out = []
    for article in articles.values():
        out.append(
            {
                "PMID": article["PMID"],
                "year": article["year"],
                "journal": article["journal"],
                "title": article["title"],
                "sentence_count": article["sentence_count"],
                "species_context": ";".join(sorted(article["species_context"])),
                "genes": ";".join(g for g, _ in article["genes"].most_common(20)),
                "themes": ";".join(sorted(article["themes"])),
            }
        )
    return sorted(out, key=lambda r: (int(r["year"]) if str(r["year"]).isdigit() else 0, int(r["sentence_count"])), reverse=True)


def build_milestones(articles: Sequence[Dict[str, object]]) -> List[Dict[str, object]]:
    out = []
    for category, pattern in MILESTONE_PATTERNS.items():
        selected = [
            row
            for row in articles
            if pattern.search(str(row["title"]) + " " + str(row["themes"]))
        ]
        selected.sort(
            key=lambda r: (
                int(r["year"]) if str(r["year"]).isdigit() else 9999,
                -int(r["sentence_count"]),
            )
        )
        for row in selected[:8]:
            out.append(
                {
                    "milestone_type": category,
                    "year": row["year"],
                    "PMID": row["PMID"],
                    "title": row["title"],
                    "genes": row["genes"],
                    "species_context": row["species_context"],
                }
            )
    return out


def representative_evidence(
    rows: Sequence[Dict[str, str]],
    genes: Sequence[str],
    per_gene: int = 4,
) -> List[Dict[str, object]]:
    out = []
    for gene in genes:
        pattern = re.compile(rf"\b{re.escape(gene)}\b", re.I)
        selected = [
            row
            for row in rows
            if pattern.search(row.get("title", "") + " " + row.get("text", ""))
        ]
        selected.sort(
            key=lambda r: (
                0 if DIRECT_RE.search(r.get("title", "") + " " + r.get("text", "")) else 1,
                -(int(r["year"]) if r.get("year", "").isdigit() else 0),
            )
        )
        seen_pmids = set()
        count = 0
        for row in selected:
            if row.get("PMID") in seen_pmids:
                continue
            seen_pmids.add(row.get("PMID"))
            out.append(
                {
                    "gene_or_locus": gene,
                    "PMID": row.get("PMID", ""),
                    "year": row.get("year", ""),
                    "journal": row.get("journal", ""),
                    "title": row.get("title", ""),
                    "sentence_id": row.get("sent_id", ""),
                    "sentence_evidence": row.get("text", ""),
                }
            )
            count += 1
            if count >= per_gene:
                break
    return out


def save_figures(
    rows: Sequence[Dict[str, str]],
    genes: Sequence[Dict[str, object]],
    themes: Sequence[Dict[str, object]],
    phase_themes: Sequence[Dict[str, object]],
    out_dir: Path,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update(
        {
            "font.sans-serif": ["Microsoft YaHei", "SimHei", "Arial Unicode MS", "DejaVu Sans"],
            "axes.unicode_minus": False,
            "figure.dpi": 160,
        }
    )

    years = Counter(int(r["year"]) for r in rows if r.get("year", "").isdigit())
    xs = sorted(years)
    fig, ax = plt.subplots(figsize=(9, 4.6))
    ax.plot(xs, [years[x] for x in xs], marker="o", linewidth=1.8, color="#1f6f8b")
    ax.fill_between(xs, [years[x] for x in xs], alpha=0.18, color="#1f6f8b")
    ax.set_xlabel("发表年份")
    ax.set_ylabel("RiceMind 句子证据数")
    ax.set_title("飞虱抗性 RiceMind 句子证据的年度分布")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(out_dir / "publication_year_trend.png", bbox_inches="tight")
    plt.close(fig)

    species_counts = Counter()
    for row in rows:
        for tag in species_tags(row.get("title", "") + " " + row.get("text", "")):
            species_counts[tag] += 1
    fig, ax = plt.subplots(figsize=(6.6, 4.2))
    labels = ["BPH", "WBPH", "SBPH"]
    vals = [species_counts[label] for label in labels]
    ax.bar(labels, vals, color=["#375a7f", "#4e9f78", "#d18f3b"])
    ax.set_ylabel("句子证据数")
    ax.set_title("不同稻飞虱类群在证据集中的覆盖")
    for idx, value in enumerate(vals):
        ax.text(idx, value, str(value), ha="center", va="bottom", fontsize=9)
    fig.tight_layout()
    fig.savefig(out_dir / "species_coverage.png", bbox_inches="tight")
    plt.close(fig)

    core = sorted(
        [row for row in genes if row["evidence_role"] == "核心抗性基因/位点"],
        key=lambda r: int(r["unique_pmids"]),
        reverse=True,
    )[:10]
    regulators = sorted(
        [
            row
            for row in genes
            if row["evidence_role"] == "功能验证的宿主调控/执行因子"
            and int(row["unique_pmids"]) >= 2
        ],
        key=lambda r: int(r["unique_pmids"]),
        reverse=True,
    )[:8]
    comparison = sorted(core + regulators, key=lambda r: int(r["unique_pmids"]))
    fig, ax = plt.subplots(figsize=(8.5, 6.6))
    colors = [
        "#244b74" if row["evidence_role"] == "核心抗性基因/位点" else "#ba6b35"
        for row in comparison
    ]
    ax.barh(
        [str(row["gene_or_locus"]) for row in comparison],
        [int(row["unique_pmids"]) for row in comparison],
        color=colors,
    )
    ax.set_xlabel("独立 PMID 数")
    ax.set_title("核心位点与功能验证调控因子的证据密度分层")
    ax.grid(axis="x", alpha=0.2)
    ax.legend(
        handles=[
            Patch(facecolor="#244b74", label="核心抗性基因/位点"),
            Patch(facecolor="#ba6b35", label="功能验证的调控/执行因子"),
        ],
        loc="lower right",
        frameon=False,
    )
    fig.tight_layout()
    fig.savefig(out_dir / "gene_evidence_density.png", bbox_inches="tight")
    plt.close(fig)

    theme_plot = sorted(themes, key=lambda r: int(r["unique_pmids"]))
    fig, ax = plt.subplots(figsize=(8.6, 5.4))
    ax.barh(
        [str(row["theme"]) for row in theme_plot],
        [int(row["unique_pmids"]) for row in theme_plot],
        color="#52796f",
    )
    ax.set_xlabel("独立 PMID 数")
    ax.set_title("由当前句子证据归纳的研究主题覆盖")
    ax.grid(axis="x", alpha=0.2)
    fig.tight_layout()
    fig.savefig(out_dir / "mechanism_theme_coverage.png", bbox_inches="tight")
    plt.close(fig)

    phase_names = [phase[0] for phase in PHASES]
    theme_names = list(THEMES)
    matrix = []
    for theme in theme_names:
        matrix.append(
            [
                next(
                    float(row["theme_share_of_phase_pmids"])
                    for row in phase_themes
                    if row["phase"] == phase and row["theme"] == theme
                )
                for phase in phase_names
            ]
        )
    fig, ax = plt.subplots(figsize=(9.5, 5.8))
    image = ax.imshow(matrix, cmap="YlGnBu", aspect="auto", vmin=0, vmax=max(max(x) for x in matrix))
    ax.set_xticks(range(len(phase_names)), phase_names, rotation=18, ha="right")
    ax.set_yticks(range(len(theme_names)), theme_names)
    ax.set_title("不同发展阶段的研究主题覆盖比例")
    for row_idx, values in enumerate(matrix):
        for col_idx, value in enumerate(values):
            ax.text(col_idx, row_idx, f"{value:.0%}", ha="center", va="center", fontsize=8)
    fig.colorbar(image, ax=ax, label="该阶段 PMID 中的主题覆盖比例")
    fig.tight_layout()
    fig.savefig(out_dir / "phase_theme_heatmap.png", bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(12.0, 5.6))
    colors = ["#244b74", "#52796f", "#c87941", "#7b5ea7"]
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 6)
    ax.axis("off")
    phase_items = {phase[0]: [] for phase in PHASES}
    for year, label, pmid in CURATED_MILESTONES:
        phase = next(name for name, start, end in PHASES if start <= year <= end)
        phase_items[phase].append((year, label, pmid))
    for idx, (phase, start, end) in enumerate(PHASES):
        x = 0.2 + idx * 2.95
        width = 2.65
        panel = FancyBboxPatch(
            (x, 0.55),
            width,
            4.75,
            boxstyle="round,pad=0.05,rounding_size=0.08",
            facecolor="#f7f7f7",
            edgecolor=colors[idx],
            linewidth=1.6,
        )
        ax.add_patch(panel)
        header = FancyBboxPatch(
            (x, 4.45),
            width,
            0.85,
            boxstyle="round,pad=0.04,rounding_size=0.08",
            facecolor=colors[idx],
            edgecolor=colors[idx],
        )
        ax.add_patch(header)
        ax.text(
            x + width / 2,
            4.97,
            phase,
            ha="center",
            va="center",
            color="white",
            fontsize=11,
            fontweight="bold",
        )
        ax.text(
            x + width / 2,
            4.62,
            f"{start}-{end}",
            ha="center",
            va="center",
            color="white",
            fontsize=8.5,
        )
        items = phase_items[phase]
        y_positions = [3.85, 2.85, 1.85, 0.90]
        for item_idx, (year, label, pmid) in enumerate(items[:4]):
            y = y_positions[item_idx]
            ax.text(
                x + 0.18,
                y,
                f"{year}",
                ha="left",
                va="top",
                color=colors[idx],
                fontsize=10,
                fontweight="bold",
            )
            ax.text(
                x + 0.68,
                y,
                f"{label}\nPMID {pmid}",
                ha="left",
                va="top",
                color="#333333",
                fontsize=8.1,
                linespacing=1.25,
            )
    ax.set_title("RiceMind 证据支持的飞虱抗性研究里程碑", fontsize=15, fontweight="bold", pad=8)
    fig.tight_layout()
    fig.savefig(out_dir / "research_milestones.png", bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10.5, 5.8))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis("off")
    boxes = [
        (0.3, 3.8, 2.0, 1.35, "核心抗性基因/位点", "Bph3, Bph6, Bph9,\nBph14, Bph18/26,\nBph29, Bph30, Bph32", "#244b74"),
        (2.8, 4.0, 2.1, 1.05, "识别与分泌运输", "NLR/LecRK/外泌体\n受体与肽信号", "#4f759b"),
        (2.8, 2.45, 2.1, 1.05, "结构与取食界面", "胼胝质、细胞壁、\n厚壁组织、韧皮部", "#52796f"),
        (5.4, 4.0, 2.05, 1.05, "信号与代谢调控", "JA/ABA/SA/BR\n苯丙烷、黄酮、GLV", "#c87941"),
        (5.4, 2.45, 2.05, 1.05, "宿主-昆虫互作", "效应子、免疫抑制、\n生物型适应", "#7b5ea7"),
        (8.0, 3.15, 1.75, 1.25, "表型与育种终点", "拒食/抗生/耐受\n抗虫谱、持久性、\n产量与环境稳定性", "#8c5e58"),
    ]
    for x, y, w, h, title, body, color in boxes:
        patch = FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.04,rounding_size=0.08",
            facecolor=color,
            edgecolor="none",
            alpha=0.93,
        )
        ax.add_patch(patch)
        ax.text(x + w / 2, y + h * 0.70, title, color="white", ha="center", va="center", fontweight="bold", fontsize=10)
        ax.text(x + w / 2, y + h * 0.32, body, color="white", ha="center", va="center", fontsize=8.4)
    arrows = [
        ((2.3, 4.45), (2.8, 4.52)),
        ((2.3, 4.15), (2.8, 2.98)),
        ((4.9, 4.48), (5.4, 4.48)),
        ((4.9, 2.98), (5.4, 2.98)),
        ((7.45, 4.42), (8.0, 3.92)),
        ((7.45, 2.98), (8.0, 3.62)),
    ]
    for start, end in arrows:
        ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=12, linewidth=1.4, color="#555555"))
    ax.text(
        5,
        0.7,
        "解释原则：核心位点决定遗传抗性骨架；下游调控因子解释防御如何执行。二者不以 PMID 数量互相替代，效应大小和育种价值需独立评价。",
        ha="center",
        va="center",
        fontsize=9.4,
        color="#333333",
        bbox={"boxstyle": "round,pad=0.45", "facecolor": "#f2f2f2", "edgecolor": "#cccccc"},
    )
    ax.set_title("基于当前 RiceMind 证据的飞虱抗性因果层级框架", fontsize=14, fontweight="bold", pad=12)
    fig.tight_layout()
    fig.savefig(out_dir / "causal_role_framework.png", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-csv", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()

    source_rows = read_csv(args.input_csv)
    selected = []
    for row in source_rows:
        query = row.get("query_trait", "")
        combined = row.get("title", "") + " " + row.get("text", "")
        if query == "brown planthopper resistance" or PLANHOPPER_RE.search(combined):
            selected.append(row)
    rows = dedupe(selected)
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    genes = build_gene_rows(rows)
    themes = build_theme_rows(rows)
    phase_themes = build_phase_theme_rows(rows)
    articles = build_article_rows(rows)
    milestones = build_milestones(articles)

    priority_genes = [
        str(row["gene_or_locus"])
        for row in genes
        if row["evidence_role"] in {"核心抗性基因/位点", "功能验证的宿主调控/执行因子"}
    ][:35]
    evidence = representative_evidence(rows, priority_genes)

    write_csv(
        out_dir / "planthopper_sentence_evidence.csv",
        rows,
        list(rows[0].keys()),
    )
    write_csv(
        out_dir / "planthopper_article_index.csv",
        articles,
        ["PMID", "year", "journal", "title", "sentence_count", "species_context", "genes", "themes"],
    )
    write_csv(
        out_dir / "candidate_role_matrix.csv",
        genes,
        [
            "gene_or_locus",
            "evidence_role",
            "effect_size_status",
            "sentence_count",
            "unique_pmids",
            "earliest_year",
            "latest_year",
            "species_context",
            "direct_perturbation_or_mapping",
            "breeding_context",
            "mechanism_themes",
            "representative_pmids",
        ],
    )
    write_csv(
        out_dir / "mechanism_theme_summary.csv",
        themes,
        [
            "theme",
            "sentence_count",
            "unique_pmids",
            "earliest_year",
            "latest_year",
            "top_genes",
            "representative_pmids",
        ],
    )
    write_csv(
        out_dir / "phase_theme_matrix.csv",
        phase_themes,
        [
            "phase",
            "start_year",
            "end_year",
            "phase_unique_pmids",
            "theme",
            "theme_unique_pmids",
            "theme_share_of_phase_pmids",
        ],
    )
    write_csv(
        out_dir / "milestone_articles.csv",
        milestones,
        ["milestone_type", "year", "PMID", "title", "genes", "species_context"],
    )
    write_csv(
        out_dir / "representative_sentence_evidence.csv",
        evidence,
        [
            "gene_or_locus",
            "PMID",
            "year",
            "journal",
            "title",
            "sentence_id",
            "sentence_evidence",
        ],
    )

    years = [int(row["year"]) for row in rows if row.get("year", "").isdigit()]
    summary = {
        "source_file": str(args.input_csv),
        "source_snapshot_date": "2026-06-05",
        "selected_sentence_records": len(rows),
        "unique_pmids": len({row["PMID"] for row in rows if row.get("PMID")}),
        "year_min": min(years) if years else None,
        "year_max": max(years) if years else None,
        "journals": len({row["journal"] for row in rows if row.get("journal")}),
        "species_sentence_counts": {
            species: sum(
                1
                for row in rows
                if pattern.search(row.get("title", "") + " " + row.get("text", ""))
            )
            for species, pattern in SPECIES_PATTERNS.items()
        },
        "role_counts": dict(Counter(str(row["evidence_role"]) for row in genes)),
        "online_api_status_2026_06_11": "Repeated timeouts; local complete RiceMind export used.",
    }
    (out_dir / "retrieval_and_analysis_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    save_figures(rows, genes, themes, phase_themes, out_dir / "figures")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
