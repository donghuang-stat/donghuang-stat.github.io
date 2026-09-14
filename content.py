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
        if char == '\\' and text[i + 1:i + 2] == '\n':
            result.append('<br>\n')
            i += 2
            continue
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


def join_markdown_lines(lines):
    """Fold ordinary line wrapping; preserve an explicit Markdown backslash break."""
    result = ''
    for line in lines:
        if result:
            trailing_slashes = len(result) - len(result.rstrip('\\'))
            result += '\n' if trailing_slashes % 2 else ' '
        result += line.strip()
    return result


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
            result.append(f'<p{attrs}>' + inline(join_markdown_lines(lines)) + '</p>')
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
    metadata: dict

    def field(self, name):
        found = [section.body for section in self.sections if section.heading == name]
        if len(found) != 1:
            raise ContentError(f'{self.path}: include exactly one "## {name}" section.')
        return found[0]

    def only(self, names):
        unexpected = [s.heading for s in self.sections if s.heading not in names]
        if unexpected:
            raise ContentError(f'{self.path}: unrecognized section(s): {", ".join(unexpected)}. Check the heading spelling in README.md.')
        if len({s.heading for s in self.sections}) != len(self.sections):
            raise ContentError(f'{self.path}: duplicate section heading.')

    def meta(self, name, allow_empty=False):
        if name not in self.metadata or (not self.metadata[name] and not allow_empty):
            raise ContentError(f'{self.path}: add "{name}: value" between the two --- lines at the top.')
        return self.metadata[name]

    def only_meta(self, names):
        unexpected = set(self.metadata) - set(names)
        if unexpected:
            raise ContentError(f'{self.path}: unrecognized option(s): {", ".join(sorted(unexpected))}. Check README.md.')


def split_sections(text, level, context):
    """Read page ## sections or ### entries without relying on HTML markup."""
    intro, sections, pending, heading = '', [], [], None
    marker = '#' * level + ' '
    for line in text.splitlines():
        if line.startswith(marker):
            body = '\n'.join(pending).strip()
            if heading is None:
                intro = body
            else:
                sections.append(Section(heading, body))
            heading, pending = line[len(marker):].strip(), []
            if not heading:
                raise ContentError(f'{context}: a {marker.strip()} heading is empty.')
        elif re.match(r'^#{1,' + str(level - 1) + r'}\s', line):
            raise ContentError(f'{context}: entries here use {marker.strip()} headings.')
        else:
            pending.append(line)
    body = '\n'.join(pending).strip()
    if heading is None:
        intro = body
    else:
        sections.append(Section(heading, body))
    return intro, sections


def frontmatter(lines, path):
    """Read one-line key: value options, the flat subset of YAML used here."""
    metadata = {}
    if not lines or lines[0].strip() != '---':
        return metadata, lines
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == '---')
    except StopIteration as exc:
        raise ContentError(f'{path}: close the top options block with a second --- line.') from exc
    for line in lines[1:end]:
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        match = re.fullmatch(r'([a-z][a-z0-9_]*)\s*:\s*(.*)', line)
        if not match:
            raise ContentError(f'{path}: keep each top option on one line, e.g. recent_news_count: 3.')
        key, value = match.groups()
        value = value.strip()
        if key in metadata:
            raise ContentError(f'{path}: duplicate top option: {key}.')
        if value.startswith(('"', "'")):
            if len(value) < 2 or value[-1] != value[0]:
                raise ContentError(f'{path}: close the quotes around {key}, or omit the quotes.')
            if value[0] == '"':
                import json
                try:
                    value = json.loads(value)
                except ValueError as exc:
                    raise ContentError(f'{path}: invalid double-quoted value for {key}.') from exc
            else:
                value = value[1:-1].replace("''", "'")
        metadata[key] = value
    return metadata, lines[end + 1:]


def read_document(path):
    try:
        text = Path(path).read_text(encoding='utf-8-sig')
    except OSError as exc:
        raise ContentError(f'{path}: cannot read Markdown file ({exc}).') from exc
    text = re.sub(r'<!--.*?-->', '', text, flags=re.S).strip()
    metadata, lines = frontmatter(text.splitlines(), path)
    while lines and not lines[0].strip():
        lines.pop(0)
    if not lines or not lines[0].startswith('# ') or not lines[0][2:].strip():
        raise ContentError(f'{path}: add one page title, e.g. # Research, below the top options.')
    title = lines[0][2:].strip()
    intro, sections = split_sections('\n'.join(lines[1:]), 2, path)
    try:
        for value in [title, intro] + [section.body for section in sections]:
            blocks(value)
    except ContentError as exc:
        raise ContentError(f'{path}: {exc}') from exc
    return Document(Path(path), title, intro, sections, metadata)


