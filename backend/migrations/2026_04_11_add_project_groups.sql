-- 图纸管理系统数据库迁移脚本
-- 版本：2026-04-11
-- 说明：添加项目组管理功能，重构权限体系

-- 1. 创建项目组表
CREATE TABLE IF NOT EXISTS `project_groups` (
  `id` VARCHAR(36) PRIMARY KEY,
  `name` VARCHAR(100) NOT NULL COMMENT '项目组名称',
  `code` VARCHAR(50) UNIQUE NOT NULL COMMENT '项目组编号',
  `leader_id` VARCHAR(36) COMMENT '项目负责人 ID',
  `department_id` VARCHAR(36) COMMENT '所属部门 ID',
  `status` VARCHAR(20) DEFAULT 'active' COMMENT '状态：active/disabled',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  FOREIGN KEY (`leader_id`) REFERENCES `users`(`id`),
  FOREIGN KEY (`department_id`) REFERENCES `departments`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='项目组表';

-- 2. 创建项目组成员关系表
CREATE TABLE IF NOT EXISTS `project_group_members` (
  `group_id` VARCHAR(36) NOT NULL COMMENT '项目组 ID',
  `user_id` VARCHAR(36) NOT NULL COMMENT '用户 ID',
  `role_type` VARCHAR(20) COMMENT '成员角色：manager/engineer',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`group_id`, `user_id`),
  INDEX `idx_group_user` (`group_id`, `user_id`),
  FOREIGN KEY (`group_id`) REFERENCES `project_groups`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='项目组成员关系表';

-- 3. 修改 products 表，添加 project_group_id 字段
ALTER TABLE `products`
ADD COLUMN `project_group_id` VARCHAR(36) COMMENT '所属项目组 ID' AFTER `status`,
ADD CONSTRAINT `fk_products_project_group`
FOREIGN KEY (`project_group_id`) REFERENCES `project_groups`(`id`);

-- 4. 为研发工程部添加默认项目组（如果部门存在）
-- 注意：这需要根据实际部门 ID 进行调整
INSERT INTO `project_groups` (`id`, `name`, `code`, `status`, `created_at`)
SELECT
  UUID() AS id,
  '研发项目组' AS name,
  'RD-001' AS code,
  'active' AS status,
  NOW() AS created_at
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM `project_groups` WHERE `code` = 'RD-001');

-- 5. 添加工程师角色（如果不存在）
INSERT INTO `roles` (`id`, `name`, `code`, `status`, `created_at`)
SELECT
  UUID() AS id,
  '工程师' AS name,
  'role_engineer' AS code,
  'active' AS status,
  NOW() AS created_at
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM `roles` WHERE `code` = 'role_engineer');

-- 6. 查看新添加的角色 ID（用于后续权限配置）
-- SELECT * FROM `roles` WHERE `code` = 'role_engineer';

-- 迁移说明：
-- 1. 项目组表用于管理研发工程部下的各个项目组
-- 2. 项目组成员关系表用于分配用户到项目组，并区分项目经理和工程师角色
-- 3. 产品/项目表现在关联到项目组，而不是直接关联到部门
-- 4. 权限体系基于项目组进行重构：
--    - 项目经理：可查看负责项目组内的所有图纸
--    - 工程师：仅可查看自己参与项目组内的图纸
--    - 设计师/审定人：仅可查看自己创建的图纸
--    - CTO/管理员：查看所有图纸
--    - 部门负责人：查看本部门图纸
