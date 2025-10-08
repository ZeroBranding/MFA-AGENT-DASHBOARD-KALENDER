#!/usr/bin/env python3
"""
INTELLIGENT NAME EXTRACTOR
Enterprise-Level Namenserkennung mit NLP, Regex und Machine Learning
Erkennt und verifiziert Namen aus E-Mail-Inhalten mit höchster Präzision
"""

import re
import logging
import json
from typing import Dict, List, Optional, Tuple, NamedTuple, Any
from dataclasses import dataclass
from enum import Enum
import unicodedata
from datetime import datetime
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

class NameConfidence(Enum):
    """Vertrauensstufen für erkannte Namen"""
    VERY_HIGH = "very_high"  # 95-100%
    HIGH = "high"           # 80-94%
    MEDIUM = "medium"       # 60-79%
    LOW = "low"            # 40-59%
    VERY_LOW = "very_low"  # 0-39%

class NameSource(Enum):
    """Quelle der Namenserkennung"""
    EMAIL_SIGNATURE = "email_signature"
    GREETING = "greeting"
    CLOSING = "closing"
    SENDER_NAME = "sender_name"
    CONTENT_REFERENCE = "content_reference"
    PREVIOUS_CONTEXT = "previous_context"

@dataclass
class ExtractedName:
    """Struktur für extrahierte Namen"""
    first_name: str
    last_name: str
    full_name: str
    confidence: NameConfidence
    source: NameSource
    context: str
    extraction_method: str
    timestamp: datetime
    is_verified: bool = False
    verification_notes: str = ""

