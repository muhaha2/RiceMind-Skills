from __future__ import annotations

import csv
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "report_output"
DATA = OUT / "水稻飞虱微效位点报告_data"
FIGURES = DATA / "figures"

SOURCE_FILES = {
    "BPH resistance": ROOT / "bph_resistance_data" / "bph_resistance_sentences.csv",
    "BPH damage": ROOT / "bph_damage_data" / "bph_damage_sentences.csv",
    "WBPH resistance": ROOT / "wbph_resistance_data" / "wbph_resistance_sentences.csv",
    "WBPH damage": ROOT / "wbph_damage_data" / "wbph_damage_sentences.csv",
    "Broad planthopper": ROOT / "planthopper_broad_data" / "planthopper_broad_sentences.csv",
}

PAYLOAD_FILES = {
    "brown planthopper resistance": ROOT / "payload_brown_planthopper_resistance.json",
    "Brown planthopper damage": ROOT / "payload_brown_planthopper_damage.json",
    "white-backed planthopper resistance": ROOT / "payload_white_backed_planthopper_resistance.json",
    "Whitebacked planthopper damage": ROOT / "payload_whitebacked_planthopper_damage.json",
    "planthopper": ROOT / "payload_planthopper_broad.json",
}

DIRECT_TERMS = re.compile(
    r"resistan|susceptib|knock|silenc|overexpress|mutant|mutation|RNAi|CRISPR|"
    r"field|yield|feeding|oviposition|survival|honeydew|weight gain|bioassay|"
    r"positively regulate|negatively regulate|confers",
    re.I,
)
STRONG_CONCLUSION_TERMS = re.compile(
    r"knocking out|knockout|silencing .{0,80}(?:enhanc|increas|reduc)|"
    r"overexpression .{0,100}(?:resistan|susceptib)|"
    r"(?:positively|negatively) regulates?|"
    r"laboratory and (?:the )?field|little effect on rice yield|"
    r"compromises rice growth and grain yield|"
    r"increased resistance|enhanced resistance|decreased resistance",
    re.I,
)
METHOD_TERMS = re.compile(
    r"full-length cDNA|PCR amplification|temperature|photoperiod|relative humidity|"
    r"obtained from rice fields|maintained on the susceptible|RNA was isolated",
    re.I,
)


def candidate(
    name: str,
    aliases: list[str],
    pmids: list[str],
    scope: str,
    group: str,
    direction: str,
    role: str,
    mechanism: str,
    readiness: int,
    tradeoff_risk: int,
    tradeoff: str,
    priority: str,
    boundary: str = "功能修饰位点；效应量未量化",
) -> dict:
    return {
        "candidate": name,
        "aliases": aliases,
        "primary_pmids": pmids,
        "scope": scope,
        "mechanism_group": group,
        "direction": direction,
        "role": role,
        "mechanism": mechanism,
        "readiness": readiness,
        "tradeoff_risk": tradeoff_risk,
        "tradeoff": tradeoff,
        "priority": priority,
        "classification_boundary": boundary,
    }


