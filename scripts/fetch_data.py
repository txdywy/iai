#!/usr/bin/env python3
"""
AI Nexus - Multi-source intelligence aggregator.
Fetches deep intelligence from: HN Algolia, GitHub, OpenRouter, Reddit, npm, PyPI.
Uses only Python stdlib (no pip dependencies).
"""

import json
import urllib.request
import urllib.parse
import datetime
import os
import time
import re

UA = 'AINexus/2.0'
TIMEOUT = 15

# ---------------------------------------------------------------------------
# Shared HTTP helpers
# ---------------------------------------------------------------------------

def _get_json(url, headers=None):
    """Fetch JSON from a URL. Returns parsed dict/list or None on failure."""
    hdrs = {'User-Agent': UA, 'Accept': 'application/json'}
    if headers:
        hdrs.update(headers)
    req = urllib.request.Request(url, headers=hdrs)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        print(f"  [WARN] GET {url[:100]}... -> {e}")
        return None


def _get_text(url):
    """Fetch text from a URL. Returns str or None on failure."""
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return resp.read().decode('utf-8')
    except Exception as e:
        print(f"  [WARN] GET {url[:100]}... -> {e}")
        return None


# ---------------------------------------------------------------------------
# Source 1: Hacker News Algolia — deep per-item intelligence
# ---------------------------------------------------------------------------

def fetch_hn_intel(query, limit=3):
    """Return up to `limit` recent HN stories for a query, sorted by date."""
    encoded = urllib.parse.quote(query)
    url = f"https://hn.algolia.com/api/v1/search_by_date?query={encoded}&tags=story&hitsPerPage={limit}"
    data = _get_json(url)
    if not data:
        return []
    results = []
    for h in data.get('hits', []):
        link = h.get('url', '')
        if not link:
            link = f"https://news.ycombinator.com/item?id={h.get('objectID')}"
        results.append({
            "title": h.get('title', ''),
            "url": link,
            "date": h.get('created_at', '')[:10],
            "points": h.get('points', 0),
            "comments": h.get('num_comments', 0),
            "source": "Hacker News"
        })
    return results


def fetch_hn_trending(limit=10):
    """Fetch top AI stories from HN sorted by relevance/points."""
    url = f"https://hn.algolia.com/api/v1/search?query=AI%20OR%20LLM%20OR%20GPT%20OR%20Claude%20OR%20Gemini%20OR%20Agent&tags=story&hitsPerPage={limit}"
    data = _get_json(url)
    if not data:
        return []
    results = []
    for h in data.get('hits', []):
        link = h.get('url', '')
        if not link:
            link = f"https://news.ycombinator.com/item?id={h.get('objectID')}"
        results.append({
            "title": h.get('title', ''),
            "badge": f"HN ({h.get('points', 0)} pts)",
            "description": f"by {h.get('author', '?')} | {h.get('num_comments', 0)} comments",
            "meta": ["Hacker News", "资讯"],
            "link": link,
            "points": h.get('points', 0),
            "comments": h.get('num_comments', 0)
        })
    return sorted(results, key=lambda x: x.get('points', 0), reverse=True)


# ---------------------------------------------------------------------------
# Source 2: GitHub API — releases, stars, trending
# ---------------------------------------------------------------------------

def _gh_headers():
    """GitHub API headers. Uses GITHUB_TOKEN if available for higher rate limits."""
    hdrs = {'User-Agent': UA, 'Accept': 'application/vnd.github+json'}
    token = os.environ.get('GITHUB_TOKEN', '')
    if token:
        hdrs['Authorization'] = f'Bearer {token}'
    return hdrs


def fetch_github_release(owner, repo):
    """Get latest release for a GitHub repo."""
    url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
    data = _get_json(url, _gh_headers())
    if not data:
        return None
    return {
        "version": data.get('tag_name', '').lstrip('vV'),
        "date": data.get('published_at', '')[:10],
        "name": data.get('name', ''),
        "url": data.get('html_url', ''),
        "notes": (data.get('body', '') or '')[:500]
    }


def fetch_github_repo_info(owner, repo):
    """Get repo stats: stars, forks, description, language."""
    url = f"https://api.github.com/repos/{owner}/{repo}"
    data = _get_json(url, _gh_headers())
    if not data:
        return None
    return {
        "stars": data.get('stargazers_count', 0),
        "forks": data.get('forks_count', 0),
        "open_issues": data.get('open_issues_count', 0),
        "language": data.get('language', ''),
        "description": data.get('description', ''),
        "updated_at": data.get('updated_at', '')[:10],
        "topics": data.get('topics', [])[:6]
    }


