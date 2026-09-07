CREATE DATABASE IF NOT EXISTS highdim_region_vis DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE highdim_region_vis;

CREATE TABLE IF NOT EXISTS datasets (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(120) NOT NULL,
    description TEXT NULL,
    source_type VARCHAR(32) NOT NULL,
    file_path VARCHAR(255) NOT NULL,
    sample_count INT NOT NULL DEFAULT 0,
    dimension_count INT NOT NULL DEFAULT 0,
    label_column VARCHAR(64) NULL,
    meta_info JSON NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS analysis_runs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    dataset_id INT NOT NULL,
    algorithm VARCHAR(32) NOT NULL,
    reducer VARCHAR(32) NOT NULL,
    preprocess_config JSON NULL,
    algorithm_config JSON NULL,
    quality_metrics JSON NULL,
    performance_metrics JSON NULL,
    result_payload JSON NULL,
    preservation_score DOUBLE NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_analysis_dataset_id (dataset_id)
);