CANDIDATES = [
    candidate(
        "OsWRKY36",
        ["OsWRKY36"],
        ["40042898"],
        "BPH/WBPH/SBPH",
        "Growth-defense editing",
        "负调控",
        "敲除后增强多种稻飞虱抗性；不是经典Bph主效位点。",
        "转录调控与防御输出重排，并具有跨虫种抗性表型。",
        2,
        1,
        "RiceMind句证支持成熟期评价和多虫种抗性；仍需多背景、田间和产量稳定性验证。",
        "高",
    ),
    candidate(
        "JAZ10/FJ10",
        ["JAZ10", "FJ10"],
        ["39693337"],
        "BPH",
        "Growth-defense editing",
        "特定移码等位变异增抗",
        "JAZ10移码产生FJ10，兼顾生长与褐飞虱抗性。",
        "改变JA抑制子功能，提示可通过等位基因设计缓解生长-防御矛盾。",
        2,
        1,
        "目前RiceMind仅提供单项研究的关键结论，缺少多环境和多遗传背景验证。",
        "高",
        "功能修饰等位变异；不等同于已部署主效抗性基因",
    ),
    candidate(
        "OsClpP6",
        ["OsClpP6"],
        ["38612510"],
        "BPH",
        "Growth-defense editing",
        "负调控",
        "沉默增强实验室与田间抗性，田间产量影响较小。",
        "通过JA、JA-Ile、ABA和挥发物调控防御，同时参与叶绿体蛋白稳态。",
        3,
        1,
        "已有田间与产量信息，但仍需稳定遗传编辑材料和跨生态区验证。",
        "高",
    ),
    candidate(
        "OsTPS19/OsTPS20",
        ["OsTPS19", "OsTPS20", "TPS19", "TPS20"],
        ["39340817"],
        "BPH",
        "Volatile and indirect defense",
        "正调控",
        "过表达提高柠檬烯释放并降低田间BPH发生，报告中未见显著产量性状损失。",
        "柠檬烯影响取食偏好和卵孵化，并连接抗虫与抗病。",
        3,
        2,
        "高柠檬烯可能促进二化螟等非目标害虫，存在虫谱转换风险。",
        "高",
    ),
    candidate(
        "OsGF14e-OsEDR1l",
        ["OsGF14e", "OsEDR1l", "EDR1l"],
        ["39853648"],
        "BPH",
        "Growth-defense editing",
        "负调控",
        "敲除增强抗性，但过表达增感；属于昆虫效应子利用的宿主免疫抑制模块。",
        "BPH效应子Nl14模拟宿主调控因子，抑制JA、JA-Ile和H2O2防御。",
        2,
        3,
        "敲除导致生长和籽粒产量下降，不适合直接作为无条件编辑靶点。",
        "中",
    ),
    candidate(
        "OsPGI1c",
        ["OsPGI1c"],
        ["39796027"],
        "BPH",
        "Growth-defense editing",
        "正调控",
        "过表达同时增强植株生长和BPH抗性。",
        "胞质磷酸葡萄糖异构酶连接糖代谢、海藻糖水平和抗虫反应。",
        2,
        1,
        "缺少田间、多生物型和产量品质验证。",
        "高",
    ),
    candidate(
        "OsMYB1-OsSPL14",
        ["OsMYB1", "OsSPL14"],
        ["39724382"],
        "BPH",
        "Transcriptional and metabolic defense",
        "依赖拮抗关系",
        "MYB与SPL转录调控模块影响BPH及细菌病害抗性。",
        "通过转录因子拮抗协调不同生物胁迫下的防御输出。",
        2,
        1,
        "需要明确自然等位变异、背景依赖和产量构成影响。",
        "中",
    ),
    candidate(
        "MYC2-JAMYB",
        ["MYC2", "JAMYB"],
        ["40169387"],
        "BPH",
        "Hormone signaling",
        "正调控",
        "MYC2-JAMYB转录级联参与JA介导的BPH抗性。",
        "将JA感知与下游转录防御连接。",
        2,
        1,
        "最新单项研究为主，尚缺育种材料和田间验证。",
        "中",
    ),
    candidate(
        "OsmiR319-OsPCF5",
        ["OsmiR319", "OsPCF5"],
        ["38520013"],
        "BPH",
        "Small RNA regulation",
        "OsmiR319负调控",
        "OsmiR319过表达增感，降低其活性可增强抗性。",
        "OsPCF5与MYB蛋白网络连接小RNA调控和苯丙烷防御。",
        2,
        1,
        "需要验证靶向编辑是否影响发育及其他胁迫响应。",
        "中",
    ),
    candidate(
        "OsNCED3",
        ["OsNCED3"],
        ["36064309", "38988632"],
        "BPH",
        "Hormone signaling",
        "正调控",
        "过表达增强抗性，RNAi材料抗性降低。",
        "ABA合成促进黄酮、草酸等防御化合物积累并改变取食。",
        2,
        2,
        "过表达材料株高、根系和生物量下降，存在明显生长代价。",
        "中",
    ),
    candidate(
        "OsRCI-1",
        ["OsRCI-1", "RCI-1"],
        ["38891303"],
        "BPH",
        "Volatile and indirect defense",
        "正调控",
        "过表达降低取食和产卵偏好，并提高卵寄生蜂寄生率。",
        "促进绿叶挥发物形成，兼具直接拒食与间接防御。",
        2,
        1,
        "田间稳定性和对非目标昆虫群落的影响仍需验证。",
        "中",
    ),
    candidate(
        "OsRLK7-1",
        ["OsRLK7-1"],
        ["37834016"],
        "BPH/WBPH/SBPH",
        "Growth-defense editing",
        "负调控",
        "敲除增强稻飞虱抗性，但损害生长发育。",
        "受体激酶调节生长与防御平衡。",
        2,
        3,
        "生长发育代价明确，直接育种利用风险较高。",
        "低",
    ),
    candidate(
        "SDG703",
        ["SDG703", "SET Domain Group 703"],
        ["37629184"],
        "BPH/WBPH/SBPH",
        "Epigenetic regulation",
        "负调控",
        "抑制防御相关基因表达并影响多种稻飞虱抗性。",
        "组蛋白甲基化相关表观调控。",
        2,
        2,
        "表观遗传靶点可能具有广泛多效性，需精细等位基因或组织特异调控。",
        "中",
    ),
    candidate(
        "OsEBF2",
        ["OsEBF2"],
        ["36462682"],
        "BPH",
        "Hormone signaling",
        "正调控",
        "F-box蛋白促进BPH抗性。",
        "通过乙烯与JA信号协同调节防御。",
        2,
        1,
        "缺少田间和多背景资料。",
        "中",
    ),
    candidate(
        "OsJMJ715",
        ["OsJMJ715"],
        ["34884830"],
        "BPH",
        "Epigenetic regulation",
        "负调控",
        "沉默后通过ABA和JA信号增强抗性。",
        "组蛋白去甲基化相关调控连接染色质状态与激素防御。",
        2,
        2,
        "潜在多效性和长期稳定性尚不清楚。",
        "中",
    ),
    candidate(
        "OsI-BAK1",
        ["OsI-BAK1"],
        ["34830062"],
        "BPH",
        "Growth-defense editing",
        "负调控",
        "沉默该胞外LRR基因增强BPH抗性。",
        "可能通过受体复合体或细胞表面信号影响防御阈值。",
        2,
        2,
        "缺少自然变异、田间和发育代价验证。",
        "中",
    ),
    candidate(
        "OM64",
        ["OM64"],
        ["32542992"],
        "BPH及咀嚼式害虫",
        "Growth-defense editing",
        "负调控",
        "线粒体外膜蛋白缺失增强对刺吸式和咀嚼式昆虫的抗性。",
        "线粒体功能与广谱抗虫防御耦合。",
        2,
        2,
        "广谱效应有价值，但线粒体相关多效性需系统评价。",
        "中",
    ),
    candidate(
        "MYB22-TOPLESS-HDAC1",
        ["MYB22", "TOPLESS", "HDAC1"],
        ["37149887"],
        "BPH",
        "Transcriptional and metabolic defense",
        "正调控",
        "转录抑制复合体通过抑制F3'H促进BPH抗性。",
        "重排黄酮代谢分支，说明代谢物组成而非总量决定防御效果。",
        2,
        1,
        "需明确对品质、色素和其他代谢性状的影响。",
        "中",
    ),
    candidate(
        "OsSPL10",
        ["OsSPL10"],
        ["37819387"],
        "BPH",
        "Transcriptional and metabolic defense",
        "调控方向依赖研究材料",
        "组学与功能分析支持其参与BPH防御。",
        "连接转录调控、代谢变化和抗性表型。",
        1,
        1,
        "RiceMind句证中的直接遗传效应信息有限。",
        "低",
    ),
    candidate(
        "OsWRKY71",
        ["OsWRKY71"],
        ["38023936"],
        "BPH",
        "Major-locus-dependent modifier",
        "正向依赖",
        "敲除削弱Bph15介导的抗性，属于主效位点下游修饰节点。",
        "连接Bph15识别与转录防御。",
        2,
        1,
        "不能作为独立微效抗性来源评价，必须在Bph15背景中验证。",
        "中",
        "主效位点依赖型修饰节点；不是独立抗性位点",
    ),
    candidate(
        "OsPep3-OsPEPRs",
        ["OsPep3", "OsPEPR", "OsPEPRs"],
        ["35068048"],
        "BPH/WBPH",
        "Peptide immunity",
        "正调控",
        "OsPEPR敲除削弱抗性，外源OsPep3增强抗性。",
        "内源损伤肽信号激活刺吸式昆虫防御。",
        2,
        1,
        "外源施用与遗传改良的应用路径不同，需评价持续性和成本。",
        "中",
    ),
    candidate(
        "OsEXO70H3",
        ["OsEXO70H3"],
        ["35119102"],
        "BPH",
        "Structural defense",
        "正调控",
        "参与SAMSL分泌和细胞壁木质素沉积，是抗性执行节点。",
        "囊泡运输连接代谢酶外排与细胞壁加固。",
        2,
        1,
        "缺少自然等位变异、田间和产量信息。",
        "中",
    ),
    candidate(
        "OsMYB30-OsPAL6/OsPAL8",
        ["OsMYB30", "OsPAL6", "OsPAL8"],
        ["31848246"],
        "BPH",
        "Transcriptional and metabolic defense",
        "正调控",
        "转录因子及PAL通路遗传操作改变BPH抗性。",
        "苯丙烷、SA与木质素积累共同增强结构和化学防御。",
        2,
        1,
        "属于机制明确的修饰/执行模块，但尚不能据此认定为主效育种基因。",
        "中",
    ),
    candidate(
        "OsmiR396-OsGRF8-OsF3H",
        ["OsmiR396", "miR396", "OsGRF8", "OsF3H", "F3H"],
        ["30734457", "32895423", "33401742", "36499636"],
        "BPH/WBPH",
        "Transcriptional and metabolic defense",
        "OsF3H正调控",
        "黄酮通路同时获得BPH功能验证和WBPH QTL/过表达支持。",
        "小RNA-转录因子-黄酮合成轴改变抗虫代谢物。",
        2,
        1,
        "WBPH研究将F3H与QTL联系，但其效应是否稳定达到主效标准仍需跨群体验证。",
        "高",
        "QTL支持的代谢调控基因；效应类别需按群体和虫种分别判断",
    ),
    candidate(
        "OsMKK3",
        ["OsMKK3"],
        ["31226870"],
        "BPH",
        "Hormone signaling",
        "正调控",
        "过表达增强BPH抗性。",
        "MAPK级联改变JA、JA-Ile和ABA动态。",
        2,
        1,
        "缺少田间、多背景和长期产量资料。",
        "中",
    ),
    candidate(
        "OsHLH61-OsbHLH96",
        ["OsHLH61", "OsbHLH96"],
        ["30796564"],
        "BPH",
        "Transcriptional and metabolic defense",
        "调控抗性",
        "bHLH模块影响病程相关基因和BPH防御。",
        "转录因子互作调整防御基因表达。",
        1,
        1,
        "功能和育种验证深度低于核心候选。",
        "低",
    ),
    candidate(
        "OsGID1-OsSLR1",
        ["OsGID1", "OsSLR1"],
        ["30217023", "28666057"],
        "BPH",
        "Growth-defense editing",
        "背景与节点依赖",
        "OsGID1过表达和OsSLR1沉默均可增强抗性，显示GA通路存在非线性调控。",
        "GA-DELLA网络影响木质素、JA、乙烯和H2O2。",
        2,
        2,
        "不同干预方向均出现增抗，提示不宜直接外推为简单线性育种靶点。",
        "中",
    ),
    candidate(
        "OsEXPA10",
        ["OsEXPA10"],
        ["29619515"],
        "BPH",
        "Growth-defense editing",
        "负调控抗性",
        "过表达促进生长但增感，敲低增抗但降低株高和粒重。",
        "细胞壁松弛蛋白直接体现生长-防御权衡。",
        2,
        3,
        "明确存在株高和粒重代价，直接敲除育种价值有限。",
        "低",
    ),
    candidate(
        "OsWRKY45/OsWRKY53/OsWRKY70/OsERF3",
        ["OsWRKY45", "OsWRKY53", "OsWRKY70", "OsERF3"],
        ["27258255", "27031005", "26083713", "21831212", "23228240"],
        "BPH",
        "Hormone signaling",
        "方向因成员而异",
        "多个转录因子经沉默或过表达验证会改变BPH抗性。",
        "围绕H2O2、乙烯、JA及其他昆虫防御形成早期调控网络。",
        2,
        2,
        "成员作用方向和对咀嚼式害虫的效应不同，不能作为统一模块直接编辑。",
        "中",
    ),
    candidate(
        "OsHPL3/OsHI-LOX",
        ["OsHPL3", "OsHI-LOX"],
        ["22519706", "19656341", "19891707", "38891303"],
        "BPH/WBPH及咀嚼式害虫",
        "Species-specific defense",
        "虫种依赖",
        "同一氧脂素/挥发物节点对BPH、WBPH和咀嚼式害虫可能产生相反效应。",
        "JA分支与绿叶挥发物分支的资源分配改变不同昆虫的取食和天敌招募。",
        2,
        3,
        "具有明显虫谱权衡，不适合作为单一方向的广谱抗虫靶点。",
        "低",
        "虫种依赖型修饰节点；不能脱离目标虫种讨论效应",
    ),
    candidate(
        "OsCM",
        ["OsCM", "chorismate mutase"],
        ["34829551", "33401742"],
        "WBPH",
        "Transcriptional and metabolic defense",
        "正调控",
        "过表达提高SA、木质素和抗氧化物，并增强WBPH响应。",
        "莽草酸/SA相关代谢连接木质素和抗氧化防御。",
        2,
        1,
        "证据主要来自特定遗传材料，需独立重复和田间验证。",
        "中",
        "WBPH功能修饰基因；是否属于QTL因研究定义而异",
    ),
    candidate(
        "OsNPR1",
        ["OsNPR1"],
        ["40042898", "34943188"],
        "WBPH/BPH",
        "Species-specific defense",
        "对WBPH可能负调控",
        "病害抗性增强可能伴随WBPH抗性下降，体现跨胁迫权衡。",
        "SA-JA拮抗改变不同病虫害的防御配置。",
        1,
        3,
        "直接WBPH遗传验证有限，且跨病虫权衡突出。",
        "低",
        "权衡信号节点；目前不宜视为可直接利用的微效抗性位点",
    ),
]