def single_link(value, context):
    value = value.strip()
    found = _link_at(value, 0)
    if not found or found[0] or found[3] != len(value):
        raise ContentError(f'{context}: use a Markdown link, e.g. [All research →](research.html).')
    return {'label': found[1], 'url': found[2]}


def number(value, context, minimum=0):
    if not re.fullmatch(r'\d+', value) or not minimum <= int(value) <= 9999:
        raise ContentError(f'{context}: use a whole number from {minimum} to 9999.')
    return int(value)


def paper_record(section, group, doc, root):
    """Each ### paper is a compact, readable Markdown list in research.md."""
    context = f'{doc.path}, {section.heading}'
    fields, links, prose = {}, [], []
    allowed = {'ID', 'Authors', 'Year', 'Venue', 'Short venue', 'Author order',
               'Equal contribution', 'Note', 'Selected note'}
    last_field = None
    for line in section.body.splitlines():
        if not line.strip():
            prose.append('')
            last_field = None
            continue
        match = re.fullmatch(r'\s{0,3}[-*+]\s+(.+)', line)
        if match:
            value = match[1]
            last_field = None
            if value.startswith('['):
                links.append(public_link(single_link(value, context), doc.path, root))
                continue
            if ':' not in value:
                raise ContentError(f'{context}: use - Field: value or - [Link](URL); see the paper example in README.md.')
            key, value = value.split(':', 1)
            key, value = key.strip(), value.strip()
            if key not in allowed or key in fields:
                raise ContentError(f'{context}: unknown or duplicate paper field: {key}.')
            fields[key] = value
            last_field = key
        elif line.startswith(('  ', '\t')) and last_field:
            fields[last_field] = join_markdown_lines((fields[last_field], line))
        else:
            if line.startswith('#'):
                raise ContentError(f'{context}: each paper starts with ###, followed by its field list.')
            prose.append(line)
            last_field = None
    for key in ('ID', 'Authors', 'Year', 'Venue', 'Short venue', 'Author order'):
        if not fields.get(key):
            raise ContentError(f'{context}: add a nonempty - {key}: value line.')
    paper_id = fields['ID']
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*', paper_id):
        raise ContentError(f'{context}: ID uses letters, numbers, dots, dashes, or underscores.')
    authors = [name.strip() for name in fields['Authors'].split(';')]
    cofirst = [name.strip() for name in fields.get('Equal contribution', '').split(';') if name.strip()]
    if not all(authors) or len(set(authors)) != len(authors) or not set(cofirst) <= set(authors):
        raise ContentError(f'{context}: separate unique authors with semicolons; equal contributors must be in Authors.')
    if fields['Author order'] not in ('Alphabetical', 'Listed'):
        raise ContentError(f'{context}: Author order must be Alphabetical or Listed.')
    note = '\n\n'.join(value for value in (fields.get('Note', ''), '\n'.join(prose).strip()) if value)
    return {
        'id': paper_id, 'title': section.heading, 'authors': authors,
        'year': number(fields['Year'], context + ', Year', minimum=1), 'group': group,
        'venue': site_text(fields['Venue'], doc.path, root), 'short_venue': fields['Short venue'],
        'alphabetical': fields['Author order'] == 'Alphabetical', 'cofirst': cofirst,
        'links': links, 'note': site_text(note, doc.path, root),
        'selected_note': site_text(fields.get('Selected note', ''), doc.path, root),
    }


MONTHS = 'January February March April May June July August September October November December'.split()
HOME_OPTIONS = {'chinese_name', 'tagline', 'role', 'email', 'scholar', 'cv', 'photo',
                'photo_alt', 'photo_caption', 'description', 'selected_papers', 'recent_news_count'}


