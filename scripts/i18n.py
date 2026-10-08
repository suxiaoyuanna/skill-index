"""Render-time strings for the generated lookup tables.

Chinese support in this project is a *capability* (the alias table and the CJK
bigram search in skillfind.py); the language selected here only decides what the
generated Markdown looks like. Switching `--lang` never changes what is
findable, only what is printed.

Category labels and one-line summaries live in taxonomy.py, next to the
classifier signal they describe -- keeping them there is what stops the two
from drifting. Everything else (titles, table headers, prose) lives here.

The `en` and `zh` tables must have identical key sets; that is asserted at
import time rather than trusted, because a missing key would silently emit
Chinese into an English document.
"""
from __future__ import annotations

from taxonomy import ALL_CATEGORIES

LANGS = ("en", "zh")
DEFAULT_LANG = "en"

STRINGS: dict[str, dict[str, str]] = {
    "en": {
        # SKILLS.md -------------------------------------------------------
        "skills.title": "# Skill Master Index",
        "skills.summary": "**{n}** skills across **{cats}** categories.",
        "skills.search_hint": "> Prefer search: `{run} \"<keywords>\"` · browse by category: "
                              "[by-category/](by-category/).",
        "skills.h2": "## Category index",
        "skills.th": "| Category | Label | Count | Summary |",
        "skills.cat_heading": "## {label} (`{cid}`)",
        "skills.cat_meta": "{desc} — **{n}** skills",
        "skills.th_skills": "| Skill | Description | Tags |",
        "none": "_(no description)_",

        # by-category/<id>.md ---------------------------------------------
        "cat.title": "# {label} — `{cid}`",
        "cat.triggers": "**{n}** skills | triggers: {triggers}",
        "cat.back": "[← back to master index](../SKILLS.md)",

        # ROUTER.md -------------------------------------------------------
        "router.title": "# Skill Routing Table (always-on index)",
        "router.summary": "{n} skills in {cats} categories on this machine.",
        "router.purpose": "This file gives only \"category + trigger words\", to point you in a "
                          "direction. Pick the actual skill from `by-category/`.",
        "router.cmd_search": "search:  ",
        "router.cmd_cat": "by cat:  ",
        "router.cmd_tag": "by tag:  ",
        "router.th": "| Category | Label | Count | When to use (triggers) |",
        "router.reps_h2": "## Representative skills",
        "router.reps_note": "One or two canonical names per category (full lists in `by-category/`):",
        "router.more": " … ({n} total)",

        # by-tag.md -------------------------------------------------------
        "tag.title": "# Tag Reverse Index",
        "tag.summary": "**{n}** tags, at least 2 skills each, sorted by coverage.",
        "tag.h2": "## Singleton tags",

        # GOVERNANCE.md ---------------------------------------------------
        "gov.title": "# Governance report: redundancy and dead skills",
        "gov.warn": "> This report only flags things. It never moves or deletes a file.",
        "gov.th": "| Class | Count | Meaning | Suggested action |",
        "gov.r_nested": "Nested duplicates",
        "gov.r_nested_m": "Same skill installed twice (`X` and `X/X`)",
        "gov.r_nested_a": "Delete the inner copy — unambiguous",
        "gov.r_alias": "Pure aliases",
        "gov.r_alias_m": "Description says it is an alias for another skill",
        "gov.r_alias_a": "Keep one of the two",
        "gov.r_lookalike": "Near-identical descriptions",
        "gov.r_lookalike_m": "Descriptions overlap heavily; needs a human call",
        "gov.r_lookalike_a": "Compare one by one",
        "gov.r_langvar": "Language-bound variants",
        "gov.r_langvar_m": "Same capability, different language SDK",
        "gov.r_langvar_a": "Pick one per project language",
        "gov.r_deprecated": "Likely deprecated",
        "gov.r_deprecated_m": "Description says deprecated / renamed / obsolete",
        "gov.r_deprecated_a": "Confirm, then archive",
        "gov.r_zombie": "Zombie skills",
        "gov.r_zombie_m": "Description missing or a placeholder",
        "gov.r_zombie_a": "Write a description or archive",
        "gov.h_nested": "## 1. Nested duplicates (unambiguous)",
        "gov.n_nested": "The same skill installed at two nesting levels. Search shows both as "
                        "near-identical candidates.",
        "gov.th_dup": "| Outer | Inner copy | Outer path |",
        "gov.h_alias": "## 2. Pure aliases",
        "gov.th_alias": "| Skill | Points at |",
        "gov.h_lookalike": "## 3. Near-identical descriptions",
        "gov.n_lookalike": "Descriptions overlap heavily — either one template generated them "
                           "in bulk, or they are genuine duplicates. **A human has to decide**: "
                           "if each one targets a different service or object (say "
                           "`google-calendar-*` vs `google-drive-*`) that is fine; if the object "
                           "is the same too, it is a real duplicate.",
        "gov.h_langvar": "## 4. Language-bound variants",
        "gov.n_langvar": "One capability with an SDK per language. **Not duplicates** — pick the "
                         "one matching your project.",
        "gov.h_deprecated": "## 5. Likely deprecated",
        "gov.th_deprecated": "| Skill | Description excerpt |",
        "gov.h_zombie": "## 6. Zombie skills (missing or placeholder description)",
        "gov.n_zombie": "These can never be found by search, so they may as well not exist. "
                        "Write a description or archive them.",
        "gov.th_zombie": "| Skill | Raw description | Path |",
        "gov.none": "_none_",
        "gov.more": "_({n} more groups not listed.)_",
        "gov.more_langvar": "- …{n} more groups",
        "gov.more_lookalike": "_Another {n} groups are not listed._",

        # refresh.py ------------------------------------------------------
        # taxonomy_doctor.py ----------------------------------------------
        "doc.title": "taxonomy fit: {n} skills across {cats} categories",
        "doc.coverage": "unclassified   {n:5}  {pct:5.1f}%   (category \"{cat}\")",
        "doc.confidence": "confidence     high {hi:5}  medium {med:5}  low {lo:5}  ({lopct:.1f}%)",
        "doc.h_buckets": "Largest categories",
        "doc.h_findings": "Findings",
        "doc.bucket": "  {cat:22} {n:5}  {pct:5.1f}%",
        "doc.f_add": "[add]   {n} skills in \"{cat}\" share the name family \"{fam}\". "
                     "A category for it would claim them.",
        "doc.f_longtail": "[ok]    \"{cat}\" holds {n} skills; its largest name family has "
                          "{fam} of them, under the {min} that would suggest a category. "
                          "A long tail, not a missing one. Nothing to add.",
        "doc.f_split": "[split] \"{cat}\" holds {n} skills ({pct:.1f}%), too many to browse. "
                       "Largest name families: {fams}",
        "doc.f_low": "[llm]   {n} skills ({pct:.1f}%) are low confidence. "
                     "Run make_batches.py to refine them.",
        "doc.f_none": "[ok]    No category is missing, oversized or ambiguous. "
                      "This taxonomy fits your library.",
        "doc.fams": "{fam} ({n})",
        "doc.hint": "Act on any of this by editing scripts/taxonomy.py, then re-running "
                    "refresh.py - it reclassifies automatically.",

        "refresh.scanning": "== 1/5 scan skill roots",
        "refresh.classifying": "== 2/5 rule classification (incremental)",
        "refresh.merging": "== 3/5 merge LLM overrides",
        "refresh.reporting": "== 4/5 generate lookup tables ({lang})",
        "refresh.done": "== done in {secs:.1f}s",
    },
    "zh": {
        "skills.title": "# Skill 总查找表",
        "skills.summary": "共 **{n}** 个技能，分为 **{cats}** 个类目。",
        "skills.search_hint": "> 检索优先：`{run} \"关键词\"`；按类目看：[by-category/](by-category/)。",
        "skills.h2": "## 类目索引",
        "skills.th": "| 类目 | 名称 | 数量 | 一句话 |",
        "skills.cat_heading": "## {label} (`{cid}`)",
        "skills.cat_meta": "{desc} — **{n}** 个",
        "skills.th_skills": "| 技能 | 说明 | 标签 |",
        "none": "_(无描述)_",

        "cat.title": "# {label} — `{cid}`",
        "cat.triggers": "**{n}** 个技能 ｜ 触发词：{triggers}",
        "cat.back": "[← 返回总表](../SKILLS.md)",

        "router.title": "# Skill 路由表（常驻索引）",
        "router.summary": "本机共 {n} 个 skill，分 {cats} 个类目。",
        "router.purpose": "本文件只给「类目 + 触发词」，用于判断该往哪个方向找；具体选型再查 `by-category/`。",
        "router.cmd_search": "检索：  ",
        "router.cmd_cat": "按类目：",
        "router.cmd_tag": "按标签：",
        "router.th": "| 类目 | 名称 | 数量 | 什么时候用（触发词） |",
        "router.reps_h2": "## 高频技能速查",
        "router.reps_note": "按类目挑出的代表性技能（完整清单见 `by-category/`）：",
        "router.more": " …（共 {n}）",

        "tag.title": "# 标签反查表",
        "tag.summary": "共 **{n}** 个标签。按覆盖度排序，只列出 ≥2 个技能的标签。",
        "tag.h2": "## 单例标签",

        "gov.title": "# 治理报告：冗余与失效技能",
        "gov.warn": "> 本报告只做标记，不移动或删除任何文件。",
        "gov.th": "| 类别 | 数量 | 含义 | 建议动作 |",
        "gov.r_nested": "嵌套重复",
        "gov.r_nested_m": "同一 skill 装了两遍（`X` 与 `X/X`）",
        "gov.r_nested_a": "删掉内层副本，确定性问题",
        "gov.r_alias": "纯别名",
        "gov.r_alias_m": "描述自称是另一个 skill 的别名",
        "gov.r_alias_a": "保留其一",
        "gov.r_lookalike": "描述雷同系列",
        "gov.r_lookalike_m": "描述高度重合，需人工判断",
        "gov.r_lookalike_a": "逐一比对",
        "gov.r_langvar": "语言绑定变体",
        "gov.r_langvar_m": "同一能力的不同语言 SDK",
        "gov.r_langvar_a": "按项目语言取一个",
        "gov.r_deprecated": "疑似废弃",
        "gov.r_deprecated_m": "描述标了 deprecated/renamed/obsolete",
        "gov.r_deprecated_a": "确认后归档",
        "gov.r_zombie": "僵尸技能",
        "gov.r_zombie_m": "描述缺失或为占位符",
        "gov.r_zombie_a": "补描述或归档",
        "gov.h_nested": "## 一、嵌套重复（确定性）",
        "gov.n_nested": "同一技能在两层目录各装了一份，检索时会出现两个近乎相同的候选。",
        "gov.th_dup": "| 外层 | 内层副本 | 外层路径 |",
        "gov.h_alias": "## 二、纯别名",
        "gov.th_alias": "| 技能 | 指向 |",
        "gov.h_lookalike": "## 三、描述雷同系列",
        "gov.n_lookalike": "描述文本高度重合（可能是同模板批量生成，也可能是真重复）。"
                           "**需要人工判断**：若各技能对应不同服务/对象"
                           "（如 `google-calendar-*` vs `google-drive-*`）则属正常；"
                           "若连对象都相同，就是真重复。",
        "gov.h_langvar": "## 四、语言绑定变体",
        "gov.n_langvar": "同一能力的多语言 SDK。**不是重复**，按项目语言取一个即可。",
        "gov.h_deprecated": "## 五、疑似废弃",
        "gov.th_deprecated": "| 技能 | 描述片段 |",
        "gov.h_zombie": "## 六、僵尸技能（描述缺失或为占位符）",
        "gov.n_zombie": "这些技能无法被检索命中，等于不存在；建议补描述或归档。",
        "gov.th_zombie": "| 技能 | 描述原文 | 路径 |",
        "gov.none": "_无_",
        "gov.more": "_另有 {n} 组未列出。_",
        "gov.more_langvar": "- …另有 {n} 组",
        "gov.more_lookalike": "_另有 {n} 组未列出。_",

        # taxonomy_doctor.py ----------------------------------------------
        "doc.title": "分类表适配度：{n} 个技能，{cats} 个类目",
        "doc.coverage": "未归类         {n:5}  {pct:5.1f}%   （类目 \"{cat}\"）",
        "doc.confidence": "置信度         high {hi:5}  medium {med:5}  low {lo:5}  ({lopct:.1f}%)",
        "doc.h_buckets": "最大的类目",
        "doc.h_findings": "诊断",
        "doc.bucket": "  {cat:22} {n:5}  {pct:5.1f}%",
        "doc.f_add": "[补类目] \"{cat}\" 里有 {n} 个技能的命名同属 \"{fam}\" 家族，值得为它建一个类目。",
        "doc.f_longtail": "[正常]  \"{cat}\" 里有 {n} 个技能，最大的命名家族也只有 {fam} 个"
                          "（够不上建类目的 {min} 个）——这是长尾，不是漏了类目。不用改。",
        "doc.f_split": "[拆分]  \"{cat}\" 有 {n} 个技能（{pct:.1f}%），多到没法浏览。"
                       "最大的命名家族：{fams}",
        "doc.f_low": "[精修]  {n} 个技能（{pct:.1f}%）是低置信度，可跑 make_batches.py 精修。",
        "doc.f_none": "[正常]  没有缺失、过大或含糊的类目，这张分类表适配你的库。",
        "doc.fams": "{fam}（{n}）",
        "doc.hint": "要动手就编辑 scripts/taxonomy.py，再跑一次 refresh.py —— 会自动重新分类。",

        "refresh.scanning": "== 1/5 扫描 skill 根目录",
        "refresh.classifying": "== 2/5 规则分类（增量）",
        "refresh.merging": "== 3/5 合并 LLM 覆盖",
        "refresh.reporting": "== 4/5 生成查找表（{lang}）",
        "refresh.done": "== 完成，用时 {secs:.1f}s",
    },
}

