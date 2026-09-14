"""Read the site's editable Markdown; no third-party packages are needed.

The small Markdown subset is deliberate: paragraphs, lists, links, images,
strong/emphasis, inline code, and backslash escapes. Section headings also
provide the structure used by the page templates. Raw HTML is escaped.
"""
from dataclasses import dataclass
from html import escape
from pathlib import Path
from urllib.parse import urlsplit, unquote, quote, urlunsplit
import re


class ContentError(ValueError):
    """A content file needs an edit before the website can be built."""


def safe_url(value):
    if not value or any(c.isspace() or ord(c) < 32 for c in value):
        raise ContentError(f'Invalid link URL: {value!r}; encode spaces as %20.')
    if '\\' in value or value.startswith('//') or urlsplit(value).scheme.lower() not in ('', 'http', 'https', 'mailto'):
        raise ContentError(f'Unsupported link URL: {value!r}. Use https://, mailto:, or a local file path.')
    return value


def site_url(value, source, root):
    """Resolve normal Markdown-relative links into root-page-relative URLs."""
    url = urlsplit(value)
    if url.scheme or url.netloc or not url.path:
        return value
    path = (root / unquote(url.path).lstrip('/')) if url.path.startswith('/') else source.parent / unquote(url.path)
    path = path.resolve()
    if not path.is_relative_to(root.resolve()):
        raise ContentError(f'{source}: link leaves the website folder: {value}')
    relative = path.relative_to(root.resolve()).as_posix()
    if url.path.endswith('/') and relative != '.':
        relative += '/'
    return urlunsplit(('', '', quote(relative, safe='/'), url.query, url.fragment))


def site_text(text, source, root):
    result, i = [], 0
    while i < len(text):
        if text[i] == '\\' and i + 1 < len(text):
            result.append(text[i:i + 2])
            i += 2
            continue
        if text[i] == '`':
            end = text.find('`', i + 1)
            if end >= 0:
                result.append(text[i:end + 1])
                i = end + 1
                continue
        found = _link_at(text, i) if text[i] == '[' or text.startswith('![', i) else None
        if found:
            image, label, url, i = found
            result.append(('!' if image else '') + f'[{label}]({site_url(url, source, root)})')
        else:
            result.append(text[i])
            i += 1
    return ''.join(result)


def public_link(item, source, root):
    return dict(item, url=site_url(item['url'], source, root))


def _closing(text, start, opening, closing):
    depth = 1
    i = start
    while i < len(text):
        if text[i] == '\\':
            i += 2
            continue
        if text[i] == opening:
            depth += 1
        elif text[i] == closing:
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return -1


def _link_at(text, start):
    image = text.startswith('![', start)
    bracket = start + 1 if image else start
    if bracket >= len(text) or text[bracket] != '[':
        return None
    end_label = _closing(text, bracket + 1, '[', ']')
    if end_label < 0 or text[end_label + 1:end_label + 2] != '(':
        return None
    end_url = _closing(text, end_label + 2, '(', ')')
    if end_url < 0:
        raise ContentError('A Markdown link is missing its closing ).')
    url = text[end_label + 2:end_url].strip()
    if url.startswith('<') and url.endswith('>'):
        url = url[1:-1]
    return image, text[bracket + 1:end_label], safe_url(url), end_url + 1


def inline(text, allow_links=True):
    """Render inline Markdown, escaping text and attributes by default."""
    result = []
    i = 0
    while i < len(text):
        char = text[i]
        if char == '\\' and i + 1 < len(text) and text[i + 1] in r'\`*_{}[]()#+-.!<>|':
            result.append(escape(text[i + 1], quote=True))
            i += 2
            continue
        if char == '`':
            end = text.find('`', i + 1)
            if end >= 0:
                result.append('<code>' + escape(text[i + 1:end], quote=True) + '</code>')
                i = end + 1
                continue
        if allow_links and (char == '[' or text.startswith('![', i)):
            found = _link_at(text, i)
            if found:
                image, label, url, i = found
                if image:
                    result.append(f'<img src="{escape(url, quote=True)}" alt="{escape(label, quote=True)}">')
                else:
                    external = ' target="_blank" rel="noopener noreferrer"' if url.startswith(('https://', 'http://', 'mailto:')) else ''
                    result.append(f'<a href="{escape(url, quote=True)}"{external}>{inline(label, allow_links=False)}</a>')
                continue
        if char in '*_':
            marker = char * (2 if text.startswith(char * 2, i) else 1)
            # Underscores within words (or file names) are plain text.
            boundary = char != '_' or i == 0 or not text[i - 1].isalnum()
            end = text.find(marker, i + len(marker))
            if boundary and end > i + len(marker) and not text[i + len(marker)].isspace() and not text[end - 1].isspace():
                tag = 'strong' if len(marker) == 2 else 'em'
                result.append(f'<{tag}>{inline(text[i + len(marker):end], allow_links)}</{tag}>')
                i = end + len(marker)
                continue
        result.append(escape(char, quote=True))
        i += 1
    return ''.join(result)


