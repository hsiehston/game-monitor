from apscheduler.schedulers.blocking import BlockingScheduler
from bahamut import crawl_board
from db import save_comments, save_post


BSN = "17608"
MAX_PAGES = 3


def job():
    print("開始抓取巴哈姆特...")
    posts, all_comments = crawl_board(bsn=BSN, max_pages=MAX_PAGES)

    for post in posts:
        save_post(post)

    save_comments(all_comments)
    print(f"完成，共 {len(posts)} 篇文章、{len(all_comments)} 則留言")


# 啟動時先執行一次
job()

scheduler = BlockingScheduler()
scheduler.add_job(job, "interval", hours=1)
print("排程啟動，每小時自動抓取一次")
scheduler.start()
