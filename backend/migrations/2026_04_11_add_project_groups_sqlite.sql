-- 图纸管理系统数据库迁移脚本 (SQLite 版本)
-- 版本：2026-04-11
-- 说明：添加项目组管理功能，重构权限体系

-- 1. 创建项目组表
CREATE TABLE IF NOT EXISTS `project_groups` (
  `id` VARCHAR(36) PRIMARY KEY,
  `name` VARCHAR(100) NOT NULL,
  `code` VARCHAR(50) UNIQUE NOT NULL,
  `leader_id` VARCHAR(36),
  `department_id` VARCHAR(36),
  `status` VARCHAR(20) DEFAULT 'active',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`leader_id`) REFERENCES `users`(`id`),
  FOREIGN KEY (`department_id`) REFERENCES `departments`(`id`)
);

-- 2. 创建项目组成员关系表
CREATE TABLE IF NOT EXISTS `project_group_members` (
  `group_id` VARCHAR(36) NOT NULL,
  `user_id` VARCHAR(36) NOT NULL,
  `role_type` VARCHAR(20),
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`group_id`, `user_id`),
  FOREIGN KEY (`group_id`) REFERENCES `project_groups`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
);

-- 3. 为 project_group_members 创建索引
CREATE INDEX IF NOT EXISTS `idx_group_user` ON `project_group_members` (`group_id`, `user_id`);

-- 4. 修改 products 表，添加 project_group_id 字段
ALTER TABLE `products` ADD COLUMN `project_group_id` VARCHAR(36);

-- 5. 添加外键约束（SQLite 需要重新创建表来添加外键）
-- 由于 SQLite 限制，这里只添加数据，外键约束在 ORM 层处理

-- 6. 添加默认项目组（如果不存在）
INSERT OR IGNORE INTO `project_groups` (`id`, `name`, `code`, `status`, `created_at`)
SELECT
  'pg-' || strftime('%Y%m%d%H%M%S', 'now') || '-' || random(),
  '研发项目组',
  'RD-001',
  'active',
  datetime('now')
WHERE NOT EXISTS (SELECT 1 FROM `project_groups` WHERE `code` = 'RD-001');

-- 7. 添加工程师角色（如果不存在）
INSERT OR IGNORE INTO `roles` (`id`, `name`, `code`, `status`, `created_at`)
SELECT
  'role-' || strftime('%Y%m%d%H%M%S', 'now') || '-' || random(),
  '工程师',
  'role_engineer',
  'active',
  datetime('now')
WHERE NOT EXISTS (SELECT 1 FROM `roles` WHERE `code` = 'role_engineer');