def paragraphs(text):
    return [part.strip() for part in re.split(r'\n\s*\n', text.strip()) if part.strip()]


def blocks(text, paragraph_class=''):
    result = []
    attrs = f' class="{escape(paragraph_class, quote=True)}"' if paragraph_class else ''
    for paragraph in paragraphs(text):
        lines = paragraph.splitlines()
        bullets = [re.fullmatch(r'\s*[-*+]\s+(.+)', line) for line in lines]
        numbers = [re.fullmatch(r'\s*\d+[.)]\s+(.+)', line) for line in lines]
        if all(bullets) or all(numbers):
            tag, matches = ('ul', bullets) if all(bullets) else ('ol', numbers)
            result.append(f'<{tag}>' + ''.join(f'<li>{inline(m[1])}</li>' for m in matches) + f'</{tag}>')
        else:
            result.append(f'<p{attrs}>' + inline(' '.join(line.strip() for line in lines)) + '</p>')
    return ''.join(result)


@dataclass
class Section:
    heading: str
    body: str


@dataclass
class Document:
    path: Path
    title: str
    intro: str
    sections: list

    def field(self, name, optional=False, allow_empty=False):
        found = [section.body for section in self.sections if section.heading == name]
        if not found and optional:
            return ''
        if len(found) != 1 or (not found[0].strip() and not (allow_empty or optional)):
            raise ContentError(f'{self.path}: include exactly one nonempty "## {name}" section.')
        return found[0]

    def only(self, names, allow_intro=True):
        if self.intro and not allow_intro:
            raise ContentError(f'{self.path}: put content below its ## field heading, not directly below the # title.')
        unexpected = [s.heading for s in self.sections if s.heading not in names]
        if unexpected:
            raise ContentError(f'{self.path}: unrecognized section(s): {", ".join(unexpected)}. Check the heading spelling in README.md.')
        if len({s.heading for s in self.sections}) != len(self.sections):
            raise ContentError(f'{self.path}: duplicate section heading.')


def read_document(path):
    try:
        text = Path(path).read_text(encoding='utf-8-sig')
    except OSError as exc:
        raise ContentError(f'{path}: cannot read Markdown file ({exc}).') from exc
    text = re.sub(r'<!--.*?-->', '', text, flags=re.S).strip()
    lines = text.splitlines()
    if not lines or not lines[0].startswith('# '):
        raise ContentError(f'{path}: start with a title, e.g. # Education.')
    title = lines[0][2:].strip()
    if not title:
        raise ContentError(f'{path}: the # title must not be empty.')
    intro, sections, pending = '', [], []
    heading = None
    for line in lines[1:]:
        if line.startswith('# '):
            raise ContentError(f'{path}: use one # title; entries and fields start with ##.')
        if line.startswith('## '):
            body = '\n'.join(pending).strip()
            if heading is None:
                intro = body
            else:
                sections.append(Section(heading, body))
            heading, pending = line[3:].strip(), []
        else:
            pending.append(line)
    body = '\n'.join(pending).strip()
    if heading is None:
        intro = body
    else:
        sections.append(Section(heading, body))
    # Validate Markdown links before templates start generating files.
    try:
        for value in [title, intro] + [s.body for s in sections]:
            blocks(value)
    except ContentError as exc:
        raise ContentError(f'{path}: {exc}') from exc
    return Document(Path(path), title, intro, sections)


def scalar(doc, name):
    value = doc.field(name)
    if '\n' in value:
        raise ContentError(f'{doc.path}: "## {name}" must contain one line.')
    return value


