BEGIN;

CREATE TABLE IF NOT EXISTS resources (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS slot_capacity (
  id INTEGER PRIMARY KEY,
  resource_id INTEGER NOT NULL REFERENCES resources(id) ON DELETE CASCADE,
  slot_ts TEXT NOT NULL,
  max_bookings INTEGER NOT NULL DEFAULT 1,
  UNIQUE(resource_id, slot_ts)
);

CREATE TABLE IF NOT EXISTS reservations (
  id INTEGER PRIMARY KEY,
  resource_id INTEGER NOT NULL REFERENCES resources(id) ON DELETE CASCADE,
  slot_ts TEXT NOT NULL,
  patient_hash TEXT NOT NULL,
  created_ts TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
  UNIQUE(resource_id, slot_ts, patient_hash)
);

CREATE INDEX IF NOT EXISTS idx_res_slot ON reservations(resource_id, slot_ts);
CREATE INDEX IF NOT EXISTS idx_cap_slot ON slot_capacity(resource_id, slot_ts);

COMMIT;