def fetch_github_trending_repos(query, limit=5):
    """Search GitHub for popular recently-updated repos matching a query."""
    encoded = urllib.parse.quote(query)
    url = f"https://api.github.com/search/repositories?q={encoded}+pushed:>2026-04-01&sort=stars&order=desc&per_page={limit}"
    data = _get_json(url, _gh_headers())
    if not data:
        return []
    results = []
    for r in data.get('items', [])[:limit]:
        results.append({
            "name": r.get('full_name', ''),
            "description": r.get('description', '') or '',
            "stars": r.get('stargazers_count', 0),
            "language": r.get('language', ''),
            "url": r.get('html_url', ''),
            "updated": r.get('pushed_at', '')[:10]
        })
    return results


# ---------------------------------------------------------------------------
# Source 3: OpenRouter — model catalog with rich details
# ---------------------------------------------------------------------------

def fetch_openrouter_data():
    """Fetch free + cheap models from OpenRouter with pricing and capabilities."""
    data = _get_json("https://openrouter.ai/api/v1/models")
    if not data:
        return _openrouter_fallback()

    models = data.get('data', [])
    free_models = []
    cheap_models = []
    for m in models:
        pricing = m.get('pricing', {})
        p_prompt = float(pricing.get('prompt', 1) or 1)
        p_completion = float(pricing.get('completion', 1) or 1)
        if p_prompt == 0 and p_completion == 0:
            free_models.append(m)
        elif p_prompt < 0.000003 and p_completion < 0.000015:
            cheap_models.append(m)

    # Sort free by context length, cheap by context length
    free_models.sort(key=lambda x: x.get('context_length', 0), reverse=True)
    cheap_models.sort(key=lambda x: x.get('context_length', 0), reverse=True)

    result = []
    for m in free_models[:5]:
        result.append(_format_openrouter_model(m, is_free=True))
    for m in cheap_models[:3]:
        result.append(_format_openrouter_model(m, is_free=False))

    return result if result else _openrouter_fallback()


def _format_openrouter_model(m, is_free=True):
    pricing = m.get('pricing', {})
    ctx = m.get('context_length', 0)
    ctx_display = f"{ctx // 1000}K" if ctx >= 1000 else str(ctx)
    modality = m.get('architecture', {})
    modality_str = modality.get('modality', 'text') if modality else 'text'

    return {
        "title": m.get('name', m.get('id', 'Unknown')),
        "badge": "免费" if is_free else "超低价",
        "description": (m.get('description', '') or '')[:200] or f"上下文 {ctx_display} tokens。",
        "meta": [
            f"上下文 {ctx_display}",
            modality_str,
            "免费" if is_free else f"${float(pricing.get('prompt', 0)):.2f}/M tok"
        ],
        "link": f"https://openrouter.ai/models/{m.get('id')}",
        "model_id": m.get('id', ''),
        "context_length": ctx,
        "pricing": {
            "prompt": pricing.get('prompt', '?'),
            "completion": pricing.get('completion', '?')
        }
    }


def _openrouter_fallback():
    return [
        {"title": "Llama 3 8B (Free)", "badge": "免费", "description": "OpenRouter 上最受欢迎的免费开源模型。", "meta": ["Meta", "免费"], "link": "https://openrouter.ai"},
        {"title": "Mistral Nemo", "badge": "免费新星", "description": "性能强悍的 12B 开源模型。", "meta": ["12B", "免费"], "link": "https://openrouter.ai"},
    ]


# ---------------------------------------------------------------------------
# Source 4: Reddit (public JSON) — community discussions
# ---------------------------------------------------------------------------

def fetch_reddit_posts(subreddit, query, limit=3):
    """Search a subreddit for relevant posts via public JSON endpoint."""
    encoded = urllib.parse.quote(query)
    url = f"https://www.reddit.com/r/{subreddit}/search.json?q={encoded}&sort=new&t=week&restrict_sr=on&limit={limit}"
    data = _get_json(url)
    if not data:
        return []
    results = []
    for child in data.get('data', {}).get('children', []):
        post = child.get('data', {})
        results.append({
            "title": post.get('title', ''),
            "url": f"https://reddit.com{post.get('permalink', '')}",
            "score": post.get('score', 0),
            "comments": post.get('num_comments', 0),
            "date": datetime.datetime.fromtimestamp(post.get('created_utc', 0), tz=datetime.timezone.utc).strftime('%Y-%m-%d') if post.get('created_utc') else '',
            "source": f"r/{subreddit}"
        })
    return results


