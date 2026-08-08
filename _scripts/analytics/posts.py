"""公開URLと `_posts/` の記事ファイルを対応づける。

サイトのURLは `/カテゴリ/2026/07/14/slug.html` の形なので、日付とスラッグだけで
記事ファイルを一意に引ける。カテゴリは日本語でURLエンコードされるが、対応づけには
使わないので触らない。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import unquote, urlsplit

import yaml

from config import REPO_ROOT

POSTS_DIR = REPO_ROOT / "_posts"

FILENAME_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})-(?P<slug>.+)\.md$")
URL_RE = re.compile(r"/(?P<y>\d{4})/(?P<m>\d{2})/(?P<d>\d{2})/(?P<slug>[^/]+)\.html$")


@dataclass
class Post:
    slug: str
    date: str  # YYYY-MM-DD
    lang: str  # "ja" or "en"
    title: str
    path: Path
    key: str = field(init=False)

    def __post_init__(self) -> None:
        self.key = f"{self.date}/{self.slug}"


def _front_matter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    try:
        data = yaml.safe_load(parts[1])
    except yaml.YAMLError:
        return {}
    return data if isinstance(data, dict) else {}


def load_posts() -> dict[str, Post]:
    """key（YYYY-MM-DD/slug）から Post を引く辞書を返す。"""
    posts: dict[str, Post] = {}
    for path in sorted(POSTS_DIR.glob("*.md")):
        matched = FILENAME_RE.match(path.name)
        if not matched:
            continue
        slug = matched.group("slug")
        date = f"{matched.group(1)}-{matched.group(2)}-{matched.group(3)}"
        front = _front_matter(path)
        lang = front.get("lang") or ("en" if slug.endswith("-en") else "ja")
        title = str(front.get("title") or slug)
        post = Post(slug=slug, date=date, lang=str(lang), title=title, path=path)
        posts[post.key] = post
    return posts


def url_to_key(url: str) -> str | None:
    """GA4のpagePathやSearch ConsoleのURLから記事キーを取り出す。

    記事以外（トップ、カテゴリ一覧、タグ一覧など）は None を返す。
    """
    path = unquote(urlsplit(url).path)
    matched = URL_RE.search(path)
    if not matched:
        return None
    return f"{matched['y']}-{matched['m']}-{matched['d']}/{matched['slug']}"
