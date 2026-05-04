import json
import urllib.request
import datetime
import os
import time

def fetch_latest_intelligence(query):
    """Deeply mine the latest news and feature updates for a specific keyword."""
    # We use URL encoding for the query
    encoded_query = urllib.parse.quote(query)
    url = f"https://hn.algolia.com/api/v1/search_by_date?query={encoded_query}&tags=story&hitsPerPage=1"
    req = urllib.request.Request(url, headers={'User-Agent': 'AINexus/1.0'})
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            hits = data.get('hits', [])
            if hits:
                h = hits[0]
                return {
                    "title": h.get('title', ''),
                    "url": h.get('url', f"https://news.ycombinator.com/item?id={h.get('objectID')}"),
                    "date": h.get('created_at', '')[:10]
                }
    except Exception as e:
        print(f"Error fetching intelligence for {query}: {e}")
    return None

def fetch_openrouter_data():
    url = "https://openrouter.ai/api/v1/models"
    req = urllib.request.Request(url, headers={'User-Agent': 'AINexus/1.0'})
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            models = data.get('data', [])
            
            # Sort models to find free ones and popular ones
            # OpenRouter model objects have pricing.prompt and pricing.completion
            free_models = []
            for m in models:
                pricing = m.get('pricing', {})
                # Some models have pricing as string "0", some as float 0.0
                if float(pricing.get('prompt', 1)) == 0 and float(pricing.get('completion', 1)) == 0:
                    free_models.append(m)
            
            # Get top 4 free models based on some criteria (e.g. context length or name)
            top_free = sorted(free_models, key=lambda x: x.get('context_length', 0), reverse=True)[:4]
            
            result = []
            for m in top_free:
                name = m.get('name', '')
                if not name:
                    name = m.get('id', 'Unknown')
                ctx = m.get('context_length', 0)
                result.append({
                    "title": name,
                    "badge": "免费体验",
                    "description": f"OpenRouter 提供的免费访问模型。ID: {m.get('id')}。上下文长度: {ctx} tokens。",
                    "meta": ["免费", "API 开放"],
                    "link": f"https://openrouter.ai/models/{m.get('id')}"
                })
            
            # If API fails or doesn't return free models, add a fallback
            if not result:
                result = [
                    { "title": 'Llama 3 8B (Free)', "badge": '免费', "description": '在 OpenRouter 上免费提供。', "meta": ['Meta', '免费'], "link": 'https://openrouter.ai' },
                    { "title": 'Mistral Nemo (Free)', "badge": '免费', "description": '性能强悍的 12B 开源模型。', "meta": ['12B', '免费'], "link": 'https://openrouter.ai' }
                ]
            return result
    except Exception as e:
        print(f"Error fetching OpenRouter models: {e}")
        return [
            { "title": 'Llama 3 8B (Free)', "badge": '免费', "description": '在 OpenRouter 上最受欢迎的免费开源模型。', "meta": ['Meta', '开源', '免费'], "link": 'https://openrouter.ai' },
            { "title": 'Mistral Nemo', "badge": '免费新星', "description": '性能强悍且在 OpenRouter 上免费提供。', "meta": ['12B', '免费'], "link": 'https://openrouter.ai' }
        ]

def fetch_hn_news():
    url = "https://hn.algolia.com/api/v1/search_by_date?query=AI%20OR%20LLM%20OR%20Agent&tags=story&hitsPerPage=6"
    req = urllib.request.Request(url, headers={'User-Agent': 'AINexus/1.0'})
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            hits = data.get('hits', [])
            result = []
            for h in hits:
                title = h.get('title', '')
                link = h.get('url', '')
                if not link:
                    link = f"https://news.ycombinator.com/item?id={h.get('objectID')}"
                author = h.get('author', 'unknown')
                points = h.get('points', 0)
                result.append({
                    "title": title,
                    "badge": f"HN 热点 ({points} pts)",
                    "description": f"由 {author} 发布。在 Hacker News 上最新讨论的 AI 资讯。",
                    "meta": ["Hacker News", "资讯"],
                    "link": link
                })
            return result
    except Exception as e:
        print(f"Error fetching HN news: {e}")
        return []

