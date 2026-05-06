import sys
import time

from apscheduler.schedulers.blocking import BlockingScheduler
from bahamut import crawl_board
from db import save_comments, save_post


BSN = "17608"
MAX_PAGES = 2


def job():
    print("開始抓取巴哈姆特...")
    posts, all_comments = crawl_board(bsn=BSN, max_pages=MAX_PAGES)

    for post in posts:
        save_post(post)

    save_comments(all_comments)
    print(f"完成，共 {len(posts)} 篇文章、{len(all_comments)} 則留言")


def run_schedule():
    job()
    scheduler = BlockingScheduler()
    scheduler.add_job(job, "interval", hours=1)
    print("排程啟動，每小時自動抓取一次")
    scheduler.start()


def print_usage():
    print("用法: python main.py [idle|run-once|schedule]")


def run_idle():
    print("crawler 容器待命中，使用 run-once 或 schedule 來啟動抓取。")
    while True:
        time.sleep(3600)


def main():
    command = sys.argv[1] if len(sys.argv) > 1 else "idle"

    if command == "run-once":
        job()
    elif command == "schedule":
        run_schedule()
    elif command == "idle":
        run_idle()
    else:
        print_usage()
        raise SystemExit(1)


if __name__ == "__main__":
    main()
