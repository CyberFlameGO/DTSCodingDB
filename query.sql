CREATE TABLE IF NOT EXISTS cards
(
    id          INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
    card_number TEXT UNIQUE                              NOT NULL,
    card_name   TEXT                                     NOT NULL,
    type        TEXT,
    rarity      TEXT,
    value       REAL                                     NOT NULL,
    attribute   TEXT,
    subtype     TEXT,
    level       INTEGER                                  NOT NULL,
    card_atk    INTEGER                                  NOT NULL,
    card_def    INTEGER                                  NOT NULL,
    card_text   BLOB
);
