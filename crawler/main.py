from datetime import datetime, timezone

from db import get_connection


def main() -> None:
    checked_at = datetime.now(timezone.utc)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO crawl_runs (source, status, checked_at)
                VALUES (%s, %s, %s)
                """,
                ("placeholder", "ok", checked_at),
            )
        conn.commit()

    print(f"Crawler run recorded at {checked_at.isoformat()}")


if __name__ == "__main__":
    main()
