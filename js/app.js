document.addEventListener('DOMContentLoaded', () => {
    fetchData();
});

async function fetchData() {
    try {
        const response = await fetch('data/ai_info.json');
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        const data = await response.json();
        renderData(data);
    } catch (error) {
        console.warn('Failed to load real data, showing mock data.', error);
        renderData(getMockData());
    }
}

function renderData(data) {
    document.getElementById('last-updated').textContent = `最后更新: ${data.lastUpdated}`;
    
    renderGrid('models-grid', data.models);
    renderGrid('openrouter-grid', data.openrouter);
    renderGrid('tools-grid', data.tools);
    renderGrid('plugins-grid', data.plugins);
    if (data.news) {
        renderGrid('news-grid', data.news);
    }
}

function renderGrid(containerId, items) {
    const container = document.getElementById(containerId);
    container.innerHTML = ''; // clear loading

    if (!items || items.length === 0) {
        container.innerHTML = '<p style="color: var(--text-secondary)">暂无数据更新。</p>';
        return;
    }

    items.forEach(item => {
        const card = document.createElement('div');
        card.className = 'card';
        
        let metaHtml = '';
        if (item.meta) {
            metaHtml = `<div class="card-meta">
                ${item.meta.map(m => `<span>${m}</span>`).join('')}
            </div>`;
        }

        card.innerHTML = `
            <div class="card-header">
                <div class="card-title">${item.title}</div>
                ${item.badge ? `<div class="card-badge">${item.badge}</div>` : ''}
            </div>
            <div class="card-desc">${item.description}</div>
            ${metaHtml}
            ${item.link ? `<a href="${item.link}" class="card-link" target="_blank">了解更多 &rarr;</a>` : ''}
        `;
        container.appendChild(card);
    });
}

function getMockData() {
    return {
        lastUpdated: new Date().toLocaleString('zh-CN'),
        models: [
            { title: 'OpenAI GPT-4o', badge: '领先', description: 'OpenAI 最新多模态旗舰模型，支持原生音频、视觉和文本交互，性能全面提升。', meta: ['多模态', '响应快', '闭源'], link: 'https://openai.com' },
            { title: 'Claude 3.5 Sonnet', badge: '热门', description: 'Anthropic 发布的当前最强中杯模型，代码能力与逻辑推理能力大幅超越前代。', meta: ['代码强', '长文本', '闭源'], link: 'https://anthropic.com' },
            { title: 'Google Gemini 1.5 Pro', badge: '原生多模态', description: '支持高达 2M Token 上下文窗口，在长文档分析与视频理解方面一骑绝尘。', meta: ['超长上下文', 'Google 生态', '闭源'], link: 'https://deepmind.google' },
            { title: 'DeepSeek V2', badge: '国产高性价比', description: '采用创新架构的国产开源模型，API 价格极具竞争力，综合性能比肩顶级模型。', meta: ['开源', 'API 极简', '高性价比'], link: 'https://deepseek.com' },
            { title: 'Kimi (Moonshot)', badge: '国产长文本', description: '月之暗面出品，主打超长文本处理与精准的信息提取能力，国内口碑极佳。', meta: ['长文本', '国内免翻'], link: 'https://kimi.moonshot.cn' },
            { title: 'GLM-4', badge: '智谱AI', description: '智谱AI新一代基座大模型，综合能力全面升级，支持智能体定制。', meta: ['多模态', '国产头部'], link: 'https://zhipuai.cn' }
        ],
        openrouter: [
            { title: 'Llama 3 8B (Free)', badge: '免费/用量第一', description: '当前 OpenRouter 上最受欢迎的免费开源模型，适用于日常轻量级任务。', meta: ['Meta', '开源', '免费'], link: 'https://openrouter.ai' },
            { title: 'Mistral Nemo', badge: '免费新星', description: 'Mistral 与 NVIDIA 联合发布的 12B 模型，性能强悍且在 OpenRouter 上免费提供。', meta: ['12B', '免费'], link: 'https://openrouter.ai' },
            { title: 'Command R+', badge: '企业级测试', description: 'Cohere 针对 RAG 优化的旗舰模型，适合企业级复杂检索增强生成任务。', meta: ['RAG 优化', 'Alpha'], link: 'https://openrouter.ai' }
        ],
        tools: [
            { title: 'Claude Code', badge: '官方出品', description: 'Anthropic 官方推出的命令行 AI 编程助手，深度集成 Claude 3.5 Sonnet。', meta: ['CLI', '代码生成'], link: 'https://docs.anthropic.com' },
            { title: 'Antigravity', badge: '智能体架构', description: 'Google DeepMind 团队开发的高级 Agentic 编码助手框架。', meta: ['Agent', '前沿探索'] },
            { title: 'OpenCode', badge: '开源框架', description: '开源社区驱动的下一代 AI 编程 IDE 插件框架。', meta: ['开源', 'IDE 插件'] },
            { title: 'Kiro', badge: '自动化', description: '轻量级 AI 工作流自动化工具，轻松串联各种模型 API。', meta: ['Workflow', '轻量级'] }
        ],
        plugins: [
            { title: 'cc claude', badge: '高效', description: '为 Claude 深度定制的增强插件，提供更便捷的 prompt 管理与历史记录。', meta: ['浏览器插件', '效率提升'] },
            { title: 'cliproxyapi', badge: '开发者工具', description: '一键将各类 CLI 工具转化为标准 API 接口，极大简化 Agent 调用外部工具的难度。', meta: ['API 中转', 'Agent 增强'] }
        ]
    };
}