# ---------------------------------------------------------------------------
# Source 5: npm registry — package versions for JS tools
# ---------------------------------------------------------------------------

def fetch_npm_package(package_name):
    """Get npm package metadata: latest version, description, weekly downloads."""
    url = f"https://registry.npmjs.org/{urllib.parse.quote(package_name, safe='')}"
    data = _get_json(url)
    if not data:
        return None
    dist_tags = data.get('dist-tags', {})
    latest_ver = dist_tags.get('latest', '')
    time_data = data.get('time', {})
    publish_date = time_data.get(latest_ver, '')[:10] if time_data else ''

    return {
        "version": latest_ver,
        "date": publish_date,
        "description": data.get('description', ''),
        "homepage": data.get('homepage', ''),
        "repository": (data.get('repository', {}) or {}).get('url', ''),
        "license": data.get('license', ''),
        "keywords": data.get('keywords', [])[:5]
    }


def fetch_npm_downloads(package_name):
    """Get weekly download count for an npm package."""
    url = f"https://api.npmjs.org/downloads/point/last-week/{urllib.parse.quote(package_name, safe='')}"
    data = _get_json(url)
    if not data:
        return 0
    return data.get('downloads', 0)


# ---------------------------------------------------------------------------
# Source 6: PyPI — package versions for Python tools
# ---------------------------------------------------------------------------

def fetch_pypi_package(package_name):
    """Get PyPI package metadata: latest version, description."""
    url = f"https://pypi.org/pypi/{package_name}/json"
    data = _get_json(url)
    if not data:
        return None
    info = data.get('info', {})
    releases = data.get('releases', {})
    latest_ver = info.get('version', '')
    return {
        "version": latest_ver,
        "description": info.get('summary', ''),
        "homepage": info.get('home_page', '') or info.get('project_url', ''),
        "license": info.get('license', ''),
        "keywords": (info.get('keywords', '') or '').split(',')[:5]
    }


# ---------------------------------------------------------------------------
# Source 7: arXiv — latest AI papers (via Atom feed)
# ---------------------------------------------------------------------------

def fetch_arxiv_papers(query, limit=5):
    """Fetch recent arXiv papers matching a query."""
    encoded = urllib.parse.quote(query)
    url = f"http://export.arxiv.org/api/query?search_query=all:{encoded}&sortBy=submittedDate&sortOrder=descending&max_results={limit}"
    text = _get_text(url)
    if not text:
        return []
    results = []
    # Simple XML parsing with regex (avoid xml.etree for minimal deps)
    entries = re.findall(r'<entry>(.*?)</entry>', text, re.DOTALL)
    for entry in entries:
        title_m = re.search(r'<title>(.*?)</title>', entry, re.DOTALL)
        summary_m = re.search(r'<summary>(.*?)</summary>', entry, re.DOTALL)
        published_m = re.search(r'<published>(.*?)</published>', entry)
        link_m = re.search(r'<id>(.*?)</id>', entry)
        title = title_m.group(1).strip().replace('\n', ' ') if title_m else ''
        summary = summary_m.group(1).strip().replace('\n', ' ')[:300] if summary_m else ''
        pub_date = published_m.group(1)[:10] if published_m else ''
        link = link_m.group(1).strip() if link_m else ''
        results.append({
            "title": title,
            "summary": summary,
            "date": pub_date,
            "url": link,
            "source": "arXiv"
        })
    return results


# ---------------------------------------------------------------------------
# Enrichment: combine multiple sources per tracked item
# ---------------------------------------------------------------------------

