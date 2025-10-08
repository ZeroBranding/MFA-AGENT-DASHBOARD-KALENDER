BEGIN;

-- Performance-Optimierung: Kritische Indizes für häufige Abfragen
CREATE INDEX IF NOT EXISTS idx_emails_thread_id ON emails(thread_id);
CREATE INDEX IF NOT EXISTS idx_emails_received_at ON emails(received_at);
CREATE INDEX IF NOT EXISTS idx_emails_msg_id ON emails(msg_id);
CREATE INDEX IF NOT EXISTS idx_emails_from_addr ON emails(from_addr);
CREATE INDEX IF NOT EXISTS idx_emails_state ON emails(state);

-- Reservations Performance
CREATE INDEX IF NOT EXISTS idx_reservations_resource_slot ON reservations(resource_id, slot_ts);
CREATE INDEX IF NOT EXISTS idx_reservations_patient ON reservations(patient_hash);
CREATE INDEX IF NOT EXISTS idx_reservations_created ON reservations(created_ts);

-- Settings für Business Hours
CREATE TABLE IF NOT EXISTS settings (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

-- Business Hours Standardwerte
INSERT OR REPLACE INTO settings (key, value) VALUES
('business_hours_mon', '[["08:00","12:00"],["15:00","18:00"]]'),
('business_hours_tue', '[["08:00","12:00"],["15:00","18:00"]]'),
('business_hours_wed', '[["08:00","12:00"]]'),
('business_hours_thu', '[["08:00","12:00"],["15:00","18:00"]]'),
('business_hours_fri', '[["08:00","12:00"],["15:00","18:00"]]'),
('business_hours_sat', '[]'),
('business_hours_sun', '[]');

COMMIT;
