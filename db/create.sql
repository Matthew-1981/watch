CREATE TABLE info (
    watch_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(50),
    date_of_joining DATETIME
);

CREATE TABLE logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    watch_id INTEGER NOT NULL,
    cycle INTEGER NOT NULL,
    timedate DATETIME NOT NULL,
    measure FLOAT NOT NULL
);