def load_site(root):
    root = Path(root)
    home = read_document(root / 'home.md')
    home.only({'Selected research', 'Recent news', 'Education', 'Selected awards'})
    home.only_meta(HOME_OPTIONS)
    profile = {key: home.meta(key) for key in ('chinese_name', 'tagline', 'role', 'description')}
    profile.update(name=home.title, bio=site_text(home.intro, home.path, root), caption=home.meta('photo_caption'),
                   photo={'label': home.meta('photo_alt'), 'url': site_url(safe_url(home.meta('photo')), home.path, root)})
    email = home.meta('email')
    if not re.fullmatch(r'[^\s@]+@[^\s@]+', email):
        raise ContentError(f'{home.path}: email should be the address alone, e.g. hd23@mails.tsinghua.edu.cn.')
    profile['email_url'] = 'mailto:' + email
    profile['scholar'] = site_url(safe_url(home.meta('scholar')), home.path, root)
    profile['cv'] = site_url(safe_url(home.meta('cv')), home.path, root)
    if urlsplit(profile['cv']).scheme or not urlsplit(profile['cv']).path.lower().endswith('.pdf'):
        raise ContentError(f'{home.path}: cv must point to a local PDF, e.g. assets/CV_2608.pdf.')
    profile['links'] = [{'label': label, 'url': profile[key]} for label, key in
                        [('Email', 'email_url'), ('Google Scholar', 'scholar'), ('CV (PDF)', 'cv')]]

    research = read_document(root / 'research.md')
    research.only({'Manuscripts', 'Publications'})
    research.only_meta({'author_order_note'})
    papers, research_intros = [], {}
    for heading, group in [('Manuscripts', 'manuscripts'), ('Publications', 'publications')]:
        intro, entries = split_sections(research.field(heading), 3, f'{research.path}, {heading}')
        research_intros[group] = site_text(intro, research.path, root)
        papers.extend(paper_record(entry, group, research, root) for entry in entries)
    all_ids = [paper['id'] for paper in papers]
    slugs = [paper_id.replace('.', '-') for paper_id in all_ids]
    if len(set(slugs)) != len(slugs):
        raise ContentError(f'{research.path}: every paper needs a unique ID (dots and dashes produce the same page anchor).')
    selected_ids = [value.strip() for value in home.meta('selected_papers', allow_empty=True).split(',') if value.strip()]
    if len(set(selected_ids)) != len(selected_ids) or not set(selected_ids) <= set(all_ids):
        raise ContentError(f'{home.path}: selected_papers must contain unique IDs that exist in research.md.')
    selected_parts = paragraphs(home.field('Selected research'))
    if not selected_parts:
        raise ContentError(f'{home.path}: Selected research starts with [All research →](research.html).')
    selected_link = public_link(single_link(selected_parts[0], home.path), home.path, root)
    recent_parts = paragraphs(home.field('Recent news'))
    if not recent_parts:
        raise ContentError(f'{home.path}: Recent news starts with [All news →](news.html).')
    recent_link = public_link(single_link(recent_parts[0], home.path), home.path, root)

    news_doc = read_document(root / 'news.md')
    news_doc.only_meta(set())
    news = []
    for section in news_doc.sections:
        try:
            month, year = section.heading.split()
            month_number = MONTHS.index(month) + 1
            if not re.fullmatch(r'\d{4}', year) or not section.body:
                raise ValueError()
        except ValueError as exc:
            raise ContentError(f'{news_doc.path}: use ## July 2026 followed by the news text.') from exc
        news.append({'date': f'{year}-{month_number:02}', 'label': section.heading,
                     'text': site_text(section.body, news_doc.path, root)})
    news.sort(key=lambda item: item['date'], reverse=True)

    education_intro, education_entries = split_sections(home.field('Education'), 3, f'{home.path}, Education')
    education = []
    for section in education_entries:
        fields = section.heading.split(' | ', 1)
        body = paragraphs(section.body)
        if len(fields) != 2 or not all(fields) or not body:
            raise ContentError(f'{home.path}: use ### Dates | Degree or role, then institution and details as separate paragraphs.')
        education.append({'dates': fields[0], 'title': fields[1],
                          'institution': site_text(body[0], home.path, root),
                          'detail': site_text('\n\n'.join(body[1:]), home.path, root)})
    awards_intro, awards_entries = split_sections(home.field('Selected awards'), 3, f'{home.path}, Selected awards')
    awards = [{'date': entry.heading, 'text': site_text(entry.body, home.path, root)} for entry in awards_entries]
    if any(not item['text'] for item in awards):
        raise ContentError(f'{home.path}: each ### award date needs an award description.')
    return {
        'profile': profile, 'papers': papers, 'selected_ids': selected_ids,
        'research_title': research.title, 'research_intro': site_text(research.intro, research.path, root),
        'research_note': site_text(research.meta('author_order_note', allow_empty=True), research.path, root),
        'research_intros': research_intros,
        'selected_title': 'Selected research', 'recent_title': 'Recent news',
        'selected_note': site_text('\n\n'.join(selected_parts[1:]), home.path, root),
        'recent_intro': site_text('\n\n'.join(recent_parts[1:]), home.path, root),
        'selected_link': selected_link, 'recent_link': recent_link,
        'recent_count': number(home.meta('recent_news_count'), f'{home.path}, recent_news_count'),
        'news': news, 'news_title': news_doc.title, 'news_intro': site_text(news_doc.intro, news_doc.path, root),
        'education': education, 'education_title': 'Education', 'education_intro': site_text(education_intro, home.path, root),
        'awards': awards, 'awards_title': 'Selected awards', 'awards_intro': site_text(awards_intro, home.path, root),
    }
