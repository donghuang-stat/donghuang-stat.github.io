#!/usr/bin/env python3
"""Build three static pages and compatibility redirects from home.md, research.md, and news.md."""
from collections import defaultdict
from html import escape
from pathlib import Path
import sys
from content import ContentError, blocks, inline, load_site, paragraphs

ROOT = Path(__file__).resolve().parent

def e(value):
    return escape(str(value), quote=True)

def link(label, url, class_name='', new_tab=False):
    attrs = f' class="{e(class_name)}"' if class_name else ''
    external = ' target="_blank" rel="noopener noreferrer"' if url.startswith('https://') or new_tab else ''
    return f'<a href="{e(url)}"{attrs}{external}>{e(label)}</a>'

def nav(current):
    items = [('home', 'Home', 'index.html'), ('research', 'Research', 'research.html'),
             ('news', 'News', 'news.html')]
    links = ''.join(f'<a href="{url}"' + (' aria-current="page"' if key == current else '') + f'>{label}</a>' for key, label, url in items)
    links += link('CV ↗', PROFILE['cv'], new_tab=True)
    return f'''<header class="site-header">
      <nav class="site-nav" aria-label="Main navigation">{links}</nav>
      <select class="theme-picker" data-theme-picker aria-label="Color theme">
        <option value="system">System</option><option value="light">Light</option><option value="dark">Dark</option>
      </select>
    </header>'''

def document(title, current, content):
    full_title = f'{PROFILE["name"]} · {PROFILE["chinese_name"]}' if current == 'home' else f'{title} — {PROFILE["name"]}'
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{e(PROFILE['description'])}">
  <title>{e(full_title)}</title>
  <link rel="icon" href="data:,">
  <link rel="stylesheet" href="assets/style.css">
  <script src="assets/site.js" defer></script>
</head>
<body>
  <a class="skip-link" href="#main">Skip to content</a>
  <div class="site-shell">
    {nav(current)}
    <main id="main">{content}</main>
    <footer class="site-footer"><span>© 2026 {e(PROFILE['name'])} · <span lang="zh">{e(PROFILE['chinese_name'])}</span></span>
      <div class="footer-links">{link('Email ↗', PROFILE['email_url'])}{link('Google Scholar ↗', PROFILE['scholar'])}</div>
    </footer>
  </div>
