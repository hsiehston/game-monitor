import re
import time
from dataclasses import asdict, dataclass

import requests
from bs4 import BeautifulSoup


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}


@dataclass
class Post:
    platform: str
    post_id: str
    title: str
    author: str
    gp_count: int
    created_at: str


@dataclass
class Comment:
    comment_id: str
    post_id: str
    floor: int
    author: str
    content: str
    gp: int
    bp: int
    created_at: str


def parse_count(value: str) -> int:
    text = value.strip().replace(",", "")
    if not text:
        return 0
    match = re.search(r"-?\d+", text)
    if match:
        return int(match.group())
    try:
        return int(text)
    except ValueError:
        return 0


def get_post_list(bsn: str, page: int = 1) -> list[Post]:
    url = f"https://forum.gamer.com.tw/B.php?bsn={bsn}&page={page}"
    res = requests.get(url, headers=HEADERS, timeout=20)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")

    posts = []
    for row in soup.select("tr.b-list-item"):
        # 標題：置頂是 <a>，一般文章是 <p>
        title_el = row.select_one(".b-list__main__title")
        if not title_el:
            continue

        title = title_el.text.strip()

        # 連結：優先找 <a class="b-list__main__title">，找不到就找外層 <a>
        link_el = row.select_one("a.b-list__main__title")
        if not link_el:
            link_el = row.select_one("td.b-list__main > a")

        if not link_el:
            continue

        href = link_el.get("href", "")
        post_id = ""
        if "snA=" in href:
            post_id = href.split("snA=")[1].split("&")[0]

        if not post_id:
            continue

        # 列表頁左側 GP 數
        gp_el = row.select_one(".b-list__summary__gp")
        gp_count = parse_count(gp_el.text) if gp_el else 0

        author_el = row.select_one(".b-list__count__user a")
        time_el = row.select_one(".b-list__time")

        posts.append(Post(
            platform="bahamut",
            post_id=post_id,
            title=title,
            author=author_el.text.strip() if author_el else "",
            gp_count=gp_count,
            created_at=time_el.get("title", "") if time_el else "",
        ))

    return posts


def get_comments(bsn: str, post_id: str) -> list[Comment]:
    """抓單篇文章的所有留言（含分頁）"""
    comments = []
    page = 1

    while True:
        url = f"https://forum.gamer.com.tw/C.php?bsn={bsn}&snA={post_id}&page={page}"
        res = requests.get(url, headers=HEADERS, timeout=20)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")

        rows = soup.select(".c-reply__item")
        if not rows:
            break

        for row in rows:
            comment_id = row.get("id", "").replace("Commendcontent_", "")
            if not comment_id:
                continue

            floor_el = row.select_one("[name='comment_floor']")
            author_el = row.select_one(".reply-content__user")
            content_el = row.select_one(".comment_content")
            time_el = row.select_one("[data-tippy-content^='留言時間']")
            gp_el = row.select_one(".gp-count")
            bp_el = row.select_one(".bp-count")
            floor = parse_count(floor_el.text) if floor_el else 0
            if floor == 0:
                floor = len(comments) + 1
            created_at = ""
            if time_el:
                created_at = time_el.get("data-tippy-content", "").replace("留言時間", "").strip()

            comments.append(Comment(
                comment_id=comment_id,
                post_id=post_id,
                floor=floor,
                author=author_el.text.strip() if author_el else "",
                content=content_el.get_text(strip=True) if content_el else "",
                gp=parse_count(gp_el.get("data-gp", gp_el.text)) if gp_el else 0,
                bp=parse_count(bp_el.get("data-bp", bp_el.text)) if bp_el else 0,
                created_at=created_at,
            ))

        next_btn = soup.select_one("a.next-page")
        if not next_btn:
            break

        page += 1
        time.sleep(1.2)

    return comments


def crawl_board(bsn: str, max_pages: int = 5) -> tuple[list[dict], list[dict]]:
    """主流程：抓指定哈啦板的前 N 頁文章與所有留言"""
    all_posts = []
    all_comments = []

    for page in range(1, max_pages + 1):
        print(f"抓取第 {page} 頁文章列表...")
        posts = get_post_list(bsn, page)

        for post in posts:
            print(f"  [GP：{post.gp_count}] {post.title}")
            comments = get_comments(bsn, post.post_id)
            all_posts.append(asdict(post))
            all_comments.extend(asdict(comment) for comment in comments)
            time.sleep(1.5)

        time.sleep(2)

    return all_posts, all_comments


if __name__ == "__main__":
    crawl_board(bsn="17608", max_pages=3)
