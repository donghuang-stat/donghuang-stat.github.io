#!/usr/bin/env python3
"""Build, check, commit, and push this homepage using Python's standard library."""

import argparse
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath
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
    "content/profile.md", "content/education.md", "content/awards.md",
    "content/news.md", "content/recent-news.md", "content/selected-research.md",
    "content/research.md",
    "sources/about.md", "sources/publications.md", "sources/cv-2608.txt",
    ".nojekyll", "build.py", "content.py", "serve.py",
)
PUBLISH_FILES = SITE_FILES + ("publish.py",)
OPTIONAL_FILES = ("README.md", ".gitignore")
LEGACY_FILES = ("data/content.json", "data/cv.json")
ASSET_TYPES = {".pdf", ".jpg", ".jpeg", ".png", ".webp", ".svg", ".gif",
               ".css", ".js", ".ico", ".woff", ".woff2"}


class PublishError(Exception):
    pass


def run(*args, capture=False):
    result = subprocess.run(args, cwd=ROOT, text=True, capture_output=capture)
    if result.returncode:
        detail = (result.stderr or "").strip() if capture else "See the command output above."
        raise PublishError(f"{args[0]} failed: {detail}")
    # Preserve filename whitespace in NUL-separated Git output.
    return result.stdout.rstrip("\r\n") if capture else ""


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


def owned_path(name, root=ROOT):
    """Recognize website sources/assets without including unrelated local files."""
    if name in PUBLISH_FILES + OPTIONAL_FILES:
        return True
    if name in LEGACY_FILES:
        return not (root / name).exists()  # Only remove the retired JSON sources.
    path = PurePosixPath(name)
    if path.is_absolute() or any(part.startswith(".") for part in path.parts):
        return False
    if not path.parts:
        return False
    if path.parts[0] == "content":
        return path.suffix.lower() == ".md"
    return path.parts[0] in {"assets", "_pages"} and path.suffix.lower() in ASSET_TYPES


def reject_symlinks(path, root):
    """Git stores symlinks, not their target files, so they cannot be site assets."""
    if not path.resolve().is_relative_to(root.resolve()):
        raise PublishError(f"Website files must stay inside the website folder: {path.name}")
    for parent in (path, *path.parents):
        if parent == root:
            break
        if parent.is_symlink():
            raise PublishError(f"Website files and folders must not be symlinks: {parent.name}. "
                               "Copy the actual file into assets/ instead.")


def publish_paths(root=ROOT, tracked=None):
    root = root.resolve()
    if tracked is None:
        tracked = git("ls-files", "-z", capture=True).split("\0")
    paths = set(PUBLISH_FILES)
    paths.update(name for name in tracked if name and owned_path(name, root))
    for directory in ("content", "assets", "_pages"):
        folder = root / directory
        reject_symlinks(folder, root)
        for path in folder.rglob("*"):
            name = path.relative_to(root).as_posix()
            if path.is_symlink() and path.is_dir():
                reject_symlinks(path, root)
            if path.is_file() and owned_path(name, root):
                reject_symlinks(path, root)
                paths.add(name)
    paths.update(name for name in OPTIONAL_FILES if (root / name).is_file())
    for name in paths:
        reject_symlinks(root / name, root)
    return sorted(paths)


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
    root = root.resolve()
    # Check the exact filesystem discovery used by publishing, without reading Git.
    publishable = set(publish_paths(root, tracked=[]))
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
            reject_symlinks(target, root)
            target = target.resolve()
            if not target.is_relative_to(root.resolve()):
                raise PublishError(f"Link leaves the website folder: {reference}")
            if target.is_dir():
                target = target / "index.html"
            reject_symlinks(target, root)
            if not target.is_file():
                raise PublishError(f"Broken local link in {path.name}: {reference}")
            relative_target = target.relative_to(root.resolve()).as_posix()
            if relative_target not in publishable:
                raise PublishError(f"Local link in {path.name} points to a file that will not be published: {reference}. "
                                   "Put PDFs, images, and other supported website assets in assets/ and update the link.")
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
    staged = git("diff", "--cached", "--name-only", "--no-renames", "-z", capture=True).split("\0")
    unrelated = sorted(name for name in staged if name and not owned_path(name))
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
    parser.add_argument("--check", action="store_true", help="Build from Markdown and validate locally; do not fetch, stage, commit, or push")
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

    git("add", "--", *publish_paths())
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
