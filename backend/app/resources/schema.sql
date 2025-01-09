CREATE DATABASE IF NOT EXISTS watch_db;
USE watch_db;

CREATE TABLE IF NOT EXISTS users
(
    user_id          INT AUTO_INCREMENT PRIMARY KEY,
    user_name        VARCHAR(50) UNIQUE NOT NULL,
    password_hash    VARCHAR(60) NOT NULL,
    date_of_creation DATETIME
);

CREATE TABLE IF NOT EXISTS session_token
(
    token_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id  INT                NOT NULL,
    token    VARCHAR(60) UNIQUE NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS watch
(
    watch_id         INT AUTO_INCREMENT PRIMARY KEY,
    user_id          INT NOT NULL,
    name             VARCHAR(50),
    date_of_creation DATETIME,
    FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS log
(
    log_id   INT AUTO_INCREMENT PRIMARY KEY,
    watch_id INT      NOT NULL,
    cycle    INT      NOT NULL,
    timedate DATETIME NOT NULL,
    measure  FLOAT    NOT NULL,
    FOREIGN KEY (watch_id) REFERENCES watch (watch_id) ON DELETE CASCADE
);
