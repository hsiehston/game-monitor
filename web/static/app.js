const { useEffect, useState } = React;
const PAGE_SIZE = 8;

function formatDate(value) {
  if (!value) {
    return "未知時間";
  }
  return String(value).replace("T", " ").slice(0, 19);
}

async function fetchJson(url) {
  const response = await fetch(url);
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`${response.status} ${text || response.statusText}`);
  }
  return response.json();
}

function SummaryCard({ label, value, accent }) {
  return (
    <div className={`summary-card ${accent || ""}`}>
      <div className="summary-label">{label}</div>
      <div className="summary-value">{value}</div>
    </div>
  );
}

function PostBarChart({ posts }) {
  const top = posts.slice(0, 6);
  const max = Math.max(...top.map((post) => post.gp_count || 0), 1);

  if (!top.length) {
    return <div className="empty-state">目前沒有符合條件的文章。</div>;
  }

  return (
    <div className="chart-panel">
      {top.map((post) => (
        <div className="chart-row" key={post.post_id}>
          <div className="chart-label" title={post.title}>{post.title}</div>
          <div className="chart-track">
            <div
              className="chart-fill"
              style={{ width: `${Math.max((post.gp_count / max) * 100, 4)}%` }}
            />
          </div>
          <div className="chart-value">GP {post.gp_count}</div>
        </div>
      ))}
    </div>
  );
}

function PostCard({ post }) {
  return (
    <article className="data-card">
      <div className="data-card__title">{post.title}</div>
      <div className="data-card__meta">
        <span>作者 {post.author || "未知"}</span>
        <span>文章 GP {post.gp_count}</span>
        <span>留言 {post.comment_count}</span>
        <span>最高留言 GP {post.top_comment_gp}</span>
      </div>
      <div className="data-card__foot">
        <span>文章編號 {post.post_id}</span>
        <span>{formatDate(post.created_at)}</span>
      </div>
    </article>
  );
}

function Pagination({ label, page, total, onPageChange }) {
  const pageCount = Math.max(Math.ceil(total / PAGE_SIZE), 1);

  return (
    <div className="pagination" aria-label={label}>
      <button
        className="page-button"
        type="button"
        onClick={() => onPageChange(Math.max(page - 1, 1))}
        disabled={page <= 1}
      >
        上一頁
      </button>
      <span>{page} / {pageCount}</span>
      <button
        className="page-button"
        type="button"
        onClick={() => onPageChange(Math.min(page + 1, pageCount))}
        disabled={page >= pageCount}
      >
        下一頁
      </button>
    </div>
  );
}

function CommentCard({ comment }) {
  return (
    <article className="data-card">
      <div className="data-card__title">{comment.title}</div>
      <div className="data-card__meta">
        <span>{comment.author || "匿名"}</span>
        <span>B{comment.floor}</span>
        <span>GP {comment.gp}</span>
        <span>BP {comment.bp}</span>
      </div>
      <div className="data-card__content">{comment.content || "無內容"}</div>
      <div className="data-card__foot">
        <span>文章編號 {comment.post_id}</span>
        <span>{formatDate(comment.created_at)}</span>
      </div>
    </article>
  );
}

function KeywordCloud({ keywords }) {
  if (!keywords.length) {
    return <div className="empty-state">目前沒有關鍵字資料。</div>;
  }

  const max = Math.max(...keywords.map((item) => item.count), 1);
  return (
    <div className="keyword-cloud">
      {keywords.map((item) => {
        const size = 0.9 + (item.count / max) * 1.4;
        return (
          <div
            className="keyword-pill"
            key={item.keyword}
            style={{ fontSize: `${size}rem` }}
          >
            <span>{item.keyword}</span>
            <strong>{item.count}</strong>
          </div>
        );
      })}
    </div>
  );
}