def enrich_item(item, gh_owner=None, gh_repo=None, npm_name=None, pypi_name=None, reddit_subs=None, search_query=None):
    """
    Deeply enrich a tracked item with data from multiple sources.
    Mutates `item` in place and returns it.
    """
    updates = []

    # 1. HN intelligence (multiple stories)
    if search_query:
        hn_stories = fetch_hn_intel(search_query, limit=3)
        for s in hn_stories:
            updates.append({
                "title": s["title"],
                "url": s["url"],
                "date": s["date"],
                "source": "Hacker News",
                "engagement": f"{s['points']} pts, {s['comments']} comments"
            })
        time.sleep(0.1)

    # 2. GitHub release + repo info
    if gh_owner and gh_repo:
        release = fetch_github_release(gh_owner, gh_repo)
        if release:
            item["latest_version"] = release["version"]
            item["version_date"] = release["date"]
            item["release_url"] = release["url"]
            item["release_notes"] = release["notes"][:300]
            updates.append({
                "title": f"Release {release['version']}: {release['name']}",
                "url": release["url"],
                "date": release["date"],
                "source": "GitHub Release"
            })
        time.sleep(0.15)

        repo = fetch_github_repo_info(gh_owner, gh_repo)
        if repo:
            item["github"] = {
                "stars": repo["stars"],
                "forks": repo["forks"],
                "language": repo["language"],
                "updated": repo["updated_at"],
                "topics": repo["topics"]
            }
        time.sleep(0.15)

    # 3. npm package info
    if npm_name:
        npm = fetch_npm_package(npm_name)
        if npm:
            item.setdefault("latest_version", npm["version"])
            item.setdefault("version_date", npm["date"])
            downloads = fetch_npm_downloads(npm_name)
            if downloads:
                item["npm_downloads_weekly"] = downloads
            updates.append({
                "title": f"npm v{npm['version']}" + (f" — {npm['description']}" if npm.get('description') else ''),
                "url": npm.get("homepage", f"https://www.npmjs.com/package/{npm_name}"),
                "date": npm["date"],
                "source": "npm"
            })
        time.sleep(0.1)

    # 4. PyPI package info
    if pypi_name:
        pypi = fetch_pypi_package(pypi_name)
        if pypi:
            item.setdefault("latest_version", pypi["version"])
            updates.append({
                "title": f"PyPI v{pypi['version']}" + (f" — {pypi['description']}" if pypi.get('description') else ''),
                "url": pypi.get("homepage", f"https://pypi.org/project/{pypi_name}/"),
                "date": "",
                "source": "PyPI"
            })
        time.sleep(0.1)

    # 5. Reddit discussions
    if reddit_subs:
        for sub in reddit_subs[:2]:
            posts = fetch_reddit_posts(sub, item.get("_reddit_query", item["title"]), limit=2)
            for p in posts:
                updates.append({
                    "title": p["title"],
                    "url": p["url"],
                    "date": p["date"],
                    "source": p["source"],
                    "engagement": f"{p['score']} pts, {p['comments']} comments"
                })
            time.sleep(0.15)

    # Sort updates by date (newest first) and attach
    updates.sort(key=lambda x: x.get('date', ''), reverse=True)
    item["recent_updates"] = updates[:6]

    # Clean internal fields
    item.pop('_reddit_query', None)
    return item


# ---------------------------------------------------------------------------
# Tracked item definitions — the intelligence targets
# ---------------------------------------------------------------------------

