const fs = require("fs");
const path = require("path");
const {
  AlignmentType,
  BorderStyle,
  Document,
  Footer,
  HeadingLevel,
  ImageRun,
  LevelFormat,
  PageBreak,
  PageNumber,
  Packer,
  Paragraph,
  ShadingType,
  Table,
  TableCell,
  TableRow,
  TextRun,
  VerticalAlign,
  WidthType,
} = require("docx");

const root = __dirname;
const outputDir = path.join(root, "report_output");
const dataDir = path.join(outputDir, "水稻飞虱微效位点报告_data");
const model = JSON.parse(fs.readFileSync(path.join(dataDir, "report_model.json"), "utf8"));
const outputPath = path.join(outputDir, "水稻稻飞虱抗性微效位点与功能修饰基因证据报告.docx");

const border = { style: BorderStyle.SINGLE, size: 1, color: "B8C2CC" };
const borders = { top: border, bottom: border, left: border, right: border };
const FONT_CN = "SimSun";

function run(text, options = {}) {
  return new TextRun({ text: String(text ?? ""), font: FONT_CN, size: 21, ...options });
}

function p(text, options = {}) {
  return new Paragraph({
    spacing: { line: 360, after: 120 },
    alignment: options.alignment || AlignmentType.JUSTIFIED,
    indent: options.noIndent ? undefined : { firstLine: 420 },
    keepNext: options.keepNext || false,
    children: [run(text, options.run || {})],
  });
}

function heading(text, level = 1) {
  return new Paragraph({
    heading: level === 1 ? HeadingLevel.HEADING_1 : HeadingLevel.HEADING_2,
    keepNext: true,
    children: [run(text, { bold: true })],
  });
}

function bullet(text, reference = "bullet-list") {
  return new Paragraph({
    numbering: { reference, level: 0 },
    spacing: { line: 320, after: 80 },
    children: [run(text)],
  });
}

function numbered(text, reference = "number-list") {
  return new Paragraph({
    numbering: { reference, level: 0 },
    spacing: { line: 320, after: 80 },
    children: [run(text)],
  });
}

function cell(text, width, header = false, fontSize = 18) {
  return new TableCell({
    borders,
    width: { size: width, type: WidthType.DXA },
    verticalAlign: VerticalAlign.CENTER,
    shading: header ? { fill: "DCE6F1", type: ShadingType.CLEAR } : undefined,
    margins: { top: 80, bottom: 80, left: 100, right: 100 },
    children: [
      new Paragraph({
        alignment: header ? AlignmentType.CENTER : AlignmentType.LEFT,
        spacing: { line: 260, after: 0 },
        children: [run(text, { bold: header, size: fontSize })],
      }),
    ],
  });
}

function table(headers, rows, widths, fontSize = 18) {
  return new Table({
    columnWidths: widths,
    width: { size: widths.reduce((a, b) => a + b, 0), type: WidthType.DXA },
    rows: [
      new TableRow({
        tableHeader: true,
        children: headers.map((header, i) => cell(header, widths[i], true, fontSize)),
      }),
      ...rows.map(
        (row) =>
          new TableRow({
            children: row.map((value, i) => cell(value, widths[i], false, fontSize)),
          })
      ),
    ],
  });
}

function figure(item) {
  if (!fs.existsSync(item.path)) return [];
  return [
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 160, after: 80 },
      children: [
        new ImageRun({
          type: "png",
          data: fs.readFileSync(item.path),
          transformation: {
            width: item.width || 610,
            height: item.height || 340,
          },
          altText: {
            title: item.caption,
            description: item.caption,
            name: path.basename(item.path),
          },
        }),
      ],
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 160 },
      children: [run(item.caption, { italics: true, size: 18 })],
    }),
  ];
}

