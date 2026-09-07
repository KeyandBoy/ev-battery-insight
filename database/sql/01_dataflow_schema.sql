-- DataFlowCanvas 数据库结构脚本（MySQL 8.0）
-- 说明：仅建库建表，不插入业务数据。

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

CREATE DATABASE IF NOT EXISTS `dataflow_canvas`
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE `dataflow_canvas`;

-- 按依赖顺序先删子表再删父表
DROP TABLE IF EXISTS `component`;
DROP TABLE IF EXISTS `dashboard`;
DROP TABLE IF EXISTS `data_record`;
DROP TABLE IF EXISTS `dataset`;
DROP TABLE IF EXISTS `user_profile`;
DROP TABLE IF EXISTS `user`;

CREATE TABLE `user` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `username` VARCHAR(50) NOT NULL COMMENT '登录用户名',
  `password_hash` VARCHAR(255) NOT NULL COMMENT '密码哈希',
  `email` VARCHAR(100) DEFAULT NULL COMMENT '邮箱，可选',
  `status` TINYINT NOT NULL DEFAULT 1 COMMENT '状态：1启用，0禁用',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_username` (`username`),
  KEY `idx_user_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

CREATE TABLE `user_profile` (
  `user_id` BIGINT UNSIGNED NOT NULL COMMENT '用户ID',
  `display_name` VARCHAR(50) DEFAULT NULL COMMENT '显示名称',
  `avatar_url` VARCHAR(255) DEFAULT NULL COMMENT '头像地址',
  `bio` VARCHAR(255) DEFAULT NULL COMMENT '个人简介',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`user_id`),
  CONSTRAINT `fk_user_profile_user`
    FOREIGN KEY (`user_id`) REFERENCES `user` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户资料表';

CREATE TABLE `dataset` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `user_id` BIGINT UNSIGNED NOT NULL COMMENT '所属用户ID',
  `name` VARCHAR(100) NOT NULL COMMENT '数据集名称',
  `source_type` ENUM('csv', 'excel', 'json') NOT NULL COMMENT '来源类型',
  `file_path` VARCHAR(255) DEFAULT NULL COMMENT '源文件路径',
  `field_meta` JSON DEFAULT NULL COMMENT '字段映射与元数据',
  `total_rows` INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '总记录数',
  `clean_status` ENUM('pending', 'done', 'failed') NOT NULL DEFAULT 'pending' COMMENT '清洗状态',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_dataset_user_name` (`user_id`, `name`),
  KEY `idx_dataset_user_id` (`user_id`),
  KEY `idx_dataset_clean_status` (`clean_status`),
  CONSTRAINT `fk_dataset_user`
    FOREIGN KEY (`user_id`) REFERENCES `user` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='数据集表';

CREATE TABLE `data_record` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `dataset_id` BIGINT UNSIGNED NOT NULL COMMENT '所属数据集ID',
  `parent_id` BIGINT UNSIGNED DEFAULT NULL COMMENT '父节点记录ID',
  `node_key` VARCHAR(120) NOT NULL COMMENT '节点业务键',
  `node_name` VARCHAR(120) NOT NULL COMMENT '节点显示名',
  `level` INT UNSIGNED NOT NULL COMMENT '层级深度，从0开始',
  `value_num` DECIMAL(18, 4) NOT NULL DEFAULT 0.0000 COMMENT '权重/数值',
  `raw_payload` JSON DEFAULT NULL COMMENT '原始扩展字段',
  `is_abnormal` TINYINT NOT NULL DEFAULT 0 COMMENT '是否异常值：1是，0否',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_data_record_dataset_level` (`dataset_id`, `level`),
  KEY `idx_data_record_dataset_parent` (`dataset_id`, `parent_id`),
  KEY `idx_data_record_node_key` (`node_key`),
  CONSTRAINT `fk_data_record_dataset`
    FOREIGN KEY (`dataset_id`) REFERENCES `dataset` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_data_record_parent`
    FOREIGN KEY (`parent_id`) REFERENCES `data_record` (`id`)
    ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='数据记录表';

CREATE TABLE `dashboard` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `user_id` BIGINT UNSIGNED NOT NULL COMMENT '所属用户ID',
  `name` VARCHAR(100) NOT NULL COMMENT '大屏名称',
  `description` VARCHAR(255) DEFAULT NULL COMMENT '描述',
  `canvas_width` INT UNSIGNED NOT NULL DEFAULT 1920 COMMENT '画布宽度',
  `canvas_height` INT UNSIGNED NOT NULL DEFAULT 1080 COMMENT '画布高度',
  `theme` VARCHAR(50) NOT NULL DEFAULT 'light' COMMENT '主题',
  `layout_json` JSON DEFAULT NULL COMMENT '整体布局配置',
  `is_published` TINYINT NOT NULL DEFAULT 0 COMMENT '是否发布：1是，0否',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_dashboard_user_id` (`user_id`),
  KEY `idx_dashboard_published` (`is_published`),
  CONSTRAINT `fk_dashboard_user`
    FOREIGN KEY (`user_id`) REFERENCES `user` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='可视化大屏表';

CREATE TABLE `component` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `dashboard_id` BIGINT UNSIGNED NOT NULL COMMENT '所属大屏ID',
  `dataset_id` BIGINT UNSIGNED DEFAULT NULL COMMENT '绑定数据集ID',
  `type` VARCHAR(50) NOT NULL COMMENT '组件类型：treemap/bar/pie/line/table',
  `title` VARCHAR(100) DEFAULT NULL COMMENT '组件标题',
  `x` INT NOT NULL DEFAULT 0 COMMENT '画布X坐标',
  `y` INT NOT NULL DEFAULT 0 COMMENT '画布Y坐标',
  `w` INT UNSIGNED NOT NULL DEFAULT 400 COMMENT '组件宽度',
  `h` INT UNSIGNED NOT NULL DEFAULT 300 COMMENT '组件高度',
  `z_index` INT NOT NULL DEFAULT 1 COMMENT '层级',
  `config_json` JSON DEFAULT NULL COMMENT '样式与展示配置',
  `binding_json` JSON DEFAULT NULL COMMENT '维度指标绑定配置',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_component_dashboard_id` (`dashboard_id`),
  KEY `idx_component_dataset_id` (`dataset_id`),
  KEY `idx_component_type` (`type`),
  CONSTRAINT `fk_component_dashboard`
    FOREIGN KEY (`dashboard_id`) REFERENCES `dashboard` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_component_dataset`
    FOREIGN KEY (`dataset_id`) REFERENCES `dataset` (`id`)
    ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='可视化组件表';

SET FOREIGN_KEY_CHECKS = 1;
