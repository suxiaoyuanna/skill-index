"""Category taxonomy + controlled tag vocabulary for the skill library.

Two things live here:
  1. CATEGORIES / OTHER - 28 top-level buckets plus a catch-all, each with
                   id-prefix patterns (strong signal) and description keywords
                   (weaker signal) used for scoring.
  2. TECH_TAGS   - controlled vocabulary for tech/product tags, matched against
                   the skill id and description.

Each category carries its human labels in both English (`en`/`en_desc`) and
Chinese (`zh`/`zh_desc`). These are for *display only* -- `id_patterns` and
`keywords` are the classifier signal and stay language-neutral, which is why
the Chinese-description support in skillfind.py works with English output.

This list is a starting point, not an authority. If your library has domains it
does not cover, edit it -- see README "Make it yours".

Rule order matters: scoring is additive, but `weight` lets an id-prefix hit
outrank a passing keyword mention in a description.
"""
from __future__ import annotations

# --------------------------------------------------------------------------
# Categories
# --------------------------------------------------------------------------
# weight guide:   id_pattern hit = 10 (set via ID_W),  keyword hit = 1-3
ID_W = 10

CATEGORIES = [
    {
        "id": "agent-meta",
        "en": "Agent & Skill Meta",
        "zh": "Agent / 技能元工具",
        "en_desc": "Skill management, subagent orchestration, context and memory, "
                   "prompt engineering, MCP development",
        "zh_desc": "技能管理、子agent编排、上下文与记忆、提示词工程、MCP 开发等元层面工具",
        "id_patterns": [
            r"^skill[-_]", r"^agent[-_]", r"^agents[-_]?md", r"^subagent", r"^antigravity",
            r"^context[-_]", r"^memory[-_]", r"^prompt[-_]", r"^mcp[-_]", r"^claude[-_]",
            r"^manage-skills$", r"^find-skills$", r"^using-superpowers$", r"^superpowers",
            r"^autonomous-agent", r"^multi-agent", r"^parallel-agents", r"^dispatching-parallel",
            r"^orchestrat", r"^workflow-orchestration", r"^task-intelligence$", r"^tool-design$",
            r"^hierarchical-agent", r"^conversation-memory$", r"^save-context$",
        ],
        "keywords": [
            r"\bskill(s)? (library|writer|creator|audit|router|suggester|scanner|preflight)\b",
            r"\bsubagent", r"\borchestrat", r"agent team", r"\bmeta-skill", r"skill.md",
            r"context (window|management|compression|engineering)", r"prompt (engineering|optimiz|caching)",
            r"model context protocol", r"\bmcp server", r"agent memory", r"self-improv",
            r"behavioral mode", r"reasoning harness",
        ],
    },
    {
        "id": "cloud-infra",
        "en": "Cloud & Infrastructure",
        "zh": "云平台与基础设施",
        "en_desc": "AWS/Azure/GCP, Terraform, Kubernetes, Docker, serverless, message queues",
        "zh_desc": "AWS/Azure/GCP、Terraform、Kubernetes、Docker、Serverless、消息队列等",
        "id_patterns": [
            r"^azure[-_]", r"^aws[-_]", r"^gcp[-_]", r"^terraform", r"^k8s[-_]", r"^kubernetes",
            r"^helm[-_]", r"^docker", r"^cloud", r"^hybrid-cloud", r"^istio", r"^linkerd",
            r"^serverless", r"^aws-serverless", r"^neon[-_]", r"^supabase", r"^upstash",
            r"^convex$", r"^firebase$", r"^vercel", r"^cloudflare", r"^service-mesh",
            r"^multi-cloud", r"^devops", r"^conductor", r"^inngest", r"^trigger-dev",
            r"^dbos-", r"^gcp-cloud-run", r"^appdeploy$", r"^devcontainer", r"^azd-",
        ],
        "keywords": [
            r"\baws\b", r"\bazure\b", r"\bgcp\b", r"google cloud", r"\bterraform\b", r"\bkubernetes\b",
            r"\bk8s\b", r"\bhelm\b", r"\bdocker\b", r"\bserverless\b", r"cloud run",
            r"infrastructure as code", r"\bblob storage\b", r"\bcosmos\b", r"\beventhub",
            r"\bservice bus\b", r"\bfunctions\b", r"\bkey vault\b", r"\bapp configuration\b",
        ],
    },
    {
        "id": "devops-cicd",
        "en": "DevOps / CI-CD / Observability",
        "zh": "DevOps / CI-CD / 可观测",
        "en_desc": "Continuous integration, deployment pipelines, Git workflows, "
                   "monitoring and alerting, SRE, incident response",
        "zh_desc": "持续集成、部署流水线、Git 工作流、监控告警、SRE、事件响应",
        "id_patterns": [
            r"^ci[-_]?cd", r"^cicd", r"^git[-_]?(hub|lab|advanced|hooks|pr|workflow|pushing|guardrails)",
            r"^github", r"^gitlab", r"^circleci", r"^jenkins", r"^argocd", r"^gitops",
            r"^deploy", r"^deployment", r"^release", r"^changelog", r"^commit$", r"^create-pr$",
            r"^create-branch$", r"^pr-writer$", r"^iterate-pr$", r"^review$", r"^issues$",
            r"^observability", r"^monitoring", r"^prometheus", r"^grafana", r"^datadog",
            r"^sentry", r"^pagerduty", r"^slo[-_]", r"^incident", r"^postmortem", r"^on-call",
            r"^sre[-_]", r"^chaos[-_]", r"^production-scheduling", r"^runbook", r"^tech.*tracker",
            r"^openclaw", r"^smart-git", r"^using-git-worktrees", r"^finishing-a-development-branch",
            r"^resolving-merge-conflicts", r"^setup-pre-commit", r"^codebase-audit-pre-push",
        ],
        "keywords": [
            r"\bci/cd\b", r"continuous (integration|delivery|deployment)", r"\bpipeline\b.*deploy",
            r"\bgithub actions\b", r"\bgitlab ci\b", r"\bpre-commit\b", r"\bdeploy(ment|ed|ing)?\b",
            r"\brollback\b", r"\bcanary\b", r"\bblue-?green\b", r"\bmonitoring\b", r"\balerting\b",
            r"\bobservability\b", r"\bslo\b", r"\bsli\b", r"\bpostmortem\b", r"incident response",
            r"\bon-?call\b", r"site reliability", r"\bopentelemetry\b", r"\btracing\b",
        ],
    },
    {
        "id": "security",
        "en": "Security & Compliance",
        "zh": "安全与合规",
        "en_desc": "Penetration testing, vulnerability discovery, code security audit, "
                   "threat modeling, secrets management, privacy compliance",
        "zh_desc": "渗透测试、漏洞挖掘、代码安全审计、威胁建模、密钥管理、隐私合规",
        "id_patterns": [
            r"security", r"^pentest", r"^pentesting", r"^exploit", r"^vulnerab", r"^vuln",
            r"^metasploit", r"^burp", r"^sqlmap", r"^ffuf", r"^nmap", r"^shodan", r"^wireshark",
            r"^malware", r"^memory-forensics", r"^firmware-analyst$", r"^binary-analysis",
            r"^reverse-engineer", r"^anti-reversing", r"^red-team", r"^blue-?team", r"^threat",
            r"^attack-tree", r"^stride", r"^crypto", r"^solidity-security", r"^sast", r"^semgrep",
            r"^secrets-management", r"^mtls", r"^zeroize", r"^constant-time", r"^privilege-escalation",
            r"^linux-privilege", r"^windows-privilege", r"^active-directory-attacks", r"^idor",
            r"^xss", r"^file-path-traversal", r"^html-injection", r"^broken-authentication",
            r"^top-web-vulnerabilities", r"^ethical-hacking", r"^scanning-tools", r"^bug-bounty",
            r"gdpr", r"pci-compliance", r"^privacy-by-design", r"^fsi-compliance", r"^compliance",
            r"^secure-code", r"^security-", r"^zeroize-audit", r"^protect-mcp", r"^aci-", r"^aegisops",
        ],
        "keywords": [
            r"penetration test", r"\bpentest", r"vulnerabilit", r"exploit", r"\bCVE\b",
            r"threat model", r"attack (tree|surface|vector)", r"privilege escalation",
            r"security (audit|review|hardening|scan|policy)", r"vulnerability", r"\bOWASP\b",
            r"\bcryptograph", r"\bencryption\b", r"secret(s)? management", r"\bzero.?trust\b",
            r"\bGDPR\b", r"\bHIPAA\b", r"\bPCI.?DSS\b", r"\bSOC.?2\b", r"compliance",
            r"reverse engineer", r"\bmalware\b", r"forensic",
        ],
    },
    {
        "id": "testing-qa",
        "en": "Testing & QA",
        "zh": "测试与质量保障",
        "en_desc": "Unit testing, end-to-end testing, TDD, load testing, test frameworks and strategy",
        "zh_desc": "单元测试、端到端测试、TDD 流程、性能压测、测试框架与策略",
        "id_patterns": [
            r"^test", r"^tdd", r"^bats-", r"^e2e", r"^playwright", r"^cypress", r"^pytest",
            r"^jasmine", r"^jest", r"^vitest", r"^k6-", r"^load-testing", r"^qa$", r"^testing",
            r"^webapp-testing$", r"^android_ui_verification", r"^screen-reader-testing",
            r"^accessibility-compliance", r"^wcag", r"^a11y", r"^ui-a11y", r"^fixing-accessibility",
            r"^lambdatest", r"^awt-e2e", r"^acceptance-orchestrator", r"^verification-before",
            r"^verification", r"^dos-verify", r"^spec-to-code-compliance", r"^integrity-gates",
        ],
        "keywords": [
            r"\btest(s|ing|ed)?\b", r"\bTDD\b", r"\bBDD\b", r"unit test", r"integration test",
            r"end-to-end test", r"\be2e\b", r"test (suite|plan|coverage|case|fixture|double|mock)",
            r"\bmocking\b", r"load test", r"stress test", r"\bWCAG\b", r"screen reader",
            r"accessibility (audit|testing|compliance)", r"quality assurance", r"\bregression\b",
        ],
    },
    {
        "id": "debugging",
        "en": "Debugging & Troubleshooting",
        "zh": "调试与故障排查",
        "en_desc": "Error diagnosis, root cause analysis, fault isolation, profiling, debugging workflows",
        "zh_desc": "错误诊断、根因分析、故障定位、性能剖析与调试工作流",
        "id_patterns": [
            r"^debug", r"^error[-_]", r"^diagnos", r"^troubleshoot", r"^bug-", r"^find-bugs",
            r"^systematic-debugging", r"^phase-gated-debugging", r"^postmortem", r"^crash",
            r"^gdb-cli$", r"^dwarf-expert", r"^mock-hunter", r"^sharp-edges", r"^glitch",
        ],
        "keywords": [
            r"\bdebug(ging|ger)?\b", r"root cause", r"troubleshoot", r"error (analysis|trace|handling)",
            r"stack trace", r"\bcrash\b", r"\bexception\b", r"fault (injection|isolation)",
            r"diagnos(e|is|tic)", r"performance profil", r"\bprofiler\b",
        ],
    },
    {
        "id": "architecture",
        "en": "Architecture & Design Patterns",
        "zh": "架构与设计模式",
        "en_desc": "System architecture, domain-driven design, microservices, event-driven design, "
                   "architecture decision records, refactoring plans",
        "zh_desc": "系统架构、领域驱动设计、微服务、事件驱动、架构决策记录、重构规划",
        "id_patterns": [
            r"^architect", r"^architecture", r"^c4-", r"^ddd-", r"^domain-", r"^microservices",
            r"^monorepo", r"^event-sourcing", r"^cqrs", r"^saga-", r"^clean-code", r"^codebase-design",
            r"^software-architecture", r"^senior-architect", r"^legacy-modernizer", r"^code-archaeology",
            r"^refactor", r"^request-refactor", r"^orchestrate-batch-refactor", r"^blueprint$",
            r"^spec-miner", r"^wiki-architect", r"^design-md$", r"^plan-writing", r"^writing-plans",
            r"^concise-planning", r"^executing-plans", r"^project-development", r"^analysis-",
        ],
        "keywords": [
            r"(system|software|solution) architecture", r"design pattern", r"\bDDD\b",
            r"domain-driven", r"\bmicroservice", r"\bmonolith", r"architecture decision record",
            r"\bADR\b", r"event.?driven", r"\bCQRS\b", r"\bSOLID\b", r"refactor",
            r"technical design", r"migration (plan|strategy)", r"trade.?off",
        ],
    },
    {
        "id": "code-quality",
        "en": "Code Review & Quality",
        "zh": "代码审查与质量",
        "en_desc": "Code review, deduplication and simplification, technical debt, "
                   "static analysis, coding standards",
        "zh_desc": "代码评审、去重简化、技术债清理、静态检查、编码规范",
        "id_patterns": [
            r"^code-review", r"^review", r"^simplify", r"^complexity", r"^code-simplifier",
            r"^clean-code$", r"^lint", r"^shellcheck", r"^brooks-lint", r"^sharp-coder",
            r"^codebase-cleanup", r"^vibe-code", r"^vibers", r"^unslop$", r"^not-a-vibe",
            r"^tech-debt", r"^dependency-", r"^deps-audit", r"^differential-review",
            r"^comprehensive-review", r"^receiving-code-review", r"^requesting-code-review",
            r"^fix-review", r"^git-pr-review", r"^gh-review-requests", r"^address-github-comments",
        ],
        "keywords": [
            r"code review", r"code quality", r"clean code", r"best practice", r"lint",
            r"technical debt", r"duplicat", r"dead code", r"simplif", r"refactor",
            r"coding standard", r"convention", r"static analysis", r"dependency (audit|upgrade|management)",
        ],
    },
    {
        "id": "languages",
        "en": "Language Specialization",
        "zh": "编程语言专精",
        "en_desc": "Deep practice in one language or runtime: Python, Go, Rust, Java, C#, C++, "
                   "TypeScript, shell, and others",
        "zh_desc": "具体语言/运行时的深度实践：Python/Go/Rust/Java/C#/C++/TS 等",
        "id_patterns": [
            r"^python[-_]?(pro|patterns|dev|packaging|env|testing|performance)?$", r"^(-|)pro$",
            r"^golang", r"^go-", r"^rust", r"^java-", r"^csharp", r"^c-pro$", r"^cpp-pro",
            r"^dotnet", r"^php-pro", r"^ruby-pro", r"^rails", r"^scala-pro", r"^elixir-pro",
            r"^haskell-pro", r"^julia-pro", r"^kotlin", r"^swift-", r"^typescript", r"^javascript",
            r"^nodejs", r"^deno", r"^bun-development", r"^modern-javascript", r"^async-python",
            r"^fp-", r"^bcrypt", r"^linux-shell-scripting", r"^bash", r"^posix-shell", r"^powershell",
            r"^os-scripting", r"^jq$", r"^busybox", r"^systems-programming-rust", r"^cpp-pro",
        ],
        "keywords": [
            r"\bpython\b", r"\bgolang\b", r"\brust\b", r"\bjava\b", r"\bc#\b", r"\bc\+\+\b",
            r"\btypescript\b", r"\bjavascript\b", r"\bkotlin\b", r"\bswift\b", r"\bphp\b",
            r"\bruby\b", r"\bscala\b", r"\belixir\b", r"idiomatic", r"language (feature|idiom)",
            r"standard library", r"async (await|runtime)", r"coroutine",
        ],
    },
    {
        "id": "frontend",
        "en": "Frontend & Web Frameworks",
        "zh": "前端与 Web 框架",
        "en_desc": "React/Vue/Angular/Svelte, Next.js, styling systems, state management, "
                   "component libraries",
        "zh_desc": "React/Vue/Angular/Svelte、Next.js、样式系统、状态管理、组件库",
        "id_patterns": [
            r"^react", r"^vue", r"^angular", r"^svelte", r"^nextjs", r"^next-", r"^nuxt",
            r"^astro$", r"^remix", r"^solid-?js", r"^tailwind", r"^css", r"^scss", r"^sass",
            r"^shadcn", r"^radix-ui", r"^magic-ui", r"^chakra", r"^mui", r"^styled",
            r"^frontend", r"^senior-frontend", r"^ui-component$", r"^ui-page$", r"^baseline-ui",
            r"^iconsax", r"^zustand", r"^redux", r"^tanstack", r"^trpc", r"^graphql$",
            r"^trpc-fullstack", r"^hono$", r"^vite", r"^webpack", r"^turborepo", r"^nx-",
            r"^progressive-web-app", r"^web-artifacts", r"^frontend-", r"^web-design",
            r"^web-performance", r"^pagespeed", r"^3d-web", r"^threejs", r"^spline", r"^animejs",
            r"^scroll-experience", r"^magic-animator", r"^shader-programming", r"^webgl",
        ],
        "keywords": [
            r"\breact\b", r"\bvue\b", r"\bangular\b", r"\bsvelte", r"\bnext\.?js\b", r"\bnuxt\b",
            r"\btailwind\b", r"\bcss\b", r"\bhtml\b", r"\bdom\b", r"\bfrontend\b", r"web app",
            r"component (library|pattern)", r"state management", r"\bSSR\b", r"hydration",
            r"\bresponsive\b", r"\b3d\b.*web", r"\bWebGL\b", r"\bshader\b",
        ],
    },
    {
        "id": "backend-api",
        "en": "Backend & APIs",
        "zh": "后端与 API",
        "en_desc": "FastAPI/Django/Spring/Laravel, REST/GraphQL/gRPC, authentication and "
                   "authorization, messaging",
        "zh_desc": "FastAPI/Django/Spring/Laravel、REST/GraphQL/gRPC、认证授权、消息系统",
        "id_patterns": [
            r"^fastapi", r"^django", r"^flask", r"^spring", r"^laravel", r"^nestjs", r"^express",
            r"^rails-", r"^backend", r"^api-", r"^graphql-", r"^grpc-", r"^rest", r"^openapi",
            r"^auth-", r"^clerk", r"^oauth", r"^jwt", r"^websocket", r"^bullmq", r"^celery",
            r"^email-systems", r"^payment", r"^stripe", r"^paypal", r"^plaid", r"^twilio",
            r"^fullstack", r"^full-stack", r"^dotnet-backend", r"^nodejs-backend",
            r"^python-fastapi", r"^microservices-patterns", r"^service-", r"^server-management",
        ],
        "keywords": [
            r"\bREST\b", r"\bAPI\b", r"\bGraphQL\b", r"\bgRPC\b", r"\bRPC\b", r"endpoint",
            r"backend", r"web (server|service|framework)", r"authentication", r"authorization",
            r"\bOAuth\b", r"\bJWT\b", r"rate limit", r"message queue", r"\bwebhook",
            r"request (handling|validation)", r"\bORM\b",
        ],
    },
    {
        "id": "mobile",
        "en": "Mobile & Desktop Apps",
        "zh": "移动端开发",
        "en_desc": "iOS/SwiftUI, Android/Compose, Flutter, React Native, Expo, desktop shells",
        "zh_desc": "iOS/SwiftUI、Android/Compose、Flutter、React Native、Expo",
        "id_patterns": [
            r"^ios-", r"^swift", r"^swiftui", r"^android", r"^kotlin-coroutines", r"^flutter",
            r"^react-native", r"^expo", r"^mobile-", r"^hig-", r"^building-native-ui",
            r"^upgrading-expo", r"^ios-developer", r"^macos-", r"^avalonia", r"^robius",
            r"^electron", r"^tauri", r"^makepad", r"^desktop",
        ],
        "keywords": [
            r"\biOS\b", r"\bAndroid\b", r"swiftui", r"jetpack compose", r"\bflutter\b",
            r"react native", r"\bexpo\b", r"mobile app", r"human interface guidelines",
            r"app store", r"desktop app", r"\btauri\b", r"\belectron\b", r"mobile (ui|design|security)",
        ],
    },
    {
        "id": "build-tooling",
        "en": "Build Tools & Packaging",
        "zh": "构建工具与包管理",
        "en_desc": "Build systems, bundlers, dependency management, monorepo tooling, "
                   "project scaffolding",
        "zh_desc": "构建系统、打包器、依赖管理、monorepo 工具链、项目脚手架",
        "id_patterns": [
            r"^bazel", r"^webpack", r"^vite", r"^rollup", r"^esbuild", r"^turborepo", r"^nx-",
            r"^lerna", r"^pnpm", r"^yarn", r"^npm", r"^uv-package", r"^mise-configurator",
            r"^cmake", r"^maven", r"^gradle", r"^cargo", r"^platformio", r"^monorepo",
            r"^package-manager", r"^dependency-upgrade", r"^python-packaging", r"^init-project",
            r"^setup-pre-commit", r"^migrate-to-shoehorn", r"^scaffold", r"^project-template",
            r"^new-rails-project$", r"^app-builder", r"^create-", r"^starter",
        ],
        "keywords": [
            r"\bbazel\b", r"\bwebpack\b", r"\bvite\b", r"\brollup\b", r"\besbuild\b",
            r"build (system|tool|optimization|performance|cache)", r"bundler", r"\bmonorepo\b",
            r"package manager", r"dependency (management|resolution|upgrade|injection)",
            r"project (scaffold|template|bootstrap|setup)", r"toolchain setup",
            r"lockfile", r"transitive dependenc",
        ],
    },
    {
        "id": "thinking-decision",
        "en": "Thinking Frameworks & Decisions",
        "zh": "思维框架与决策",
        "en_desc": "Brainstorming, critical questioning, multi-perspective trade-offs, "
                   "design review, requirement clarification",
        "zh_desc": "头脑风暴、批判性提问、多视角权衡、方案评审、需求澄清等思维方法",
        "id_patterns": [
            r"^brainstorm", r"^grill", r"^devils-advocate", r"^multi-perspective",
            r"^decision-navigator", r"^idea-", r"^anti-sycophancy",
            r"^ask-questions-if-underspecified", r"^explain-like-socrates", r"^council",
            r"^first-principles", r"^mental-model", r"^critique", r"^objection",
            r"^socratic", r"^constraint", r"^assumption", r"^concept-validation",
            r"^pre-submission", r"^trade-?off",
        ],
        "keywords": [
            r"brainstorm", r"\bgrill\b", r"devil'?s advocate", r"critical thinking",
            r"mental model", r"first principles", r"decision (framework|making|navigator)",
            r"multi-perspective", r"trade.?off analysis", r"stress-test", r"challenge assumptions",
            r"clarify (requirements|intent)", r"interview the user", r"structured reasoning",
            r"cognitive bias", r"socratic",
        ],
    },
    {
        "id": "database",
        "en": "Databases & Storage",
        "zh": "数据库与存储",
        "en_desc": "SQL/NoSQL, Postgres, query tuning, migrations, vector stores, caching",
        "zh_desc": "SQL/NoSQL、Postgres、优化调优、迁移、向量库、缓存",
        "id_patterns": [
            r"^postgres", r"^mysql", r"^sqlite", r"^sql-", r"^mongodb", r"^nosql", r"^redis",
            r"^prisma", r"^drizzle", r"^database", r"^db-", r"^sqlalchemy", r"^clickhouse",
            r"^snowflake", r"^vector-", r"^neon-postgres", r"^using-neon", r"^supabase-automation",
            r"^claimable-postgres", r"^data-table", r"^migration", r"^dbos", r"^query-",
        ],
        "keywords": [
            r"\bSQL\b", r"\bpostgres", r"\bmysql\b", r"\bmongo", r"\bredis\b", r"\bsqlite\b",
            r"database (design|schema|migration|optimiz|admin|architect)", r"\bindex(es|ing)?\b.*query",
            r"\bN\+1\b", r"query (optimization|plan)", r"\bORM\b", r"vector (database|index|search)",
            r"connection pool", r"transaction",
        ],
    },
    {
        "id": "ai-ml",
        "en": "AI & Machine Learning",
        "zh": "AI / 机器学习",
        "en_desc": "LLM applications, RAG, model training and fine-tuning, agent frameworks, "
                   "computer vision / NLP, evaluation",
        "zh_desc": "LLM 应用、RAG、模型训练与微调、Agent 框架、CV/NLP、评估",
        "id_patterns": [
            r"^rag-", r"^llm-", r"^langchain", r"^langgraph", r"^llamaindex", r"^pydantic-ai",
            r"^crewai", r"^autogen", r"^hugging-?face", r"^hf-", r"^ml-", r"^machine-learning",
            r"^ai-", r"^openai", r"^anthropic", r"^gemini-", r"^claude-api", r"^fal-", r"^comfyui",
            r"^stability-ai", r"^replicate", r"^vector-database-engineer", r"^embedding",
            r"^fine-tuning", r"^llmops", r"^mlops", r"^synthetic-data", r"^scikit-learn",
            r"^pytorch", r"^tensorflow", r"^transformers-js", r"^computer-vision", r"^opencv",
            r"^recsys", r"^recommend", r"^evaluation$", r"^advanced-evaluation", r"^llm-evaluation",
            r"^agent-evaluation", r"^ai-engineer", r"^ml-engineer", r"^data-scientist",
            r"^ai-analyzer", r"^ai-native-cli", r"^ai-product", r"^ai-wrapper", r"^ai-seo",
            r"^local-llm", r"^hosted-agents", r"^voice-agents", r"^pipecat", r"^vapi",
        ],
        "keywords": [
            r"\bLLM\b", r"\bRAG\b", r"retrieval.augmented", r"\bGPT\b", r"language model",
            r"fine.?tun", r"embedding", r"vector (store|search|index)", r"prompt (engineering|template)",
            r"machine learning", r"deep learning", r"neural network", r"\bmodel (training|inference)\b",
            r"\bdataset\b", r"inference", r"computer vision", r"\bNLP\b", r"\bCV\b",
            r"generative ai", r"text.to.(image|video|speech)", r"\bagentic\b",
        ],
    },
    {
        "id": "data-eng",
        "en": "Data Engineering & Analysis",
        "zh": "数据工程与分析",
        "en_desc": "Data pipelines, ETL, Spark/Airflow/dbt, BI dashboards, statistics, data quality",
        "zh_desc": "数据管道、ETL、Spark/Airflow/dbt、BI 看板、统计分析、数据质量",
        "id_patterns": [
            r"^data-", r"^dataviz$", r"^pandas", r"^polars$", r"^numpy", r"^spark", r"^airflow",
            r"^dbt-", r"^etl", r"^analytics-", r"^kpi-", r"^dashboard", r"^matplotlib", r"^plotly",
            r"^seaborn", r"^statsmodels", r"^networkx", r"^sympy", r"^biopython", r"^astropy",
            r"^scanpy", r"^tabular", r"^xlsx$", r"^data-processing", r"^data-quality",
            r"^data-storytelling", r"^data-structure", r"^quant-analyst", r"^backtesting",
            r"^options-flow", r"^risk-metrics", r"^financial", r"^monte-carlo", r"^yield-",
            r"^alpha-vantage", r"^churn-", r"^cohort", r"^segmentation",
        ],
        "keywords": [
            r"data (pipeline|engineering|analysis|quality|warehouse|lake|model)", r"\bETL\b",
            r"\bELT\b", r"\bairflow\b", r"\bspark\b", r"\bdbt\b", r"dataframe",
            r"\bpandas\b", r"visualiz", r"chart", r"dashboard", r"\bKPI\b", r"statistic",
            r"time series", r"forecast", r"regression", r"backtest", r"portfolio",
        ],
    },
    {
        "id": "docs-writing",
        "en": "Docs & Writing",
        "zh": "文档与写作",
        "en_desc": "Technical docs, READMEs, academic writing, LaTeX, Office documents, "
                   "translation and proofreading",
        "zh_desc": "技术文档、README、论文写作、LaTeX、Office 文档、翻译校对",
        "id_patterns": [
            r"^doc", r"^readme$", r"^wiki-", r"^writing-", r"^latex", r"^beamer", r"^quarto",
            r"^academic-paper", r"^papers-skill", r"^research-writing", r"^scientific-writing",
            r"^citation", r"^bib-", r"^proofread", r"^copy-editing", r"^professional-proofreader",
            r"^office-", r"^pptx", r"^docx", r"^xlsx-official", r"^pdf", r"^split-pdf",
            r"^pdf-conversion", r"^doc2math", r"^documentation", r"^api-documentation",
            r"^code-documentation", r"^reference-builder", r"^unslop$", r"^humanize",
            r"^beautiful-prose", r"^avoid-ai-writing", r"^blog-writing", r"^copywriting",
            r"^content-creator", r"^technical-writing", r"^docs-architect", r"^notebooklm",
            r"^audio-transcriber", r"^app-store-changelog", r"^internal-comms", r"^changelog-automation",
        ],
        "keywords": [
            r"documentation", r"\bREADME\b", r"technical writing", r"\bLaTeX\b", r"\bBibTeX\b",
            r"academic (paper|writing)", r"manuscript", r"proofread", r"editing", r"copyedit",
            r"\bWord\b", r"\bPowerPoint\b", r"\bExcel\b", r"\bPDF\b.*(extract|form|merge|split)",
            r"\bdocx\b", r"\bpptx\b", r"\bxlsx\b", r"\bmarkdown\b", r"changelog", r"release notes",
        ],
    },
    {
        "id": "research",
        "en": "Research & Information Retrieval",
        "zh": "研究与信息检索",
        "en_desc": "Deep research, literature search, competitive analysis, web search, "
                   "data collection",
        "zh_desc": "深度调研、文献检索、竞品分析、网络搜索、数据采集",
        "id_patterns": [
            r"^deep-research", r"^research", r"^literature", r"^search-", r"^efficient-web-research",
            r"^exa-search", r"^tavily", r"^firecrawl", r"^web-scraper", r"^scrap", r"^crawl",
            r"^apify-", r"^hasdata", r"^not-human-search", r"^last30days", r"^daily-news",
            r"^news-", r"^arxiv", r"^pubmed", r"^uniprot", r"^semantic-scholar", r"^bioinformatics",
            r"^patent", r"^competitive-", r"^competitor-", r"^market-", r"^market-sizing",
            r"^startup-analyst", r"^industry-", r"^trend", r"^spec-miner", r"^datasheets$",
            r"^digikey$", r"^mouser$", r"^lcsc$", r"^find-skills$", r"^audit-paper",
        ],
        "keywords": [
            r"research", r"literature (review|search)", r"citation", r"survey",
            r"competitive (analysis|landscape|intelligence)", r"market (research|analysis|sizing)",
            r"\bscrap(e|ing)\b", r"crawl", r"web search", r"information retrieval",
            r"data collection", r"fact.?check", r"source (verification|credibility)",
            r"\barXiv\b", r"\bPubMed\b", r"bibliograph",
        ],
    },
    {
        "id": "design-ui",
        "en": "Design & UI/UX",
        "zh": "设计与 UI/UX",
        "en_desc": "Visual design, interaction design, design systems, Figma, brand guidelines, "
                   "information architecture",
        "zh_desc": "视觉设计、交互设计、设计系统、Figma、品牌规范、信息架构",
        "id_patterns": [
            r"^ui-", r"^ux-", r"^design-", r"^figma", r"^canvas-design", r"^theme-factory",
            r"^brand-", r"^stitch-", r"^design-taste", r"^visual-", r"^frontend-design",
            r"^high-end-visual", r"^minimalist-ui", r"^industrial-brutalist", r"^gpt-taste",
            r"^baseline-ui", r"^ui-visual-validator", r"^accessibility-audit", r"^accesslint",
            r"^fixing-metadata", r"^kpi-dashboard-design", r"^chart", r"^color", r"^typography",
            r"^icon", r"^svg", r"^favicon", r"^article-illustrations", r"^mockup", r"^wireframe",
            r"^design-system", r"^ui-tokens", r"^mobile-design", r"^product-design",
        ],
        "keywords": [
            r"\bUI\b", r"\bUX\b", r"user experience", r"user interface", r"design system",
            r"\bFigma\b", r"wireframe", r"mockup", r"prototyp", r"visual design",
            r"typography", r"color (palette|scheme)", r"layout", r"brand", r"icon",
            r"interaction design", r"usability", r"information architecture", r"design (tokens|language)",
        ],
    },
    {
        "id": "content-media",
        "en": "Content & Media Generation",
        "zh": "内容与媒体生成",
        "en_desc": "Image/video/audio generation, editing, podcasts, social copy, slide decks",
        "zh_desc": "图像/视频/音频生成、剪辑、播客、社媒文案、幻灯片美化",
        "id_patterns": [
            r"^image-", r"^imagen", r"^ai-studio-image", r"^unsplash", r"^video", r"^youtube",
            r"^podcast", r"^audio", r"^voice", r"^tts", r"^music", r"^remotion", r"^sora",
            r"^nanobanana", r"^2slides", r"^python-pptx", r"^frontend-slides", r"^insights-deck",
            r"^project-deck", r"^slides", r"^screenshot", r"^screen-recording", r"^reveal",
            r"^social-", r"^x-article", r"^linkedin-content", r"^xiaohongshu", r"^instagram",
            r"^tiktok", r"^wechat-official", r"^subtitle", r"^caption", r"^transcrib",
            r"^ingest-youtube", r"^youtube-summarizer", r"^video-content-extractor", r"^videodb",
            r"^seek-and-analyze-video", r"^photo", r"^photopea", r"^gif", r"^banner",
        ],
        "keywords": [
            r"image (generation|edit|upscal|processing)", r"video (generation|edit|processing|content)",
            r"audio", r"podcast", r"text.to.speech", r"speech.to.text", r"transcri",
            r"slide (deck|generation)", r"screenshot", r"social media (content|post)",
            r"\bthumbnail\b", r"\bGIF\b", r"\bmeme\b", r"render", r"animation",
        ],
    },
    {
        "id": "marketing-growth",
        "en": "Marketing & Growth",
        "zh": "营销与增长",
        "en_desc": "SEO/AEO, ad campaigns, conversion rate optimization, email marketing, "
                   "pricing and growth strategy",
        "zh_desc": "SEO/AEO、广告投放、转化率优化、邮件营销、定价与增长策略",
        "id_patterns": [
            r"^seo", r"^aeo", r"^geo-", r"^cro$", r"^.*-cro$", r"^conversion", r"^landing-page",
            r"^copywriting", r"^email-sequence", r"^cold-email", r"^newsletter", r"^ads$",
            r"^paid-ads", r"^ad-creative", r"^social-proof", r"^growth-", r"^launch-strategy",
            r"^pricing", r"^price-", r"^churn-prevention", r"^referral", r"^lead-magnet",
            r"^monetization", r"^marketing", r"^content-strategy", r"^content-marketer",
            r"^brand-perception", r"^positioning", r"^customer-psychographic", r"^audience",
            r"^onboarding-", r"^signup-flow", r"^popup-", r"^paywall", r"^form-cro",
            r"^psycholog", r"^scarcity", r"^loss-aversion", r"^headline-", r"^subject-line",
            r"^awareness-stage", r"^social-orchestrator", r"^viral-", r"^programmatic-seo",
            r"^schema-markup", r"^local-legal-seo", r"^app-store-optimization", r"^aso",
            r"^clarvia", r"^indexing-issue", r"^site-architecture", r"^keyword-", r"^link-",
            r"^free-tool-strategy", r"^revops", r"^sales-enablement", r"^sales-automator",
        ],
        "keywords": [
            r"\bSEO\b", r"search engine optimi", r"\bAEO\b", r"keyword", r"backlink",
            r"conversion rate", r"\bCRO\b", r"landing page", r"copywrit", r"marketing",
            r"advertis", r"\bads?\b", r"campaign", r"email (marketing|sequence|campaign)",
            r"lead (gen|magnet|nurtur)", r"funnel", r"growth (hack|strategy)", r"pricing",
            r"brand (voice|positioning|guidelines)", r"analytics.*traffic", r"funnel",
            r"customer (acquisition|retention|journey)", r"\bCTR\b", r"\bROI\b",
        ],
    },
    {
        "id": "business-product",
        "en": "Business / Product / Operations",
        "zh": "商业 / 产品 / 运营",
        "en_desc": "Product management, business models, startup analysis, financial modeling, "
                   "project management, CRM, legal",
        "zh_desc": "产品管理、商业模式、创业分析、财务建模、项目管理、CRM、法务",
        "id_patterns": [
            r"^product-manager", r"^product-", r"^pm-", r"^business-analyst", r"^business-",
            r"^startup", r"^saas-", r"^micro-saas", r"^monetization", r"^pricing-strategy",
            r"^osterwalder", r"^lean-", r"^jobs-to-be-done", r"^team-", r"^hr-", r"^hiring",
            r"^interview-coach", r"^resume", r"^cv-generator", r"^jobs-",
            r"^project-management", r"^task-management", r"^track-management$", r"^agile",
            r"^scrum", r"^kanban", r"^estimation", r"^progressive-estimation", r"^roadmap",
            r"^stakeholder", r"^risk-manager", r"^legal-",
            r"^employment-contract", r"^customs-trade", r"^compliance-checker", r"^itil",
            r"^it-manager", r"^event-staffing", r"^quality-nonconformance", r"^inventory-",
            r"^logistics-", r"^supply-chain", r"^returns-", r"^carrier-", r"^procurement",
            r"^energy-procurement", r"^production-scheduling", r"^billing", r"^finops",
            r"^blockchain", r"^defi-", r"^nft-", r"^web3", r"^payment-integration", r"^fintech",
            r"^persona",
        ],
        "keywords": [
            r"product (management|manager|strategy|roadmap|requirement)", r"business (model|case|analysis)",
            r"\bPRD\b", r"stakeholder", r"user story", r"backlog", r"sprint", r"agile", r"scrum",
            r"financial (model|projection)", r"revenue", r"pricing (strategy|model)",
            r"\bCRM\b", r"customer (relationship|support|success)", r"\bSOP\b", r"process (design|improvement)",
            r"contract", r"legal (advice|review)", r"regulatory", r"hiring", r"onboarding",
        ],
    },
    {
        "id": "office-automation",
        "en": "Office & SaaS Automation",
        "zh": "办公与 SaaS 自动化",
        "en_desc": "Google Workspace, Slack/Notion/Linear/Jira, CRM, email and calendar "
                   "platform automation",
        "zh_desc": "Google Workspace、Slack/Notion/Linear/Jira、CRM、邮件日历等平台自动化",
        "id_patterns": [
            r"^google-(sheets|docs|drive|slides|calendar|analytics)", r"^googlesheets",
            r"^excel", r"^airtable", r"^notion", r"^slack", r"^discord", r"^telegram", r"^whatsapp",
            r"^twilio", r"^sendgrid", r"^mailchimp", r"^klaviyo", r"^convertkit", r"^postmark",
            r"^brevo", r"^freshdesk", r"^zendesk", r"^intercom", r"^helpdesk", r"^support",
            r"^jira", r"^linear", r"^asana", r"^trello", r"^monday", r"^clickup", r"^wrike",
            r"^basecamp", r"^coda", r"^calendly", r"^cal-com", r"^zoom", r"^outlook", r"^gmail",
            r"^one-drive", r"^dropbox", r"^box-", r"^docusign", r"^miro", r"^confluence",
            r"^salesforce", r"^hubspot", r"^pipedrive", r"^zoho", r"^bamboohr", r"^workday",
            r"^shopify", r"^woocommerce", r"^odoo-", r"^moodle", r"^zapier", r"^make-automation",
            r"^n8n", r"^activecampaign", r"^segment", r"^mixpanel", r"^amplitude", r"^posthog",
            r"^stripe-automation", r"^square-", r"^paypal", r"^quickbooks", r"^xero",
            r"^bitbucket", r"^render", r"^vercel-automation", r"^netlify", r"^supabase-automation",
            r"^sentry-automation", r"^datadog-automation", r"^pagerduty-automation", r"^instagram-automation",
            r"^twitter-automation", r"^linkedin-automation", r"^reddit-automation", r"^youtube-automation",
            r"^facebook", r"^tiktok-automation", r"^microsoft-teams", r"^atlassian", r"^todoist",
            r"^office-productivity", r"^internal-comms", r"^daily$", r"^diary$", r"^session-log",
            r"^file-organizer", r"^obsidian", r"^logseq", r"^tana", r"^resume-",
            r"^billing-automation", r"^agentmail$", r"^agentphone$",
        ],
        "keywords": [
            r"\bautomation\b", r"workflow automation", r"\bAPI integration\b",
            r"google (sheets|docs|drive|calendar|slides)", r"\bslack\b", r"\bnotion\b",
            r"\bjira\b", r"\blinear\b", r"\basana\b", r"\btrello\b", r"\bcrm\b",
            r"\bwebhook\b.*trigger", r"\bno-?code\b", r"\bzapier\b", r"\bmake\.com\b", r"\bn8n\b",
            r"productivity", r"note.taking", r"\bworkspace\b", r"inbox", r"calendar",
        ],
    },
    {
        "id": "hardware-eda",
        "en": "Hardware / Embedded / EDA",
        "zh": "硬件 / 嵌入式 / EDA",
        "en_desc": "PCB design, KiCad/Altium, FPGA/Verilog, MCU/RTOS, firmware and "
                   "component selection",
        "zh_desc": "PCB 设计、KiCad/Altium、FPGA/Verilog、MCU/RTOS、固件与元器件选型",
        "id_patterns": [
            r"^kicad", r"^pcb", r"^eda-", r"^jlcpcb", r"^pcbway", r"^gerber", r"^schematic",
            r"^fpga$", r"^verilog", r"^vhdl", r"^vivado", r"^quartus", r"^platformio",
            r"^embedded", r"^firmware", r"^stm32", r"^esp32", r"^arduino", r"^raspberry",
            r"^arm-cortex", r"^riscv", r"^rtos", r"^freertos", r"^mcu", r"^microcontroller",
            r"^circuit", r"^analog", r"^electronics", r"^logic-",
            r"^product-render", r"^ltspice", r"^spice$", r"^bom$", r"^element14", r"^adafruit",
        ],
        "keywords": [
            r"\bPCB\b", r"\bKiCad\b", r"altium", r"schematic", r"\bgerber\b", r"\bDRC\b", r"\bERC\b",
            r"\bBOM\b", r"\bFPGA\b", r"verilog", r"\bVHDL\b", r"microcontroller", r"\bMCU\b",
            r"embedded (system|firmware|linux)", r"\bRTOS\b", r"\bSTM32\b", r"\bESP32\b",
            r"\bI2C\b", r"\bSPI\b", r"\bUART\b", r"datasheet", r"footprint", r"netlist",
            r"power (supply|budget|tree)", r"signal integrity",
        ],
    },
    {
        "id": "health",
        "en": "Health & Lifestyle",
        "zh": "健康与生活",
        "en_desc": "Health data analysis, lab result interpretation, nutrition and exercise, "
                   "mental health and sleep",
        "zh_desc": "健康数据分析、体检解读、营养运动、心理与睡眠等个人健康工具",
        "id_patterns": [
            r"^health-", r"^medical", r"^clinical", r"^nutrition",
            r"^fitness", r"^sleep-", r"^mental-health", r"^tcm-", r"^emergency-card",
            r"^family-health", r"^oral-health", r"^skin-health", r"^sexual-health",
            r"^travel-health", r"^occupational-health", r"^rehabilitation",
            r"^weightloss", r"^food-database",
        ],
        "keywords": [
            r"health", r"medical", r"clinical", r"patient", r"diagnosis", r"symptom",
            r"nutrition", r"diet", r"fitness", r"exercise", r"sleep", r"mental health",
            r"wellness", r"BMI", r"blood", r"medication",
        ],
    },
    {
        "id": "gamedev",
        "en": "Game Development",
        "zh": "游戏开发",
        "en_desc": "Unity, Unreal, Godot, game mechanics and ECS architecture",
        "zh_desc": "Unity、Unreal、Godot、游戏机制与 ECS 架构",
        "id_patterns": [
            r"^unity", r"^unreal", r"^godot", r"^game-", r"^minecraft", r"^bevy", r"^phaser",
            r"^roblox", r"^gamedev",
        ],
        "keywords": [
            r"\bgame (development|engine|design|loop)\b", r"\bunity\b", r"unreal engine",
            r"\bgodot\b", r"\bECS\b", r"gameplay", r"level design", r"sprite", r"physics engine",
        ],
    },
    {
        "id": "science-domain",
        "en": "Science & Specialized Domains",
        "zh": "科研与专业领域",
        "en_desc": "Scientific computing, bioinformatics, chemistry and materials, simulation, "
                   "vertical industry tools",
        "zh_desc": "科学计算、生物信息、化学材料、仿真、专业垂直行业工具",
        "id_patterns": [
            r"^qiskit", r"^cirq", r"^quantum", r"^biopython", r"^scanpy", r"^astropy",
            r"^sympy", r"^matlab", r"^scientific", r"^simulation", r"^cfd", r"^fem",
            r"^openfoam", r"^chemistry", r"^materials", r"^geo-", r"^earth-", r"^climate",
            r"^bioinformatic", r"^genomic", r"^protein", r"^lab-",
        ],
        "keywords": [
            r"scientific computing", r"simulation", r"numerical", r"\bquantum\b",
            r"bioinformatic", r"genomic", r"molecular", r"chemistry", r"physics",
            r"geospatial", r"climate", r"\bFEA\b", r"\bCFD\b",
        ],
    },
]

