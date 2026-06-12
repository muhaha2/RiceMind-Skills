from __future__ import annotations

import csv
import re
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = ROOT / "work" / "planthopper_minor_loci"
REPORT_STEM = "水稻飞虱抗性研究态势与发展脉络"
REPORT_ROOT = Path(__file__).resolve().parent / "report_output"
OUT = REPORT_ROOT / f"{REPORT_STEM}_data"

SOURCES = [
    ("BPH resistance", SOURCE_ROOT / "bph_resistance_data" / "bph_resistance_sentences.csv"),
    ("BPH damage", SOURCE_ROOT / "bph_damage_data" / "bph_damage_sentences.csv"),
    ("WBPH resistance", SOURCE_ROOT / "wbph_resistance_data" / "wbph_resistance_sentences.csv"),
    ("WBPH damage", SOURCE_ROOT / "wbph_damage_data" / "wbph_damage_sentences.csv"),
    ("Broad planthopper", SOURCE_ROOT / "planthopper_broad_data" / "planthopper_broad_sentences.csv"),
]

PHASES = [
    ("1989-2005", 1989, 2005),
    ("2006-2015", 2006, 2015),
    ("2016-2020", 2016, 2020),
    ("2021-2025", 2021, 2025),
]

THEMES = {
    "抗源鉴定与表型评价": [
        r"\bresistan(?:ce|t)\b", r"susceptib", r"germplasm", r"cultivar",
        r"variet", r"screen", r"bioassay", r"honeydew", r"feeding",
    ],
    "遗传定位、QTL与关联分析": [
        r"\bqtl\b", r"mapping", r"map-based", r"fine map", r"linkage",
        r"\bgwas\b", r"genome-wide association", r"quantitative trait",
        r"marker-assisted", r"pyramid", r"genomic prediction",
    ],
    "主效抗性基因与受体识别": [
        r"\bbph\d+\b", r"\bwbph\d+\b", r"lectin receptor", r"\blecrk",
        r"nucleotide-binding", r"\bnbs[- ]?lrr", r"resistance gene",
    ],
    "激素、转录与免疫信号": [
        r"jasmon", r"salicylic", r"abscisic", r"ethylene", r"gibberell",
        r"\bwrky\b", r"transcription factor", r"\bmapk\b", r"signaling",
        r"immune", r"defen[cs]e response",
    ],
    "代谢、挥发物与结构防御": [
        r"metabol", r"flavonoid", r"phenylpropanoid", r"lignin",
        r"volatile", r"limonene", r"cell wall", r"oxylipin",
        r"phenylalanine ammonia", r"secondary metabol",
    ],
    "组学与系统网络": [
        r"transcriptom", r"proteom", r"metabolom", r"multi-omics",
        r"microarray", r"rna-seq", r"network", r"small rna",
        r"\bmir\d+", r"lncrna", r"circrna",
    ],
    "基因编辑与功能验证": [
        r"crispr", r"knockout", r"knock-out", r"silenc", r"rna interference",
        r"\brnai\b", r"overexpress", r"transgenic", r"mutant", r"mutation",
    ],
    "宿主-昆虫互作与效应子": [
        r"effector", r"saliv", r"oviposition", r"nymphal", r"biotype",
        r"virulence", r"host[- ]plant", r"interaction", r"adaptation",
    ],
    "昆虫侧适应、毒力与药剂抗性": [
        r"insecticide", r"pesticide", r"imidacloprid", r"pymetrozine",
        r"buprofezin", r"detoxification", r"cytochrome p450", r"\bcyp\d",
        r"glutathione s-transferase", r"nicotinic acetylcholine",
        r"planthopper virulence", r"virulent biotype",
    ],
    "生长-防御权衡与育种转化": [
        r"growth.*defen", r"defen.*growth", r"yield", r"field",
        r"agronomic", r"breeding", r"trade-off", r"tradeoff",
        r"broad-spectrum", r"durab",
    ],
}

METHODS = {
    "连锁/QTL/标记育种": [
        r"\bqtl\b", r"mapping", r"linkage", r"marker-assisted", r"pyramid",
    ],
    "GWAS/群体基因组/基因组预测": [
        r"\bgwas\b", r"genome-wide association", r"genomic prediction",
        r"population genom", r"association mapping",
    ],
    "表达组学/多组学": [
        r"transcriptom", r"proteom", r"metabolom", r"microarray",
        r"rna-seq", r"small rna", r"lncrna", r"circrna",
    ],
    "转基因/RNAi/突变体": [
        r"transgenic", r"overexpress", r"\brnai\b", r"silenc",
        r"mutant", r"mutation",
    ],
    "CRISPR/精准编辑": [
        r"crispr", r"genome edit", r"gene edit",
    ],
    "田间/产量/育种评价": [
        r"field", r"yield", r"agronomic", r"breeding", r"pyramid",
    ],
}