STRICT_QTLS = [
    {
        "item": "Lemont/Teqing数量抗性QTL组合",
        "scope": "BPH",
        "evidence": "F11重组自交系、完整RFLP图谱和重复苗期鉴定证明BPH抗性具有数量遗传基础。",
        "pmids": "12582694",
        "status": "RiceMind句证未保留各QTL名称、效应值和区间，不能进一步按主效/微效拆分。",
    },
    {
        "item": "IR64的7个微效QTL",
        "scope": "BPH",
        "evidence": "二次证据称IR64在Bph1失效后仍保持的稳定抗性与分布于1、2、3、4、6和8号染色体的7个微效QTL有关。",
        "pmids": "29282566",
        "status": "当前RiceMind句证为后续论文转述，缺少原始QTL名称、标记和效应量；只能作为历史线索。",
    },
    {
        "item": "ADR52的伴随微效QTL",
        "scope": "BPH/WBPH/GLH",
        "evidence": "综述性句证指出ADR52除BPH25/BPH26外，还具有与多种叶蝉/飞虱抗性相关的微效QTL。",
        "pmids": "27300326;29282566",
        "status": "主效基因为BPH25/BPH26；微效QTL在当前句证中未被逐一解析。",
    },
    {
        "item": "Rathu Heenati的BPH32相关小效应组分",
        "scope": "BPH",
        "evidence": "一项QTL-seq研究将染色体6上含BPH32的区域称为与两个染色体4主区域共同作用的minor QTL。",
        "pmids": "30888525",
        "status": "BPH32在其他研究中作为命名抗性基因出现，效应分类具有群体和分析背景依赖，不能全局标记为微效。",
    },
    {
        "item": "MAGIC群体Qbph7/SNP簇",
        "scope": "BPH",
        "evidence": "多模型GWAS在MAGIC indica群体中检测到与Qbph7重叠的SNP簇和其他数量性关联。",
        "pmids": "33066559",
        "status": "属于关联位点而非已验证因果基因；RiceMind句证未提供单个位点PVE。",
    },
    {
        "item": "2024年自然群体GWAS与基因组预测位点",
        "scope": "BPH",
        "evidence": "502份材料进行抗性评分、增重和蜜露表型，1,520份材料用于更大规模关联和基因组预测。",
        "pmids": "38576786",
        "status": "候选位点和基因尚需因果验证；更适合数量抗性选择而非单基因结论。",
    },
]

