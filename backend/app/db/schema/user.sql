CREATE TABLE IF NOT EXISTS users
(
    user_id          INT AUTO_INCREMENT PRIMARY KEY,
    user_name        VARCHAR(32) UNIQUE NOT NULL,
    password_hash    VARCHAR(64)        NOT NULL,
    date_of_creation DATETIME
);

CREATE TABLE IF NOT EXISTS session_token
(
    token_id   INT AUTO_INCREMENT PRIMARY KEY,
    user_id    INT                 NOT NULL,
    token      VARCHAR(255) UNIQUE NOT NULL,
    expiration DATETIME            NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
);