MODELS = [
    {
        "title": "OpenAI GPT-5.5",
        "badge": "2026 旗舰",
        "description": "OpenAI 最新旗舰，大幅减少幻觉，代码工程与复杂 Agentic 任务能力颠覆性提升。原生多模态，支持自主 Agent 工作流。",
        "meta": ["多模态", "自主 Agent", "闭源", "OpenAI"],
        "link": "https://openai.com",
        "search_query": '"GPT-5" OR "OpenAI" (announce OR release OR launch)',
        "gh_owner": "openai",
        "gh_repo": "openai-python",
        "_reddit_query": "GPT-5 OR OpenAI GPT",
        "reddit_subs": ["MachineLearning", "artificial"],
        "features": ["原生多模态输入/输出", "自主 Agent 循环", "幻觉率大幅下降", "代码工程 SOTA"],
        "pricing_hint": "~$0.03/1K input tokens"
    },
    {
        "title": "Claude Opus 4.7",
        "badge": "逻辑之王",
        "description": "Anthropic 最新超大杯，原生任务预算控制，高阶规划与代码能力登顶。1M token 上下文。",
        "meta": ["精准控制", "1M 上下文", "闭源", "Anthropic"],
        "link": "https://anthropic.com",
        "search_query": '"Claude Opus" OR "Claude 4" (announce OR release OR benchmark)',
        "gh_owner": "anthropics",
        "gh_repo": "anthropic-sdk-python",
        "_reddit_query": "Claude Opus",
        "reddit_subs": ["ClaudeAI", "MachineLearning"],
        "features": ["任务预算控制", "1M token 上下文", "高阶规划", "代码能力登顶", "扩展思维"],
        "pricing_hint": "~$0.015/1K input tokens"
    },
    {
        "title": "Google Gemini 2.5 Pro",
        "badge": "原生多模态",
        "description": "Google DeepMind 出品，多项推理 Benchmark 霸榜，原生多模态与超长上下文统治级表现。",
        "meta": ["超长上下文", "Google 生态", "闭源", "DeepMind"],
        "link": "https://deepmind.google",
        "search_query": '"Gemini 2.5" OR "Gemini Pro" (release OR benchmark OR announce)',
        "gh_owner": "googleapis",
        "gh_repo": "python-genai",
        "_reddit_query": "Gemini 2.5 Pro",
        "reddit_subs": ["GoogleGemini", "MachineLearning"],
        "features": ["原生多模态", "超长上下文", "推理 Benchmark 霸榜", "Google 生态集成"],
        "pricing_hint": "~$0.00125/1K input tokens"
    },
    {
        "title": "DeepSeek V3/R1",
        "badge": "开源之光",
        "description": "开源巨兽，极致高效 MoE 架构，API 成本极具竞争力，推理能力比肩闭源旗舰。",
        "meta": ["开源/开放权重", "MoE 架构", "高性价比"],
        "link": "https://deepseek.com",
        "search_query": '"DeepSeek" (release OR V3 OR R1 OR benchmark)',
        "gh_owner": "deepseek-ai",
        "gh_repo": "DeepSeek-V3",
        "_reddit_query": "DeepSeek",
        "reddit_subs": ["LocalLLaMA", "MachineLearning"],
        "features": ["MoE 高效架构", "开源权重", "API 极低价", "推理能力顶级"],
        "pricing_hint": "~$0.27/M input tokens"
    },
    {
        "title": "Kimi K2 (月之暗面)",
        "badge": "长文本领军",
        "description": "月之暗面出品，支持超长上下文，Agent Swarm 技术进行复杂任务拆解。",
        "meta": ["Agent Swarm", "超长文本", "Moonshot AI"],
        "link": "https://kimi.moonshot.cn",
        "search_query": '"Kimi" OR "Moonshot AI" (release OR update OR agent)',
        "_reddit_query": "Kimi Moonshot",
        "reddit_subs": ["LocalLLaMA", "artificial"],
        "features": ["超长上下文窗口", "Agent Swarm 任务拆解", "中文能力顶级", "多步推理"],
        "pricing_hint": "国内定价"
    },
    {
        "title": "GLM-4 / ChatGLM",
        "badge": "智谱AI",
        "description": "智谱 AI 出品，MoE 架构，纯国产算力训练，代码与逻辑推理后训练大幅增强。",
        "meta": ["国产算力", "开源", "MoE"],
        "link": "https://zhipuai.cn",
        "search_query": '"GLM-4" OR "ChatGLM" OR "Zhipu AI" (release OR update)',
        "gh_owner": "THUDM",
        "gh_repo": "GLM-4",
        "_reddit_query": "GLM-4 ChatGLM",
        "reddit_subs": ["LocalLLaMA"],
        "features": ["MoE 架构", "国产算力", "开源可商用", "代码推理增强"],
        "pricing_hint": "国内定价"
    },
    {
        "title": "Llama 4 (Meta)",
        "badge": "开源霸主",
        "description": "Meta 最新开源大模型系列，Scout/Maverick 多尺寸覆盖，原生多模态。",
        "meta": ["开源", "多模态", "Meta"],
        "link": "https://llama.meta.com",
        "search_query": '"Llama 4" OR "Meta AI" (release OR launch OR benchmark)',
        "gh_owner": "meta-llama",
        "gh_repo": "llama-models",
        "_reddit_query": "Llama 4",
        "reddit_subs": ["LocalLLaMA", "MachineLearning"],
        "features": ["完全开源", "多尺寸", "原生多模态", "社区生态庞大"],
        "pricing_hint": "免费开源"
    },
    {
        "title": "Qwen 3 (阿里云)",
        "badge": "通义千问",
        "description": "阿里云通义千问最新系列，MoE 与 Dense 多型号覆盖，工具调用与代码能力领先。",
        "meta": ["开源", "MoE", "阿里云"],
        "link": "https://qwenlm.github.io",
        "search_query": '"Qwen 3" OR "Qwen3" OR "通义千问" (release OR update)',
        "gh_owner": "QwenLM",
        "gh_repo": "Qwen2.5",
        "_reddit_query": "Qwen 3",
        "reddit_subs": ["LocalLLaMA", "artificial"],
        "features": ["MoE + Dense 多型号", "工具调用领先", "代码生成强", "开源可商用"],
        "pricing_hint": "免费开源"
    }
]

