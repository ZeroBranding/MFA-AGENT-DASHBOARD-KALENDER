BEGIN;

-- Füge age_group-Spalte zur patients-Tabelle hinzu
ALTER TABLE patients ADD COLUMN age_group TEXT DEFAULT 'unknown';

-- Erstelle Index für bessere Performance
CREATE INDEX IF NOT EXISTS idx_patients_age_group ON patients(age_group);

COMMIT;
