#!/usr/bin/env python3
"""
Führt Datenbank-Migrationen aus
"""

import sqlite3
import os
from pathlib import Path

def run_migration(migration_file, db_path):
    """Führt eine SQL-Migration aus"""
    try:
        # Lese Migration-Datei
        with open(migration_file, 'r', encoding='utf-8') as f:
            sql = f.read()

        # Führe Migration aus
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print(f"Führe Migration aus: {migration_file}")
        print(f"SQL: {sql.strip()}")

        cursor.executescript(sql)
        conn.commit()
        conn.close()

        print(f"OK: Migration erfolgreich: {migration_file}")
        return True

    except Exception as e:
        print(f"FEHLER: Fehler bei Migration {migration_file}: {e}")
        return False

def find_patient_db():
    """Findet die Patienten-Datenbank"""
    possible_paths = [
        'patient_profiles.db',
        'patient_management_agent.db',
        'patients.db'
    ]

    for path in possible_paths:
        if os.path.exists(path):
            return path

    # Suche nach Datenbank-Dateien
    for file in os.listdir('.'):
        if file.endswith('.db') and ('patient' in file.lower() or 'profile' in file.lower()):
            return file

    return None

if __name__ == "__main__":
    print("=== DATENBANK-MIGRATION AUSFÜHREN ===")

    # Finde Patienten-Datenbank
    patient_db = find_patient_db()
    if not patient_db:
        print("FEHLER: Patienten-Datenbank nicht gefunden!")
        exit(1)

    print(f"Patienten-Datenbank gefunden: {patient_db}")

    # Führe Migration aus
    migration_file = 'MFA/migrations/005_add_patient_age_group.sql'
    if os.path.exists(migration_file):
        if run_migration(migration_file, patient_db):
            print("\nERFOLG: Migration erfolgreich abgeschlossen!")
            print("Die age_group-Spalte wurde zur patients-Tabelle hinzugefügt.")
        else:
            print("\nFEHLER: Migration fehlgeschlagen!")
            exit(1)
    else:
        print(f"FEHLER: Migration-Datei nicht gefunden: {migration_file}")
        exit(1)
