CREATE TABLE IF NOT EXISTS watch
(
    watch_id         INT AUTO_INCREMENT PRIMARY KEY,
    user_id          INT NOT NULL,
    name             VARCHAR(50),
    date_of_creation DATETIME,
    FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE,
    CONSTRAINT UNIQUE (user_id, name)
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