const body = [];
body.push(
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 1000, after: 320 },
    children: [run(model.title, { bold: true, size: 38 })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 260 },
    children: [run(model.subtitle, { size: 26, color: "44546A" })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 320, after: 120 },
    children: [run(`报告日期：${model.date}`, { size: 22 })],
  }),
  new Paragraph({ children: [new PageBreak()] })
);

body.push(heading("摘要", 1));
body.push(
  p(
    `本报告基于RiceMind完整分页句子证据，梳理水稻宿主中不属于经典Bph/Wbph主效抗性基因、但能够改变稻飞虱抗性强度、信号输出、结构防御或生长-防御权衡的遗传节点。合并证据覆盖${model.summary.unique_pmids}篇唯一PMID，年份范围为${model.summary.year_span}年；最终形成${model.summary.candidate_count}个功能修饰候选，其中高优先级研究候选${model.summary.high_priority_count}个。`
  ),
  p(
    "报告严格区分数量遗传学意义上的微效QTL与反向遗传学验证的功能修饰基因。多数调控基因缺少可跨群体比较的PVE、加性效应或自然等位变异数据，因此统一表述为“功能修饰位点，效应量未量化”，不将其等同于主效抗性基因或成熟育种靶点。"
  )
);

body.push(heading("1. 定义与判定边界", 1));
body.push(
  numbered("严格微效QTL：原研究明确报告minor QTL、数量抗性或小效应数量位点，并具有分离群体或关联群体证据。", "definition-list"),
  numbered("功能修饰位点：不是经典主效Bph/Wbph基因，但敲除、沉默、过表达或特定等位变异会改变抗性表型。", "definition-list"),
  numbered("探索性候选：仅有表达、组学或文本共现证据，未进行遗传扰动和抗性终点验证。", "definition-list"),
  p("RiceMind证据置信度、遗传效应大小和育种成熟度是三个独立评价轴，不能互相替代。")
);

body.push(heading("2. 检索范围与完整性", 1));
body.push(
  table(
    ["RiceMind检索词", "句子记录", "分页", "完整性"],
    model.retrieval.map((row) => [
      row.trait,
      row.records,
      row.pages,
      row.pagination_complete ? "完整" : "不完整",
    ]),
    [3600, 1500, 1200, 1500],
    18
  ),
  p(
    "宽泛检索词planthopper仅用于查漏。昆虫自身Nl基因、杀虫剂抗性基因、经典主效抗性基因和仅有表达响应的组学候选均不直接进入功能微效位点主表。"
  )
);

body.push(heading("3. 严格数量遗传学意义上的微效QTL", 1));
body.push(
  p(
    "严格微效QTL是最接近育种学定义的对象，但也是当前RiceMind句子层面信息最不完整的部分。历史研究已证明BPH/WBPH抗性包含数量性组分，但许多记录缺少位点名称、标记区间和效应量。"
  ),
  table(
    ["位点或群体", "虫种", "PMID", "当前可下结论"],
    model.strict_qtls.map((row) => [row.item, row.scope, row.pmids, row.status]),
    [2300, 1100, 1400, 4400],
    17
  )
);

body.push(heading("4. 功能修饰候选总览", 1));
body.push(
  p(
    "下列候选能够解释抗性如何被放大、削弱或重新分配，但不能替代经典Bph/Wbph基因解释抗性的主要遗传来源。BR0-BR3为本报告使用的育种成熟度描述，不是RiceMind官方置信等级。"
  )
);
body.push(...figure(model.figures[0]), ...figure(model.figures[1]));
body.push(
  table(
    ["候选", "虫种", "作用方向", "成熟度", "优先级"],
    model.candidates.map((row) => [
      row.candidate,
      row.scope,
      row.direction,
      `BR${row.breeding_readiness}`,
      row.priority,
    ]),
    [2700, 1700, 2500, 1100, 1200],
    17
  )
);