BOUNDARY_ITEMS = [
    {
        "item": "经典Bph/Wbph主效抗性基因",
        "examples": "Bph1/2/3/6/9/14/15/18/25/26/29/32等；Wbph1-Wbph6",
        "decision": "不纳入微效位点清单。即使其下游存在复杂网络，也不能因机制未完全阐明而降格为微效。",
    },
    {
        "item": "qWL6",
        "examples": "WBPH产卵诱导坏死/杀卵反应QTL",
        "decision": "原文明确称major QTL，因此作为边界对象说明，不归入微效QTL。",
    },
    {
        "item": "Bph3/OsLecRK基因簇",
        "examples": "OsLecRK1/2/3",
        "decision": "属于经典抗性基因簇语境，不能把其中成员简单列为独立微效位点。",
    },
    {
        "item": "仅表达响应的OsWRKY/OsNAC及组学候选",
        "examples": "WBPH诱导的多个OsWRKY、OsNAC、lncRNA和circRNA",
        "decision": "缺少遗传扰动与抗性终点时，仅列为探索候选，不进入功能微效位点主表。",
    },
    {
        "item": "昆虫基因和杀虫剂抗性基因",
        "examples": "Nl开头基因、CYP/P450等昆虫适应或药剂抗性基因",
        "decision": "不属于水稻宿主抗性位点，全部排除。",
    },
]