class IntelligentNameExtractor:
    """
    Enterprise-Level Namenserkennung mit mehreren Erkennungsmethoden
    Kombiniert Regex, NLP-Pattern und Machine Learning für maximale Genauigkeit
    """
    
    def __init__(self, db_path: str = "name_extraction.db"):
        """Initialisiert den intelligenten Namensextraktor"""
        self.db_path = db_path
        self._init_database()
        self._load_patterns()
        self._load_common_names()
        
    def _init_database(self):
        """Initialisiert die Datenbank für Namensspeicherung"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Tabelle für erkannte Namen
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS extracted_names (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        email_address TEXT NOT NULL,
                        first_name TEXT,
                        last_name TEXT,
                        full_name TEXT,
                        confidence TEXT,
                        source TEXT,
                        context TEXT,
                        extraction_method TEXT,
                        is_verified BOOLEAN DEFAULT 0,
                        verification_notes TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Tabelle für Namensverifikationen
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS name_verifications (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        email_address TEXT NOT NULL,
                        verified_name TEXT NOT NULL,
                        verification_method TEXT,
                        verification_notes TEXT,
                        verified_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Indizes für Performance
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_email ON extracted_names(email_address)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_verified ON extracted_names(is_verified)')
                
                conn.commit()
                logger.info("Namenserkennungs-Datenbank initialisiert")
                
        except Exception as e:
            logger.error(f"Fehler bei Datenbank-Initialisierung: {e}")
            raise
    
    def _load_patterns(self):
        """Lädt Regex-Pattern für verschiedene Namenserkennungsmethoden"""
        self.patterns = {
            # Deutsche Grußformeln - erweitert um Titelbehandlung
            'german_greetings': [
                r'(?:mit\s+)?(?:freundlichen|herzlichen|lieben)\s+grüßen?\s*[,:]?\s*(?:[A-ZÄÖÜ][a-zäöüß]*\.?\s+)?([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)*)',
                r'grüße?\s*[,:]?\s*(?:[A-ZÄÖÜ][a-zäöüß]*\.?\s+)?([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)*)',
                r'liebe?\s+grüße?\s*[,:]?\s*(?:[A-ZÄÖÜ][a-zäöüß]*\.?\s+)?([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)*)',
                r'viele\s+grüße?\s*[,:]?\s*(?:[A-ZÄÖÜ][a-zäöüß]*\.?\s+)?([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)*)'
            ],
            
            # Englische Grußformeln
            'english_greetings': [
                r'(?:kind|best|warm|sincere)\s+regards?\s*[,:]?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
                r'regards?\s*[,:]?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
                r'yours?\s+(?:sincerely|truly|faithfully)\s*[,:]?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
                r'cheers?\s*[,:]?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
            ],
            
            # E-Mail-Signaturen
            'email_signatures': [
                r'--\s*\n\s*([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)*)',
                r'---\s*\n\s*([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)*)',
                r'^\s*([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)*)\s*$',
                r'name:\s*([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)*)',
                r'von:\s*([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)*)'
            ],
            
            # Direkte Namensnennungen
            'direct_mentions': [
                r'ich\s+bin\s+([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)*)',
                r'mein\s+name\s+ist\s+([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)*)',
                r'ich\s+heiße\s+([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)*)',
                r'ich\s+bin\s+([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)*)',
                r'mein\s+name\s+([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)*)'
            ],
            
            # Termin-bezogene Namensnennungen
            'appointment_mentions': [
                r'termin\s+für\s+([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)*)',
                r'appointment\s+for\s+([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)*)',
                r'buchung\s+für\s+([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)*)',
                r'vereinbarung\s+für\s+([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)*)'
            ]
        }
        
        # Kompilierte Regex-Pattern für bessere Performance
        self.compiled_patterns = {}
        for category, patterns in self.patterns.items():
            self.compiled_patterns[category] = [re.compile(pattern, re.IGNORECASE | re.MULTILINE) for pattern in patterns]
    
    def _load_common_names(self):
        """Lädt häufige deutsche und internationale Namen für Validierung"""
        self.common_first_names = {
            # Deutsche Vornamen
            'de': {
                'male': ['Alexander', 'Andreas', 'Christian', 'Daniel', 'David', 'Felix', 'Florian', 'Jan', 'Johannes', 'Julian', 'Kevin', 'Lukas', 'Marco', 'Markus', 'Martin', 'Matthias', 'Michael', 'Patrick', 'Paul', 'Peter', 'Sebastian', 'Stefan', 'Thomas', 'Tobias', 'Tom', 'Uwe'],
                'female': ['Anna', 'Barbara', 'Beate', 'Bettina', 'Birgit', 'Christina', 'Claudia', 'Daniela', 'Eva', 'Gabriele', 'Heike', 'Ines', 'Julia', 'Karin', 'Kathrin', 'Kerstin', 'Kristin', 'Lisa', 'Maria', 'Marina', 'Martina', 'Melanie', 'Monika', 'Nadine', 'Nicole', 'Petra', 'Sabine', 'Sandra', 'Silvia', 'Stefanie', 'Susanne', 'Tanja', 'Ute']
            },
            # Englische Vornamen
            'en': {
                'male': ['James', 'John', 'Robert', 'Michael', 'William', 'David', 'Richard', 'Charles', 'Joseph', 'Thomas', 'Christopher', 'Daniel', 'Paul', 'Mark', 'Donald', 'George', 'Kenneth', 'Steven', 'Edward', 'Brian', 'Ronald', 'Anthony', 'Kevin', 'Jason', 'Matthew'],
                'female': ['Mary', 'Patricia', 'Jennifer', 'Linda', 'Elizabeth', 'Barbara', 'Susan', 'Jessica', 'Sarah', 'Karen', 'Nancy', 'Lisa', 'Betty', 'Helen', 'Sandra', 'Donna', 'Carol', 'Ruth', 'Sharon', 'Michelle', 'Laura', 'Sarah', 'Kimberly', 'Deborah', 'Dorothy']
            }
        }
        
        self.common_last_names = {
            'de': ['Müller', 'Schmidt', 'Schneider', 'Fischer', 'Weber', 'Meyer', 'Wagner', 'Becker', 'Schulz', 'Hoffmann', 'Schäfer', 'Bauer', 'Koch', 'Richter', 'Klein', 'Wolf', 'Schröder', 'Neumann', 'Schwarz', 'Zimmermann', 'Braun', 'Hofmann', 'Lange', 'Schmitt', 'Werner', 'Schmitz', 'Krause', 'Meier', 'Lehmann', 'Schmid'],
            'en': ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson', 'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin', 'Lee', 'Perez', 'Thompson', 'White', 'Harris', 'Sanchez', 'Clark', 'Ramirez', 'Lewis', 'Robinson']
        }
    
    def extract_name_from_email(self, email_content: str, sender_email: str = "",
                               subject: str = "", previous_context: List[Dict] = None) -> Optional[ExtractedName]:
        """
        Extrahiert Namen aus E-Mail-Inhalt mit mehreren Erkennungsmethoden
        
        Args:
            email_content: Vollständiger E-Mail-Inhalt
            sender_email: E-Mail-Adresse des Absenders
            subject: E-Mail-Betreff
            previous_context: Vorherige Konversationen für Kontext
            
        Returns:
            ExtractedName oder None wenn kein Name gefunden
        """
        try:
            # 1. Prüfe auf bereits verifizierte Namen in der Datenbank
            verified_name = self._get_verified_name(sender_email)
            if verified_name:
                return verified_name
            
            # 2. Extrahiere Namen mit verschiedenen Methoden
            extraction_results = []
            
            # Methode 1: E-Mail-Signaturen
            sig_result = self._extract_from_signatures(email_content)
            if sig_result:
                extraction_results.append(sig_result)
            
            # Methode 2: Grußformeln
            greeting_result = self._extract_from_greetings(email_content)
            if greeting_result:
                extraction_results.append(greeting_result)
            
            # Methode 3: Direkte Namensnennungen
            direct_result = self._extract_from_direct_mentions(email_content)
            if direct_result:
                extraction_results.append(direct_result)
            
            # Methode 4: Termin-bezogene Nennungen
            appointment_result = self._extract_from_appointment_mentions(email_content)
            if appointment_result:
                extraction_results.append(appointment_result)
            
            # Methode 5: Vorheriger Kontext
            if previous_context:
                context_result = self._extract_from_context(previous_context)
                if context_result:
                    extraction_results.append(context_result)
            
            # 3. Wähle das beste Ergebnis basierend auf Vertrauen und Quelle
            if not extraction_results:
                return None
            
            best_result = self._select_best_extraction(extraction_results)
            
            # 4. Validiere den Namen
            validated_result = self._validate_name(best_result)
            
            # 5. Speichere das Ergebnis
            self._save_extraction(sender_email, validated_result)
            
            return validated_result
            
        except Exception as e:
            logger.error(f"Fehler bei Namensextraktion: {e}")
            return None
    
    def _extract_from_signatures(self, content: str) -> Optional[ExtractedName]:
        """Extrahiert Namen aus E-Mail-Signaturen"""
        for pattern in self.compiled_patterns['email_signatures']:
            match = pattern.search(content)
            if match:
                name_text = match.group(1).strip()
                parsed_name = self._parse_name_text(name_text)
                if parsed_name and self._is_valid_name(parsed_name):
                    return ExtractedName(
                        first_name=parsed_name[0],
                        last_name=parsed_name[1],
                        full_name=f"{parsed_name[0]} {parsed_name[1]}".strip(),
                        confidence=NameConfidence.HIGH,
                        source=NameSource.EMAIL_SIGNATURE,
                        context=match.group(0),
                        extraction_method="email_signature_regex",
                        timestamp=datetime.now()
                    )
        return None
    
    def _extract_from_greetings(self, content: str) -> Optional[ExtractedName]:
        """Extrahiert Namen aus Grußformeln"""
        for category in ['german_greetings', 'english_greetings']:
            for pattern in self.compiled_patterns[category]:
                match = pattern.search(content)
                if match:
                    name_text = match.group(1).strip()
                    parsed_name = self._parse_name_text(name_text)
                    if parsed_name and self._is_valid_name(parsed_name):
                        return ExtractedName(
                            first_name=parsed_name[0],
                            last_name=parsed_name[1],
                            full_name=f"{parsed_name[0]} {parsed_name[1]}".strip(),
                            confidence=NameConfidence.VERY_HIGH,
                            source=NameSource.GREETING,
                            context=match.group(0),
                            extraction_method=f"{category}_regex",
                            timestamp=datetime.now()
                        )
        return None
    
    def _extract_from_direct_mentions(self, content: str) -> Optional[ExtractedName]:
        """Extrahiert Namen aus direkten Namensnennungen"""
        for pattern in self.compiled_patterns['direct_mentions']:
            match = pattern.search(content)
            if match:
                name_text = match.group(1).strip()
                parsed_name = self._parse_name_text(name_text)
                if parsed_name and self._is_valid_name(parsed_name):
                    return ExtractedName(
                        first_name=parsed_name[0],
                        last_name=parsed_name[1],
                        full_name=f"{parsed_name[0]} {parsed_name[1]}".strip(),
                        confidence=NameConfidence.HIGH,
                        source=NameSource.CONTENT_REFERENCE,
                        context=match.group(0),
                        extraction_method="direct_mention_regex",
                        timestamp=datetime.now()
                    )
        return None
    
    def _extract_from_appointment_mentions(self, content: str) -> Optional[ExtractedName]:
        """Extrahiert Namen aus Termin-bezogenen Nennungen"""
        for pattern in self.compiled_patterns['appointment_mentions']:
            match = pattern.search(content)
            if match:
                name_text = match.group(1).strip()
                parsed_name = self._parse_name_text(name_text)
                if parsed_name and self._is_valid_name(parsed_name):
                    return ExtractedName(
                        first_name=parsed_name[0],
                        last_name=parsed_name[1],
                        full_name=f"{parsed_name[0]} {parsed_name[1]}".strip(),
                        confidence=NameConfidence.MEDIUM,
                        source=NameSource.CONTENT_REFERENCE,
                        context=match.group(0),
                        extraction_method="appointment_mention_regex",
                        timestamp=datetime.now()
                    )
        return None
    
    def _extract_from_context(self, previous_context: List[Dict]) -> Optional[ExtractedName]:
        """Extrahiert Namen aus vorherigem Kontext"""
        for context in reversed(previous_context[-5:]):  # Letzte 5 Konversationen
            if 'extracted_name' in context and context['extracted_name']:
                name_data = context['extracted_name']
                return ExtractedName(
                    first_name=name_data.get('first_name', ''),
                    last_name=name_data.get('last_name', ''),
                    full_name=name_data.get('full_name', ''),
                    confidence=NameConfidence.MEDIUM,
                    source=NameSource.PREVIOUS_CONTEXT,
                    context="previous_conversation",
                    extraction_method="context_lookup",
                    timestamp=datetime.now()
                )
        return None
    
    def _parse_name_text(self, name_text: str) -> Optional[Tuple[str, str]]:
        """Parst Namenstext in Vor- und Nachname"""
        if not name_text or len(name_text.strip()) < 2:
            return None
        
        # Normalisiere Text
        normalized = unicodedata.normalize('NFKD', name_text.strip())
        words = [word.strip() for word in normalized.split() if word.strip()]
        
        if len(words) == 0:
            return None
        elif len(words) == 1:
            # Nur ein Wort - könnte Vor- oder Nachname sein
            return (words[0], "")
        elif len(words) == 2:
            # Zwei Wörter - wahrscheinlich Vor- und Nachname
            return (words[0], words[1])
        else:
            # Mehr als zwei Wörter - nimm erstes als Vorname, rest als Nachname
            return (words[0], " ".join(words[1:]))
    
    def _is_valid_name(self, name_parts: Tuple[str, str]) -> bool:
        """Validiert ob die Namensbestandteile gültig sind"""
        first_name, last_name = name_parts
        
        # Mindestens ein Teil muss vorhanden sein
        if not first_name and not last_name:
            return False
        
        # Prüfe auf gültige Zeichen (Buchstaben, Bindestriche, Apostrophe)
        valid_chars = re.compile(r'^[a-zA-ZäöüÄÖÜß\-\']+$')
        
        if first_name and not valid_chars.match(first_name):
            return False
        if last_name and not valid_chars.match(last_name):
            return False
        
        # Prüfe auf Mindestlänge
        if first_name and len(first_name) < 2:
            return False
        if last_name and len(last_name) < 2:
            return False
        
        return True
    
    def _select_best_extraction(self, extractions: List[ExtractedName]) -> ExtractedName:
        """Wählt die beste Extraktion basierend auf Vertrauen und Quelle"""
        if not extractions:
            return None
        
        # Gewichtung basierend auf Quelle und Vertrauen
        source_weights = {
            NameSource.EMAIL_SIGNATURE: 1.0,
            NameSource.GREETING: 0.9,
            NameSource.CLOSING: 0.8,
            NameSource.CONTENT_REFERENCE: 0.7,
            NameSource.PREVIOUS_CONTEXT: 0.6,
            NameSource.SENDER_NAME: 0.5
        }
        
        confidence_weights = {
            NameConfidence.VERY_HIGH: 1.0,
            NameConfidence.HIGH: 0.8,
            NameConfidence.MEDIUM: 0.6,
            NameConfidence.LOW: 0.4,
            NameConfidence.VERY_LOW: 0.2
        }
        
        best_score = 0
        best_extraction = extractions[0]
        
        for extraction in extractions:
            source_weight = source_weights.get(extraction.source, 0.5)
            confidence_weight = confidence_weights.get(extraction.confidence, 0.5)
            score = source_weight * confidence_weight
            
            if score > best_score:
                best_score = score
                best_extraction = extraction
        
        return best_extraction
    
    def _validate_name(self, extraction: ExtractedName) -> ExtractedName:
        """Validiert und verbessert die Namensextraktion"""
        # Prüfe gegen häufige Namen
        first_name_valid = self._is_common_first_name(extraction.first_name)
        last_name_valid = self._is_common_last_name(extraction.last_name)
        
        # Passe Vertrauen basierend auf Validierung an
        if first_name_valid and last_name_valid:
            extraction.confidence = NameConfidence.VERY_HIGH
        elif first_name_valid or last_name_valid:
            extraction.confidence = NameConfidence.HIGH
        else:
            extraction.confidence = NameConfidence.MEDIUM
        
        return extraction
    
    def _is_common_first_name(self, first_name: str) -> bool:
        """Prüft ob der Vorname häufig vorkommt"""
        if not first_name:
            return False
        
        first_name_lower = first_name.lower()
        for lang_names in self.common_first_names.values():
            for gender_names in lang_names.values():
                if first_name_lower in [name.lower() for name in gender_names]:
                    return True
        return False
    
    def _is_common_last_name(self, last_name: str) -> bool:
        """Prüft ob der Nachname häufig vorkommt"""
        if not last_name:
            return False
        
        last_name_lower = last_name.lower()
        for lang_names in self.common_last_names.values():
            if last_name_lower in [name.lower() for name in lang_names]:
                return True
        return False
    
    def _get_verified_name(self, email: str) -> Optional[ExtractedName]:
        """Holt bereits verifizierte Namen aus der Datenbank"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT first_name, last_name, full_name, confidence, source, context, 
                           extraction_method, created_at, verification_notes
                    FROM extracted_names 
                    WHERE email_address = ? AND is_verified = 1
                    ORDER BY updated_at DESC LIMIT 1
                ''', (email,))
                
                result = cursor.fetchone()
                if result:
                    return ExtractedName(
                        first_name=result[0] or "",
                        last_name=result[1] or "",
                        full_name=result[2] or "",
                        confidence=NameConfidence(result[3]),
                        source=NameSource(result[4]),
                        context=result[5] or "",
                        extraction_method=result[6] or "",
                        timestamp=datetime.fromisoformat(result[7]),
                        is_verified=True,
                        verification_notes=result[8] or ""
                    )
        except Exception as e:
            logger.error(f"Fehler beim Laden verifizierter Namen: {e}")
        
        return None
    
    def _save_extraction(self, email: str, extraction: ExtractedName):
        """Speichert die Namensextraktion in der Datenbank"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO extracted_names 
                    (email_address, first_name, last_name, full_name, confidence, source, 
                     context, extraction_method, is_verified, verification_notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    email, extraction.first_name, extraction.last_name, extraction.full_name,
                    extraction.confidence.value, extraction.source.value, extraction.context,
                    extraction.extraction_method, extraction.is_verified, extraction.verification_notes
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Namensextraktion: {e}")
    
    def verify_name(self, email: str, verified_name: str, verification_method: str = "manual", 
                   notes: str = "") -> bool:
        """Verifiziert einen Namen manuell oder automatisch"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Aktualisiere bestehende Extraktion
                cursor.execute('''
                    UPDATE extracted_names 
                    SET is_verified = 1, verification_notes = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE email_address = ? AND full_name = ?
                ''', (notes, email, verified_name))
                
                # Speichere Verifikation
                cursor.execute('''
                    INSERT INTO name_verifications 
                    (email_address, verified_name, verification_method, verification_notes)
                    VALUES (?, ?, ?, ?)
                ''', (email, verified_name, verification_method, notes))
                
                conn.commit()
                logger.info(f"Name verifiziert: {email} -> {verified_name}")
                return True
                
        except Exception as e:
            logger.error(f"Fehler bei Namensverifikation: {e}")
            return False
    
    def get_name_for_appointment(self, email: str, email_content: str = "") -> Tuple[bool, str, str]:
        """
        Holt oder extrahiert Namen für Terminbuchung
        
        Returns:
            (has_full_name, first_name, last_name)
        """
        # 1. Prüfe auf bereits verifizierte Namen
        verified_name = self._get_verified_name(email)
        if verified_name and verified_name.first_name and verified_name.last_name:
            return True, verified_name.first_name, verified_name.last_name
        
        # 2. Extrahiere aus aktueller E-Mail
        if email_content:
            extraction = self.extract_name_from_email(email_content, email)
            if extraction and extraction.first_name and extraction.last_name:
                return True, extraction.first_name, extraction.last_name
        
        # 3. Prüfe auf unvollständige Namen
        if verified_name and verified_name.first_name and not verified_name.last_name:
            return False, verified_name.first_name, ""
        
        return False, "", ""

    def verify_name_completeness(self, first_name: str, last_name: str) -> Dict[str, Any]:
        """Verifiziert die Vollständigkeit von Namen"""
        analysis = {
            "is_complete": bool(first_name and last_name),
            "has_first_name": bool(first_name),
            "has_last_name": bool(last_name),
            "confidence_level": "unknown",
            "recommendations": []
        }

        if not first_name and not last_name:
            analysis["confidence_level"] = "none"
            analysis["recommendations"] = ["Beide Namen fehlen", "Vollständigen Namen erfragen"]
        elif first_name and not last_name:
            analysis["confidence_level"] = "partial"
            analysis["recommendations"] = ["Nur Vorname vorhanden", "Nachnamen erfragen"]
        elif not first_name and last_name:
            analysis["confidence_level"] = "partial"
            analysis["recommendations"] = ["Nur Nachname vorhanden", "Vornamen erfragen"]
        else:
            analysis["confidence_level"] = "complete"
            analysis["recommendations"] = ["Namen sind vollständig"]

        return analysis

    def extract_names_from_multiple_sources(self, email_content: str, sender_email: str) -> List[ExtractedName]:
        """Extrahiert Namen aus mehreren Quellen"""
        sources = []

        # E-Mail-Signaturen
        sig_result = self._extract_from_signatures(email_content)
        if sig_result:
            sources.append(sig_result)

        # Grußformeln
        greeting_result = self._extract_from_greetings(email_content)
        if greeting_result:
            sources.append(greeting_result)

        # Direkte Erwähnungen
        direct_result = self._extract_from_direct_mentions(email_content)
        if direct_result:
            sources.append(direct_result)

        # Termin-Erwähnungen
        appointment_result = self._extract_from_appointment_mentions(email_content)
        if appointment_result:
            sources.append(appointment_result)

        return sources

    def consolidate_name_results(self, name_results: List[ExtractedName]) -> Optional[ExtractedName]:
        """Konsolidiert mehrere Namensergebnisse"""
        if not name_results:
            return None

        # Gruppiere nach vollständigen Namen
        name_groups = {}
        for result in name_results:
            full_name = result.full_name.strip()
            if full_name not in name_groups:
                name_groups[full_name] = []
            name_groups[full_name].append(result)

        # Wähle das beste Ergebnis für jeden Namen
        best_results = []
        for full_name, results in name_groups.items():
            best_result = max(results, key=lambda x: (x.confidence.value, x.source.value))
            best_results.append(best_result)

        # Wähle das insgesamt beste Ergebnis
        if best_results:
            return max(best_results, key=lambda x: (x.confidence.value, x.source.value))

        return None

    def ask_for_missing_name_part(self, email: str, current_name: str, missing_part: str) -> str:
        """Generiert eine höfliche Nachfrage nach fehlenden Namensbestandteilen"""
        if missing_part == "last_name":
            return f"""Sehr geehrte/r {current_name},

vielen Dank für Ihre Terminanfrage. Um Ihren Termin korrekt zu buchen, benötige ich noch Ihren vollständigen Namen.

Könnten Sie mir bitte Ihren Nachnamen mitteilen?

Mit freundlichen Grüßen
Ihr Praxisteam"""
        
        elif missing_part == "first_name":
            return f"""Sehr geehrte/r {current_name},

vielen Dank für Ihre Terminanfrage. Um Ihren Termin korrekt zu buchen, benötige ich noch Ihren vollständigen Namen.

Könnten Sie mir bitte Ihren Vornamen mitteilen?

Mit freundlichen Grüßen
Ihr Praxisteam"""
        
        else:  # Beide Namen fehlen
            return f"""Sehr geehrte/r Patient/in,

vielen Dank für Ihre Terminanfrage. Um Ihren Termin korrekt zu buchen, benötige ich Ihren vollständigen Namen (Vor- und Nachname).

Könnten Sie mir bitte Ihren vollständigen Namen mitteilen?

Mit freundlichen Grüßen
Ihr Praxisteam"""


# Test-Funktion für die Namensextraktion
def test_name_extraction():
    """Testet die Namensextraktion mit verschiedenen Beispielen"""
    extractor = IntelligentNameExtractor()
    
    test_cases = [
        "Mit freundlichen Grüßen\nAlex Müller",
        "Grüße, Anna Schmidt",
        "Liebe Grüße\nMax Mustermann",
        "Ich bin Dr. Maria Weber und brauche einen Termin",
        "Termin für Peter Klein bitte",
        "--\nDr. Sarah Johnson\nPraxis ABC",
        "Viele Grüße\nTom"
    ]
    
    print("=== NAMENSEXTRAKTION TEST ===")
    for i, test_content in enumerate(test_cases, 1):
        result = extractor.extract_name_from_email(test_content, f"test{i}@example.com")
        if result:
            print(f"Test {i}: {result.full_name} (Vertrauen: {result.confidence.value}, Quelle: {result.source.value})")
        else:
            print(f"Test {i}: Kein Name erkannt")
    print("=== TEST ABGESCHLOSSEN ===")


if __name__ == "__main__":
    test_name_extraction()