def bullet_values(value, context):
    items = []
    for line in value.splitlines():
        if not line.strip():
            continue
        match = re.fullmatch(r'\s*[-*+]\s+(.+)', line)
        if not match:
            raise ContentError(f'{context}: write one bullet per item, e.g. - Dong Huang.')
        items.append(match[1])
    if not items:
        raise ContentError(f'{context}: the list is empty.')
    return items


def single_link(value, context, image=False):
    found = _link_at(value.strip(), 0)
    if not found or found[0] != image or found[3] != len(value.strip()):
        example = '![Description](assets/portrait.jpg)' if image else '[Label](https://example.com)'
        raise ContentError(f'{context}: use a Markdown {"image" if image else "link"}, e.g. {example}.')
    return {'label': found[1], 'url': found[2]}


def link_list(doc, name, allow_empty=False):
    value = doc.field(name, allow_empty=allow_empty)
    if not value and allow_empty:
        return []
    return [single_link(item, f'{doc.path}, {name}') for item in bullet_values(value, f'{doc.path}, {name}')]


def integer(doc, name):
    value = scalar(doc, name)
    if not value.isdigit() or not 1 <= int(value) <= 9999:
        raise ContentError(f'{doc.path}: "## {name}" needs a positive whole number.')
    return int(value)


def _paper(path, root):
    doc = read_document(path)
    doc.only({'Authors', 'Year', 'Venue', 'Short venue', 'Author order', 'Equal contribution', 'Links', 'Note', 'Selected note'}, allow_intro=False)
    order = scalar(doc, 'Author order')
    if order not in ('Alphabetical', 'Listed'):
        raise ContentError(f'{path}: Author order must be Alphabetical or Listed.')
    authors = bullet_values(doc.field('Authors'), f'{path}, Authors')
    cofirst = bullet_values(doc.field('Equal contribution'), f'{path}, Equal contribution') if doc.field('Equal contribution', optional=True) else []
    if len(set(authors)) != len(authors) or not set(cofirst) <= set(authors):
        raise ContentError(f'{path}: authors must be unique; equal contributors must be in Authors.')
    return {
        'id': path.stem, 'title': doc.title, 'authors': authors, 'year': integer(doc, 'Year'),
        'venue': site_text(doc.field('Venue'), path, root), 'short_venue': scalar(doc, 'Short venue'),
        'alphabetical': order == 'Alphabetical', 'cofirst': cofirst,
        'links': [public_link(item, path, root) for item in link_list(doc, 'Links', allow_empty=True)],
        'note': site_text(doc.field('Note', optional=True), path, root),
        'selected_note': site_text(doc.field('Selected note', optional=True), path, root),
    }


def paper_references(doc, name, root):
    ids = []
    for item in link_list(doc, name, allow_empty=True):
        path = (doc.path.parent / unquote(item['url'])).resolve()
        if path.parent != (root / 'content/papers').resolve() or path.suffix != '.md' or not path.is_file():
            raise ContentError(f'{doc.path}: {item["url"]} must point to an existing content/papers/*.md file.')
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*', path.stem):
            raise ContentError(f'{doc.path}: use letters, numbers, dots, dashes, or underscores in paper filenames.')
        ids.append(path.stem)
    if len(set(ids)) != len(ids):
        raise ContentError(f'{doc.path}: duplicate paper in {name}.')
    return ids


MONTHS = 'January February March April May June July August September October November December'.split()


