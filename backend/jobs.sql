CREATE TABLE IF NOT EXISTS jobs (
    id           VARCHAR(36)  PRIMARY KEY,
    status       VARCHAR(20)  NOT NULL DEFAULT 'pending',
    progress     INTEGER      NOT NULL DEFAULT 0,
    file_path    VARCHAR(255),
    error        TEXT,
    created_at   TIMESTAMP    NOT NULL DEFAULT NOW(),
    started_at   TIMESTAMP,
    completed_at TIMESTAMP
);