</body>
</html>
'''

def author_list(paper):
    cofirst = paper.get('cofirst', [])
    names = []
    for name in paper['authors']:
        rendered = e(name) + ('<sup>*</sup>' if name in cofirst else '')
        if name == PROFILE['name']:
            rendered = f'<span class="author-self">{rendered}</span>'
        names.append(rendered)
    return ', '.join(names) + (' <span>(α–β)</span>' if paper.get('alphabetical') else '')

def paper_item(paper, compact=False):
    target = paper['links'][0]['url'] if paper.get('links') else ''
    title = link(paper['title'], target) if target else e(paper['title'])
    short_venue = e(paper['short_venue'])
    extra = ''
    if not compact:
        extra += blocks(paper['venue'], 'paper-note')
    elif paper.get('selected_note'):
        extra += blocks(paper['selected_note'], 'paper-note')
    if paper.get('note') and not compact:
        extra += blocks(paper['note'], 'paper-note')
    links = ''.join(link(item['label'] + ' ↗', item['url']) for item in paper.get('links', []))
    return f'''<li class="paper" id="paper-{e(paper['id'].replace('.', '-'))}">
      <div class="paper-meta"><span>{paper['year']}</span><span>{short_venue}</span></div>
      <article><h3>{title}</h3><p class="authors">{author_list(paper)}</p>{extra}<div class="paper-links">{links}</div></article>
    </li>'''

def papers_html(papers, compact=False):
    return '<ul class="paper-list">' + ''.join(paper_item(p, compact) for p in papers) + '</ul>'

def news_html(items):
    rows = []
    for item in items:
        body = blocks(item['text'])
        if len(paragraphs(item['text'])) > 1:
            body = '<div class="markdown-body">' + body + '</div>'
        rows.append(f'<li class="news-item"><time datetime="{e(item["date"])}">{e(item["label"])}</time>{body}</li>')
    return '<ul class="news-list">' + ''.join(rows) + '</ul>'

def education_html():
    rows = []
    for item in DATA['education']:
        detail_html = blocks(item['detail'], 'education-detail')
        rows.append(f'''<div class="education-item"><div class="education-dates">{e(item['dates'])}</div>
          <div><h3 class="education-title">{e(item['title'])}</h3><p class="education-institution">{inline(item['institution'])}</p>{detail_html}</div></div>''')
    return '<div class="education-list">' + ''.join(rows) + '</div>'

def awards_html():
    rows = []
    for item in DATA['awards']:
        body = blocks(item['text'])
        if body.startswith('<p>') and body.count('<p>') == 1 and body.endswith('</p>'):
            body = '<span>' + body[3:-4] + '</span>'
        else:
            body = '<div class="markdown-body">' + body + '</div>'
        rows.append(f'<li class="award"><span class="award-date">{e(item["date"])}</span>{body}</li>')
    return '<ul class="award-list">' + ''.join(rows) + '</ul>'

def home_page():
    by_id = {p['id']: p for p in DATA['papers']}
    selected = [by_id[paper_id] for paper_id in DATA['selected_ids']]
    bio = blocks(PROFILE['bio'])
    selected_link = DATA['selected_link']
    recent_link = DATA['recent_link']
    return f'''
    <section class="hero" aria-labelledby="name">
      <div>
        <p class="eyebrow">{inline(PROFILE['tagline'])}</p>
        <h1 id="name">{e(PROFILE['name'])} <span class="chinese-name" lang="zh">{e(PROFILE['chinese_name'])}</span></h1>
        <p class="role">{inline(PROFILE['role'])}</p>
        <div class="bio">{bio}</div>
        <div class="hero-links">{''.join(link(item['label'] + ' ↗', item['url'], new_tab=item['label'] == 'CV (PDF)') for item in PROFILE['links'])}</div>
      </div>
      <figure class="portrait"><img src="{e(PROFILE['photo']['url'])}" width="4160" height="6240" alt="{e(PROFILE['photo']['label'])}" fetchpriority="high"><figcaption>{inline(PROFILE['caption'])}</figcaption></figure>
    </section>
    <section class="content-section" id="selected-research" aria-labelledby="selected-title">
      <div class="section-heading"><h2 id="selected-title">{e(DATA['selected_title'])}</h2>{link(selected_link['label'], selected_link['url'], 'section-link')}</div>
      {papers_html(selected, compact=True)}
      {blocks(DATA['selected_note'], 'alpha-note')}
    </section>
    <section class="content-section" id="recent-news" aria-labelledby="recent-title">
      <div class="section-heading"><h2 id="recent-title">{e(DATA['recent_title'])}</h2>{link(recent_link['label'], recent_link['url'], 'section-link')}</div>
      {blocks(DATA['recent_intro'])}{news_html(DATA['news'][:DATA['recent_count']])}
    </section>
    <section class="content-section" id="education" aria-labelledby="education-title">
      <div class="section-heading"><h2 id="education-title">{e(DATA['education_title'])}</h2></div>
      {blocks(DATA['education_intro'])}{education_html()}
    </section>
    <section class="content-section" id="selected-awards" aria-labelledby="awards-title">
      <div class="section-heading"><h2 id="awards-title">{e(DATA['awards_title'])}</h2></div>
      {blocks(DATA['awards_intro'])}{awards_html()}
    </section>'''

def research_page():
    manuscripts = [p for p in DATA['papers'] if p['group'] == 'manuscripts']
    publications = [p for p in DATA['papers'] if p['group'] == 'publications']
    return f'''<header class="page-intro"><p class="eyebrow">{e(PROFILE['name'])} · {e(DATA['research_title'])}</p><h1>{e(DATA['research_title'])}</h1>
      {blocks(DATA['research_intro'])}{blocks(DATA['research_note'], 'subtle')}
      <nav class="section-nav" aria-label="Research sections"><a href="#manuscripts">Manuscripts</a><a href="#publications">Publications</a>{link('Google Scholar ↗', PROFILE['scholar'])}</nav></header>
      <section class="content-section" id="manuscripts"><div class="status-heading"><h2>Manuscripts</h2><span class="count">{len(manuscripts)}</span></div>{blocks(DATA['research_intros']['manuscripts'])}{papers_html(manuscripts)}</section>
      <section class="content-section" id="publications"><div class="status-heading"><h2>Publications</h2><span class="count">{len(publications)}</span></div>{blocks(DATA['research_intros']['publications'])}{papers_html(publications)}</section>'''

def news_page():
    groups = defaultdict(list)
    for item in DATA['news']:
        groups[item['date'][:4]].append(item)
    sections = ''.join(f'<section class="news-year" id="news-{year}"><h2>{year}</h2>{news_html(items)}</section>' for year, items in groups.items())
    year_links = ''.join(f'<a href="#news-{year}">{year}</a>' for year in groups)
    return f'<header class="page-intro"><p class="eyebrow">{e(PROFILE["name"])} · {e(DATA["news_title"])}</p><h1>{e(DATA["news_title"])}</h1>{blocks(DATA["news_intro"])}<nav class="section-nav" aria-label="News by year">{year_links}</nav></header>{sections}'

def redirect_page(target, title):
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta http-equiv="refresh" content="0;url={e(target)}"><title>{e(title)}</title></head>
<body><p>{link(title, target)}</p></body></html>
'''

def main():
    global DATA, PROFILE
    DATA = load_site(ROOT)
    PROFILE = DATA['profile']
    # Render everything before writing so a malformed Markdown edit leaves the
    # last successful preview intact.
    rendered = {}
    for title, slug, path, fn in [('Home', 'home', 'index.html', home_page), ('Research', 'research', 'research.html', research_page), ('News', 'news', 'news.html', news_page)]:
        rendered[path] = document(title, slug, fn())
    for directory, target, title in [('publications', '../research.html', 'Research'), ('news', '../news.html', 'News'), ('cv', '../' + PROFILE['cv'], 'CV PDF')]:
        rendered[f'{directory}/index.html'] = redirect_page(target, f'{title} — {PROFILE["name"]}')
    for path, html in rendered.items():
        destination = ROOT / path
        destination.parent.mkdir(exist_ok=True)
        temporary = destination.with_suffix('.html.tmp')
        temporary.write_text(html, encoding='utf-8')
        temporary.replace(destination)
        print(f'Built {path}')

if __name__ == '__main__':
    try:
        main()
    except (ContentError, OSError) as exc:
        print(f'Build stopped: {exc}', file=sys.stderr)
        sys.exit(1)
