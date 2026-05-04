import json
import urllib.request
import datetime
import os

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

def main():
    curated_data = {
        "lastUpdated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S (UTC)"),
        "models": [
            { "title": 'OpenAI GPT-4o', "badge": '领先', "description": 'OpenAI 最新多模态旗舰模型，支持原生音频、视觉和文本交互，性能全面提升。', "meta": ['多模态', '响应快', '闭源'], "link": 'https://openai.com' },
            { "title": 'Claude 3.5 Sonnet', "badge": '热门', "description": 'Anthropic 发布的当前最强中杯模型，代码能力与逻辑推理能力大幅超越前代。', "meta": ['代码强', '长文本', '闭源'], "link": 'https://anthropic.com' },
            { "title": 'Google Gemini 1.5 Pro', "badge": '原生多模态', "description": '支持高达 2M Token 上下文窗口，在长文档分析与视频理解方面一骑绝尘。', "meta": ['超长上下文', 'Google 生态', '闭源'], "link": 'https://deepmind.google' },
            { "title": 'DeepSeek V2', "badge": '国产高性价比', "description": '采用创新架构的国产开源模型，API 价格极具竞争力，综合性能比肩顶级模型。', "meta": ['开源', 'API 极简', '高性价比'], "link": 'https://deepseek.com' },
            { "title": 'Kimi (Moonshot)', "badge": '国产长文本', "description": '月之暗面出品，主打超长文本处理与精准的信息提取能力，国内口碑极佳。', "meta": ['长文本', '国内免翻'], "link": 'https://kimi.moonshot.cn' },
            { "title": 'GLM-4', "badge": '智谱AI', "description": '智谱AI新一代基座大模型，综合能力全面升级，支持智能体定制。', "meta": ['多模态', '国产头部'], "link": 'https://zhipuai.cn' },
            { "title": 'MiniMax', "badge": '语音/多模态', "description": '在语音合成与拟人化交互方面有独到优势的国产大模型。', "meta": ['语音', '拟人化'], "link": 'https://api.minimax.chat' },
            { "title": 'Mimo', "badge": '前沿探索', "description": '备受关注的新锐 AI 模型，在特定任务上展现出强大潜力。', "meta": ['新星', '高效推理'], "link": '#' }
        ],
        "openrouter": fetch_openrouter_data(),
        "tools": [
            { "title": 'Claude Code', "badge": '官方出品', "description": 'Anthropic 官方推出的命令行 AI 编程助手，深度集成 Claude 3.5 Sonnet。', "meta": ['CLI', '代码生成'], "link": 'https://docs.anthropic.com' },
            { "title": 'Antigravity', "badge": '智能体架构', "description": '高级 Agentic 编码助手框架。', "meta": ['Agent', '前沿探索'] },
            { "title": 'OpenCode', "badge": '开源框架', "description": '开源社区驱动的下一代 AI 编程 IDE 插件框架。', "meta": ['开源', 'IDE 插件'] },
            { "title": 'Kiro', "badge": '自动化', "description": '轻量级 AI 工作流自动化工具，轻松串联各种模型 API。', "meta": ['Workflow', '轻量级'] },
            { "title": 'Gemini-CLI', "badge": '命令行', "description": '快速调用 Google Gemini API 的终端工具。', "meta": ['CLI', 'Google'] }
        ],
        "plugins": [
            { "title": 'cc claude', "badge": '高效', "description": '为 Claude 深度定制的增强插件，提供更便捷的 prompt 管理与历史记录。', "meta": ['浏览器插件', '效率提升'] },
            { "title": 'cliproxyapi', "badge": '开发者工具', "description": '一键将各类 CLI 工具转化为标准 API 接口，极大简化 Agent 调用外部工具的难度。', "meta": ['API 中转', 'Agent 增强'] }
        ]
    }
    
    os.makedirs('data', exist_ok=True)
    with open('data/ai_info.json', 'w', encoding='utf-8') as f:
        json.dump(curated_data, f, ensure_ascii=False, indent=2)
    print("Data successfully updated.")

if __name__ == "__main__":
    main()