CATEGORY_IDS = [c["id"] for c in CATEGORIES]

# The catch-all bucket. It is not in CATEGORIES because it is never *scored* --
# the classifier only reaches it by falling through everything else. Defined
# once here so report.py, skillfind.py and make_batches.py cannot drift apart
# on its label.
FALLBACK_ID = "other"

OTHER = {
    "id": FALLBACK_ID,
    "en": "Other / Unclassified",
    "zh": "其他",
    "en_desc": "Skills that match none of the categories above",
    "zh_desc": "不属于以上任何类别的杂项技能",
    "id_patterns": [],
    "keywords": [],
}

ALL_CATEGORIES = CATEGORIES + [OTHER]
CAT_BY_ID = {c["id"]: c for c in ALL_CATEGORIES}


def label(cat: dict, lang: str = "en") -> str:
    """Display name for a category dict."""
    return cat["en"] if lang == "en" else cat["zh"]


def desc(cat: dict, lang: str = "en") -> str:
    """One-line summary for a category dict."""
    return cat["en_desc"] if lang == "en" else cat["zh_desc"]

# --------------------------------------------------------------------------
# Controlled tag vocabulary:  tag -> regex matched against id + description
# --------------------------------------------------------------------------
TECH_TAGS = {
    # languages
    "python": r"\bpython\b|^python-|^fastapi|^django|^flask|^pandas|^polars\b",
    "javascript": r"\bjavascript\b|^javascript|^nodejs|^modern-javascript",
    "typescript": r"\btypescript\b|\.tsx?\b|^typescript-|^ts-",
    "go": r"\bgolang\b|\bgo (language|module|routine|interface)|\bgo1\.|^go-|^golang",
    "rust": r"\brust\b|^rust-|^systems-programming-rust",
    "java": r"\bjava\b|^java-",
    "csharp": r"\bc#\b|\bc-?sharp\b|\bdotnet\b|\basp\.net\b|\.net (framework|core|maui)|\bvb\.net\b",
    "cpp": r"\bc\+\+\b|^cpp-|^c-pro$",
    "php": r"\bphp\b|^php-|^laravel",
    "ruby": r"\bruby\b|^ruby-|^rails",
    "kotlin": r"\bkotlin\b|^kotlin-",
    "swift": r"\bswift\b|^swift",
    "sql": r"\bsql\b|^sql-|^postgres|^mysql",
    "bash": r"\bbash\b|^bash|shell script|^posix-shell",
    "powershell": r"\bpowershell\b|^powershell",
    # frontend
    "react": r"\breact\b|^react-|^nextjs|^next-",
    "vue": r"\bvue\b|^vue-",
    "angular": r"\bangular\b|^angular-",
    "svelte": r"\bsvelte\b|^svelte|^sveltekit",
    "nextjs": r"\bnext\.?js\b|^nextjs|^next-",
    "tailwind": r"\btailwind\b|^tailwind",
    "css": r"\bcss\b|^css|^scss|^sass",
    "html": r"\bhtml\b|^html-",
    "threejs": r"\bthree\.?js\b|^threejs",
    "webgl": r"\bwebgl\b|shader|^shader-",
    # backend / api
    "fastapi": r"\bfastapi\b|^fastapi",
    "django": r"\bdjango\b|^django",
    "spring": r"\bspring\b|^spring-",
    "nestjs": r"\bnest\.?js\b|^nestjs",
    "graphql": r"\bgraphql\b|^graphql",
    "grpc": r"\bgrpc\b|^grpc",
    "rest": r"\brest(ful)?\s*(api|endpoint|service)|\brest-?api\b|^rest-|^api-|^openapi",
    "websocket": r"\bwebsocket\b|^websocket",
    "auth": r"authentication|authorization|\boauth\b|\bjwt\b|^auth-|^clerk",
    "payment": r"\bpayment|stripe|paypal|billing|checkout",
    # mobile
    "ios": r"\bios\b|swiftui|^swiftui|^ios-",
    "android": r"\bandroid\b|jetpack compose|^android",
    "flutter": r"\bflutter\b",
    "react-native": r"react native|^react-native|^expo",
    # infra
    "aws": r"\baws\b|^aws-",
    "azure": r"\bazure\b|^azure-",
    "gcp": r"\bgcp\b|google cloud|^gcp-",
    "kubernetes": r"\bkubernetes\b|\bk8s\b|^k8s-|^kubestellar",
    "docker": r"\bdocker\b|containeri[sz]ed|container (image|registry|orchestration)|^docker",
    "terraform": r"\bterraform\b|^terraform",
    "serverless": r"serverless|lambda|cloud function|^azure-functions",
    "cicd": r"\bci/cd\b|continuous (integration|deployment)|github actions|gitlab ci|^circleci|^jenkins",
    "git": r"\bgit\b|^git-|^github|^gitlab|version control",
    "monitoring": r"monitoring|observability|\bslo\b|prometheus|grafana|datadog|opentelemetry",
    "incident": r"incident|on-?call|postmortem|outage|runbook",
    # data
    "postgres": r"\bpostgres",
    "mysql": r"\bmysql\b",
    "sqlite": r"\bsqlite\b",
    "mongodb": r"\bmongo",
    "redis": r"\bredis\b",
    "vector-db": r"vector (database|store|index|search)|pgvector|pinecone|weaviate|qdrant|chroma",
    "etl": r"\betl\b|\belt\b|data pipeline|^airflow|^dbt-|^spark",
    "analytics": r"\banalytics\b|dashboard|\bbi\b|visualiz|reporting",
    # ai
    "llm": r"\bllm\b|large language model|gpt|claude|language model",
    "rag": r"\brag\b|retrieval.augmented",
    "prompt-eng": r"prompt (engineering|optimization|template|library)|^prompt-|^enhance-prompt",
    "agents": r"\bagent(s|ic)\b|^agent-|^multi-agent|^subagent",
    "mcp": r"model context protocol|\bmcp\b",
    "fine-tuning": r"fine.?tun|training (a )?model|lora|peft|rlhf",
    "computer-vision": r"computer vision|\bopencv\b|image (recognition|classif|detect)",
    "nlp": r"\bnlp\b|natural language|text (classif|analys)|tokeniz",
    "huggingface": r"hugging.?face|^hf-|transformers",
    "langchain": r"langchain|langgraph|llamaindex",
    # security
    "pentest": r"penetration test|\bpentest|ethical hack|bug bounty|red team",
    "vulnerability": r"vulnerabilit|exploit|\bcve\b|\bowasp\b",
    "cryptography": r"cryptograph|\bencrypt|cipher|\bhash\b|\bmtls\b|\btls\b",
    "forensics": r"forensic|malware|reverse engineer|memory dump",
    "compliance": r"compliance|\bgdpr\b|\bhipaa\b|\bpci\b|\bsoc2?\b|\biso 27001\b|audit trail",
    "secrets": r"secret(s)? (management|rotation)|key vault|vault",
    # testing
    "testing": r"(?<![-\w])tests?\b|\btesting\b|^test-|^tdd",
    "tdd": r"\btdd\b|test.driven",
    "e2e": r"end.to.end|\be2e\b|playwright|cypress|selenium|^playwright",
    "performance-testing": r"load test|stress test|\bk6\b|benchmark",
    "accessibility": r"\bwcag\b|accessibility|a11y|screen reader|aria",
    # design
    "ui-design": r"\bui\b|user interface|design system|component library",
    "ux": r"\bux\b|user experience|usability|user research",
    "figma": r"\bfigma\b",
    "design-system": r"design system|design token|style guide|component library",
    "branding": r"\bbrand\b|logo|visual identity",
    "iconography": r"\bicon(s)?\b|svg|favicon|illustration",
    # content
    "image-gen": r"image (generation|edit|upscal)|text.to.image|flux|stable diffusion|midjourney|dall-?e",
    "video": r"\bvideo\b|\bvideo (edit|gen|process|render)|motion graphic|^remotion|^threejs-animation",
    "audio": r"\baudio\b|speech|voice|\btts\b|\bstt\b|music",
    "podcast": r"podcast",
    "slides": r"slide|deck|presentation|powerpoint|^pptx",
    "writing": r"writing|copywrit|prose|narrative|blog|article",
    "translation": r"translat|localiz|i18n|l10n",
    # marketing
    "seo": r"\bseo\b|search engine optimi|^seo-|\baeo\b|\bserp\b",
    "ads": r"advertis|\bads\b|ppc|campaign|^ad-creative",
    "cro": r"conversion rate|\bcro\b|a/b test|^ab-test|funnel optimi",
    "email-marketing": r"email (marketing|sequence|campaign)|newsletter|drip|^cold-email",
    "social-media": r"social media|twitter|linkedin|instagram|tiktok|xiaohongshu|facebook",
    "analytics-marketing": r"\bga4\b|google analytics|attribution|\bctr\b|traffic",
    "pricing": r"pricing|monetiz|revenue model",
    # hardware
    "kicad": r"\bkicad\b",
    "pcb": r"\bpcb\b|\bgerber|\bfootprint|\bpcb layout\b|board layout|schematic capture",
    "fpga": r"\bfpga\b|verilog|\bvhdl\b|vivado|quartus",
    "embedded": r"embedded (system|firmware|device|linux|software|engineer)|\bmicrocontroller\b|\bmcu\b|\brtos\b|\bfirmware\b|\bstm32\b|\besp32\b|\barduino\b|\bbare-?metal\b",
    "electronics": r"circuit|schematic|\bi2c\b|\bspi\b|\buart\b|analog|datasheet",
    # workflow / meta
    "office": r"\bword (document|doc)\b|ms ?word|microsoft word|powerpoint|\bexcel\b|^docx|^pptx|^xlsx|^office-",
    "pdf": r"\bpdf\b",
    "latex": r"\blatex\b|\bbibtex\b|^bib-|^beamer",
    "spreadsheet": r"spreadsheet|^xlsx|google sheets|^excel",
    "productivity": r"productivity|note.taking|^obsidian|^notion|task manage|todoist",
    "automation": r"\bautomation\b|\bzapier\b|\bn8n\b|workflow automation|^make-automation",
    "no-code": r"no-?code|low-?code|^lovable",
    "research": r"\bresearch\b|literature|survey|^deep-research",
    "scraping": r"\bscrap(e|ing)\b|crawl|^firecrawl|^apify",
    "documentation": r"documentation|\breadme\b|^docs?-|technical writ",
    "refactoring": r"refactor|technical debt|clean.?up|moderniz|migration",
    "code-review": r"code review|pull request|\bpr\b review|^review$|^code-review",
    "debugging": r"\bdebug|\btroubleshoot|root cause|error (analysis|trace)",
    "architecture": r"architecture|design pattern|\bddd\b|microservice|\badr\b",
    "planning": r"\bplan(ning)?\b|roadmap|estimation|specification|\bspec\b",
    "documentation-gen": r"generate (docs|documentation)|doc generator",
    "product-management": r"product manage|\bprd\b|roadmap|user story|backlog",
    "data-viz": r"data visualiz|chart|plot|dashboard|^matplotlib|^plotly|^dataviz",
    "excel": r"\bexcel\b|spreadsheet|xlsx",
    "i18n": r"i18n|l10n|localiz|translat",
}

# Tags that are too generic to be useful as a filter
TAG_STOPWORDS = {"ai", "tool", "tools", "code", "file", "data", "app", "web"}