def read_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    seen_sentences: set[tuple[str, str, str]] = set()
    for scope, path in SOURCES:
        with path.open(encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                pmid = row.get("PMID", "").strip()
                sent_id = row.get("sent_id", "").strip()
                key = (pmid, sent_id, row.get("text", ""))
                if not pmid or key in seen_sentences:
                    continue
                seen_sentences.add(key)
                row["retrieval_scope"] = scope
                rows.append(row)
    return rows


def phase_for(year: int) -> str:
    for label, start, end in PHASES:
        if start <= year <= end:
            return label
    return "Other"


def matches(text: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    rows = read_rows()
    articles: dict[str, dict[str, object]] = {}
    for row in rows:
        pmid = row["PMID"].strip()
        article = articles.setdefault(
            pmid,
            {
                "PMID": pmid,
                "year": row.get("year", "").strip(),
                "journal": row.get("journal", "").strip(),
                "title": row.get("title", "").strip(),
                "sentences": [],
                "scopes": set(),
            },
        )
        if not article["year"] and row.get("year"):
            article["year"] = row["year"].strip()
        if not article["journal"] and row.get("journal"):
            article["journal"] = row["journal"].strip()
        if not article["title"] and row.get("title"):
            article["title"] = row["title"].strip()
        article["sentences"].append(row.get("text", ""))
        article["scopes"].add(row["retrieval_scope"])

    article_rows: list[dict[str, object]] = []
    annual = Counter()
    phase_counts = Counter()
    journal_counts = Counter()
    theme_phase = defaultdict(Counter)
    method_phase = defaultdict(Counter)

    for article in articles.values():
        try:
            year = int(str(article["year"]))
        except ValueError:
            continue
        phase = phase_for(year)
        text = " ".join(
            [str(article["title"]), *[str(item) for item in article["sentences"]]]
        )
        article_themes = [name for name, patterns in THEMES.items() if matches(text, patterns)]
        article_methods = [name for name, patterns in METHODS.items() if matches(text, patterns)]
        annual[year] += 1
        phase_counts[phase] += 1
        journal = str(article["journal"]).strip() or "Unknown"
        journal_counts[journal] += 1
        for theme in article_themes:
            theme_phase[phase][theme] += 1
        for method in article_methods:
            method_phase[phase][method] += 1
        article_rows.append(
            {
                "PMID": article["PMID"],
                "year": year,
                "phase": phase,
                "journal": journal,
                "title": article["title"],
                "retrieval_scopes": "; ".join(sorted(article["scopes"])),
                "sentence_count": len(article["sentences"]),
                "themes": "; ".join(article_themes),
                "methods": "; ".join(article_methods),
            }
        )

    annual_rows = [
        {"year": year, "unique_PMIDs": count}
        for year, count in sorted(annual.items())
    ]
    phase_rows = []
    for label, start, end in PHASES:
        total = phase_counts[label]
        phase_rows.append(
            {
                "phase": label,
                "start_year": start,
                "end_year": end,
                "unique_PMIDs": total,
                "share_percent": round(total * 100 / sum(phase_counts.values()), 1),
            }
        )
    theme_rows = []
    for label, _, _ in PHASES:
        total = phase_counts[label]
        for theme in THEMES:
            count = theme_phase[label][theme]
            theme_rows.append(
                {
                    "phase": label,
                    "theme": theme,
                    "unique_PMIDs": count,
                    "phase_share_percent": round(count * 100 / total, 1) if total else 0,
                }
            )
    method_rows = []
    method_wide_rows = []
    for label, _, _ in PHASES:
        total = phase_counts[label]
        wide_row: dict[str, object] = {"phase": label}
        for method in METHODS:
            count = method_phase[label][method]
            share = round(count * 100 / total, 1) if total else 0
            method_rows.append(
                {
                    "phase": label,
                    "method": method,
                    "unique_PMIDs": count,
                    "phase_share_percent": share,
                }
            )
            wide_row[method] = share
        method_wide_rows.append(wide_row)
    journal_rows = [
        {"journal": journal, "unique_PMIDs": count}
        for journal, count in journal_counts.most_common()
    ]

    write_csv(
        OUT / "article_classification.csv",
        sorted(article_rows, key=lambda item: (-int(item["year"]), str(item["PMID"]))),
        [
            "PMID", "year", "phase", "journal", "title", "retrieval_scopes",
            "sentence_count", "themes", "methods",
        ],
    )
    write_csv(OUT / "annual_publication_counts.csv", annual_rows, ["year", "unique_PMIDs"])
    write_csv(
        OUT / "phase_summary.csv",
        phase_rows,
        ["phase", "start_year", "end_year", "unique_PMIDs", "share_percent"],
    )
    write_csv(
        OUT / "theme_by_phase.csv",
        theme_rows,
        ["phase", "theme", "unique_PMIDs", "phase_share_percent"],
    )
    write_csv(
        OUT / "method_by_phase.csv",
        method_rows,
        ["phase", "method", "unique_PMIDs", "phase_share_percent"],
    )
    write_csv(
        OUT / "method_by_phase_wide.csv",
        method_wide_rows,
        ["phase", *METHODS.keys()],
    )
    write_csv(OUT / "journal_counts.csv", journal_rows, ["journal", "unique_PMIDs"])

    print(f"sentences={len(rows)}")
    print(f"articles={len(article_rows)}")
    print(f"years={min(annual)}-{max(annual)}")
    print("phases=" + ", ".join(f"{k}:{v}" for k, v in phase_counts.items()))
    print("top_journals=" + ", ".join(f"{k}:{v}" for k, v in journal_counts.most_common(10)))


if __name__ == "__main__":
    main()