function App() {
  const [filters, setFilters] = useState({
    minGp: "0",
    minComments: "0",
    minCommentGp: "1",
  });
  const [summary, setSummary] = useState(null);
  const [posts, setPosts] = useState([]);
  const [comments, setComments] = useState([]);
  const [keywords, setKeywords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [lastQuery, setLastQuery] = useState(filters);
  const [postPage, setPostPage] = useState(1);
  const [commentPage, setCommentPage] = useState(1);

  const runQuery = async (queryFilters = filters) => {
    setLoading(true);
    setError("");
    setPostPage(1);
    setCommentPage(1);

    const params = new URLSearchParams({
      min_gp: queryFilters.minGp || "0",
      min_comments: queryFilters.minComments || "0",
      limit: "50",
    });
    const commentParams = new URLSearchParams({
      min_gp: queryFilters.minCommentGp || "0",
      limit: "50",
    });

    const results = await Promise.allSettled([
      fetchJson("/api/summary"),
      fetchJson(`/api/posts?${params.toString()}`),
      fetchJson(`/api/comments/top?${commentParams.toString()}`),
      fetchJson("/api/keywords?limit=40"),
    ]);

    const failures = results
      .filter((item) => item.status === "rejected")
      .map((item) => item.reason?.message || "Unknown error");

    if (results[0].status === "fulfilled") setSummary(results[0].value);
    if (results[1].status === "fulfilled") setPosts(results[1].value);
    else setPosts([]);
    if (results[2].status === "fulfilled") setComments(results[2].value);
    else setComments([]);
    if (results[3].status === "fulfilled") setKeywords(results[3].value);
    else setKeywords([]);

    setLastQuery({ ...queryFilters });
    setError(failures.join(" | "));
    setLoading(false);
  };

  useEffect(() => {
    runQuery(filters);
  }, []);

  const onSubmit = (event) => {
    event.preventDefault();
    runQuery(filters);
  };

  const pagedPosts = posts.slice((postPage - 1) * PAGE_SIZE, postPage * PAGE_SIZE);
  const pagedComments = comments.slice((commentPage - 1) * PAGE_SIZE, commentPage * PAGE_SIZE);

  return (
    <div className="app-shell">
      <div className="hero">
        <div className="hero-copy">
          <div className="eyebrow">Bahamut Monitor</div>
          <h1>文章熱度、留言互動與關鍵字，一頁看清楚。</h1>
          <p>
            直接用資料庫裡已抓下來的文章與留言做查詢，支援文章 GP、
            留言數門檻與高讚留言篩選。
          </p>
        </div>
        <div className="hero-stats">
          <div className="hero-chip">查詢即時回應</div>
          <div className="hero-chip alt">React 儀表板</div>
          <div className="hero-chip">熱門關鍵字</div>
        </div>
      </div>

      <main className="page">
        <section className="summary-grid">
          <SummaryCard label="文章數" value={summary?.posts ?? "-"} accent="warm" />
          <SummaryCard label="留言數" value={summary?.comments ?? "-"} accent="cool" />
          <SummaryCard label="最高文章 GP" value={summary?.max_post_gp ?? "-"} />
          <SummaryCard label="最高留言 GP" value={summary?.max_comment_gp ?? "-"} />
        </section>

        <section className="query-panel">
          <div className="panel-heading">
            <div>
              <h2>條件查詢</h2>
              <p>用門檻快速縮小文章與留言結果。</p>
            </div>
            <button
              className="secondary-button"
              type="button"
              onClick={() => runQuery(filters)}
              disabled={loading}
            >
              {loading ? "載入中" : "重新整理"}
            </button>
          </div>

          <form className="filter-grid" onSubmit={onSubmit}>
            <label>
              文章 GP 至少
              <input
                type="number"
                min="0"
                value={filters.minGp}
                onChange={(event) => setFilters({ ...filters, minGp: event.target.value })}
              />
            </label>
            <label>
              文章留言數至少
              <input
                type="number"
                min="0"
                value={filters.minComments}
                onChange={(event) => setFilters({ ...filters, minComments: event.target.value })}
              />
            </label>
            <label>
              留言 GP 至少
              <input
                type="number"
                min="0"
                value={filters.minCommentGp}
                onChange={(event) => setFilters({ ...filters, minCommentGp: event.target.value })}
              />
            </label>
            <button className="primary-button" type="submit" disabled={loading}>
              {loading ? "查詢中" : "套用查詢"}
            </button>
          </form>

          <div className="query-meta">
            <span>文章 GP &gt;= {lastQuery.minGp}</span>
            <span>留言數 &gt;= {lastQuery.minComments}</span>
            <span>留言 GP &gt;= {lastQuery.minCommentGp}</span>
          </div>

          {error ? <div className="error-banner">部分資料載入失敗：{error}</div> : null}
        </section>

        <section className="content-grid">
          <div className="surface">
            <div className="panel-heading">
              <div>
                <h2>熱門文章</h2>
                <p>依文章 GP 與留言數排序，共 {posts.length} 筆。</p>
              </div>
            </div>
            <PostBarChart posts={posts} />
            <div className="card-list">
              {pagedPosts.length ? pagedPosts.map((post) => (
                <PostCard key={post.post_id} post={post} />
              )) : <div className="empty-state">目前沒有符合條件的文章。</div>}
            </div>
            {posts.length > PAGE_SIZE ? (
              <Pagination
                label="熱門文章分頁"
                page={postPage}
                total={posts.length}
                onPageChange={setPostPage}
              />
            ) : null}
          </div>

          <div className="surface">
            <div className="panel-heading">
              <div>
                <h2>高讚留言</h2>
                <p>找出 GP 較高的留言內容，共 {comments.length} 筆。</p>
              </div>
            </div>
            <div className="card-list">
              {pagedComments.length ? pagedComments.map((comment) => (
                <CommentCard key={comment.comment_id || `${comment.post_id}-${comment.floor}-${comment.author}`} comment={comment} />
              )) : <div className="empty-state">目前沒有符合條件的留言。</div>}
            </div>
            {comments.length > PAGE_SIZE ? (
              <Pagination
                label="高讚留言分頁"
                page={commentPage}
                total={comments.length}
                onPageChange={setCommentPage}
              />
            ) : null}
          </div>
        </section>

        <section className="surface">
          <div className="panel-heading">
            <div>
              <h2>熱門關鍵字</h2>
              <p>統計文章標題與留言內容裡的高頻詞。</p>
            </div>
          </div>
          <KeywordCloud keywords={keywords} />
        </section>
      </main>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