# Trigger words for the router table, per category. Hand-picked for dispatch:
# these are what an agent greps the table with when it does not know the
# vocabulary yet, so they are the one genuinely language-bound column.
ROUTER_TRIGGERS: dict[str, dict[str, str]] = {
    "en": {
        "agent-meta": "skill management / skill authoring / subagents / context / memory / "
                      "prompt engineering / MCP / hooks",
        "cloud-infra": "aws azure gcp terraform kubernetes docker serverless message queue "
                       "cloud resources",
        "devops-cicd": "ci/cd pipeline deploy release git workflow monitoring alerting SRE "
                       "postmortem",
        "security": "security pentest vulnerability audit threat model secrets compliance GDPR "
                    "reverse engineering forensics",
        "testing-qa": "testing unit test e2e playwright load test coverage accessibility a11y",
        "debugging": "debug error root cause troubleshoot crash profiling fault isolation",
        "architecture": "architecture system design design pattern DDD microservices "
                        "refactoring plan ADR technical design",
        "code-quality": "code review simplify technical debt lint conventions dependency "
                        "governance",
        "languages": "python go rust java c# c++ php ruby kotlin swift language features CLI",
        "frontend": "react vue angular svelte next.js tailwind css components state management "
                    "3D web",
        "backend-api": "backend REST GraphQL gRPC auth authorization payment messaging "
                       "server-side",
        "mobile": "iOS Android Flutter React Native Expo SwiftUI desktop app mobile",
        "build-tooling": "build bazel webpack vite monorepo dependency management scaffolding "
                         "package manager",
        "thinking-decision": "brainstorm challenge assumptions multi-perspective trade-off "
                             "decision critical thinking requirement clarification",
        "database": "database sql postgres mysql mongodb redis index migration vector store",
        "ai-ml": "LLM RAG fine-tuning training inference embedding evaluation computer vision NLP",
        "data-eng": "data pipeline ETL spark airflow dbt analytics dashboard statistics backtest",
        "docs-writing": "documentation README manual paper LaTeX Word PPT Excel PDF proofread "
                        "translation",
        "research": "research literature search competitive analysis market web scraping "
                    "data collection news",
        "design-ui": "interface design UI UX design system Figma color icon brand visual",
        "content-media": "image generation video audio voiceover podcast subtitles slide design "
                         "social content",
        "marketing-growth": "SEO marketing ads conversion rate landing page copywriting email "
                            "growth pricing",
        "business-product": "product management PRD requirements business startup finance "
                            "project contract legal supply chain",
        "office-automation": "Google/Office workspace Slack Notion Jira CRM calendar email "
                             "platform automation",
        "hardware-eda": "PCB hardware KiCad EDA schematic FPGA Verilog embedded STM32 ESP32 "
                        "circuit components",
        "health": "health medical checkup nutrition exercise sleep mental health medication",
        "gamedev": "game Unity Unreal Godot game mechanics",
        "science-domain": "scientific computing quantum bioinformatics chemistry materials "
                          "geospatial simulation",
        "other": "unclassified / unclear purpose / missing description",
    },
    "zh": {
        "agent-meta": "skill 管理 / skill 编写 / 子agent / 上下文 / 记忆 / 提示词 / MCP 开发 / hook",
        "cloud-infra": "aws azure gcp terraform kubernetes docker serverless 消息队列 云资源",
        "devops-cicd": "ci/cd 流水线 部署 发布 git 工作流 监控 告警 SRE 事故复盘",
        "security": "安全 渗透 漏洞 审计 威胁建模 密钥 合规 GDPR 逆向 取证",
        "testing-qa": "测试 单测 e2e playwright 压测 覆盖率 可访问性无障碍",
        "debugging": "调试 报错 根因 排查 crash 性能剖析 故障定位",
        "architecture": "架构 系统设计 设计模式 DDD 微服务 重构规划 ADR 技术方案",
        "code-quality": "代码审查 评审 简化 技术债 lint 规范 依赖治理",
        "languages": "python go rust java c# c++ php ruby kotlin swift 语言特性 CLI",
        "frontend": "react vue angular svelte next.js tailwind css 组件 状态管理 3D web",
        "backend-api": "后端 REST GraphQL gRPC 认证 授权 支付 消息 服务端",
        "mobile": "iOS Android Flutter React Native Expo SwiftUI 桌面应用 移动端",
        "build-tooling": "构建 bazel webpack vite monorepo 依赖管理 脚手架 包管理",
        "thinking-decision": "头脑风暴 方案质疑 多视角权衡 决策 批判性思维 需求澄清",
        "database": "数据库 sql postgres mysql mongodb redis 索引 迁移 向量库",
        "ai-ml": "LLM RAG 大模型 微调 训练 推理 向量 embedding 评估 CV NLP",
        "data-eng": "数据管道 ETL spark airflow dbt 分析 看板 统计 回测",
        "docs-writing": "文档 README 说明书 论文 LaTeX Word PPT Excel PDF 校对 翻译",
        "research": "调研 深度研究 文献 检索 竞品 市场 爬取 采集 资讯",
        "design-ui": "界面设计 UI UX 设计系统 Figma 配色 图标 品牌 视觉",
        "content-media": "图像生成 视频 音频 配音 播客 字幕 幻灯片美化 社媒内容",
        "marketing-growth": "SEO 营销 广告 转化率 落地页 文案 邮件 增长 定价",
        "business-product": "产品管理 PRD 需求 商业 创业 财务 项目 合同 法务 供应链",
        "office-automation": "Google/Office 办公 Slack Notion Jira CRM 日历 邮件 平台自动化",
        "hardware-eda": "PCB 硬件 KiCad EDA 原理图 FPGA Verilog 嵌入式 STM32 ESP32 电路 元器件",
        "health": "健康 体检 营养 运动 睡眠 心理 用药",
        "gamedev": "游戏 Unity Unreal Godot 游戏机制",
        "science-domain": "科学计算 量子 生物信息 化学 材料 地理 仿真",
        "other": "未归类 / 用途不明 / 缺少描述",
    },
}

# Fail loudly at import rather than silently emitting a half-translated document.
for _lang in LANGS:
    _missing = sorted(set(STRINGS[DEFAULT_LANG]) - set(STRINGS[_lang]))
    _extra = sorted(set(STRINGS[_lang]) - set(STRINGS[DEFAULT_LANG]))
    if _missing or _extra:
        raise RuntimeError(
            f"i18n: '{_lang}' string table does not match '{DEFAULT_LANG}' "
            f"(missing={_missing}, extra={_extra})"
        )
    _missing_cats = [c["id"] for c in ALL_CATEGORIES if c["id"] not in ROUTER_TRIGGERS[_lang]]
    if _missing_cats:
        raise RuntimeError(f"i18n: no '{_lang}' router triggers for {_missing_cats}")


def t(lang: str, key: str, **kw) -> str:
    """Look up a render-time string. Raises on an unknown key, deliberately."""
    s = STRINGS[lang][key]
    return s.format(**kw) if kw else s


def trigger(cid: str, lang: str) -> str:
    return ROUTER_TRIGGERS[lang].get(cid, "—")
