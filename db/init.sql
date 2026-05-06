CREATE TABLE IF NOT EXISTS posts (
    id          SERIAL PRIMARY KEY,
    platform    VARCHAR(20) NOT NULL,
    post_id     VARCHAR(50) UNIQUE NOT NULL,
    title       TEXT,
    author      VARCHAR(100),
    gp_count    INT DEFAULT 0,
    created_at  TIMESTAMP,
    fetched_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS comments (
    id         SERIAL PRIMARY KEY,
    comment_id VARCHAR(50) UNIQUE NOT NULL,
    post_id    VARCHAR(50) REFERENCES posts(post_id),
    floor      INT,
    author     VARCHAR(100),
    content    TEXT,
    gp         INT DEFAULT 0,
    bp         INT DEFAULT 0,
    created_at TIMESTAMP,
    fetched_at TIMESTAMP DEFAULT NOW()
);
