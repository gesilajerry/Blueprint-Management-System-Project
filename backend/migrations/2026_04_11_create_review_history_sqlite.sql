-- 创建审定历史记录表
CREATE TABLE IF NOT EXISTS review_history (
    id VARCHAR(36) PRIMARY KEY,
    drawing_id VARCHAR(36) NOT NULL,
    old_level VARCHAR(10),
    new_level VARCHAR(10) NOT NULL,
    reason TEXT,
    reviewer_id VARCHAR(36) NOT NULL,
    reviewer_name VARCHAR(100),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (drawing_id) REFERENCES drawings(id),
    FOREIGN KEY (reviewer_id) REFERENCES users(id)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_review_history_drawing ON review_history(drawing_id);
CREATE INDEX IF NOT EXISTS idx_review_history_reviewer ON review_history(reviewer_id);
