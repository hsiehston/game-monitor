from apscheduler.schedulers.blocking import BlockingScheduler
from bahamut import crawl_board
from db import save_comments, save_post


def job():
    print("開始抓取巴哈姆特...")
    posts, all_comments = crawl_board(bsn="37273", max_pages=3)
    for post in posts:
        save_post(post)
    save_comments(all_comments)
    print(f"完成，共 {len(posts)} 篇文章")


scheduler = BlockingScheduler()
scheduler.add_job(job, "interval", hours=1)
scheduler.start()
