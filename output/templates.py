"""
output/templates.py - HTML template for the news aggregator.

Contains the Jinja2 template for rendering the curated news page.
"""
from jinja2 import Template

# =============================================================================
# HTML TEMPLATE
# =============================================================================

HTML_TEMPLATE = Template('''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>News Aggregator — {{ today }}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #0a0a0f;
      --bg-elevated: #12121a;
      --bg-card: #1a1a24;
      --bg-card-hover: #22222e;
      --border: #2a2a3a;
      --text: #f0f0f5;
      --text-secondary: #a0a0b0;
      --text-muted: #707080;
      --accent: #6366f1;
      --accent-light: #818cf8;
      --accent-glow: rgba(99, 102, 241, 0.3);
      --breaking: #ef4444;
      --important: #f59e0b;
      --gradient: linear-gradient(135deg, #6366f1, #8b5cf6, #a855f7);
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'Inter', system-ui, sans-serif; background: var(--bg); color: var(--text); line-height: 1.6; }
    .wrap { max-width: 1280px; margin: 0 auto; padding: 0 1.5rem; }
    
    header { background: linear-gradient(135deg, #0a0a0f, #1a1a2e); border-bottom: 1px solid var(--border); padding: 2rem 0; position: relative; }
    header::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px; background: var(--gradient); }
    h1 { font-size: 2rem; font-weight: 700; background: var(--gradient); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 0.75rem; }
    .meta-bar { display: flex; gap: 0.75rem; flex-wrap: wrap; margin-bottom: 1rem; }
    .pill { display: inline-flex; align-items: center; gap: 0.5rem; padding: 0.4rem 0.9rem; background: var(--bg-card); border: 1px solid var(--border); border-radius: 999px; font-size: 0.8rem; color: var(--text-secondary); }
    nav { display: flex; gap: 0.5rem; flex-wrap: wrap; }
    nav a { color: var(--text-secondary); text-decoration: none; font-size: 0.85rem; font-weight: 500; padding: 0.5rem 1rem; border-radius: 0.5rem; background: var(--bg-card); border: 1px solid var(--border); transition: all 0.2s; }
    nav a:hover { background: var(--bg-card-hover); border-color: var(--accent); color: var(--text); }
    
    main { padding: 2rem 0; }
    section { margin-bottom: 2.5rem; }
    h2 { font-size: 1.25rem; font-weight: 600; margin-bottom: 1rem; display: flex; align-items: center; gap: 0.75rem; }
    h2::before { content: ''; width: 4px; height: 1.5rem; background: var(--gradient); border-radius: 2px; }
    
    .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 1.25rem; }
    article { background: var(--bg-card); border: 1px solid var(--border); border-radius: 1rem; overflow: hidden; transition: all 0.3s; display: flex; flex-direction: column; }
    article:hover { border-color: var(--accent); box-shadow: 0 0 30px var(--accent-glow); transform: translateY(-2px); }
    article img { width: 100%; height: 160px; object-fit: cover; }
    .no-img { height: 160px; background: var(--bg-elevated); display: flex; align-items: center; justify-content: center; font-size: 2rem; opacity: 0.3; }
    .card-body { padding: 1rem; flex: 1; display: flex; flex-direction: column; }
    .card-meta { display: flex; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 0.5rem; }
    .chip { font-size: 0.65rem; font-weight: 600; padding: 0.2rem 0.5rem; border-radius: 999px; text-transform: uppercase; }
    .chip-date { background: rgba(99,102,241,0.15); color: var(--accent-light); }
    .chip-source { background: var(--bg-elevated); color: var(--text-secondary); }
    .chip-breaking { background: rgba(239,68,68,0.2); color: #f87171; }
    .chip-important { background: rgba(245,158,11,0.2); color: #fbbf24; }
    .chip-time { background: rgba(16,185,129,0.15); color: #34d399; }
    .card-title { font-size: 0.95rem; font-weight: 600; line-height: 1.4; margin-bottom: 0.5rem; }
    .card-title a { color: inherit; text-decoration: none; }
    .card-title a:hover { color: var(--accent-light); }
    .card-summary { font-size: 0.8rem; color: var(--text-secondary); line-height: 1.6; margin-bottom: 0.75rem; flex: 1; display: -webkit-box; -webkit-line-clamp: 5; -webkit-box-orient: vertical; overflow: hidden; }
    .card-footer { display: flex; flex-wrap: nowrap; align-items: flex-end; justify-content: space-between; gap: 0.5rem; margin-top: auto; padding-top: 0.75rem; }
    .card-link { display: inline-flex; align-items: center; gap: 0.25rem; padding: 0.4rem 0.8rem; background: var(--accent); color: white; text-decoration: none; border-radius: 0.4rem; font-size: 0.75rem; font-weight: 500; transition: all 0.2s; flex-shrink: 0; }
    .card-link:hover { background: var(--accent-light); }
    
    /* Multi-source buttons - horizontal row, right-aligned at bottom */
    .source-buttons { display: flex; flex-direction: row; align-items: center; gap: 0.3rem; }
    .source-btn { padding: 0.25rem 0.5rem; background: var(--bg-elevated); color: var(--text-secondary); text-decoration: none; border-radius: 0.3rem; font-size: 0.65rem; font-weight: 500; border: 1px solid var(--border); transition: all 0.2s; white-space: nowrap; }
    .source-btn:hover { background: var(--accent); color: white; border-color: var(--accent); }
    
    /* Compact section for small categories */
    .compact-section { margin-bottom: 2.5rem; }
    .compact-grid { display: flex; flex-direction: column; gap: 1rem; }
    .compact-card { display: flex; gap: 1rem; padding: 1rem; background: var(--bg-card); border: 1px solid var(--border); border-radius: 1rem; transition: all 0.2s; }
    .compact-card:hover { border-color: var(--accent); box-shadow: 0 0 20px var(--accent-glow); }
    .compact-cat { font-size: 1.5rem; padding: 0.5rem; background: var(--bg-elevated); border-radius: 0.5rem; height: fit-content; }
    .compact-body { flex: 1; min-width: 0; }
    .compact-meta { display: flex; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 0.5rem; }
    .compact-title { font-size: 1rem; font-weight: 600; line-height: 1.4; margin-bottom: 0.5rem; }
    .compact-title a { color: var(--text); text-decoration: none; }
    .compact-title a:hover { color: var(--accent-light); }
    .compact-summary { font-size: 0.85rem; color: var(--text-secondary); line-height: 1.5; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
    .compact-img { width: 120px; height: 90px; object-fit: cover; border-radius: 0.5rem; flex-shrink: 0; }
    @media (max-width: 600px) { .compact-img { display: none; } }
    
    .other-section { background: var(--bg-card); border: 1px solid var(--border); border-radius: 1rem; padding: 1.5rem; }
    .other-section h2 { margin-bottom: 1.5rem; }
    .other-list { list-style: none; display: flex; flex-direction: column; gap: 0.75rem; }
    .other-item { display: flex; gap: 1rem; padding: 1rem; background: var(--bg-elevated); border: 1px solid var(--border); border-radius: 0.75rem; transition: all 0.2s; }
    .other-item:hover { border-color: var(--accent); }
    .other-num { display: flex; align-items: center; justify-content: center; width: 2rem; height: 2rem; background: var(--gradient); border-radius: 50%; font-size: 0.8rem; font-weight: 600; flex-shrink: 0; }
    .other-content { flex: 1; min-width: 0; }
    .other-title { font-weight: 500; margin-bottom: 0.25rem; }
    .other-title a { color: var(--text); text-decoration: none; }
    .other-title a:hover { color: var(--accent-light); }
    .other-meta { font-size: 0.75rem; color: var(--text-muted); }
    
    footer { padding: 2rem 0; border-top: 1px solid var(--border); margin-top: 2rem; }
    .footer-text { font-size: 0.75rem; color: var(--text-muted); }
    .footer-text strong { color: var(--text-secondary); }
    
    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-track { background: var(--bg); }
    ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 4px; }
  </style>
</head>
<body>
<header>
  <div class="wrap">
    <h1>📰 News Aggregator — {{ today }}</h1>
    <div class="meta-bar">
      <span class="pill">📅 {{ start }} → {{ today }}</span>
      <span class="pill">📰 {{ total_main }} main stories</span>
      <span class="pill">📋 {{ total_other }} other stories</span>
      <span class="pill">🌐 {{ unique_sources }} sources</span>
    </div>
    <nav>
      {% for cat_key, cat_data in categories.items() %}
      {% if sections[cat_key] %}
      <a href="#{{ cat_key }}">{{ cat_data.icon }} {{ cat_data.title }}</a>
      {% endif %}
      {% endfor %}
      <a href="#other">📋 Other Interesting</a>
    </nav>
  </div>
</header>

<main class="wrap">
  {# Large categories (3+ items) get full grid sections #}
  {% for cat_key, cat_data in categories.items() %}
  {% if sections[cat_key]|length >= 3 %}
  <section id="{{ cat_key }}">
    <h2>{{ cat_data.icon }} {{ cat_data.title }}</h2>
    <div class="grid">
      {% for article in sections[cat_key] %}
      <article>
        {% if article.image_url %}
        <img src="{{ article.image_url }}" alt="" loading="lazy" onerror="this.outerHTML='<div class=no-img>📰</div>'">
        {% else %}
        <div class="no-img">📰</div>
        {% endif %}
        <div class="card-body">
          <div class="card-meta">
            <span class="chip chip-date">{{ article.date_str }}</span>
            <span class="chip chip-source">{{ article.outlet }}</span>
            {% if article.reading_time %}
            <span class="chip chip-time">⏱️ {{ article.reading_time }} min</span>
            {% endif %}
            {% if article.priority == 'breaking' %}
            <span class="chip chip-breaking">🔴 Breaking</span>
            {% elif article.priority == 'important' %}
            <span class="chip chip-important">🟠 Important</span>
            {% endif %}
          </div>
          <h3 class="card-title"><a href="{{ article.url }}" target="_blank" rel="noopener">{{ article.title }}</a></h3>
          <p class="card-summary">{{ article.summary }}</p>
          <div class="card-footer">
            <a href="{{ article.url }}" class="card-link" target="_blank" rel="noopener">Read more →</a>
            {% if article.related_articles %}
            <div class="source-buttons">
              {% for outlet, url in article.related_articles[:2] %}
              <a href="{{ url }}" class="source-btn" target="_blank" rel="noopener" title="Also on {{ outlet }}">{{ outlet.split('.')[0]|title }}</a>
              {% endfor %}
            </div>
            {% endif %}
          </div>
        </div>
      </article>
      {% endfor %}
    </div>
  </section>
  {% endif %}
  {% endfor %}

  {# Small categories (1-2 items) grouped together in compact section #}
  {% set small_cats = [] %}
  {% for cat_key, cat_data in categories.items() %}
  {% if sections[cat_key]|length >= 1 and sections[cat_key]|length < 3 %}
  {% set _ = small_cats.append(cat_key) %}
  {% endif %}
  {% endfor %}
  
  {% if small_cats %}
  <section id="more-news" class="compact-section">
    <h2>📌 More Top Stories</h2>
    <div class="compact-grid">
      {% for cat_key in small_cats %}
      {% for article in sections[cat_key] %}
      <div class="compact-card">
        <div class="compact-cat">{{ categories[cat_key].icon }}</div>
        <div class="compact-body">
          <div class="compact-meta">
            <span class="chip chip-date">{{ article.date_str }}</span>
            <span class="chip chip-source">{{ article.outlet }}</span>
            {% if article.priority == 'breaking' %}
            <span class="chip chip-breaking">🔴</span>
            {% elif article.priority == 'important' %}
            <span class="chip chip-important">🟠</span>
            {% endif %}
          </div>
          <h3 class="compact-title"><a href="{{ article.url }}" target="_blank" rel="noopener">{{ article.title }}</a></h3>
          <p class="compact-summary">{{ article.summary }}</p>
        </div>
        {% if article.image_url %}
        <img src="{{ article.image_url }}" alt="" class="compact-img" loading="lazy" onerror="this.style.display='none'">
        {% endif %}
      </div>
      {% endfor %}
      {% endfor %}
    </div>
  </section>
  {% endif %}

  <section id="other" class="other-section">
    <h2>📋 Other Interesting News</h2>
    <ul class="other-list">
      {% for article in other_articles %}
      <li class="other-item">
        <span class="other-num">{{ loop.index }}</span>
        <div class="other-content">
          <div class="other-title"><a href="{{ article.url }}" target="_blank" rel="noopener">{{ article.title }}</a></div>
          <div class="other-meta">{{ article.date_str }} • {{ article.outlet }} • {{ categories[article.category].icon }} {{ categories[article.category].title }}</div>
        </div>
      </li>
      {% endfor %}
    </ul>
  </section>
</main>

<footer>
  <div class="wrap">
    <p class="footer-text"><strong>Method:</strong> Intelligent multi-factor scoring, NLP classification, source diversity enforcement.<br>
    <strong>Generated:</strong> {{ generated_at }}</p>
  </div>
</footer>
</body>
</html>''')
