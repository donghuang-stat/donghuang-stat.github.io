# Dong Huang's personal homepage

Source for [donghuang-stat.github.io](https://donghuang-stat.github.io/), with Home, Research, News, and a direct CV PDF link. The site uses static HTML, CSS, JavaScript, and a Python standard-library generator. Python 3.9 or newer is sufficient; no package installation is required.

## Preview locally

Run these commands from this repository's root directory:

```sh
python3 publish.py --check
python3 serve.py
```

Open [http://127.0.0.1:4173/](http://127.0.0.1:4173/). Use `python3 serve.py --port 4174` if port 4173 is already in use. Press Control-C to stop the server.

`--check` rebuilds the HTML and validates required files, local links, links to this site's domain, and HTML anchors. It does not fetch, commit, or push. After editing content, rerun it and refresh the preview.

## Update content

| Change | Edit |
| --- | --- |
| Biography, contact details, papers, selected research, news, education, awards | `data/content.json` |
| CV PDF path and metadata; research interests used on Research | `data/cv.json` |
| Downloadable CV | `assets/CV_2608.pdf` |
| Home photograph | `assets/portrait.jpg` |
| Page structure and generated navigation | `build.py` |
| Typography, spacing, responsive layout, colors | `assets/style.css` |
| Theme selection behavior | `assets/site.js` |

Edit the data files instead of generated `index.html`, `research.html`, or `news.html`; rebuilding replaces those HTML files. Paper records are shared between Home and Research, and `selected_ids` controls the selection and order on Home. News entries retain the author's original first-person wording.

The CV PDF is an independent document: changing the website data does not modify its contents. To update it without changing links, replace `assets/CV_2608.pdf` and update its metadata in `data/cv.json`. If you choose a new filename, also update the PDF entry in `SITE_FILES` in `publish.py`.

The `sources/` directory retains the original public biography, publication list, and extracted CV text for reference. These are historical snapshots, not the current content source for the generated pages.

## Publish an update

The publishing branch is **`homepage-redesign`**. GitHub Pages publishes its **`/(root)`** directory. The `master` branch retains the old website as a backup.

After checking the local preview, run:

```sh
python3 publish.py -m "Update research and news"
```

The script checks the repository and branch, rebuilds and validates the site, fetches the publishing branch, commits changed website files, and pushes to `origin/homepage-redesign`. It requires Git and working GitHub write access. If the remote contains commits missing locally, or unrelated changes are already staged, it stops with an explanation; it never force-pushes.

After a successful push, check [GitHub Actions](https://github.com/donghuang-stat/donghuang-stat.github.io/actions) for the Pages deployment, then refresh the [live website](https://donghuang-stat.github.io/). A push finishes before the website deployment does.

For a fresh checkout on another computer:

```sh
git clone --branch homepage-redesign https://github.com/donghuang-stat/donghuang-stat.github.io.git
cd donghuang-stat.github.io
python3 publish.py --check
```

Configure GitHub write access on that computer before publishing. The publishing script accepts the repository's HTTPS or SSH origin URL.

## Files kept for existing links

The original Jekyll template, example content, dependencies, and unused media have been removed. `.nojekyll` tells GitHub Pages to serve the generated static files directly.

Five research posters remain at their original paths because the current site links to them:

```text
_pages/2024_PKU_THU_poster.pdf
_pages/2026_Peking_Tsinghua_Poster.pdf
_pages/Bounded_degree_poster.pdf
_pages/ICML2025_poster.pdf
_pages/ICML2026poster.pdf
```

Small generated redirects preserve `/publications/`, `/news/`, and `/cv/`. The CV redirect opens the PDF; there is no separate CV content page. When adding a new local asset or PDF, add its path to `SITE_FILES` in `publish.py` so that validation and publishing include it.

To restore the old site, select `master` and `/(root)` in the repository's [Pages settings](https://github.com/donghuang-stat/donghuang-stat.github.io/settings/pages). Keep the old branch unchanged if this rollback option is needed.
