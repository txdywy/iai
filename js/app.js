document.addEventListener('DOMContentLoaded', () => {
    fetchData();
});

async function fetchData() {
    try {
        const response = await fetch('data/ai_info.json');
        if (!response.ok) throw new Error('Network error');
        const data = await response.json();
        renderData(data);
    } catch (error) {
        console.warn('Failed to load real data, showing mock data.', error);
        renderData(getMockData());
    }
}

function renderData(data) {
    document.getElementById('last-updated').textContent = `最后更新: ${data.lastUpdated}`;

    renderModelCards('models-grid', data.models || []);
    renderModelCards('tools-grid', data.tools || []);
    renderModelCards('plugins-grid', data.plugins || []);
    renderOpenRouterCards('openrouter-grid', data.openrouter || []);
    renderTrendingCards('trending-grid', data.github_trending || []);
    renderNewsCards('news-grid', data.news || []);
}

// ---------------------------------------------------------------------------
// Model / Tool / Plugin cards — richest intelligence display
// ---------------------------------------------------------------------------

function renderModelCards(containerId, items) {
    const container = document.getElementById(containerId);
    container.innerHTML = '';

    if (!items.length) {
        container.innerHTML = '<p style="color: var(--text-secondary)">暂无数据。</p>';
        return;
    }

    items.forEach(item => {
        const card = document.createElement('div');
        card.className = 'card intel-card';

        let headerHtml = `
            <div class="card-header">
                <div class="card-title">${escHtml(item.title)}</div>
                <div class="card-badges">
                    ${item.badge ? `<span class="card-badge">${escHtml(item.badge)}</span>` : ''}
                    ${item.latest_version ? `<span class="version-badge">v${escHtml(item.latest_version)}</span>` : ''}
                </div>
            </div>`;

        let descHtml = `<div class="card-desc">${escHtml(item.description)}</div>`;

        // Features section
        let featuresHtml = '';
        if (item.features && item.features.length) {
            featuresHtml = `<div class="features-section">
                <div class="features-title">核心特性</div>
                <ul class="features-list">
                    ${item.features.map(f => `<li>${escHtml(f)}</li>`).join('')}
                </ul>
            </div>`;
        }

        // GitHub stats bar
        let ghHtml = '';
        if (item.github) {
            const gh = item.github;
            ghHtml = `<div class="gh-stats">
                ${gh.stars ? `<span class="gh-stat"><span class="gh-icon">&#9733;</span> ${formatNumber(gh.stars)}</span>` : ''}
                ${gh.forks ? `<span class="gh-stat"><span class="gh-icon">&#9741;</span> ${formatNumber(gh.forks)}</span>` : ''}
                ${gh.language ? `<span class="gh-lang">${escHtml(gh.language)}</span>` : ''}
                ${gh.topics && gh.topics.length ? gh.topics.slice(0, 4).map(t => `<span class="gh-topic">${escHtml(t)}</span>`).join('') : ''}
            </div>`;
        }

        // npm downloads
        let npmHtml = '';
        if (item.npm_downloads_weekly) {
            npmHtml = `<div class="npm-stats">npm 周下载: <strong>${formatNumber(item.npm_downloads_weekly)}</strong></div>`;
        }

        // Pricing hint
        let pricingHtml = '';
        if (item.pricing_hint) {
            pricingHtml = `<div class="pricing-hint">${escHtml(item.pricing_hint)}</div>`;
        }

        // Meta tags
        let metaHtml = '';
        if (item.meta && item.meta.length) {
            metaHtml = `<div class="card-meta">${item.meta.map(m => `<span>${escHtml(m)}</span>`).join('')}</div>`;
        }

        // Recent updates panel
        let updatesHtml = '';
        if (item.recent_updates && item.recent_updates.length) {
            updatesHtml = `<div class="updates-panel">
                <div class="updates-title">多源情报 (${item.recent_updates.length})</div>
                ${item.recent_updates.map(u => {
                    const sourceClass = getSourceClass(u.source);
                    return `<a href="${escAttr(u.url)}" target="_blank" rel="noopener" class="update-item">
                        <span class="update-source ${sourceClass}">${escHtml(u.source)}</span>
                        <span class="update-text">${escHtml(u.title)}</span>
                        <span class="update-meta">${escHtml(u.date || '')}${u.engagement ? ' · ' + escHtml(u.engagement) : ''}</span>
                    </a>`;
                }).join('')}
            </div>`;
        }

        // Link
        let linkHtml = '';
        if (item.link && item.link !== '#') {
            linkHtml = `<a href="${escAttr(item.link)}" class="card-link" target="_blank" rel="noopener">了解更多 &rarr;</a>`;
        }

        card.innerHTML = headerHtml + descHtml + featuresHtml + ghHtml + npmHtml + pricingHtml + metaHtml + updatesHtml + linkHtml;
        container.appendChild(card);
    });
}

// ---------------------------------------------------------------------------
// OpenRouter cards
// ---------------------------------------------------------------------------

function renderOpenRouterCards(containerId, items) {
    const container = document.getElementById(containerId);
    container.innerHTML = '';

    if (!items.length) {
        container.innerHTML = '<p style="color: var(--text-secondary)">暂无 OpenRouter 数据。</p>';
        return;
    }

    items.forEach(item => {
        const card = document.createElement('div');
        card.className = 'card or-card';

        let pricingDetail = '';
        if (item.pricing) {
            const pp = item.pricing.prompt;
            const pc = item.pricing.completion;
            if (pp !== '?' || pc !== '?') {
                pricingDetail = `<div class="pricing-detail">
                    Input: $${pp}/tok | Output: $${pc}/tok
                </div>`;
            }
        }

        card.innerHTML = `
            <div class="card-header">
                <div class="card-title">${escHtml(item.title)}</div>
                ${item.badge ? `<span class="card-badge">${escHtml(item.badge)}</span>` : ''}
            </div>
            <div class="card-desc">${escHtml(item.description)}</div>
            ${pricingDetail}
            ${item.meta ? `<div class="card-meta">${item.meta.map(m => `<span>${escHtml(m)}</span>`).join('')}</div>` : ''}
            ${item.link ? `<a href="${escAttr(item.link)}" class="card-link" target="_blank" rel="noopener">OpenRouter 查看 &rarr;</a>` : ''}
        `;
        container.appendChild(card);
    });
}

// ---------------------------------------------------------------------------
// GitHub trending cards
// ---------------------------------------------------------------------------

function renderTrendingCards(containerId, items) {
    const container = document.getElementById(containerId);
    container.innerHTML = '';

    if (!items.length) {
        container.innerHTML = '<p style="color: var(--text-secondary)">暂无趋势数据。</p>';
        return;
    }

    items.forEach(item => {
        const card = document.createElement('div');
        card.className = 'card trending-card';
        card.innerHTML = `
            <div class="card-header">
                <div class="card-title">${escHtml(item.name)}</div>
                <span class="gh-stat"><span class="gh-icon">&#9733;</span> ${formatNumber(item.stars)}</span>
            </div>
            <div class="card-desc">${escHtml(item.description)}</div>
            <div class="card-meta">
                ${item.language ? `<span>${escHtml(item.language)}</span>` : ''}
                <span>Updated: ${escHtml(item.updated)}</span>
            </div>
            <a href="${escAttr(item.url)}" class="card-link" target="_blank" rel="noopener">GitHub 查看 &rarr;</a>
        `;
        container.appendChild(card);
    });
}

// ---------------------------------------------------------------------------
// News cards
// ---------------------------------------------------------------------------

function renderNewsCards(containerId, items) {
    const container = document.getElementById(containerId);
    container.innerHTML = '';

    if (!items.length) {
        container.innerHTML = '<p style="color: var(--text-secondary)">暂无资讯。</p>';
        return;
    }

    items.forEach(item => {
        const card = document.createElement('div');
        card.className = 'card news-card';
        card.innerHTML = `
            <div class="card-header">
                <div class="card-title">${escHtml(item.title)}</div>
                ${item.badge ? `<span class="card-badge badge-hot">${escHtml(item.badge)}</span>` : ''}
            </div>
            <div class="card-desc">${escHtml(item.description)}</div>
            ${item.meta ? `<div class="card-meta">${item.meta.map(m => `<span>${escHtml(m)}</span>`).join('')}</div>` : ''}
            ${item.link ? `<a href="${escAttr(item.link)}" class="card-link" target="_blank" rel="noopener">阅读原文 &rarr;</a>` : ''}
        `;
        container.appendChild(card);
    });
}

// ---------------------------------------------------------------------------
// Utility helpers
// ---------------------------------------------------------------------------

function escHtml(str) {
    if (!str) return '';
    return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function escAttr(str) {
    return escHtml(str);
}

function formatNumber(n) {
    if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M';
    if (n >= 1000) return (n / 1000).toFixed(1) + 'K';
    return String(n);
}

function getSourceClass(source) {
    if (!source) return 'src-default';
    const s = source.toLowerCase();
    if (s.includes('github')) return 'src-github';
    if (s.includes('hacker')) return 'src-hn';
    if (s.includes('reddit')) return 'src-reddit';
    if (s.includes('npm')) return 'src-npm';
    if (s.includes('pypi')) return 'src-pypi';
    if (s.includes('arxiv')) return 'src-arxiv';
    return 'src-default';
}

// ---------------------------------------------------------------------------
// Mock data fallback (minimal)
// ---------------------------------------------------------------------------

function getMockData() {
    return {
        lastUpdated: new Date().toLocaleString('zh-CN') + ' (本地)',
        version: "2.0",
        models: [
            { title: 'OpenAI GPT-5.5', badge: '2026 旗舰', description: 'OpenAI 最新旗舰，代码工程与 Agentic 任务颠覆性提升。', meta: ['多模态', 'Agent', '闭源'], features: ['原生多模态', '自主 Agent', '幻觉率下降'], link: 'https://openai.com' },
            { title: 'Claude Opus 4.7', badge: '逻辑之王', description: 'Anthropic 超大杯，任务预算控制，1M 上下文。', meta: ['精准控制', '1M 上下文', '闭源'], features: ['任务预算控制', '扩展思维', '代码能力登顶'], link: 'https://anthropic.com' },
            { title: 'DeepSeek V3/R1', badge: '开源之光', description: '开源巨兽，MoE 架构，API 成本极具竞争力。', meta: ['开源', 'MoE', '高性价比'], features: ['MoE 架构', '开源权重', '推理能力顶级'], link: 'https://deepseek.com' }
        ],
        openrouter: [
            { title: 'Llama 3 8B (Free)', badge: '免费', description: 'OpenRouter 最受欢迎的免费开源模型。', meta: ['Meta', '免费'], link: 'https://openrouter.ai' }
        ],
        tools: [
            { title: 'Claude Code', badge: 'AI 编程旗舰', description: 'Anthropic 官方命令行 AI 编程助手。', meta: ['CLI', 'Agent'], features: ['自主编码', 'MCP 支持', 'Git 集成'], link: 'https://docs.anthropic.com' },
            { title: 'Cursor', badge: 'AI IDE', description: 'AI-native IDE，Tab 补全与 Agent 模式。', meta: ['IDE', '多模型'], features: ['Tab 补全', 'Agent 模式'], link: 'https://cursor.com' }
        ],
        plugins: [
            { title: 'MCP 生态', badge: '协议标准', description: 'AI 工具调用开放标准。', meta: ['协议', '开放'], features: ['标准化工具调用', '安全沙箱'], link: 'https://modelcontextprotocol.io' }
        ],
        news: [
            { title: 'AI News (mock)', badge: 'HN (100 pts)', description: '示例新闻数据。', meta: ['Hacker News'], link: '#' }
        ],
        github_trending: []
    };
}