def read_rows() -> list[dict]:
    rows = []
    seen = set()
    for scope, path in SOURCE_FILES.items():
        if not path.is_file():
            continue
        with path.open(encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                marker = (row.get("PMID", ""), row.get("sent_id", ""), row.get("text", ""))
                if marker in seen:
                    continue
                seen.add(marker)
                item = dict(row)
                item["retrieval_scope"] = scope
                rows.append(item)
    return rows


def payload_stats() -> list[dict]:
    stats = []
    for trait, path in PAYLOAD_FILES.items():
        payload = json.loads(path.read_text(encoding="utf-8"))
        stats.append(
            {
                "trait": trait,
                "records": payload.get("records_retrieved", 0),
                "pages": payload.get("pages_retrieved", 0),
                "pagination_complete": payload.get("pagination_complete", False),
                "stop_reason": payload.get("pagination_stop_reason", ""),
            }
        )
    return stats


def compile_pattern(aliases: list[str]) -> re.Pattern:
    terms = sorted((re.escape(alias) for alias in aliases), key=len, reverse=True)
    return re.compile(r"(?<![A-Za-z0-9_.-])(?:" + "|".join(terms) + r")(?![A-Za-z0-9_.-])", re.I)


def score_sentence(row: dict, pattern: re.Pattern) -> tuple[int, int, int]:
    text = row.get("text", "")
    return (
        4 if STRONG_CONCLUSION_TERMS.search(text) else 0,
        1 if DIRECT_TERMS.search(text) else 0,
        1 if pattern.search(text) else 0,
        -3 if METHOD_TERMS.search(text) else 0,
        min(len(text), 700),
    )


def candidate_rows(rows: list[dict]) -> tuple[list[dict], list[dict]]:
    matrix = []
    excerpts = []
    by_pmid: dict[str, list[dict]] = {}
    for row in rows:
        by_pmid.setdefault(row.get("PMID", ""), []).append(row)

    for item in CANDIDATES:
        pattern = compile_pattern(item["aliases"])
        all_hits = [
            row
            for row in rows
            if pattern.search(row.get("text", "")) or pattern.search(row.get("title", ""))
        ]
        direct_pmids = [pmid for pmid in item["primary_pmids"] if pmid in by_pmid]
        primary_rows = []
        for pmid in direct_pmids:
            pmid_rows = by_pmid[pmid]
            matching = [
                row
                for row in pmid_rows
                if pattern.search(row.get("text", "")) or pattern.search(row.get("title", ""))
            ]
            primary_rows.extend(matching or pmid_rows)
        primary_rows = sorted(
            primary_rows,
            key=lambda row: score_sentence(row, pattern),
            reverse=True,
        )
        selected = []
        seen_text = set()
        for row in primary_rows:
            text = row.get("text", "").strip()
            if not text or text in seen_text:
                continue
            seen_text.add(text)
            selected.append(row)
            if len(selected) >= 3:
                break
        years = sorted(
            {
                int(row["year"])
                for row in all_hits
                if str(row.get("year", "")).isdigit()
            }
        )
        matrix.append(
            {
                "candidate": item["candidate"],
                "scope": item["scope"],
                "mechanism_group": item["mechanism_group"],
                "direction": item["direction"],
                "role": item["role"],
                "classification_boundary": item["classification_boundary"],
                "primary_pmids": ";".join(direct_pmids),
                "primary_pmid_count": len(direct_pmids),
                "all_matching_pmids": len(
                    {row.get("PMID", "") for row in all_hits if row.get("PMID", "")}
                ),
                "first_year": years[0] if years else "",
                "latest_year": years[-1] if years else "",
                "breeding_readiness": item["readiness"],
                "tradeoff_risk": item["tradeoff_risk"],
                "tradeoff": item["tradeoff"],
                "priority": item["priority"],
                "mechanism": item["mechanism"],
            }
        )
        for row in selected:
            excerpts.append(
                {
                    "candidate": item["candidate"],
                    "PMID": row.get("PMID", ""),
                    "year": row.get("year", ""),
                    "journal": row.get("journal", ""),
                    "title": row.get("title", ""),
                    "sent_id": row.get("sent_id", ""),
                    "retrieval_scope": row.get("retrieval_scope", ""),
                    "evidence_sentence": row.get("text", ""),
                }
            )
    return matrix, excerpts


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def citation_records(rows: list[dict], matrix: list[dict]) -> list[dict]:
    selected_pmids = {
        pmid
        for row in matrix
        for pmid in str(row["primary_pmids"]).split(";")
        if pmid
    }
    selected_pmids.update(
        pmid
        for item in STRICT_QTLS
        for pmid in item["pmids"].split(";")
        if pmid
    )
    records = {}
    for row in rows:
        pmid = row.get("PMID", "")
        if pmid in selected_pmids and pmid not in records:
            records[pmid] = {
                "PMID": pmid,
                "year": row.get("year", ""),
                "journal": row.get("journal", ""),
                "title": row.get("title", ""),
            }
    return sorted(
        records.values(),
        key=lambda row: (int(row["year"]) if str(row["year"]).isdigit() else 0, row["PMID"]),
        reverse=True,
    )


def md_table(headers: list[str], rows: list[list[object]]) -> list[str]:
    lines = [
        "| " + " | ".join(headers) + " |",
        "|" + "|".join(["---"] * len(headers)) + "|",
    ]
    for row in rows:
        values = [str(value).replace("|", "/").replace("\n", " ") for value in row]
        lines.append("| " + " | ".join(values) + " |")
    return lines


def build_markdown(
    stats: list[dict],
    all_rows: list[dict],
    matrix: list[dict],
    citations: list[dict],
) -> str:
    unique_pmids = {row.get("PMID", "") for row in all_rows if row.get("PMID")}
    years = sorted(
        int(row["year"])
        for row in all_rows
        if str(row.get("year", "")).isdigit()
    )
    high_priority = [row for row in matrix if row["priority"] == "高"]
    lines = [
        "# 水稻稻飞虱抗性微效位点与功能修饰基因证据报告",
        "",
        f"**报告日期：** {date.today().isoformat()}",
        "",
        "## 摘要",
        "",
        "本报告以RiceMind完整分页检索的句子级证据为基础，专门梳理水稻宿主中不属于经典Bph/Wbph主效抗性基因、但能够改变稻飞虱抗性强度、信号输出、结构防御或生长-防御权衡的遗传节点。报告严格区分两类对象：一是数量遗传学意义上被明确报道为minor QTL的位点；二是经敲除、沉默、过表达或特定等位变异验证的功能修饰基因。后者虽常被称为“微效基因”，但多数研究未报告可跨群体比较的效应量，因此本报告统一标注为“功能修饰位点，效应量未量化”，不将其等同于主效抗性基因，也不直接视为成熟育种靶点。",
        "",
        f"本次合并证据覆盖{len(unique_pmids)}篇唯一PMID，年份范围为{years[0]}-{years[-1]}年。筛选后形成{len(matrix)}个功能修饰候选，其中高优先级研究候选{len(high_priority)}个。严格意义上的微效QTL证据明显少于反向遗传学调控基因证据，而且若干历史微效QTL在RiceMind句子层面缺少名称、效应量和精确区间，说明目前最可靠的结论是“数量抗性广泛存在”，而不是已经获得一套可直接部署的命名微效QTL清单。",
        "",
        "## 1. 定义与判定边界",
        "",
        "### 1.1 本报告所称微效位点",
        "",
        "1. **严格微效QTL**：原研究明确使用minor QTL、quantitative resistance或小效应数量位点等表述，并具有分离群体或关联群体证据。",
        "2. **功能修饰位点**：不是经典主效Bph/Wbph抗性基因，但遗传操作能够改变抗性表型、昆虫行为或防御输出。若论文未报告PVE、加性效应或跨背景效应量，不把它自动称为严格微效QTL。",
        "3. **探索性候选**：仅有表达、组学或文本共现证据，未进行遗传扰动和抗性终点验证，不进入核心微效位点表。",
        "",
        "### 1.2 三个相互独立的评价轴",
        "",
        "- RiceMind证据置信度用于说明证据来源和可追溯性，不代表遗传效应大小。",
        "- 遗传效应类别用于区分主效基因、数量QTL、功能修饰节点和表达候选。",
        "- 育种成熟度用于评价是否具有田间、多背景、多虫种和产量权衡证据。",
        "",
        "## 2. 检索范围与完整性",
        "",
    ]
    lines.extend(
        md_table(
            ["RiceMind检索词", "句子记录", "分页", "完整性", "终止条件"],
            [
                [
                    row["trait"],
                    row["records"],
                    row["pages"],
                    "完整" if row["pagination_complete"] else "不完整",
                    row["stop_reason"],
                ]
                for row in stats
            ],
        )
    )
    lines.extend(
        [
            "",
            "宽泛检索词`planthopper`只用于查漏；候选进入主表必须能够回溯到具体BPH/WBPH抗性、危害或遗传操作证据。昆虫自身的Nl基因、杀虫剂抗性基因以及仅在综述中泛化提及的通路不计为水稻微效位点。",
            "",
            "## 3. 严格数量遗传学意义上的微效QTL",
            "",
            "这一部分最能直接回答育种学意义上的“微效位点”，但也是当前RiceMind句证最不完整的部分。",
            "",
        ]
    )
    lines.extend(
        md_table(
            ["位点或群体", "虫种", "证据", "PMID", "当前可下结论"],
            [
                [item["item"], item["scope"], item["evidence"], item["pmids"], item["status"]]
                for item in STRICT_QTLS
            ],
        )
    )
    lines.extend(
        [
            "",
            "**判断：** 历史研究已经证明BPH/WBPH抗性包含数量性组分，但多数被后续文献概括为“多个微效QTL”，当前句子证据没有保留足够的标记、区间和PVE信息。若目标是开发可用于分子设计育种的微效QTL清单，下一步必须回到原始定位论文及其补充数据，而不能仅依赖综述转述。",
            "",
            "## 4. 经功能验证的抗性修饰位点",
            "",
            "下表中的对象不是经典主效抗性基因。它们更适合解释抗性如何被放大、削弱或重新分配，而不是替代Bph/Wbph基因解释抗性表型的主要遗传来源。",
            "",
        ]
    )
    display = sorted(
        matrix,
        key=lambda row: (
            {"高": 3, "中": 2, "低": 1}.get(row["priority"], 0),
            int(row["breeding_readiness"]),
            int(row["primary_pmid_count"]),
        ),
        reverse=True,
    )
    lines.extend(
        md_table(
            ["候选", "范围", "方向/角色", "主要机制", "成熟度", "权衡", "PMID"],
            [
                [
                    row["candidate"],
                    row["scope"],
                    row["direction"],
                    row["mechanism"],
                    f"BR{row['breeding_readiness']}",
                    row["tradeoff"],
                    row["primary_pmids"],
                ]
                for row in display
            ],
        )
    )
    lines.extend(
        [
            "",
            "### 4.1 优先关注的编辑或等位变异节点",
            "",
            "OsClpP6、JAZ10/FJ10、OsWRKY36、OsPGI1c和OsTPS19/OsTPS20构成当前最值得进一步验证的一组候选。OsClpP6沉默同时具有实验室、田间和初步产量信息；FJ10提示可以通过特定移码等位变异而非完全敲除缓解生长-防御冲突；OsWRKY36敲除产生跨BPH、WBPH和SBPH的抗性表型；OsPGI1c同时促进生长与抗性；OsTPS19/20具有田间抗虫和无显著产量性状损失证据，但存在促进二化螟等非目标害虫的风险。[38612510, 39693337, 40042898, 39796027, 39340817]",
            "",
            "这些候选仍不能直接视为育种可用基因。除OsClpP6和OsTPS19/20外，多数研究集中于单一遗传背景和有限虫源；即使出现“生长与抗性同时提高”，也需要在多环境、不同生物型及产量品质条件下重新估计效应。",
            "",
            "### 4.2 生长-防御负调控节点",
            "",
            "OsGF14e-OsEDR1l、OsRLK7-1、OsEXPA10、OsNCED3等节点说明，解除负调控常能增强抗性，但并不等于具有育种价值。OsGF14e或OsEDR1l敲除虽然增抗，却降低生长和籽粒产量；OsRLK7-1敲除损害生长发育；OsEXPA10敲低导致株高和粒重下降；OsNCED3过表达伴随株高、根系和生物量下降。[39853648, 37834016, 29619515, 38988632]",
            "",
            "因此，对负调控位点更合理的应用策略是筛选弱等位基因、启动子编辑、组织特异表达或诱导型调控，而不是默认采用完全敲除。",
            "",
            "### 4.3 代谢与结构防御修饰网络",
            "",
            "OsMYB30-OsPAL6/8、OsmiR396-OsGRF8-OsF3H、MYB22-TOPLESS-HDAC1和OsEXO70H3共同表明，苯丙烷、黄酮、SA、木质素及细胞壁分泌构成一组可重复观察到的抗性执行网络。[31848246, 30734457, 37149887, 35119102] 这些基因能够解释抗性执行过程，但目前尚无证据证明它们在自然群体中普遍解释大比例抗性变异。",
            "",
            "OsF3H是其中证据最特殊的对象：它既在BPH中具有小RNA-转录因子-黄酮通路的功能证据，又在WBPH研究中通过QTL定位和过表达得到支持。[30734457, 32895423, 33401742, 36499636] 但不同论文对其“主要基因”“代谢基因”或QTL候选的表述并不等同于跨群体主效基因，因此报告将其列为QTL支持的功能修饰基因，而不直接归入经典主效抗性基因。",
            "",
            "### 4.4 激素、小RNA和表观调控",
            "",
            "MYC2-JAMYB、OsMKK3、OsmiR319-OsPCF5、OsJMJ715、SDG703和OsEBF2分别从JA转录级联、MAPK激素动态、小RNA、染色质状态和乙烯信号层面改变抗性。[40169387, 31226870, 38520013, 34884830, 37629184, 36462682] 这类节点适合用于解析网络层级和开发精细调控策略，但其多效性通常高于经典抗性受体。",
            "",
            "### 4.5 主效基因依赖型修饰节点",
            "",
            "OsWRKY71敲除会削弱Bph15介导的抗性，说明它是主效位点下游的重要修饰节点。[38023936] 这类基因不能与Bph15并列为独立抗性来源，其价值在于解释主效基因为何在不同背景中表现不同，以及能否通过背景优化提高主效基因的稳定性。",
            "",
            "### 4.6 虫种特异性与方向相反的节点",
            "",
            "OsHPL3、OsHI-LOX和OsNPR1显示，同一个信号节点对BPH、WBPH、咀嚼式害虫或病原菌可能产生相反效果。[22519706, 19656341, 38891303, 40042898] 这些对象最不适合被描述为“广谱增抗基因”，却非常适合用于解释虫种特异性和设计多胁迫权衡试验。",
            "",
            "## 5. 育种与实验优先级",
            "",
            "### 5.1 建议优先进行多背景验证",
            "",
            "1. **OsClpP6**：已有实验室、田间和较低产量影响证据，优先验证稳定编辑等位基因。",
            "2. **JAZ10/FJ10**：优先复现特定移码等位变异，而不是一般性JAZ10敲除。",
            "3. **OsWRKY36**：优先测试不同籼粳背景、多个BPH/WBPH种群及成熟期产量。",
            "4. **OsPGI1c**：优先验证生长与抗性双增益能否跨背景保持。",
            "5. **OsTPS19/OsTPS20**：应在多害虫群落中同步监测BPH、WBPH、二化螟和天敌，防止虫谱替换。",
            "6. **OsF3H及其调控轴**：适合开展自然等位变异、代谢物定量和BPH/WBPH双虫种验证。",
            "",
            "### 5.2 不宜直接进入育种导入的候选",
            "",
            "OsGF14e-OsEDR1l、OsRLK7-1和OsEXPA10具有明确生长或产量代价；OsHPL3/OsHI-LOX和OsNPR1具有虫种或病虫方向冲突；仅表达响应的OsWRKY/OsNAC家族成员缺乏因果验证。这些对象应优先用于机制研究、弱等位基因筛选或条件性表达设计。",
            "",
            "## 6. 不能归入微效位点的边界对象",
            "",
        ]
    )
    lines.extend(
        md_table(
            ["对象", "示例", "本报告处理"],
            [[item["item"], item["examples"], item["decision"]] for item in BOUNDARY_ITEMS],
        )
    )
    lines.extend(
        [
            "",
            "## 7. 证据局限",
            "",
            "1. RiceMind句子证据适合发现和追溯候选，但并不稳定保存QTL效应量、置信区间、LOD、PVE、加性效应及完整材料背景。",
            "2. 多数功能基因研究使用转基因或RNAi材料，观察到的效应不等同于自然群体中的微效等位变异。",
            "3. 文献数量和句子数量代表研究关注度，不代表效应大小或育种价值。",
            "4. BPH、WBPH和SBPH必须分开分析；相同基因可能产生方向相反的抗性效应。",
            "5. 报告中的BR0-BR3是本次任务用于组织证据的育种成熟度描述，不是RiceMind官方置信等级。",
            "",
            "## 8. 结论",
            "",
            "水稻稻飞虱抗性确实包含数量性和微效遗传组分，但当前可直接命名、具有明确效应量和可用于标记选择的微效QTL证据远少于功能修饰基因证据。现阶段更成熟的认识是：经典Bph/Wbph基因决定主要抗性入口，OsClpP6、JAZ10/FJ10、OsWRKY36、OsPGI1c、OsTPS19/20、OsF3H等节点调节防御强度、虫种范围和生长代价。它们能够提高对抗性执行机制的理解，其中少数具有应用潜力，但不能用来替代主效抗性基因解释抗性如何产生。",
            "",
            "未来最有价值的工作不是继续按文献数量扩大候选清单，而是为这些修饰节点补齐自然等位变异、多背景效应量、多生物型稳定性、田间产量和多害虫权衡数据，并把它们作为主效抗性基因的背景优化因子进行验证。",
            "",
            "## 参考文献索引",
            "",
        ]
    )
    for record in citations:
        lines.append(
            f"- PMID {record['PMID']} ({record['year']}). {record['title']} {record['journal']}."
        )
    lines.extend(
        [
            "",
            "## 附件说明",
            "",
            "- `candidate_role_matrix.csv`：候选角色、方向、成熟度和权衡分类。",
            "- `candidate_evidence_sentences.csv`：每个候选的代表性RiceMind原句和句子ID。",
            "- `strict_minor_qtl_evidence.csv`：严格数量遗传微效QTL证据及缺口。",
            "- `selected_references.csv`：主报告引用的PMID、题目、年份和期刊。",
            "- 原始分页JSON与完整标准化句子表保留在本次工作目录中，未复制进最终报告目录以避免冗余。",
        ]
    )
    return "\n".join(lines) + "\n"


def build_report_model(
    stats: list[dict],
    all_rows: list[dict],
    matrix: list[dict],
    excerpts: list[dict],
    citations: list[dict],
) -> dict:
    unique_pmids = sorted({row.get("PMID", "") for row in all_rows if row.get("PMID")})
    years = sorted(
        int(row["year"])
        for row in all_rows
        if str(row.get("year", "")).isdigit()
    )
    sorted_matrix = sorted(
        matrix,
        key=lambda row: (
            {"高": 3, "中": 2, "低": 1}.get(row["priority"], 0),
            int(row["breeding_readiness"]),
        ),
        reverse=True,
    )
    evidence_by_candidate = Counter(row["candidate"] for row in excerpts)
    return {
        "title": "水稻稻飞虱抗性微效位点与功能修饰基因证据报告",
        "subtitle": "基于RiceMind完整分页句子证据",
        "date": date.today().isoformat(),
        "summary": {
            "unique_pmids": len(unique_pmids),
            "year_span": f"{years[0]}-{years[-1]}",
            "candidate_count": len(matrix),
            "high_priority_count": sum(1 for row in matrix if row["priority"] == "高"),
            "evidence_excerpt_count": len(excerpts),
        },
        "retrieval": stats,
        "strict_qtls": STRICT_QTLS,
        "candidates": sorted_matrix,
        "boundary_items": BOUNDARY_ITEMS,
        "citations": citations,
        "evidence_by_candidate": dict(evidence_by_candidate),
        "figures": [
            {
                "path": str(FIGURES / "candidate_mechanism_groups.png"),
                "width": 610,
                "height": 430,
                "caption": "图1 功能修饰候选的机制类别分布。该图表示候选数量，不表示遗传效应大小。",
            },
            {
                "path": str(FIGURES / "candidate_readiness_tradeoff.png"),
                "width": 480,
                "height": 600,
                "caption": "图2 候选的育种成熟度与权衡风险。右上区域需要重点审查多效性，不能仅凭增抗表型推进。",
            },
            {
                "path": str(FIGURES / "selected_evidence_timeline.png"),
                "width": 610,
                "height": 330,
                "caption": "图3 入选候选代表性证据的发表年份分布，反映研究关注与功能验证积累。",
            },
        ],
    }


def write_figure_plan() -> None:
    plan = {
        "language": "en",
        "figures": [
            {
                "id": "candidate_mechanism_groups",
                "type": "category_bar",
                "source": "candidate_role_matrix.csv",
                "category": "mechanism_group",
                "split_values": False,
                "top_n": 12,
                "plot_title": "Mechanistic groups of planthopper resistance modifiers",
                "xlabel": "Candidate count",
                "color": "#4C78A8",
            },
            {
                "id": "candidate_readiness_tradeoff",
                "type": "grouped_bar",
                "source": "candidate_role_matrix.csv",
                "category": "candidate",
                "values": ["breeding_readiness", "tradeoff_risk"],
                "series_labels": {
                    "breeding_readiness": "Breeding readiness",
                    "tradeoff_risk": "Trade-off risk",
                },
                "aggregate": "max",
                "top_n": 16,
                "plot_title": "Breeding readiness and trade-off risk of prioritized candidates",
                "xlabel": "Ordinal score (0-3)",
                "colors": ["#4C78A8", "#F58518"],
            },
            {
                "id": "selected_evidence_timeline",
                "type": "timeline",
                "source": "candidate_evidence_sentences.csv",
                "year": "year",
                "plot_title": "Publication timeline of representative RiceMind evidence",
                "xlabel": "Publication year",
                "ylabel": "Evidence sentences",
                "color": "#54A24B",
            },
        ],
    }
    (DATA / "figure_plan.json").write_text(
        json.dumps(plan, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    DATA.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)
    rows = read_rows()
    stats = payload_stats()
    matrix, excerpts = candidate_rows(rows)
    citations = citation_records(rows, matrix)
    write_csv(DATA / "candidate_role_matrix.csv", matrix)
    write_csv(DATA / "candidate_evidence_sentences.csv", excerpts)
    write_csv(DATA / "strict_minor_qtl_evidence.csv", STRICT_QTLS)
    write_csv(DATA / "selected_references.csv", citations)
    write_csv(DATA / "retrieval_scope.csv", stats)
    markdown = build_markdown(stats, rows, matrix, citations)
    (OUT / "水稻稻飞虱抗性微效位点与功能修饰基因证据报告.md").write_text(
        markdown,
        encoding="utf-8",
    )
    model = build_report_model(stats, rows, matrix, excerpts, citations)
    (DATA / "report_model.json").write_text(
        json.dumps(model, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_figure_plan()
    print(f"rows={len(rows)}")
    print(f"candidates={len(matrix)}")
    print(f"excerpts={len(excerpts)}")
    print(f"references={len(citations)}")
    print(OUT)


if __name__ == "__main__":
    main()