TOOLS = [
    {
        "title": "Claude Code",
        "badge": "AI 编程旗舰",
        "description": "Anthropic 官方命令行 AI 编程助手，深度集成 Claude 模型，支持自主编码、测试、调试全流程。",
        "meta": ["CLI", "代码生成", "Agent", "Anthropic"],
        "link": "https://docs.anthropic.com/en/docs/claude-code",
        "search_query": '"Claude Code" (release OR update OR feature)',
        "npm_name": "@anthropic-ai/claude-code",
        "gh_owner": "anthropics",
        "gh_repo": "claude-code",
        "_reddit_query": "Claude Code",
        "reddit_subs": ["ClaudeAI", "programming"],
        "features": ["自主编码全流程", "MCP 协议支持", "Git 深度集成", "扩展思维模式"]
    },
    {
        "title": "Cursor",
        "badge": "AI IDE 先驱",
        "description": "基于 VS Code 的 AI-native IDE，集成多模型支持，Tab 补全与 Agent 模式并行。",
        "meta": ["IDE", "多模型", "Tab 补全"],
        "link": "https://cursor.com",
        "search_query": '"Cursor" AI (IDE OR editor OR update)',
        "_reddit_query": "Cursor AI IDE",
        "reddit_subs": ["cursor", "programming"],
        "features": ["AI-native 代码编辑", "多模型切换", "Tab 智能补全", "Agent 模式", "代码库索引"]
    },
    {
        "title": "Windsurf (Codeium)",
        "badge": "流式 AI",
        "description": "Codeium 推出的 AI IDE，主打 Cascade 流式 Agent 和深度代码理解。",
        "meta": ["IDE", "Cascade", "流式 Agent"],
        "link": "https://codeium.com/windsurf",
        "search_query": '"Windsurf" OR "Codeium" AI (IDE OR update)',
        "_reddit_query": "Windsurf Codeium",
        "reddit_subs": ["programming"],
        "features": ["Cascade 流式 Agent", "深度代码理解", "多文件编辑", "免费额度"]
    },
    {
        "title": "OpenAI Codex CLI",
        "badge": "OpenAI 官方",
        "description": "OpenAI 推出的开源命令行编码 Agent，支持沙箱执行与自主代码生成。",
        "meta": ["CLI", "开源", "Agent", "OpenAI"],
        "link": "https://github.com/openai/codex",
        "search_query": '"Codex CLI" OR "OpenAI Codex" (release OR launch)',
        "gh_owner": "openai",
        "gh_repo": "codex",
        "_reddit_query": "OpenAI Codex CLI",
        "reddit_subs": ["ChatGPT", "programming"],
        "features": ["开源 CLI Agent", "沙箱安全执行", "自主代码生成", "多语言支持"]
    },
    {
        "title": "Gemini CLI",
        "badge": "Google 出品",
        "description": "Google 官方命令行 Gemini 交互工具，支持代码生成与 API 调用。",
        "meta": ["CLI", "Google", "Gemini"],
        "link": "https://github.com/google-gemini/gemini-cli",
        "search_query": '"Gemini CLI" (release OR launch)',
        "gh_owner": "google-gemini",
        "gh_repo": "gemini-cli",
        "_reddit_query": "Gemini CLI",
        "reddit_subs": ["GoogleGemini"],
        "features": ["官方命令行工具", "Gemini 模型调用", "代码生成", "免费额度"]
    },
    {
        "title": "GitHub Copilot",
        "badge": "行业标配",
        "description": "GitHub + Microsoft 的 AI 编程助手，支持 Agent 模式、多模型切换、Copilot Workspace。",
        "meta": ["IDE 集成", "Agent 模式", "多模型"],
        "link": "https://github.com/features/copilot",
        "search_query": '"GitHub Copilot" (update OR feature OR agent)',
        "_reddit_query": "GitHub Copilot update",
        "reddit_subs": ["programming", "github"],
        "features": ["Agent 模式", "多模型支持", "VS Code/JetBrains 集成", "Copilot Workspace"]
    },
    {
        "title": "Aider",
        "badge": "终端 AI 助手",
        "description": "AI pair programming in your terminal. 支持多种 LLM 后端，Git 深度集成。",
        "meta": ["CLI", "多模型", "开源"],
        "link": "https://aider.chat",
        "search_query": '"Aider" AI (coding OR programming OR update)',
        "pypi_name": "aider-chat",
        "gh_owner": "Aider-AI",
        "gh_repo": "aider",
        "_reddit_query": "Aider AI coding",
        "reddit_subs": ["LocalLLaMA", "ChatGPTCoding"],
        "features": ["多 LLM 后端支持", "Git 深度集成", "终端原生", "开源"]
    },
    {
        "title": "Cline",
        "badge": "VS Code Agent",
        "description": "VS Code 内的自主编码 Agent，支持 Plan & Act 模式，MCP 工具扩展。",
        "meta": ["VS Code", "Agent", "MCP", "开源"],
        "link": "https://github.com/cline/cline",
        "search_query": '"Cline" AI (VS Code OR agent OR update)',
        "npm_name": "claude-dev",
        "gh_owner": "cline",
        "gh_repo": "cline",
        "_reddit_query": "Cline VS Code",
        "reddit_subs": ["ChatGPTCoding", "programming"],
        "features": ["Plan & Act 模式", "MCP 工具扩展", "自主编码", "多模型支持"]
    }
]

