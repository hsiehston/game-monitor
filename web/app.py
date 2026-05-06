import os
import re
from collections import Counter

import psycopg2
import psycopg2.extras
from flask import Flask, jsonify, request, send_from_directory


app = Flask(__name__, static_folder="static")
DATABASE_URL = os.environ["DB_URL"]
KEYWORD_RE = re.compile(r"[\u4e00-\u9fff]{2,}|[A-Za-z][A-Za-z0-9_+-]{2,}")
STOPWORDS = {
    "https",
    "http",
    "www",
    "com",
    "forum",
    "gamer",
    "bahamut",
}


def query(sql: str, params: tuple = ()) -> list[dict]:
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            return [dict(row) for row in cur.fetchall()]


@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.get("/api/summary")
def summary():
    rows = query("""
        SELECT
            COUNT(*)::INT AS posts,
            COALESCE(SUM(comment_count), 0)::INT AS comments,
            COALESCE(MAX(gp_count), 0)::INT AS max_post_gp,
            COALESCE(MAX(comment_max_gp), 0)::INT AS max_comment_gp
        FROM (
            SELECT
                p.post_id,
                p.gp_count,
                COUNT(c.id)::INT AS comment_count,
                COALESCE(MAX(c.gp), 0)::INT AS comment_max_gp
            FROM posts p
            LEFT JOIN comments c ON c.post_id = p.post_id
            GROUP BY p.post_id, p.gp_count
        ) s
    """)
    return jsonify(rows[0] if rows else {})


@app.get("/api/posts")
def posts():
    min_gp = int(request.args.get("min_gp", 0))
    min_comments = int(request.args.get("min_comments", 0))
    limit = min(int(request.args.get("limit", 50)), 200)

    rows = query("""
        SELECT
            p.post_id,
            p.title,
            p.author,
            p.gp_count,
            p.created_at,
            p.fetched_at,
            COUNT(c.id)::INT AS comment_count,
            COALESCE(MAX(c.gp), 0)::INT AS top_comment_gp
        FROM posts p
        LEFT JOIN comments c ON c.post_id = p.post_id
        GROUP BY p.post_id, p.title, p.author, p.gp_count, p.created_at, p.fetched_at
        HAVING p.gp_count >= %s AND COUNT(c.id) >= %s
        ORDER BY p.gp_count DESC, comment_count DESC, p.fetched_at DESC
        LIMIT %s
    """, (min_gp, min_comments, limit))
    return jsonify(rows)


@app.get("/api/comments/top")
def top_comments():
    min_gp = int(request.args.get("min_gp", 1))
    limit = min(int(request.args.get("limit", 50)), 200)

    rows = query("""
        SELECT
            c.comment_id,
            c.post_id,
            p.title,
            c.floor,
            c.author,
            c.content,
            c.gp,
            c.bp,
            c.created_at
        FROM comments c
        JOIN posts p ON p.post_id = c.post_id
        WHERE c.gp >= %s
        ORDER BY c.gp DESC, c.created_at DESC NULLS LAST
        LIMIT %s
    """, (min_gp, limit))
    return jsonify(rows)


@app.get("/api/keywords")
def keywords():
    limit = min(int(request.args.get("limit", 30)), 100)
    rows = query("""
        SELECT title AS text FROM posts WHERE title IS NOT NULL
        UNION ALL
        SELECT content AS text FROM comments WHERE content IS NOT NULL
    """)

    counter = Counter()
    for row in rows:
        for token in KEYWORD_RE.findall(row["text"] or ""):
            normalized = token.lower()
            if normalized not in STOPWORDS:
                counter[normalized] += 1

    return jsonify([
        {"keyword": keyword, "count": count}
        for keyword, count in counter.most_common(limit)
    ])


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