def main():
    base_models = [
        { "title": 'OpenAI GPT-5.5', "search_query": '"GPT-5" OR "OpenAI"', "badge": '2026 新旗舰', "description": '2026年最新发布，大幅减少幻觉，在代码工程与复杂 Agentic 任务上具备颠覆性提升。', "meta": ['多模态', '自主 Agent', '闭源'], "link": 'https://openai.com' },
        { "title": 'Claude Opus 4.7', "search_query": '"Claude Opus" OR "Anthropic"', "badge": '逻辑之王', "description": 'Anthropic 发布的最新超大杯，原生引入“任务预算”控制，极强的高阶规划和代码能力。', "meta": ['精准控制', '长文本', '闭源'], "link": 'https://anthropic.com' },
        { "title": 'Google Gemini 3.1 Pro', "search_query": '"Gemini 1.5" OR "Gemini Pro" OR "DeepMind"', "badge": '原生多模态', "description": '霸榜多项推理 Benchmark，在多模态理解与超长上下文方面维持统治级表现。', "meta": ['超长上下文', 'Google生态', '闭源'], "link": 'https://deepmind.google' },
        { "title": 'DeepSeek V4', "search_query": '"DeepSeek"', "badge": '国产之光', "description": '最新发布的开源巨兽，采用极致高效架构，API 成本依然极具竞争力。', "meta": ['开源/开放权重', 'API极简'], "link": 'https://deepseek.com' },
        { "title": 'Kimi K2.6', "search_query": '"Moonshot AI" OR "Kimi"', "badge": '长文本领军', "description": '支持恐怖的超长上下文，并引入全新 "Agent Swarm" 技术进行复杂任务拆解。', "meta": ['Agent Swarm', '长文本'], "link": 'https://kimi.moonshot.cn' },
        { "title": 'GLM-5.1', "search_query": '"Zhipu" OR "GLM-4"', "badge": '智谱AI', "description": 'MoE 架构，纯国产算力训练，在代码和逻辑推理上获得巨大后训练提升。', "meta": ['国产算力', '开源'], "link": 'https://zhipuai.cn' },
        { "title": 'MiniMax M2.7', "search_query": '"MiniMax AI"', "badge": '高吞吐', "description": '自进化模型架构，在自动化工具调用和办公流（Productivity）场景下表现绝佳。', "meta": ['工具调用', '办公流'], "link": 'https://api.minimax.chat' },
        { "title": 'MiMo V2.5-Pro', "search_query": '"Xiaomi AI" OR "MiMo model"', "badge": '全能新星', "description": '小米 AI 实验室最新大作，万亿参数 MoE 架构，强力支撑多步 Agentic 规划。', "meta": ['百万上下文', '全模态'], "link": '#' }
    ]

    base_tools = [
        { "title": 'OpenClaw', "search_query": '"OpenClaw" OR "Gateway agent"', "badge": '生态互联', "description": '最热门的开源 Gateway-first 智能体框架，拥有海量技能插件，轻松打通工作流。', "meta": ['Agent', '多平台生态'], "link": 'https://github.com/openclaw' },
        { "title": 'Hermes Agent', "search_query": '"Hermes Agent" OR "Nous Research"', "badge": '自主进化', "description": 'Nous Research 推出的 Agent-first 框架，主打自学习与长记忆循环，持续进化。', "meta": ['长记忆', '自学习'], "link": 'https://nousresearch.com/hermes' },
        { "title": 'Claude Code', "search_query": '"Claude Code"', "badge": '官方出品', "description": 'Anthropic 官方推出的命令行 AI 编程助手，深度集成最新 Claude 模型。', "meta": ['CLI', '代码生成'], "link": 'https://docs.anthropic.com' },
        { "title": 'Antigravity', "search_query": '"Antigravity" "Agent"', "badge": '智能体架构', "description": '高级 Agentic 编码助手框架。', "meta": ['Agent', '前沿探索'] },
        { "title": 'OpenCode', "search_query": '"OpenCode" AI', "badge": '开源框架', "description": '开源社区驱动的下一代 AI 编程 IDE 插件框架。', "meta": ['开源', 'IDE插件'] },
        { "title": 'Kiro', "search_query": '"Kiro" AI workflow', "badge": '自动化', "description": '轻量级 AI 工作流自动化工具，轻松串联各种模型 API。', "meta": ['Workflow', '轻量级'] },
        { "title": 'Gemini-CLI', "search_query": '"Gemini CLI"', "badge": '命令行', "description": '快速调用 Google Gemini API 的终端工具。', "meta": ['CLI', 'Google'] }
    ]
    
    base_plugins = [
        { "title": 'cc claude', "search_query": '"cc claude"', "badge": '高效', "description": '为 Claude 深度定制的增强插件，提供更便捷的 prompt 管理与历史记录。', "meta": ['浏览器插件', '效率提升'] },
        { "title": 'cliproxyapi', "search_query": '"cliproxyapi"', "badge": '开发者工具', "description": '一键将各类 CLI 工具转化为标准 API 接口，极大简化 Agent 调用外部工具的难度。', "meta": ['API中转', 'Agent增强'] }
    ]

    # Dynamically fetch intelligence for each item
    for item in base_models + base_tools + base_plugins:
        query = item.pop("search_query")
        intel = fetch_latest_intelligence(query)
        if intel:
            item["latest_update"] = intel
        time.sleep(0.1) # Be nice to the API

    curated_data = {
        "lastUpdated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S (UTC)"),
        "models": base_models,
        "openrouter": fetch_openrouter_data(),
        "tools": base_tools,
        "plugins": base_plugins,
        "news": fetch_hn_news()
    }
    
    os.makedirs('data', exist_ok=True)
    with open('data/ai_info.json', 'w', encoding='utf-8') as f:
        json.dump(curated_data, f, ensure_ascii=False, indent=2)
    print("Data successfully updated.")

if __name__ == "__main__":
    main()