body.push(heading("5. 关键候选的科学解释", 1));
body.push(heading("5.1 优先进行多背景验证的候选", 2));
body.push(
  p(
    "OsClpP6、JAZ10/FJ10、OsWRKY36、OsPGI1c和OsTPS19/OsTPS20构成当前最值得进一步验证的一组候选。OsClpP6已有实验室、田间和初步产量信息；FJ10提示特定移码等位变异可缓解生长-防御冲突；OsWRKY36敲除具有跨BPH、WBPH和SBPH的表型；OsPGI1c同时促进生长与抗性；OsTPS19/20具有田间抗虫和无显著产量性状损失证据，但需要监测二化螟等非目标害虫。[38612510, 39693337, 40042898, 39796027, 39340817]"
  )
);
body.push(heading("5.2 生长-防御负调控节点", 2));
body.push(
  p(
    "OsGF14e-OsEDR1l、OsRLK7-1、OsEXPA10和OsNCED3说明解除负调控能够增强抗性，但同时可能造成生长、根系、粒重或产量损失。[39853648, 37834016, 29619515, 38988632] 对这类位点更合理的策略是弱等位基因、启动子编辑、组织特异表达或诱导型调控，而不是默认完全敲除。"
  )
);
body.push(heading("5.3 代谢与结构防御修饰网络", 2));
body.push(
  p(
    "OsMYB30-OsPAL6/8、OsmiR396-OsGRF8-OsF3H、MYB22-TOPLESS-HDAC1和OsEXO70H3将苯丙烷、黄酮、SA、木质素和细胞壁分泌连接到抗性执行过程。[31848246, 30734457, 37149887, 35119102] 这些证据支持其机制价值，但尚不能证明它们在自然群体中普遍解释大比例抗性变异。"
  ),
  p(
    "OsF3H同时具有BPH功能证据和WBPH QTL/过表达支持，是连接数量定位与机制验证的代表对象。[30734457, 32895423, 33401742, 36499636] 由于不同群体和虫种中的效应类别尚未统一，本报告将其界定为QTL支持的功能修饰基因。"
  )
);
body.push(heading("5.4 主效基因依赖与虫种特异性", 2));
body.push(
  p(
    "OsWRKY71是Bph15介导抗性的下游修饰节点，不能作为独立抗性来源与Bph15并列。[38023936] OsHPL3、OsHI-LOX和OsNPR1则显示同一节点对BPH、WBPH、咀嚼式害虫或病原菌可能产生相反效应。[22519706, 19656341, 38891303, 40042898] 这类候选必须按目标虫种和多胁迫组合进行评价。"
  )
);

body.push(heading("6. 育种与实验优先级", 1));
body.push(
  numbered("OsClpP6：优先验证稳定编辑等位基因、跨背景田间抗性和产量。", "priority-list"),
  numbered("JAZ10/FJ10：优先复现特定移码等位变异，而不是一般性完全敲除。", "priority-list"),
  numbered("OsWRKY36：测试不同籼粳背景、多个BPH/WBPH种群和成熟期产量。", "priority-list"),
  numbered("OsPGI1c：验证生长与抗性双增益能否跨环境保持。", "priority-list"),
  numbered("OsTPS19/OsTPS20：开展多害虫和天敌群落联合评价，防止虫谱替换。", "priority-list"),
  numbered("OsF3H调控轴：开展自然等位变异、代谢定量和BPH/WBPH双虫种验证。", "priority-list")
);

body.push(...figure(model.figures[2]));

body.push(heading("7. 不能归入微效位点的边界对象", 1));
body.push(
  table(
    ["对象", "示例", "本报告处理"],
    model.boundary_items.map((row) => [row.item, row.examples, row.decision]),
    [2400, 2900, 4000],
    17
  )
);

