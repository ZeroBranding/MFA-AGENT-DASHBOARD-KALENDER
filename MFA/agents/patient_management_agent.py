#!/usr/bin/env python3
"""
PATIENTEN-MANAGEMENT-AGENT
Zentrale Patienten-Datenbank und Profil-Verwaltung
"""

import sqlite3
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class PatientStatus(Enum):
    """Patienten-Status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DECEASED = "deceased"
    MOVED = "moved"

@dataclass
class PatientProfile:
    """Vollständiges Patienten-Profil"""
    patient_id: str
    email: str
    name: str = ""
    phone: str = ""
    date_of_birth: str = ""
    address: str = ""
    emergency_contact: str = ""
    medical_history: List[str] = None
    allergies: List[str] = None
    medications: List[str] = None
    insurance_info: str = ""
    language_preference: str = "de"
    communication_style: str = "formal"  # formal, friendly, direct
    age_group: str = "unknown"  # child, adult, senior
    last_contact: Optional[datetime] = None
    appointment_count: int = 0
    status: PatientStatus = PatientStatus.ACTIVE
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        if self.medical_history is None:
            self.medical_history = []
        if self.allergies is None:
            self.allergies = []
        if self.medications is None:
            self.medications = []
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

class PatientManagementAgent:
    """Zentraler Patienten-Management-Agent"""

    def __init__(self, db_path: str = "patient_profiles.db"):
        """Initialisiert den Patienten-Management-Agent"""
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Initialisiert die Patienten-Datenbank"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Erstelle Tabelle mit allen Feldern
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS patients (
                        patient_id TEXT PRIMARY KEY,
                        email TEXT NOT NULL,
                        name TEXT,
                        phone TEXT,
                        date_of_birth TEXT,
                        address TEXT,
                        emergency_contact TEXT,
                        medical_history TEXT,
                        allergies TEXT,
                        medications TEXT,
                        insurance_info TEXT,
                        language_preference TEXT DEFAULT 'de',
                        communication_style TEXT DEFAULT 'formal',
                        age_group TEXT DEFAULT 'unknown',
                        last_contact TEXT,
                        appointment_count INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')

                # Erstelle Indizes
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_patients_email ON patients(email)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_patients_status ON patients(status)')

                conn.commit()
                logger.info("Patienten-Datenbank initialisiert")

        except Exception as e:
            logger.error(f"Fehler bei Datenbank-Initialisierung: {e}")

    def create_or_update_profile(self, email: str, profile_data: Dict[str, Any]) -> PatientProfile:
        """Erstellt oder aktualisiert ein Patienten-Profil"""
        try:
            # Pruefe ob Patient bereits existiert
            existing_profile = self.get_profile_by_email(email)

            if existing_profile:
                # Update bestehendes Profil
                return self._update_profile(existing_profile.patient_id, profile_data)
            else:
                # Erstelle neues Profil
                return self._create_profile(email, profile_data)

        except Exception as e:
            logger.error(f"Fehler beim Profil-Update: {e}")
            raise

    def _create_profile(self, email: str, profile_data: Dict[str, Any]) -> PatientProfile:
        """Erstellt ein neues Patienten-Profil"""
        patient_id = f"patient_{int(datetime.now().timestamp())}_{email.split('@')[0]}"

        # Entferne email aus profile_data
        profile_data_copy = profile_data.copy()
        profile_data_copy.pop("email", None)

        profile = PatientProfile(
            patient_id=patient_id,
            email=email,
            **profile_data_copy
        )

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    INSERT INTO patients (
                        patient_id, email, name, phone, date_of_birth, address,
                        emergency_contact, medical_history, allergies, medications,
                        insurance_info, language_preference, communication_style, age_group,
                        last_contact, appointment_count, status, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    profile.patient_id, profile.email, profile.name, profile.phone,
                    profile.date_of_birth, profile.address, profile.emergency_contact,
                    json.dumps(profile.medical_history), json.dumps(profile.allergies),
                    json.dumps(profile.medications), profile.insurance_info,
                    profile.language_preference, profile.communication_style, profile.age_group,
                    profile.last_contact.isoformat() if profile.last_contact else None,
                    profile.appointment_count, profile.status.value,
                    profile.created_at.isoformat(), profile.updated_at.isoformat()
                ))

                conn.commit()
                logger.info(f"Neues Patienten-Profil erstellt: {patient_id}")
                return profile

        except Exception as e:
            logger.error(f"Fehler beim Profil-Erstellen: {e}")
            raise

    def _update_profile(self, patient_id: str, profile_data: Dict[str, Any]) -> PatientProfile:
        """Aktualisiert ein bestehendes Patienten-Profil"""
        try:
            # Hole aktuelles Profil
            current_profile = self.get_profile_by_id(patient_id)
            if not current_profile:
                raise ValueError(f"Patient {patient_id} nicht gefunden")

            # Aktualisiere Felder
            for key, value in profile_data.items():
                if hasattr(current_profile, key):
                    setattr(current_profile, key, value)

            current_profile.updated_at = datetime.now()
            current_profile.appointment_count += 1

            # Speichere in Datenbank
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    UPDATE patients SET
                        name = ?, phone = ?, date_of_birth = ?, address = ?,
                        emergency_contact = ?, medical_history = ?, allergies = ?,
                        medications = ?, insurance_info = ?, language_preference = ?,
                        communication_style = ?, age_group = ?, last_contact = ?, appointment_count = ?,
                        status = ?, updated_at = ?
                    WHERE patient_id = ?
                ''', (
                    current_profile.name, current_profile.phone, current_profile.date_of_birth,
                    current_profile.address, current_profile.emergency_contact,
                    json.dumps(current_profile.medical_history), json.dumps(current_profile.allergies),
                    json.dumps(current_profile.medications), current_profile.insurance_info,
                    current_profile.language_preference, current_profile.communication_style, current_profile.age_group,
                    current_profile.last_contact.isoformat() if current_profile.last_contact else None,
                    current_profile.appointment_count, current_profile.status.value,
                    current_profile.updated_at.isoformat(), patient_id
                ))

                conn.commit()
                logger.info(f"Patienten-Profil aktualisiert: {patient_id}")
                return current_profile

        except Exception as e:
            logger.error(f"Fehler beim Profil-Update: {e}")
            raise

    def get_profile_by_email(self, email: str) -> Optional[PatientProfile]:
        """Holt Patienten-Profil per E-Mail"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM patients WHERE email = ?', (email,))
                row = cursor.fetchone()

            if row:
                return self._row_to_profile(row)
            return None

        except Exception as e:
            logger.error(f"Fehler beim Profil-Abrufen: {e}")
            return None

    def get_profile_by_id(self, patient_id: str) -> Optional[PatientProfile]:
        """Holt Patienten-Profil per ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM patients WHERE patient_id = ?', (patient_id,))
                row = cursor.fetchone()

            if row:
                return self._row_to_profile(row)
            return None

        except Exception as e:
            logger.error(f"Fehler beim Profil-Abrufen: {e}")
            return None

    def _row_to_profile(self, row) -> PatientProfile:
        """Konvertiert Datenbank-Row zu PatientProfile"""
        def _safe_fromiso(value):
            try:
                if value and isinstance(value, str):
                    return datetime.fromisoformat(value)
            except Exception:
                logger.warning(f"_safe_fromiso: could not parse date: {value}")
            return None

        return PatientProfile(
            patient_id=row[0],
            email=row[1],
            name=row[2] or "",
            phone=row[3] or "",
            date_of_birth=row[4] or "",
            address=row[5] or "",
            emergency_contact=row[6] or "",
            medical_history=json.loads(row[7]) if row[7] else [],
            allergies=json.loads(row[8]) if row[8] else [],
            medications=json.loads(row[9]) if row[9] else [],
            insurance_info=row[10] or "",
            language_preference=row[11] or "de",
            communication_style=row[12] or "formal",
            age_group=row[13] if len(row) > 13 and row[13] else "unknown",
            last_contact=_safe_fromiso(row[14]) if len(row) > 14 else None,
            appointment_count=row[15] or 0,
            status=PatientStatus(row[16]) if row[16] else PatientStatus.ACTIVE,
            created_at=_safe_fromiso(row[17]) or datetime.now(),
            updated_at=_safe_fromiso(row[18]) or datetime.now()
        )

    def update_last_contact(self, email: str):
        """Aktualisiert den letzten Kontakt eines Patienten"""
        try:
            profile = self.get_profile_by_email(email)
            if profile:
                self._update_profile(profile.patient_id, {"last_contact": datetime.now()})
        except Exception as e:
            logger.error(f"Fehler beim Kontakt-Update: {e}")
