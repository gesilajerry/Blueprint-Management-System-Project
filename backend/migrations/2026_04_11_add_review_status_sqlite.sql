-- 添加 review_status 字段到 drawings 表

-- 添加 review_status 字段，默认 'approved'（已审核）
ALTER TABLE drawings ADD COLUMN review_status VARCHAR(20) DEFAULT 'approved';

-- 更新所有现有图纸为已审核状态（历史数据不需要重新审核）
UPDATE drawings SET review_status = 'approved' WHERE review_status IS NULL;

-- 创建索引以加速待审核列表查询
CREATE INDEX IF NOT EXISTS idx_drawings_review_status ON drawings(review_status);
