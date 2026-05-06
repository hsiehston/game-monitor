import os

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


engine = create_engine(os.environ["DB_URL"])
Session = sessionmaker(bind=engine)


def save_post(post: dict):
    with Session() as session:
        session.execute(text("""
            INSERT INTO posts (platform, post_id, title, author, reply_count, created_at)
            VALUES (:platform, :post_id, :title, :author, :reply_count, :created_at)
            ON CONFLICT (post_id) DO UPDATE
                SET reply_count = EXCLUDED.reply_count
        """), post)
        session.commit()


def save_comments(comments: list[dict]):
    with Session() as session:
        for c in comments:
            session.execute(text("""
                INSERT INTO comments (post_id, floor, author, content, gp, bp, created_at)
                VALUES (:post_id, :floor, :author, :content, :gp, :bp, :created_at)
                ON CONFLICT DO NOTHING
            """), c)
        session.commit()
