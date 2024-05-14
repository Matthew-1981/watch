CREATE DATABASE IF NOT EXISTS watch_db;
USE watch_db;

CREATE TABLE info
(
    watch_id        INT AUTO_INCREMENT PRIMARY KEY,
    name            VARCHAR(50),
    date_of_joining DATETIME
);

CREATE TABLE logs
(
    log_id   INT AUTO_INCREMENT PRIMARY KEY,
    watch_id INT      NOT NULL,
    cycle    INT      NOT NULL,
    timedate DATETIME NOT NULL,
    measure  FLOAT    NOT NULL,
    FOREIGN KEY (watch_id) REFERENCES info (watch_id)
);
