-- 1. Creating the database if it doesn't already exist
CREATE DATABASE IF NOT EXISTS credit91_analytics;

-- 2. Select it as active
USE credit91_analytics;

-- 3. Create the table schema
CREATE TABLE IF NOT EXISTS customer_events (
    event_id VARCHAR(50) PRIMARY KEY,
    user_id VARCHAR(50),
    event_name VARCHAR(50),
    event_timestamp DATETIME,
    utm_source VARCHAR(50),
    device_type VARCHAR(50)
);
SHOW DATABASES;

SELECT * FROM credit91_analytics.customer_events;

SELECT COUNT(*) FROM customer_events;