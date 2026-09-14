#!/usr/bin/env python3
"""Build three static pages and legacy URL redirects from official-source content."""
from collections import defaultdict
from html import escape
from html.parser import HTMLParser
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent
DATA = json.loads((ROOT / 'data/content.json').read_text())
CV = json.loads((ROOT / 'data/cv.json').read_text())
PROFILE = DATA['profile']

def e(value):
    return escape(str(value), quote=True)

def link(label, url, class_name='', new_tab=False):
    attrs = f' class="{e(class_name)}"' if class_name else ''
    external = ' target="_blank" rel="noopener noreferrer"' if url.startswith('https://') or new_tab else ''
    return f'<a href="{e(url)}"{attrs}{external}>{e(label)}</a>'

class RichText(HTMLParser):
    """Keep source prose and safe links, without inheriting site markup."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.open_link = False
    def handle_starttag(self, tag, attrs):
        if tag != 'a':
            return
        url = dict(attrs).get('href', '')
        if url.startswith(('https://', 'mailto:')):
            self.parts.append(f'<a href="{e(url)}" target="_blank" rel="noopener noreferrer">')
            self.open_link = True
    def handle_endtag(self, tag):
        if tag == 'a' and self.open_link:
            self.parts.append('</a>')
            self.open_link = False
    def handle_data(self, data):
        self.parts.append(e(data))

def rich(value):
    parser = RichText()
    parser.feed(value)
    return ''.join(parser.parts)

def nav(current):
    items = [('home', 'Home', 'index.html'), ('research', 'Research', 'research.html'),
             ('news', 'News', 'news.html')]
    links = ''.join(f'<a href="{url}"' + (' aria-current="page"' if key == current else '') + f'>{label}</a>' for key, label, url in items)
    links += link('CV ↗', CV['pdf']['path'], new_tab=True)
    return f'''<header class="site-header">
      <nav class="site-nav" aria-label="Main navigation">{links}</nav>
      <select class="theme-picker" data-theme-picker aria-label="Color theme">
        <option value="system">System</option><option value="light">Light</option><option value="dark">Dark</option>
      </select>
    </header>'''

def document(title, current, content):
    full_title = 'Dong Huang · 黄栋' if current == 'home' else f'{title} — Dong Huang'
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="Dong Huang, fourth-year Ph.D. student in Statistics at Tsinghua University. Research in statistics, probability and theoretical computer science.">
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
    <footer class="site-footer"><span>© 2026 Dong Huang · <span lang="zh">黄栋</span></span>
      <div class="footer-links">{link('Email ↗', 'mailto:' + PROFILE['email'])}{link('Google Scholar ↗', PROFILE['scholar'])}</div>
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
    if paper.get('group') == 'manuscripts':
        short_venue = 'Manuscript'
    elif paper['id'] == '2406.05428':
        short_venue = 'IEEE TIT / COLT'
    elif 'ICML' in paper['venue']:
        short_venue = 'ICML'
    elif 'SLADS' in paper['venue']:
        short_venue = 'SLADS'
    else:
        short_venue = 'Neurocomputing'
    extra = ''
    if not compact:
        extra += f'<p class="paper-note">{e(paper["venue"])}</p>'
    elif paper['id'] == '2406.05428':
        extra += '<p class="paper-note">IEEE Transactions on Information Theory, 2025 · COLT, 2024</p>'
    if paper.get('note') and not compact:
        extra += f'<p class="paper-note">{e(paper["note"])}</p>'
    links = ''.join(link(item['label'] + ' ↗', item['url']) for item in paper.get('links', []))
    return f'''<li class="paper" id="paper-{e(paper['id'].replace('.', '-'))}">
      <div class="paper-meta"><span>{paper['year']}</span><span>{short_venue}</span></div>
      <article><h3>{title}</h3><p class="authors">{author_list(paper)}</p>{extra}<div class="paper-links">{links}</div></article>
    </li>'''

def papers_html(papers, compact=False):
    return '<ul class="paper-list">' + ''.join(paper_item(p, compact) for p in papers) + '</ul>'

def news_html(items):
    return '<ul class="news-list">' + ''.join(f'<li class="news-item"><time datetime="{e(item["date"])}">{e(item["label"])}</time><p>{rich(item["html"])}</p></li>' for item in items) + '</ul>'

def education_html():
    rows = []
    for item in DATA['education']:
        detail = item.get('detail', '')
        detail_html = e(detail)
        for person, url in [('Shuangping Li', 'https://fifalsp.github.io/'), (PROFILE['advisor_name'], PROFILE['advisor_url'])]:
            if person in detail:
                detail_html = detail_html.replace(e(person), link(person, url))
        rows.append(f'''<div class="education-item"><div class="education-dates">{e(item['dates'])}</div>
          <div><h3 class="education-title">{e(item['title'])}</h3><p class="education-institution">{e(item['institution'])}</p><p class="education-detail">{detail_html}</p></div></div>''')
    return '<div class="education-list">' + ''.join(rows) + '</div>'

def awards_html():
    rows = ''.join(f'<li class="award"><span class="award-date">{e(item["date"])}</span><span>{link(item["text"], item["url"]) if item.get("url") else e(item["text"])}</span></li>' for item in DATA['awards'])
    return '<ul class="award-list">' + rows + '</ul>'

def home_page():
    by_id = {p['id']: p for p in DATA['papers']}
    selected = [by_id[paper_id] for paper_id in DATA['selected_ids']]
    bio = ''.join(f'<p>{rich(p)}</p>' for p in PROFILE['bio_html'])
    return f'''
    <section class="hero" aria-labelledby="name">
      <div>
        <p class="eyebrow">Statistics · Probability</p>
        <h1 id="name">Dong Huang <span class="chinese-name" lang="zh">黄栋</span></h1>
        <p class="role">Fourth-year Ph.D. student in Statistics · Tsinghua University</p>
        <div class="bio">{bio}</div>
        <div class="hero-links">{link('Email ↗', 'mailto:' + PROFILE['email'])}{link('Google Scholar ↗', PROFILE['scholar'])}{link('CV (PDF) ↗', CV['pdf']['path'], new_tab=True)}</div>
      </div>
      <figure class="portrait"><img src="assets/portrait.jpg" width="4160" height="6240" alt="Dong Huang standing on rocks beside the sea" fetchpriority="high"><figcaption>DONG HUANG / 黄栋</figcaption></figure>
    </section>
    <section class="content-section" id="selected-research" aria-labelledby="selected-title">
      <div class="section-heading"><h2 id="selected-title">Selected research</h2>{link('All research →', 'research.html', 'section-link')}</div>
      {papers_html(selected, compact=True)}
      <p class="alpha-note">α–β denotes alphabetical author order.</p>
    </section>
    <section class="content-section" id="recent-news" aria-labelledby="recent-title">
      <div class="section-heading"><h2 id="recent-title">Recent news</h2>{link('All news →', 'news.html', 'section-link')}</div>
      {news_html(DATA['news'][:3])}
    </section>
    <section class="content-section" id="education" aria-labelledby="education-title">
      <div class="section-heading"><h2 id="education-title">Education</h2></div>
      {education_html()}
    </section>
    <section class="content-section" id="selected-awards" aria-labelledby="awards-title">
      <div class="section-heading"><h2 id="awards-title">Selected awards</h2></div>
      {awards_html()}
    </section>'''

def research_page():
    by_id = {p['id']: p for p in DATA['papers']}
    manuscripts = [by_id[i] for i in DATA['selected_ids'] if by_id[i]['group'] == 'manuscripts']
    publications = [p for p in DATA['papers'] if p['group'] == 'publications']
    return f'''<header class="page-intro"><p class="eyebrow">Dong Huang · Research</p><h1>Research</h1>
      <p>{e(CV['research_interests'])}</p><p class="subtle">α–β denotes alphabetical author order.</p>
      <nav class="section-nav" aria-label="Research sections"><a href="#manuscripts">Manuscripts</a><a href="#publications">Publications</a>{link('Google Scholar ↗', PROFILE['scholar'])}</nav></header>
      <section class="content-section" id="manuscripts"><div class="status-heading"><h2>Manuscripts</h2><span class="count">{len(manuscripts)}</span></div>{papers_html(manuscripts)}</section>
      <section class="content-section" id="publications"><div class="status-heading"><h2>Publications</h2><span class="count">{len(publications)}</span></div>{papers_html(publications)}</section>'''

def news_page():
    groups = defaultdict(list)
    for item in DATA['news']:
        groups[item['date'][:4]].append(item)
    sections = ''.join(f'<section class="news-year" id="news-{year}"><h2>{year}</h2>{news_html(items)}</section>' for year, items in groups.items())
    year_links = ''.join(f'<a href="#news-{year}">{year}</a>' for year in groups)
    return f'<header class="page-intro"><p class="eyebrow">Dong Huang · News</p><h1>News</h1><nav class="section-nav" aria-label="News by year">{year_links}</nav></header>{sections}'

def redirect_page(target, title):
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta http-equiv="refresh" content="0;url={e(target)}"><title>{e(title)}</title></head>
<body><p>{link(title, target)}</p></body></html>
'''

def main():
    for title, slug, path, fn in [('Home', 'home', 'index.html', home_page), ('Research', 'research', 'research.html', research_page), ('News', 'news', 'news.html', news_page)]:
        (ROOT / path).write_text(document(title, slug, fn()), encoding='utf-8')
        print(f'Built {path}')
    for directory, target, title in [('publications', '../research.html', 'Research — Dong Huang'), ('news', '../news.html', 'News — Dong Huang'), ('cv', '../' + CV['pdf']['path'], 'CV PDF — Dong Huang')]:
        destination = ROOT / directory / 'index.html'
        destination.parent.mkdir(exist_ok=True)
        destination.write_text(redirect_page(target, title), encoding='utf-8')
        print(f'Built {directory}/index.html (redirect)')

if __name__ == '__main__':
    main()
