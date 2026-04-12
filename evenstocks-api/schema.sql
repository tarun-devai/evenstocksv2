-- EvenStocks Database Schema
-- Run: mysql -u root -p < schema.sql

CREATE DATABASE IF NOT EXISTS evenstocks_db;
USE evenstocks_db;

CREATE TABLE IF NOT EXISTS users (
  user_id INT AUTO_INCREMENT PRIMARY KEY,
  user_name VARCHAR(255),
  user_mobile VARCHAR(20),
  user_email VARCHAR(255) UNIQUE,
  user_password VARCHAR(255),
  user_age INT,
  verified TINYINT DEFAULT 0,
  otp VARCHAR(6),
  user_token VARCHAR(16),
  created_date DATETIME,
  created_by VARCHAR(255),
  modification_date DATETIME,
  modification_by VARCHAR(255),
  delete_user VARCHAR(255),
  user_status TINYINT DEFAULT 1,
  username VARCHAR(10) UNIQUE,
  plan_name VARCHAR(10),
  order_id VARCHAR(64),
  requests_remaining INT,
  param1 VARCHAR(255),
  param2 VARCHAR(255),
  param3 VARCHAR(255),
  param4 VARCHAR(255),
  param5 VARCHAR(255),
  param6 VARCHAR(255),
  param7 VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS user_feedback (
  feedback_id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(10),
  feedback TEXT,
  user_query TEXT,
  created_date DATETIME,
  param1 VARCHAR(255),
  param2 VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS contact_info (
  contact_id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(10),
  user_token VARCHAR(16),
  name VARCHAR(255),
  email VARCHAR(255),
  subject VARCHAR(255),
  message TEXT,
  param1 VARCHAR(255),
  param2 VARCHAR(255),
  created_date DATETIME
);

CREATE TABLE IF NOT EXISTS user_billing_history (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT,
  plan_name VARCHAR(10),
  status VARCHAR(10),
  subscribed_at DATETIME,
  order_id VARCHAR(64),
  param1 VARCHAR(255),
  param2 VARCHAR(255),
  param3 VARCHAR(255),
  FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS user_queries (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(10),
  user_token VARCHAR(16),
  user_query TEXT,
  response TEXT,
  created_date DATETIME
);
