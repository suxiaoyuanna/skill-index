#!/usr/bin/env python3
"""skillfind - search the skill library.

Usage:
    python3 scripts/skillfind.py "keywords" [--limit 8] [--cat ID] [--tag T]
    python3 scripts/skillfind.py --cat hardware-eda --limit 50     # browse
    python3 scripts/skillfind.py "竞品分析" --json                   # Chinese query

Scoring is IDF-weighted field overlap:
    id exact > id token > tag > name token > category / description
Chinese queries are expanded through an alias table (zh -> en concepts) so
"做PCB设计" still finds `kicad`; Chinese that the table does not cover stays
in the query as CJK bigrams, which match Chinese skill descriptions directly.
This works regardless of --lang: the alias table and the bigram index are
capabilities, not translations.

--lang only picks the language the *results* are printed in. It defaults to
`auto`, which follows the language of the query.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from taxonomy import CATEGORIES, CAT_BY_ID, FALLBACK_ID  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

# Windows consoles default to GBK; force UTF-8 so Chinese output survives.
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass

# --------------------------------------------------------------------------
# Chinese alias table: query substrings -> concept terms injected into search
# --------------------------------------------------------------------------
ZH_ALIASES = {
    "技能": "skill agent", "技能管理": "skill audit manage",
    "测试": "test testing", "单测": "unit test", "调试": "debug troubleshoot",
    "部署": "deploy deployment", "上线": "deploy release", "发布": "release publish",
    "数据库": "database sql postgres", "接口": "api endpoint rest",
    "前端": "frontend react ui", "后端": "backend api server", "界面": "ui design",
    "设计": "design ui ux", "视觉": "visual design", "配色": "color palette",
    "文档": "documentation docs writing", "写作": "writing copywriting",
    "论文": "academic paper latex", "引用": "citation bibtex reference",
    "幻灯片": "slides pptx deck presentation", "演示": "presentation slides",
    "表格": "spreadsheet excel xlsx", "报告": "report writing",
    "安全": "security audit vulnerability", "渗透": "penetration test pentest",
    "漏洞": "vulnerability exploit cve", "审计": "audit review",
    "架构": "architecture design pattern", "重构": "refactor cleanup",
    "代码审查": "code review", "评审": "review audit",
    "性能": "performance optimization profiling", "优化": "optimiz improve",
    "爬虫": "scraper crawling", "抓取": "scrape crawl fetch",
    "搜索": "search research retrieval", "调研": "research investigation",
    "检索": "search retrieval find", "研究": "research",
    "竞品": "competitor competitive alternatives landscape",
    "对标": "benchmark competitor comparison",
    "网页": "web webpage frontend landing page html",
    "网站": "website web site frontend",
    "落地页": "landing page cro conversion",
    "界面设计": "ui design interface",
    "排版": "typography layout typesetting",
    "行情": "market price data financial",
    "论文写作": "academic paper writing latex",
    "投稿": "submit journal conference paper",
    "开题": "research proposal thesis",
    "专利": "patent intellectual property",
    "招投标": "tender bidding procurement",
    "简历": "resume cv",
    "面试": "interview hiring",
    "报销": "expense invoice receipt",
    "发票": "invoice receipt billing",
    "记账": "bookkeeping accounting finance",
    "排班": "scheduling shift roster",
    "库存": "inventory stock warehouse",
    "物流": "logistics shipping supply-chain",
    "质检": "quality inspection nonconformance",
    "教学": "teaching course curriculum",
    "课件": "courseware slides teaching",
    "考试": "exam test assessment",
    "题库": "question bank exam",
    "方言": "dialect language",
    "语音": "voice speech audio",
    "识别": "recognition detection ocr",
    "人脸": "face detection recognition",
    "大屏": "dashboard big-screen visualization",
    "报表": "report spreadsheet analytics",
    "数据": "data analysis pipeline", "数据分析": "data analysis analytics",
    "可视化": "visualization chart dashboard dataviz", "图表": "chart plot graph",
    "机器学习": "machine learning ml", "深度学习": "deep learning neural",
    "模型": "model training inference", "训练": "training fine-tune",
    "提示词": "prompt engineering", "智能体": "agent autonomous",
    "知识库": "rag knowledge base retrieval",
    "嵌入式": "embedded microcontroller mcu firmware stm32 esp32",
    "单片机": "mcu microcontroller embedded stm32",
    "硬件": "hardware pcb circuit electronics", "电路": "circuit schematic electronics",
    "原理图": "schematic kicad", "画板": "pcb layout kicad", "布线": "layout routing pcb",
    "元器件": "component bom part", "芯片": "chip ic semiconductor",
    "驱动": "driver kernel device", "固件": "firmware embedded",
    "云": "cloud aws azure gcp", "容器": "docker container kubernetes",
    "监控": "monitoring observability alert", "日志": "log logging",
    "运维": "devops operations sre",
    "营销": "marketing growth", "增长": "growth acquisition",
    "广告": "ads advertising campaign", "推广": "promotion marketing",
    "文案": "copywriting content", "标题": "headline title",
    "邮件": "email sequence campaign", "客户": "customer crm",
    "价格": "pricing monetization", "转化": "conversion cro funnel",
    "产品": "product management roadmap", "需求": "requirement prd spec",
    "项目": "project management planning", "计划": "plan planning",
    "会议": "meeting notes summary", "日历": "calendar schedule",
    "办公": "office productivity automation", "自动化": "automation workflow",
    "视频": "video generation editing", "音频": "audio speech voice",
    "图片": "image generation editing", "图像": "image vision processing",
    "生成": "generate generation", "剪辑": "editing video",
    "健康": "health medical wellness", "睡眠": "sleep", "营养": "nutrition diet",
    "财务": "finance financial model", "投资": "invest portfolio trading",
    "法律": "legal contract compliance", "合同": "contract legal",
    "翻译": "translation localization i18n", "本地化": "localization i18n",
    "工具": "tool cli utility", "脚本": "script shell automation",
    "学习": "learning tutorial", "教程": "tutorial guide",
    "思考": "thinking reasoning decision", "决策": "decision framework",
    "头脑风暴": "brainstorm idea", "复盘": "retrospective review postmortem",
    "记忆": "memory context", "上下文": "context window",
    "游戏": "game development unity",
    "3d": "3d threejs model",

    # Compound phrases. Longest match wins, so these resolve before the generic
    # two-character entries above (which would otherwise inject noise -- "深度
    # 研究" via "研究" alone pulls in every survey skill in the library).
    "深度研究": "deep research",
    "用户研究": "user research interview",
    "文献综述": "literature review survey",
    "竞品分析": "competitor competitive analysis",
    "市场调研": "market research survey",
    "技术选型": "technology comparison evaluation tradeoff",
    "数据可视化": "data visualization dashboard dataviz",
    "可视化大屏": "dashboard big-screen visualization",
    "性能优化": "performance optimization profiling",
    "架构设计": "architecture design",
    "接口文档": "api documentation",
    "单元测试": "unit test testing",
    "合同审查": "contract review legal",
    "财务报表": "financial statement report",
    "网页设计": "web design ui frontend",
    "图片生成": "image generation editing",
    "视频剪辑": "video editing",
    "简历优化": "resume cv",
}

CJK_RUN = re.compile(r"[一-鿿]+")
TOKEN = re.compile(r"[a-z0-9][a-z0-9+#.\-]*")


def norm_text(s: str) -> str:
    return (s or "").lower()


def cjk_ngrams(s: str) -> list[str]:
    """Bigrams over each CJK run, so Chinese text is indexable without a segmenter."""
    out: list[str] = []
    for run in CJK_RUN.findall(s):
        # Single characters carry too little signal to index on their own.
        if len(run) >= 2:
            out.extend(run[i:i + 2] for i in range(len(run) - 1))
    return out


def tokenize(s: str) -> list[str]:
    s = norm_text(s)
    return [t for t in TOKEN.findall(s) if len(t) > 1 or t.isdigit()] + cjk_ngrams(s)


def expand_query(q: str) -> tuple[list[str], list[str], list[str]]:
    """Split a query into (latin, cjk, alias).

    `latin` are the user's own alphanumeric tokens. `cjk` are bigrams of the
    Chinese left over after alias expansion — they can match Chinese skill
    descriptions, but a bigram of filler ("好看" out of "画个好看的") carries
    little signal, so it is down-weighted and never gates a match. `alias`
    holds the concepts pulled in by the zh->en table.
    """
    q_low = q.lower()
    extra: list[str] = []
    # longest-match alias expansion
    for zh, en in sorted(ZH_ALIASES.items(), key=lambda kv: -len(kv[0])):
        if zh in q_low:
            extra.extend(en.split())
            q_low = q_low.replace(zh, " ")
    latin = list(dict.fromkeys(t for t in TOKEN.findall(q_low) if len(t) > 1 or t.isdigit()))
    cjk = cjk_ngrams(q_low)
    alias = [t for t in dict.fromkeys(extra) if t not in latin]
    return latin, cjk, alias


class Searcher:
    def __init__(self, records: list[dict], categories: dict[str, dict]):
        self.records = records
        self.categories = categories
        self.df: Counter = Counter()
        self._prep()

    def _prep(self) -> None:
        for r in self.records:
            toks = set(self._fields(r))
            for t in toks:
                self.df[t] += 1
        self.n = max(len(self.records), 1)

    @staticmethod
    def _fields(r: dict) -> list[str]:
        return (
            tokenize(r["id"])
            + tokenize(r.get("name", ""))
            + [t for tg in r.get("tags", []) for t in tokenize(tg)]
            + tokenize(r.get("description", ""))
            + [t for t in tokenize(self_cat_text(r))]
        )

    def idf(self, term: str) -> float:
        return math.log(1 + self.n / (1 + self.df.get(term, 0)))

    def score(self, r: dict, latin: list[str], cjk: list[str], alias: list[str]) -> float:
        sid = norm_text(r["id"])
        sid_tok = set(tokenize(sid))
        sname = norm_text(r.get("name", ""))
        sname_tok = set(tokenize(sname))
        sdesc = norm_text(r.get("description", ""))
        stags = [norm_text(t) for t in r.get("tags", [])]
        # Both labels are scored so an English query for "compliance" or
        # "hardware" gets the same weak category-label prior a Chinese query
        # already had. Deliberately *not* in _fields(): those tokens would then
        # enter df, and the resulting IDF shift would reshuffle every ranking
        # the pinned tests depend on.
        scap = (norm_text(self_cat_text(r)) + " " + norm_text(r.get("category_zh", ""))
                + " " + norm_text(r.get("category_en", "")))

        # Given latin tokens of its own, a query is looked up literally and the
        # expansions only add context around it. Given none, the query was pure
        # Chinese and the expansions are the query itself.
        if latin:
            terms = ([(t, 1.0) for t in latin]
                     + [(t, self.CJK_W) for t in cjk]
                     + [(t, self.ALIAS_W) for t in alias])
        else:
            terms = [(t, 1.0) for t in alias] + [(t, self.CJK_W) for t in cjk]

        total = 0.0
        gained = 0.0
        latin_hits = 0
        latin_set = set(latin)
        for t, weight in terms:
            w = self.idf(t)
            got = 0.0
            if sid == t:
                got = 12.0
            elif t in sid_tok:
                got = 8.0
            elif t in sid:
                got = 5.0
            if t in stags:
                got = max(got, 6.0)
            if t in sname_tok:
                got = max(got, 4.0)
            if t in scap:
                got = max(got, 1.5)
            if t in sdesc:
                got = max(got, 1.5)
            if got:
                gained += weight
                if t in latin_set:
                    latin_hits += 1
                total += got * (1.0 + w) * weight

        # A query that named something concrete must match it, or an expanded
        # concept ends up answering a question the user never asked.
        if latin and not latin_hits:
            return 0.0
        span = sum(w for _, w in terms) or 1.0
        return total * (0.5 + 0.5 * gained / span)

    ALIAS_W = 0.45
    CJK_W = 0.6

    def search(self, query: str, limit: int = 8, cat: str | None = None,
               tag: str | None = None) -> list[tuple[float, dict]]:
        latin, cjk, alias = expand_query(query)
        # A token that occurs nowhere in the corpus is a typo or an unknown
        # product name; keeping it would zero out every record.
        latin = [t for t in latin if self.df.get(t, 0) > 0]
        pool = self.records
        if cat:
            pool = [r for r in pool if r.get("category") == cat]
        if tag:
            pool = [r for r in pool if tag.lower() in [t.lower() for t in r.get("tags", [])]]
        # No query at all: with a filter that is a browse request, without one
        # there is nothing to do.
        if not (latin or cjk or alias):
            return [(0.0, r) for r in pool[:limit]] if (cat or tag) else []
        scored = [(self.score(r, latin, cjk, alias), r) for r in pool]
        scored = [s for s in scored if s[0] > 0]
        scored.sort(key=lambda x: -x[0])
        return scored[:limit]


def self_cat_text(r: dict) -> str:
    return f'{r.get("category", "")} {r.get("evidence", "") if isinstance(r.get("evidence"), str) else " ".join(r.get("evidence", []) or [])}'


def load(path: str) -> tuple[list[dict], dict[str, dict]]:
    """Read the index and hang both category labels off every record.

    Labels are derived here from taxonomy.py rather than stored in the index:
    a copy in the JSON would be a copy that can go stale, and switching --lang
    would then mean rebuilding a multi-megabyte index.
    """
    records = json.loads(Path(path).read_text(encoding="utf-8"))
    for r in records:
        c = CAT_BY_ID.get(r.get("category", FALLBACK_ID), {})
        r["category_en"] = c.get("en", "")
        r["category_zh"] = c.get("zh", "")
    return records, CAT_BY_ID


def resolve_lang(flag: str, query: str) -> str:
    """`auto` answers in the language the question was asked in."""
    if flag != "auto":
        return flag
    return "zh" if CJK_RUN.search(query) else "en"


def main() -> int:
    ap = argparse.ArgumentParser(description="Search the skill library")
    ap.add_argument("query", nargs="*", help="omit when browsing with --cat/--tag")
    ap.add_argument("--index", default="output/skills_final.json")
    ap.add_argument("--limit", type=int, default=8)
    ap.add_argument("--cat", default=None, help="restrict to one category id")
    ap.add_argument("--tag", default=None, help="restrict to skills carrying this tag")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--show-path", action="store_true")
    ap.add_argument("--full", action="store_true", help="do not truncate descriptions")
    ap.add_argument("--lang", choices=("auto", "en", "zh"), default="auto",
                    help="language of the printed result labels (default: %(default)s)")
    a = ap.parse_args()

    query = " ".join(a.query)
    index_path = Path(a.index)
    if not index_path.is_absolute():
        index_path = ROOT / a.index
    if not index_path.exists():
        print(f"index not found: {index_path}", file=sys.stderr)
        print(f'run: "{sys.executable or "python3"}" "{Path(__file__).resolve()}" '
              f'--help   # then: {ROOT / "scripts" / "refresh.py"}', file=sys.stderr)
        return 2

    records, cats = load(str(index_path))
    s = Searcher(records, cats)
    results = s.search(query, a.limit, a.cat, a.tag)
    lang = resolve_lang(a.lang, query)

    if a.json:
        # Machine-facing output carries both labels regardless of --lang: the
        # consumer (an agent) decides what to show, and this keeps the shape
        # stable for anything already parsing it.
        print(json.dumps(
            [{"score": round(sc, 1), **{k: r.get(k) for k in
              ("id", "name", "category", "category_en", "category_zh", "tags",
               "description", "path", "confidence", "source_kind")}}
             for sc, r in results], ensure_ascii=False, indent=1))
        return 0

    if not results:
        print(f'no match for: {query}')
        print("hint: try a broader term, or browse a category with --cat")
        return 1

    what = f"query: {query}" if query.strip() else f"browse: --cat {a.cat or '-'} --tag {a.tag or '-'}"
    print(f"{what}   ({len(results)} of {len(records)} skills)\n")
    for sc, r in results:
        tags = " ".join(f"#{t}" for t in (r.get("tags") or [])[:6])
        # Browse results carry no score, so leave the column blank rather than
        # printing a wall of 0.0.
        print(f"{sc:6.1f}  {r['id']}" if sc else f"{'':6}  {r['id']}")
        cat_label = r.get("category_zh" if lang == "zh" else "category_en", "")
        print(f"        [{cat_label or '?'}/{r.get('category','?')}]  {tags}")
        d = r.get("description", "")
        if not a.full and len(d) > 200:
            d = d[:197] + "..."
        print(f"        {d}")
        if a.show_path:
            print(f"        {r.get('path','')}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
