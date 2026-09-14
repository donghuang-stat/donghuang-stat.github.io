#!/usr/bin/env python3
"""Build, check, commit, and push this homepage using Python's standard library."""

import argparse
from html.parser import HTMLParser
from pathlib import Path
import subprocess
import sys
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parent
BRANCH = "homepage-redesign"
REPOSITORY = "donghuang-stat/donghuang-stat.github.io"
SITE_HOST = "donghuang-stat.github.io"
SITE_FILES = (
    "index.html", "research.html", "news.html",
    "publications/index.html", "news/index.html", "cv/index.html",
    "assets/style.css", "assets/site.js", "assets/portrait.jpg", "assets/CV_2608.pdf",
    "_pages/2024_PKU_THU_poster.pdf", "_pages/2026_Peking_Tsinghua_Poster.pdf",
    "_pages/Bounded_degree_poster.pdf", "_pages/ICML2025_poster.pdf",
    "_pages/ICML2026poster.pdf",
    "data/content.json", "data/cv.json",
    "sources/about.md", "sources/publications.md", "sources/cv-2608.txt",
    ".nojekyll", "build.py", "serve.py",
)
PUBLISH_FILES = SITE_FILES + ("publish.py",)
OPTIONAL_FILES = ("README.md", ".gitignore")


class PublishError(Exception):
    pass


def run(*args, capture=False):
    result = subprocess.run(args, cwd=ROOT, text=True, capture_output=capture)
    if result.returncode:
        detail = (result.stderr or "").strip() if capture else "See the command output above."
        raise PublishError(f"{args[0]} failed: {detail}")
    return result.stdout.strip() if capture else ""


def git(*args, capture=False):
    return run("git", *args, capture=capture)


def valid_origin(url):
    return url in {
        f"https://github.com/{REPOSITORY}",
        f"https://github.com/{REPOSITORY}.git",
        f"git@github.com:{REPOSITORY}",
        f"git@github.com:{REPOSITORY}.git",
        f"ssh://git@github.com/{REPOSITORY}",
        f"ssh://git@github.com/{REPOSITORY}.git",
    }


class Page(HTMLParser):
    def __init__(self, path):
        super().__init__(convert_charrefs=True)
        self.path = path
        self.ids = set()
        self.references = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            if attrs["id"] in self.ids:
                raise PublishError(f"Duplicate HTML id in {self.path.name}: {attrs['id']}")
            self.ids.add(attrs["id"])
        for key in ("href", "src"):
            if attrs.get(key):
                self.references.append(attrs[key])
        if tag == "meta" and attrs.get("http-equiv", "").lower() == "refresh":
            content = attrs.get("content", "")
            if ";url=" in content.lower():
                self.references.append(content.split("=", 1)[1].strip().strip("\"'"))


def validate_site(root=ROOT):
    pages = {}
    for name in SITE_FILES:
        path = root / name
        if not path.is_file():
            raise PublishError(f"Required website file is missing: {name}")
        if path.suffix == ".html":
            page = Page(path)
            page.feed(path.read_text(encoding="utf-8"))
            pages[path.resolve()] = page

    for path, page in pages.items():
        for reference in page.references:
            url = urlsplit(reference)
            same_site = url.hostname == SITE_HOST and url.scheme in ("", "http", "https")
            if (url.scheme or url.netloc) and not same_site:
                continue
            if unquote(url.path).rstrip("/").split("/")[-1] == "cv.html":
                raise PublishError(f"Obsolete CV page link in {path.name}: {reference}")
            local_path = unquote(url.path)
            if same_site:
                target = root / local_path.lstrip("/")
            else:
                target = ((root / local_path.lstrip("/")) if local_path.startswith("/")
                          else path.parent / local_path) if local_path else path
            target = target.resolve()
            if not target.is_relative_to(root.resolve()):
                raise PublishError(f"Link leaves the website folder: {reference}")
            if target.is_dir():
                target = target / "index.html"
            if not target.is_file():
                raise PublishError(f"Broken local link in {path.name}: {reference}")
            if url.fragment and target.suffix == ".html":
                if target not in pages:
                    target_page = Page(target)
                    target_page.feed(target.read_text(encoding="utf-8"))
                else:
                    target_page = pages[target]
                if unquote(url.fragment) not in target_page.ids:
                    raise PublishError(f"Missing anchor in {path.name}: {reference}")
    print(f"Checked {len(pages)} HTML pages: local and same-site links, anchors, assets, and PDF links are valid.")


def verify_staging():
    allowed = set(PUBLISH_FILES + OPTIONAL_FILES)
    staged = git("diff", "--cached", "--name-only", "--no-renames", "-z", capture=True).split("\0")
    unrelated = sorted(name for name in staged if name and name not in allowed)
    if unrelated:
        raise PublishError("Unrelated files are already staged. Unstage or commit them separately before publishing: "
                           + ", ".join(unrelated))


def verify_checkout():
    top = Path(git("rev-parse", "--show-toplevel", capture=True)).resolve()
    if top != ROOT:
        raise PublishError("The page folder must be the Git repository root. No parent repository will be published.")
    if git("branch", "--show-current", capture=True) != BRANCH:
        raise PublishError(f"Switch to the {BRANCH} branch before publishing.")
    fetch_urls = git("remote", "get-url", "--all", "origin", capture=True).splitlines()
    push_urls = git("remote", "get-url", "--push", "--all", "origin", capture=True).splitlines()
    if len(fetch_urls) != 1 or len(push_urls) != 1 or not all(valid_origin(url) for url in fetch_urls + push_urls):
        raise PublishError(f"origin must fetch from and push to github.com/{REPOSITORY}, with no additional remote URLs.")
    verify_staging()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-m", "--message", default="Update personal homepage", help="Git commit message")
    parser.add_argument("--check", action="store_true", help="Build and validate locally; do not fetch, stage, commit, or push")
    args = parser.parse_args()
    if not args.message.strip():
        raise PublishError("The commit message cannot be empty.")

    if not args.check:
        verify_checkout()
    run(sys.executable, "build.py")
    validate_site()
    if args.check:
        print("Local checks passed. Nothing was committed or pushed.")
        return

    git("fetch", "--no-tags", "origin", BRANCH)
    ahead, behind = map(int, git("rev-list", "--left-right", "--count", "HEAD...FETCH_HEAD", capture=True).split())
    if behind:
        raise PublishError(f"The remote has {behind} commit(s) missing locally (local is ahead by {ahead}). "
                           "Review and integrate the remote changes first, then rerun. "
                           f"For a simple fast-forward after saving your edits: git pull --ff-only origin {BRANCH}")

    paths = list(PUBLISH_FILES)
    for name in OPTIONAL_FILES:
        if (ROOT / name).is_file() or git("ls-files", "--", name, capture=True):
            paths.append(name)
    git("add", "--", *paths)
    verify_staging()
    if git("diff", "--cached", "--name-only", capture=True):
        git("commit", "-m", args.message)
    else:
        print("No new website changes to commit; pushing any existing local commits.")
    git("push", "origin", f"HEAD:{BRANCH}")
    print("Push succeeded. GitHub Pages will publish the commit; check the Actions run for deployment status.")
    print("Website: https://donghuang-stat.github.io/")


if __name__ == "__main__":
    try:
        main()
    except (PublishError, OSError, ValueError) as exc:
        print(f"Publish stopped: {exc}", file=sys.stderr)
        sys.exit(1)
