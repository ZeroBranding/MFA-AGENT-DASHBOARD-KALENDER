import Database from "better-sqlite3";

export const db = new Database("calendar.db");
db.pragma("journal_mode = WAL");
db.pragma("synchronous = NORMAL");

export const stmts = {
  upsertEmail: db.prepare(`
    INSERT INTO emails (id, msg_id, from_addr, subject, text_hash, received_at, state, klass, score, flags, pii_flags)
    VALUES (@id, @msg_id, @from_addr, @subject, @text_hash, @received_at, @state, @klass, @score, @flags, @pii_flags)
    ON CONFLICT(msg_id) DO NOTHING
  `),
  findByMsgId: db.prepare(`SELECT * FROM emails WHERE msg_id = ?`),
  appendEvent: db.prepare(`
    INSERT INTO events (email_id, type, data) VALUES (?, ?, ?)
  `),
};
