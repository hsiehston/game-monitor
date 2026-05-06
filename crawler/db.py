import os

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


engine = create_engine(os.environ["DB_URL"])
Session = sessionmaker(bind=engine)


def _none_if_empty(d: dict, *keys) -> dict:
    """把指定欄位的空字串轉成 None"""
    for key in keys:
        if d.get(key) == "":
            d[key] = None
    return d


def save_post(post: dict):
    post = _none_if_empty(post, "created_at")
    with Session() as session:
        session.execute(text("""
            INSERT INTO posts (platform, post_id, title, author, gp_count, created_at)
            VALUES (:platform, :post_id, :title, :author, :gp_count, :created_at)
            ON CONFLICT (post_id) DO UPDATE
                SET title = EXCLUDED.title,
                    author = EXCLUDED.author,
                    gp_count = EXCLUDED.gp_count,
                    created_at = EXCLUDED.created_at,
                    fetched_at = NOW()
        """), post)
        session.commit()


def save_comments(comments: list[dict]):
    with Session() as session:
        for c in comments:
            c = _none_if_empty(c, "created_at")
            session.execute(text("""
                INSERT INTO comments (comment_id, post_id, floor, author, content, gp, bp, created_at)
                VALUES (:comment_id, :post_id, :floor, :author, :content, :gp, :bp, :created_at)
                ON CONFLICT (comment_id) DO UPDATE
                    SET author = EXCLUDED.author,
                        floor = EXCLUDED.floor,
                        content = EXCLUDED.content,
                        gp = EXCLUDED.gp,
                        bp = EXCLUDED.bp,
                        created_at = EXCLUDED.created_at,
                        fetched_at = NOW()
            """), c)
        session.commit()