body.push(heading("8. 证据局限", 1));
body.push(
  bullet("RiceMind句子证据不稳定保存QTL效应量、LOD、PVE、加性效应和完整材料背景。", "limits-list"),
  bullet("转基因或RNAi效应不等同于自然群体中的微效等位变异。", "limits-list"),
  bullet("文献与句子数量代表关注度，不代表遗传效应大小或育种价值。", "limits-list"),
  bullet("BPH、WBPH和SBPH必须分开评价，同一基因可能产生相反方向。", "limits-list"),
  bullet("严格微效QTL的标记、区间和效应量需要回到原始定位论文及补充数据核验。", "limits-list")
);

body.push(heading("9. 结论", 1));
body.push(
  p(
    "水稻稻飞虱抗性包含数量性和微效遗传组分，但当前可直接命名、具有明确效应量并可用于标记选择的微效QTL证据，远少于功能修饰基因证据。经典Bph/Wbph基因决定主要抗性入口；OsClpP6、JAZ10/FJ10、OsWRKY36、OsPGI1c、OsTPS19/20、OsF3H等节点调节防御强度、虫种范围和生长代价。"
  ),
  p(
    "下一步应为这些修饰节点补齐自然等位变异、多背景效应量、多生物型稳定性、田间产量和多害虫权衡数据，并把它们作为主效抗性基因的背景优化因子进行验证，而不是用其替代主效基因解释抗性如何产生。"
  )
);

body.push(heading("参考文献索引", 1));
for (const record of model.citations) {
  body.push(
    p(
      `PMID ${record.PMID} (${record.year}). ${record.title} ${record.journal}.`,
      { noIndent: true }
    )
  );
}

const doc = new Document({
  styles: {
    default: {
      document: {
        run: { font: FONT_CN, size: 21 },
        paragraph: { spacing: { line: 360, after: 120 } },
      },
    },
    paragraphStyles: [
      {
        id: "Heading1",
        name: "Heading 1",
        basedOn: "Normal",
        next: "Normal",
        quickFormat: true,
        run: { font: FONT_CN, size: 30, bold: true, color: "1F4E79" },
        paragraph: { spacing: { before: 300, after: 160 }, outlineLevel: 0 },
      },
      {
        id: "Heading2",
        name: "Heading 2",
        basedOn: "Normal",
        next: "Normal",
        quickFormat: true,
        run: { font: FONT_CN, size: 25, bold: true, color: "2F5597" },
        paragraph: { spacing: { before: 220, after: 120 }, outlineLevel: 1 },
      },
    ],
  },
  numbering: {
    config: [
      {
        reference: "bullet-list",
        levels: [
          {
            level: 0,
            format: LevelFormat.BULLET,
            text: "•",
            alignment: AlignmentType.LEFT,
            style: { paragraph: { indent: { left: 720, hanging: 360 } } },
          },
        ],
      },
      ...["definition-list", "priority-list", "limits-list"].map((reference) => ({
        reference,
        levels: [
          {
            level: 0,
            format: reference === "limits-list" ? LevelFormat.BULLET : LevelFormat.DECIMAL,
            text: reference === "limits-list" ? "•" : "%1.",
            alignment: AlignmentType.LEFT,
            style: { paragraph: { indent: { left: 720, hanging: 360 } } },
          },
        ],
      })),
    ],
  },
  sections: [
    {
      properties: {
        page: {
          size: { width: 11906, height: 16838 },
          margin: { top: 1134, right: 1134, bottom: 1134, left: 1134 },
          pageNumbers: { start: 1, formatType: "decimal" },
        },
      },
      footers: {
        default: new Footer({
          children: [
            new Paragraph({
              alignment: AlignmentType.CENTER,
              children: [
                run("RiceMind稻飞虱微效位点报告  |  "),
                new TextRun({ children: [PageNumber.CURRENT], font: FONT_CN, size: 18 }),
              ],
            }),
          ],
        }),
      },
      children: body,
    },
  ],
});

Packer.toBuffer(doc).then((buffer) => {
  fs.writeFileSync(outputPath, buffer);
  console.log(outputPath);
});