def load_site(root):
    root = Path(root)
    folder = root / 'content'
    profile_doc = read_document(folder / 'profile.md')
    profile_doc.only({'Chinese name', 'Tagline', 'Role', 'Biography', 'Links', 'Photo', 'Photo caption', 'Description'}, allow_intro=False)
    profile = {key: scalar(profile_doc, name) for key, name in (
        ('chinese_name', 'Chinese name'), ('tagline', 'Tagline'), ('role', 'Role'),
        ('caption', 'Photo caption'), ('description', 'Description'))}
    profile.update(name=profile_doc.title, bio=site_text(profile_doc.field('Biography'), profile_doc.path, root),
                   links=[public_link(item, profile_doc.path, root) for item in link_list(profile_doc, 'Links')],
                   photo=public_link(single_link(profile_doc.field('Photo'), profile_doc.path, image=True), profile_doc.path, root))
    for label, key in [('Email', 'email_url'), ('Google Scholar', 'scholar'), ('CV (PDF)', 'cv')]:
        values = [item['url'] for item in profile['links'] if item['label'] == label]
        if len(values) != 1:
            raise ContentError(f'{profile_doc.path}: Links must include exactly one [{label}](...).')
        profile[key] = values[0]
    if urlsplit(profile['cv']).scheme or urlsplit(profile['cv']).netloc or not profile['cv'].endswith('.pdf') or profile['cv'].startswith('/'):
        raise ContentError(f'{profile_doc.path}: CV (PDF) must use a local PDF path, e.g. ../assets/CV_2608.pdf.')

    research = read_document(folder / 'research.md')
    research.only({'Note', 'Manuscripts', 'Publications'})
    groups = {group: paper_references(research, heading, root) for group, heading in [('manuscripts', 'Manuscripts'), ('publications', 'Publications')]}
    all_ids = [paper_id for items in groups.values() for paper_id in items]
    if len(set(all_ids)) != len(all_ids):
        raise ContentError(f'{research.path}: each paper belongs to exactly one research section.')
    unused = {p.stem for p in (folder / 'papers').glob('*.md')} - set(all_ids)
    if unused:
        raise ContentError(f'{research.path}: add these paper files to Manuscripts or Publications: {", ".join(sorted(unused))}.')
    papers = []
    for group, ids in groups.items():
        for paper_id in ids:
            paper = _paper(folder / 'papers' / (paper_id + '.md'), root)
            paper['group'] = group
            papers.append(paper)
    selected = read_document(folder / 'selected-research.md')
    selected.only({'Papers', 'Note'})
    selected_ids = paper_references(selected, 'Papers', root)
    if not set(selected_ids) <= set(all_ids):
        raise ContentError(f'{selected.path}: selected papers must also be listed in research.md.')
    research.intro = site_text(research.intro, research.path, root)
    for doc in (research, selected):
        for section in doc.sections:
            if section.heading == 'Note':
                section.body = site_text(section.body, doc.path, root)

    news_doc = read_document(folder / 'news.md')
    news = []
    for section in news_doc.sections:
        try:
            month, year = section.heading.split()
            month_number = MONTHS.index(month) + 1
            if not re.fullmatch(r'\d{4}', year) or not section.body:
                raise ValueError()
        except ValueError as exc:
            raise ContentError(f'{news_doc.path}: use a month/year heading (## July 2026) followed by the news text.') from exc
        news.append({'date': f'{year}-{month_number:02}', 'label': section.heading, 'text': site_text(section.body, news_doc.path, root)})
    news.sort(key=lambda item: item['date'], reverse=True)
    recent = read_document(folder / 'recent-news.md')
    recent.only({'Display count'})

    education_doc = read_document(folder / 'education.md')
    education = []
    for section in education_doc.sections:
        fields = section.heading.split(' | ', 1)
        body = paragraphs(section.body)
        if len(fields) != 2 or not body:
            raise ContentError(f'{education_doc.path}: use ## Dates | Degree or role, then institution and details as separate paragraphs.')
        education.append({'dates': fields[0], 'title': fields[1], 'institution': site_text(body[0], education_doc.path, root), 'detail': site_text('\n\n'.join(body[1:]), education_doc.path, root)})
    awards_doc = read_document(folder / 'awards.md')
    awards = [{'date': section.heading, 'text': site_text(section.body, awards_doc.path, root)} for section in awards_doc.sections]
    if any(not item['text'] for item in awards):
        raise ContentError(f'{awards_doc.path}: each date heading needs an award description.')
    return {
        'profile': profile, 'papers': papers, 'selected_ids': selected_ids,
        'research': research, 'selected': selected, 'recent': recent,
        'selected_link': public_link(single_link(selected.intro, selected.path), selected.path, root),
        'recent_link': public_link(single_link(recent.intro, recent.path), recent.path, root),
        'recent_count': integer(recent, 'Display count'),
        'news': news, 'news_title': news_doc.title,
        'news_intro': site_text(news_doc.intro, news_doc.path, root),
        'education': education, 'education_title': education_doc.title,
        'education_intro': site_text(education_doc.intro, education_doc.path, root),
        'awards': awards, 'awards_title': awards_doc.title,
        'awards_intro': site_text(awards_doc.intro, awards_doc.path, root),
    }