PLUGINS = [
    {
        "title": "MCP 生态 (Model Context Protocol)",
        "badge": "工具协议标准",
        "description": "Anthropic 发起的开放工具协议标准，让 AI 模型安全调用外部工具与数据源。生态快速扩展中。",
        "meta": ["协议标准", "工具调用", "开放生态"],
        "link": "https://modelcontextprotocol.io",
        "search_query": '"Model Context Protocol" OR "MCP" (server OR tool OR launch)',
        "gh_owner": "modelcontextprotocol",
        "gh_repo": "specification",
        "_reddit_query": "MCP Model Context Protocol",
        "reddit_subs": ["ClaudeAI", "programming"],
        "features": ["标准化工具调用", "安全沙箱执行", "多语言 SDK", "活跃社区生态"]
    },
    {
        "title": "OpenRouter",
        "badge": "模型聚合网关",
        "description": "统一 API 接入 100+ 模型提供商，支持免费模型、价格对比与智能路由。",
        "meta": ["API 网关", "多模型", "价格透明"],
        "link": "https://openrouter.ai",
        "search_query": '"OpenRouter" (model OR API OR update)',
        "_reddit_query": "OpenRouter",
        "reddit_subs": ["LocalLLaMA"],
        "features": ["100+ 模型接入", "免费模型池", "智能路由", "价格对比"]
    },
    {
        "title": "Ollama",
        "badge": "本地模型运行",
        "description": "一行命令在本地运行开源 LLM。支持 Llama、Qwen、DeepSeek 等主流开源模型。",
        "meta": ["本地部署", "开源", "一键运行"],
        "link": "https://ollama.com",
        "search_query": '"Ollama" (release OR update OR model)',
        "gh_owner": "ollama",
        "gh_repo": "ollama",
        "_reddit_query": "Ollama",
        "reddit_subs": ["LocalLLaMA"],
        "features": ["一键本地运行", "多模型支持", "API 兼容", "跨平台"]
    },
    {
        "title": "LangChain / LangGraph",
        "badge": "AI 应用框架",
        "description": "最流行的 LLM 应用开发框架，LangGraph 支持有状态 Agent 工作流编排。",
        "meta": ["框架", "Agent 编排", "Python/JS"],
        "link": "https://langchain.com",
        "search_query": '"LangChain" OR "LangGraph" (update OR release OR agent)',
        "npm_name": "langchain",
        "pypi_name": "langchain",
        "gh_owner": "langchain-ai",
        "gh_repo": "langchain",
        "_reddit_query": "LangChain LangGraph",
        "reddit_subs": ["LangChain", "MachineLearning"],
        "features": ["LLM 应用开发", "Agent 工作流", "工具调用链", "多语言 SDK"]
    },
    {
        "title": "Hugging Face Transformers",
        "badge": "模型 Hub 标配",
        "description": "最流行的开源 ML 库，统一接口调用数万个预训练模型，社区生态庞大。",
        "meta": ["开源", "模型 Hub", "Python"],
        "link": "https://huggingface.co/docs/transformers",
        "search_query": '"Hugging Face" OR "transformers" (update OR release)',
        "pypi_name": "transformers",
        "gh_owner": "huggingface",
        "gh_repo": "transformers",
        "_reddit_query": "Hugging Face transformers",
        "reddit_subs": ["MachineLearning", "LocalLLaMA"],
        "features": ["数万预训练模型", "统一推理接口", "活跃社区", "多框架支持"]
    },
    {
        "title": "vLLM",
        "badge": "高性能推理",
        "description": "高吞吐量 LLM 推理引擎，PagedAttention 技术大幅提升 GPU 利用率。",
        "meta": ["推理引擎", "高性能", "开源"],
        "link": "https://github.com/vllm-project/vllm",
        "search_query": '"vLLM" (update OR release OR performance)',
        "pypi_name": "vllm",
        "gh_owner": "vllm-project",
        "gh_repo": "vllm",
        "_reddit_query": "vLLM",
        "reddit_subs": ["LocalLLaMA", "MachineLearning"],
        "features": ["PagedAttention", "高吞吐量推理", "GPU 利用率优化", "OpenAI 兼容 API"]
    }
]


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("AI Nexus Intelligence Aggregator v2.0")
    print("=" * 60)

    # --- Enrich models ---
    print("\n[1/5] Enriching models...")
    for item in MODELS:
        print(f"  -> {item['title']}")
        enrich_item(
            item,
            gh_owner=item.get('gh_owner'),
            gh_repo=item.get('gh_repo'),
            search_query=item.get('search_query'),
            reddit_subs=item.get('reddit_subs')
        )

    # --- Enrich tools ---
    print("\n[2/5] Enriching tools...")
    for item in TOOLS:
        print(f"  -> {item['title']}")
        enrich_item(
            item,
            gh_owner=item.get('gh_owner'),
            gh_repo=item.get('gh_repo'),
            npm_name=item.get('npm_name'),
            pypi_name=item.get('pypi_name'),
            search_query=item.get('search_query'),
            reddit_subs=item.get('reddit_subs')
        )

    # --- Enrich plugins/ecosystem ---
    print("\n[3/5] Enriching ecosystem...")
    for item in PLUGINS:
        print(f"  -> {item['title']}")
        enrich_item(
            item,
            gh_owner=item.get('gh_owner'),
            gh_repo=item.get('gh_repo'),
            npm_name=item.get('npm_name'),
            pypi_name=item.get('pypi_name'),
            search_query=item.get('search_query'),
            reddit_subs=item.get('reddit_subs')
        )

    # --- OpenRouter models ---
    print("\n[4/5] Fetching OpenRouter model catalog...")
    openrouter = fetch_openrouter_data()

    # --- Trending news ---
    print("\n[5/5] Fetching trending AI news...")
    news = fetch_hn_trending(limit=10)

    # --- GitHub trending repos ---
    print("\n[Bonus] Fetching GitHub trending AI repos...")
    gh_trending = fetch_github_trending_repos("AI agent framework", limit=5)

    # --- Clean up internal fields before writing ---
    for item in MODELS + TOOLS + PLUGINS:
        for key in ['search_query', 'gh_owner', 'gh_repo', 'npm_name', 'pypi_name', 'reddit_subs', '_reddit_query']:
            item.pop(key, None)

    # --- Assemble final output ---
    output = {
        "lastUpdated": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S (UTC)"),
        "version": "2.0",
        "models": MODELS,
        "openrouter": openrouter,
        "tools": TOOLS,
        "plugins": PLUGINS,
        "news": news,
        "github_trending": gh_trending
    }

    os.makedirs('data', exist_ok=True)
    out_path = 'data/ai_info.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    # Count intelligence items
    total_updates = sum(len(item.get('recent_updates', [])) for item in MODELS + TOOLS + PLUGINS)
    print(f"\n{'=' * 60}")
    print(f"Done! Wrote {os.path.getsize(out_path)} bytes to {out_path}")
    print(f"  Models: {len(MODELS)} | Tools: {len(TOOLS)} | Plugins: {len(PLUGINS)}")
    print(f"  Intelligence items: {total_updates} updates across all sources")
    print(f"  OpenRouter models: {len(openrouter)} | News: {len(news)}")
    print(f"  GitHub trending: {len(gh_trending)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
