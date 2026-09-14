# Dong Huang's academic homepage

Personal website: <https://donghuang-stat.github.io/>

This branch contains the redesigned static website. The original Academic Pages site is preserved on `master`.

## Edit and preview

Update personal information, papers, news, education and awards in `data/content.json`. The CV PDF link is configured in `data/cv.json`; the PDF is stored in `assets/CV_2608.pdf`.

Rebuild the pages with Python 3 (standard library only):

```sh
python3 build.py
python3 serve.py --port 4173
```

Open <http://127.0.0.1:4173/> to preview. Edit `assets/style.css` for layout and colors, and `assets/site.js` for theme selection.

## Publish

Build, validate, commit and push local edits in one step:

```sh
python3 publish.py -m "Update homepage content"
```

Use `python3 publish.py --check` to rebuild and check links without committing or pushing. The publishing script stages only the listed website files and stops if the remote branch contains newer commits that have not been integrated locally.

Commit source and generated HTML changes to `homepage-redesign`. GitHub Pages publishes this branch from `/(root)` using **Deploy from a branch**. The `.nojekyll` file serves the site as static HTML.

- Home: `index.html`
- Research: `research.html`
- News: `news.html`
- CV: `assets/CV_2608.pdf`

The legacy `/publications/`, `/news/` and `/cv/` addresses redirect to their current destinations. Keep the existing `_pages/`, `images/` and `files/` directories: previously shared paper and poster links may still refer to those assets.

To restore the previous site, select `master` and `/(root)` in Settings → Pages.
