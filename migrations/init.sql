-- GPT Proxy Service 数据库初始化脚本
-- PostgreSQL

-- 创建数据库（如果需要单独执行）
-- CREATE DATABASE gpt_proxy;

-- ==================== 用户表 ====================
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(255) UNIQUE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_admin BOOLEAN NOT NULL DEFAULT FALSE,
    notes TEXT,
    monthly_quota_tokens INTEGER NOT NULL DEFAULT 1000000,
    monthly_quota_amount FLOAT NOT NULL DEFAULT 10.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);

-- ==================== API Key 表 ====================
CREATE TABLE IF NOT EXISTS api_keys (
    id SERIAL PRIMARY KEY,
    key VARCHAR(255) NOT NULL UNIQUE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    allowed_models TEXT,  -- JSON 格式，如 ["gpt-3.5-turbo", "gpt-4"]
    rate_limit_rpm INTEGER,
    rate_limit_tpm INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_api_keys_key ON api_keys(key);
CREATE INDEX idx_api_keys_user_id ON api_keys(user_id);

-- ==================== 上游 Key 表 ====================
CREATE TABLE IF NOT EXISTS upstream_keys (
    id SERIAL PRIMARY KEY,
    upstream_type VARCHAR(20) NOT NULL,  -- openai 或 azure
    encrypted_key VARCHAR(500) NOT NULL,
    azure_endpoint VARCHAR(500),
    azure_deployment_name VARCHAR(100),
    azure_api_version VARCHAR(50),
    weight INTEGER NOT NULL DEFAULT 1,
    status VARCHAR(20) NOT NULL DEFAULT 'healthy',  -- healthy, cooldown, disabled
    failure_count INTEGER NOT NULL DEFAULT 0,
    last_failure_at VARCHAR(50),
    cooldown_until VARCHAR(50),
    total_requests INTEGER NOT NULL DEFAULT 0,
    total_tokens INTEGER NOT NULL DEFAULT 0,
    total_errors INTEGER NOT NULL DEFAULT 0,
    notes VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_upstream_keys_type_status ON upstream_keys(upstream_type, status);

-- ==================== 请求记录表 ====================
CREATE TABLE IF NOT EXISTS usage_records (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    api_key_id INTEGER REFERENCES api_keys(id),
    upstream_key_id INTEGER REFERENCES upstream_keys(id),
    model VARCHAR(100) NOT NULL,
    prompt_tokens INTEGER NOT NULL DEFAULT 0,
    completion_tokens INTEGER NOT NULL DEFAULT 0,
    total_tokens INTEGER NOT NULL DEFAULT 0,
    request_body TEXT,
    response_status INTEGER NOT NULL,
    response_time_ms FLOAT NOT NULL,
    client_ip VARCHAR(50),
    user_agent VARCHAR(500),
    error_type VARCHAR(100),
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_usage_records_user_id ON usage_records(user_id);
CREATE INDEX idx_usage_records_api_key_id ON usage_records(api_key_id);
CREATE INDEX idx_usage_records_upstream_key_id ON usage_records(upstream_key_id);
CREATE INDEX idx_usage_records_model ON usage_records(model);
CREATE INDEX idx_usage_records_client_ip ON usage_records(client_ip);
CREATE INDEX idx_usage_records_user_date ON usage_records(user_id, created_at);
CREATE INDEX idx_usage_records_date ON usage_records(created_at);

-- ==================== 每日用量聚合表 ====================
CREATE TABLE IF NOT EXISTS usage_daily (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    date VARCHAR(10) NOT NULL,  -- YYYY-MM-DD
    total_requests INTEGER NOT NULL DEFAULT 0,
    total_prompt_tokens INTEGER NOT NULL DEFAULT 0,
    total_completion_tokens INTEGER NOT NULL DEFAULT 0,
    total_tokens INTEGER NOT NULL DEFAULT 0,
    total_cost FLOAT NOT NULL DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, date)
);

CREATE INDEX idx_usage_daily_user_id ON usage_daily(user_id);
CREATE INDEX idx_usage_daily_date ON usage_daily(date);

-- ==================== 每月用量聚合表 ====================
CREATE TABLE IF NOT EXISTS usage_monthly (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    total_requests INTEGER NOT NULL DEFAULT 0,
    total_prompt_tokens INTEGER NOT NULL DEFAULT 0,
    total_completion_tokens INTEGER NOT NULL DEFAULT 0,
    total_tokens INTEGER NOT NULL DEFAULT 0,
    total_cost FLOAT NOT NULL DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, year, month)
);

CREATE INDEX idx_usage_monthly_user_id ON usage_monthly(user_id);
CREATE INDEX idx_usage_monthly_year_month ON usage_monthly(year, month);

-- ==================== 自动更新 updated_at 触发器 ====================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_api_keys_updated_at BEFORE UPDATE ON api_keys
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_upstream_keys_updated_at BEFORE UPDATE ON upstream_keys
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_usage_records_updated_at BEFORE UPDATE ON usage_records
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_usage_daily_updated_at BEFORE UPDATE ON usage_daily
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_usage_monthly_updated_at BEFORE UPDATE ON usage_monthly
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ==================== 完成 ====================
-- 执行: psql -U gpt_proxy -d gpt_proxy -f init.sql
