#!/usr/bin/env python3
"""
ADVANCED CHAT HISTORY SYSTEM
Enterprise-Level Chat-Historie mit Kontextanalyse und Thread-Management
Speichert und analysiert Konversationen für menschlichere Interaktionen
"""

import sqlite3
import logging
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import re
from pathlib import Path

logger = logging.getLogger(__name__)

class ConversationStatus(Enum):
    """Status einer Konversation"""
    ACTIVE = "active"
    RESOLVED = "resolved"
    PENDING = "pending"
    ESCALATED = "escalated"
    ARCHIVED = "archived"

class MessageType(Enum):
    """Typ einer Nachricht"""
    INCOMING = "incoming"
    OUTGOING = "outgoing"
    SYSTEM = "system"
    APPOINTMENT = "appointment"
    FOLLOW_UP = "follow_up"

class ContextType(Enum):
    """Typ des Kontexts"""
    APPOINTMENT_BOOKING = "appointment_booking"
    MEDICAL_INQUIRY = "medical_inquiry"
    PRESCRIPTION_REQUEST = "prescription_request"
    GENERAL_QUESTION = "general_question"
    COMPLAINT = "complaint"
    FOLLOW_UP = "follow_up"

@dataclass
class ConversationMessage:
    """Struktur für eine Konversationsnachricht"""
    message_id: str
    thread_id: str
    email_address: str
    subject: str
    content: str
    message_type: MessageType
    intent_type: str
    confidence: float
    entities: Dict[str, Any]
    context_type: ContextType
    timestamp: datetime
    is_processed: bool = False
    response_generated: bool = False
    extracted_name: Optional[Dict[str, Any]] = None
    sentiment: Optional[str] = None
    urgency_level: Optional[str] = None

@dataclass
class ConversationContext:
    """Kontext einer Konversation"""
    thread_id: str
    email_address: str
    primary_intent: str
    context_type: ContextType
    status: ConversationStatus
    created_at: datetime
    last_activity: datetime
    message_count: int
    patient_name: Optional[str] = None
    appointment_id: Optional[str] = None
    medical_context: Optional[Dict[str, Any]] = None
    preferences: Optional[Dict[str, Any]] = None
    escalation_notes: Optional[str] = None

class AdvancedChatHistory:
    """
    Enterprise-Level Chat-Historie-System
    Verwaltet Konversationen mit erweiterten Kontextanalysen
    """
    
    def __init__(self, db_path: str = "advanced_chat_history.db"):
        """Initialisiert das erweiterte Chat-Historie-System"""
        self.db_path = db_path
        self._init_database()
        self._load_context_patterns()
        
    def _init_database(self):
        """Initialisiert die Datenbank für Chat-Historie"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Tabelle für Konversationskontext
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS conversation_contexts (
                        thread_id TEXT PRIMARY KEY,
                        email_address TEXT NOT NULL,
                        primary_intent TEXT,
                        context_type TEXT,
                        status TEXT DEFAULT 'active',
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
                        message_count INTEGER DEFAULT 0,
                        patient_name TEXT,
                        appointment_id TEXT,
                        medical_context TEXT,  -- JSON
                        preferences TEXT,     -- JSON
                        escalation_notes TEXT
                    )
                ''')
                
                # Tabelle für Nachrichten
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS conversation_messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        message_id TEXT UNIQUE NOT NULL,
                        thread_id TEXT NOT NULL,
                        email_address TEXT NOT NULL,
                        subject TEXT,
                        content TEXT NOT NULL,
                        message_type TEXT NOT NULL,
                        intent_type TEXT,
                        confidence REAL,
                        entities TEXT,  -- JSON
                        context_type TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        is_processed BOOLEAN DEFAULT 0,
                        response_generated BOOLEAN DEFAULT 0,
                        extracted_name TEXT,  -- JSON
                        sentiment TEXT,
                        urgency_level TEXT,
                        FOREIGN KEY (thread_id) REFERENCES conversation_contexts(thread_id)
                    )
                ''')
                
                # Tabelle für Kontextanalyse
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS context_analysis (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        thread_id TEXT NOT NULL,
                        analysis_type TEXT NOT NULL,
                        analysis_data TEXT NOT NULL,  -- JSON
                        confidence REAL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (thread_id) REFERENCES conversation_contexts(thread_id)
                    )
                ''')
                
                # Tabelle für Thread-Änderungen
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS thread_changes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        thread_id TEXT NOT NULL,
                        old_subject TEXT,
                        new_subject TEXT,
                        change_reason TEXT,
                        changed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (thread_id) REFERENCES conversation_contexts(thread_id)
                    )
                ''')
                
                # Indizes für Performance
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_email ON conversation_contexts(email_address)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON conversation_contexts(status)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_message_thread ON conversation_messages(thread_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_message_email ON conversation_messages(email_address)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_message_timestamp ON conversation_messages(timestamp)')
                
                conn.commit()
                logger.info("Erweiterte Chat-Historie-Datenbank initialisiert")
                
        except Exception as e:
            logger.error(f"Fehler bei Datenbank-Initialisierung: {e}")
            raise
    
    def _load_context_patterns(self):
        """Lädt Pattern für Kontextanalyse"""
        self.context_patterns = {
            ContextType.APPOINTMENT_BOOKING: [
                r'termin', r'appointment', r'buchung', r'vereinbarung',
                r'wann.*kann', r'verfügbar', r'kalender'
            ],
            ContextType.MEDICAL_INQUIRY: [
                r'schmerzen', r'symptom', r'krank', r'untersuchung',
                r'behandlung', r'diagnose', r'medizin'
            ],
            ContextType.PRESCRIPTION_REQUEST: [
                r'rezept', r'medikament', r'verschreibung', r'nachfüllen',
                r'medizin', r'arznei'
            ],
            ContextType.COMPLAINT: [
                r'beschwerde', r'problem', r'unzufrieden', r'fehler',
                r'falsch', r'nicht.*funktioniert'
            ],
            ContextType.FOLLOW_UP: [
                r'nachfrage', r'folge', r'update', r'status',
                r'wie.*geht', r'fortschritt'
            ]
        }
        
        # Kompilierte Pattern für bessere Performance
        self.compiled_patterns = {}
        for context_type, patterns in self.context_patterns.items():
            self.compiled_patterns[context_type] = [
                re.compile(pattern, re.IGNORECASE) for pattern in patterns
            ]
    
    def generate_thread_id(self, email_address: str, subject: str, content: str) -> str:
        """Generiert eine eindeutige Thread-ID basierend auf E-Mail-Adresse und Inhalt"""
        # Normalisiere Subject (entferne Re: Fwd: etc.)
        normalized_subject = re.sub(r'^(re:|fwd?:|aw:)\s*', '', subject, flags=re.IGNORECASE).strip()
        
        # Erstelle Hash aus E-Mail-Adresse und normalisiertem Subject
        hash_input = f"{email_address}:{normalized_subject}"
        thread_hash = hashlib.md5(hash_input.encode()).hexdigest()[:16]
        
        return f"thread_{thread_hash}"
    
    def store_message(self, message: ConversationMessage) -> bool:
        """Speichert eine Nachricht in der Chat-Historie"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Konvertiere EntityType-Keys zu Strings für JSON-Serialisierung
                entities_for_db = {k.value if hasattr(k, 'value') else str(k): v for k, v in message.entities.items()}

                # Speichere Nachricht
                cursor.execute('''
                    INSERT OR REPLACE INTO conversation_messages
                    (message_id, thread_id, email_address, subject, content, message_type,
                     intent_type, confidence, entities, context_type, timestamp, is_processed,
                     response_generated, extracted_name, sentiment, urgency_level)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    message.message_id, message.thread_id, message.email_address,
                    message.subject, message.content, message.message_type.value,
                    message.intent_type, message.confidence, json.dumps(entities_for_db),
                    message.context_type.value, message.timestamp.isoformat(),
                    message.is_processed, message.response_generated,
                    json.dumps(message.extracted_name) if isinstance(message.extracted_name, dict) else (
                        json.dumps(asdict(message.extracted_name)) if hasattr(message.extracted_name, '__dataclass_fields__') else None
                    ),
                    message.sentiment, message.urgency_level
                ))
                
                # Aktualisiere Konversationskontext
                self._update_conversation_context(message)
                
                conn.commit()
                logger.info(f"Nachricht gespeichert: {message.message_id}")
                return True
                
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Nachricht: {e}")
            return False
    
    def _update_conversation_context(self, message: ConversationMessage):
        """Aktualisiert den Konversationskontext"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Prüfe ob Kontext bereits existiert
                cursor.execute('SELECT * FROM conversation_contexts WHERE thread_id = ?', (message.thread_id,))
                existing_context = cursor.fetchone()
                
                if existing_context:
                    # Aktualisiere bestehenden Kontext
                    cursor.execute('''
                        UPDATE conversation_contexts SET
                            last_activity = CURRENT_TIMESTAMP,
                            message_count = message_count + 1,
                            primary_intent = COALESCE(?, primary_intent),
                            context_type = COALESCE(?, context_type),
                            patient_name = COALESCE(?, patient_name)
                        WHERE thread_id = ?
                    ''', (
                        message.intent_type, message.context_type.value,
                        message.extracted_name.get('full_name') if message.extracted_name else None,
                        message.thread_id
                    ))
                else:
                    # Erstelle neuen Kontext
                    cursor.execute('''
                        INSERT INTO conversation_contexts
                        (thread_id, email_address, primary_intent, context_type, status,
                         created_at, last_activity, message_count, patient_name)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        message.thread_id, message.email_address, message.intent_type,
                        message.context_type.value, ConversationStatus.ACTIVE.value,
                        message.timestamp.isoformat(), message.timestamp.isoformat(),
                        1, message.extracted_name.get('full_name') if message.extracted_name else None
                    ))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Fehler beim Aktualisieren des Konversationskontexts: {e}")
    
    def get_conversation_history(self, email_address: str, limit: int = 10) -> List[ConversationMessage]:
        """Holt die Chat-Historie für eine E-Mail-Adresse"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT message_id, thread_id, email_address, subject, content, message_type,
                           intent_type, confidence, entities, context_type, timestamp, is_processed,
                           response_generated, extracted_name, sentiment, urgency_level
                    FROM conversation_messages
                    WHERE email_address = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (email_address, limit))
                
                messages = []
                for row in cursor.fetchall():
                    # Konvertiere entities zurück von strings zu EntityType-Objekten
                    entities_raw = json.loads(row[8]) if row[8] else {}
                    entities_converted = {}

                    # Importiere EntityType hier, um zirkuläre Imports zu vermeiden
                    from enterprise_nlu import EntityType
                    for key_str, value in entities_raw.items():
                        try:
                            # Versuche, den String zurück zu EntityType zu konvertieren
                            entities_converted[EntityType(key_str)] = value
                        except ValueError:
                            # Fallback: behalte als String
                            entities_converted[key_str] = value

                    message = ConversationMessage(
                        message_id=row[0],
                        thread_id=row[1],
                        email_address=row[2],
                        subject=row[3] or "",
                        content=row[4],
                        message_type=MessageType(row[5]),
                        intent_type=row[6] or "",
                        confidence=row[7] or 0.0,
                        entities=entities_converted,
                        context_type=ContextType(row[9]) if row[9] else ContextType.GENERAL_QUESTION,
                        timestamp=datetime.fromisoformat(row[10]),
                        is_processed=bool(row[11]),
                        response_generated=bool(row[12]),
                        extracted_name=json.loads(row[13]) if row[13] else None,
                        sentiment=row[14],
                        urgency_level=row[15]
                    )
                    messages.append(message)
                
                return messages
                
        except Exception as e:
            logger.error(f"Fehler beim Laden der Chat-Historie: {e}")
            return []
    
    def get_thread_context(self, thread_id: str) -> Optional[ConversationContext]:
        """Holt den Kontext für einen Thread"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT thread_id, email_address, primary_intent, context_type, status,
                           created_at, last_activity, message_count, patient_name,
                           appointment_id, medical_context, preferences, escalation_notes
                    FROM conversation_contexts
                    WHERE thread_id = ?
                ''', (thread_id,))
                
                row = cursor.fetchone()
                if row:
                    return ConversationContext(
                        thread_id=row[0],
                        email_address=row[1],
                        primary_intent=row[2] or "",
                        context_type=ContextType(row[3]) if row[3] else ContextType.GENERAL_QUESTION,
                        status=ConversationStatus(row[4]),
                        created_at=datetime.fromisoformat(row[5]),
                        last_activity=datetime.fromisoformat(row[6]),
                        message_count=row[7],
                        patient_name=row[8],
                        appointment_id=row[9],
                        medical_context=json.loads(row[10]) if row[10] else None,
                        preferences=json.loads(row[11]) if row[11] else None,
                        escalation_notes=row[12]
                    )
                
        except Exception as e:
            logger.error(f"Fehler beim Laden des Thread-Kontexts: {e}")
        
        return None
    
    def analyze_conversation_context(self, email_content: str, email_address: str) -> ContextType:
        """Analysiert den Kontext einer Konversation"""
        content_lower = email_content.lower()

        # Prüfe Pattern für verschiedene Kontexttypen
        context_scores = {}
        for context_type, patterns in self.compiled_patterns.items():
            score = 0
            for pattern in patterns:
                matches = pattern.findall(content_lower)
                score += len(matches)
            context_scores[context_type] = score

        # Wähle Kontext mit höchstem Score
        if context_scores:
            best_context = max(context_scores.items(), key=lambda x: x[1])
            if best_context[1] > 0:
                return best_context[0]

        return ContextType.GENERAL_QUESTION

    def get_conversation_flow_analysis(self, email_address: str) -> Dict[str, Any]:
        """Analysiert den Gesprächsfluss für eine E-Mail-Adresse"""
        try:
            history = self.get_conversation_history(email_address, limit=20)

            if not history:
                return {"analysis": "Keine Konversationen gefunden", "flow": []}

            # Analysiere Gesprächsfluss
            flow = []
            for i, msg in enumerate(history):
                flow_entry = {
                    "message_index": i,
                    "timestamp": msg.timestamp.isoformat(),
                    "intent": msg.intent_type,
                    "context": msg.context_type.value,
                    "message_type": msg.message_type.value,
                    "urgency": msg.urgency_level,
                    "has_response": msg.response_generated
                }
                flow.append(flow_entry)

            # Identifiziere Muster
            intent_sequence = [msg.intent_type for msg in history if msg.intent_type]
            context_sequence = [msg.context_type.value for msg in history]

            # Finde häufigste Sequenzen
            intent_patterns = self._find_frequent_sequences(intent_sequence, 3)
            context_patterns = self._find_frequent_sequences(context_sequence, 3)

            return {
                "analysis": "Gesprächsfluss analysiert",
                "total_messages": len(history),
                "flow": flow,
                "intent_patterns": intent_patterns,
                "context_patterns": context_patterns,
                "avg_confidence": sum(msg.confidence for msg in history if msg.confidence) / len([msg for msg in history if msg.confidence])
            }

        except Exception as e:
            logger.error(f"Fehler bei Gesprächsfluss-Analyse: {e}")
            return {"analysis": "Fehler bei Analyse", "flow": []}

    def _find_frequent_sequences(self, sequence: List[str], max_length: int) -> List[Tuple[str, int]]:
        """Findet häufige Sequenzen in einer Liste"""
        from collections import defaultdict

        patterns = defaultdict(int)

        for length in range(2, min(max_length + 1, len(sequence))):
            for i in range(len(sequence) - length + 1):
                pattern = " -> ".join(sequence[i:i+length])
                patterns[pattern] += 1

        # Sortiere nach Häufigkeit
        return sorted(patterns.items(), key=lambda x: x[1], reverse=True)[:5]
    
    def get_contextual_summary(self, email_address: str) -> Dict[str, Any]:
        """Erstellt eine kontextuelle Zusammenfassung für eine E-Mail-Adresse"""
        try:
            history = self.get_conversation_history(email_address, limit=20)
            
            if not history:
                return {"summary": "Keine vorherigen Konversationen", "context": {}}
            
            # Analysiere Historie
            intents = [msg.intent_type for msg in history if msg.intent_type]
            context_types = [msg.context_type for msg in history]
            recent_messages = history[:5]
            
            # Finde häufigste Intents und Kontexte
            intent_counts = {}
            for intent in intents:
                intent_counts[intent] = intent_counts.get(intent, 0) + 1
            
            context_counts = {}
            for context in context_types:
                context_counts[context] = context_counts.get(context, 0) + 1
            
            # Extrahiere Patientennamen
            patient_names = []
            for msg in history:
                if msg.extracted_name and msg.extracted_name.get('full_name'):
                    patient_names.append(msg.extracted_name['full_name'])
            
            # Erstelle Zusammenfassung
            summary = {
                "total_messages": len(history),
                "recent_activity": recent_messages[0].timestamp.isoformat() if recent_messages else None,
                "most_common_intent": max(intent_counts.items(), key=lambda x: x[1])[0] if intent_counts else None,
                "most_common_context": max(context_counts.items(), key=lambda x: x[1])[0] if context_counts else None,
                "patient_names": list(set(patient_names)),
                "recent_intents": [msg.intent_type for msg in recent_messages if msg.intent_type],
                "conversation_flow": [
                    {
                        "timestamp": msg.timestamp.isoformat(),
                        "intent": msg.intent_type,
                        "context": msg.context_type.value,
                        "subject": msg.subject
                    }
                    for msg in recent_messages
                ]
            }
            
            return {"summary": "Konversationshistorie analysiert", "context": summary}
            
        except Exception as e:
            logger.error(f"Fehler bei Kontextanalyse: {e}")
            return {"summary": "Fehler bei Kontextanalyse", "context": {}}
    
    def update_thread_subject(self, thread_id: str, old_subject: str, new_subject: str, reason: str = "subject_change"):
        """Aktualisiert den Betreff eines Threads und protokolliert die Änderung"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Protokolliere Betreff-Änderung
                cursor.execute('''
                    INSERT INTO thread_changes
                    (thread_id, old_subject, new_subject, change_reason)
                    VALUES (?, ?, ?, ?)
                ''', (thread_id, old_subject, new_subject, reason))
                
                # Aktualisiere alle Nachrichten in diesem Thread
                cursor.execute('''
                    UPDATE conversation_messages
                    SET subject = ?
                    WHERE thread_id = ?
                ''', (new_subject, thread_id))
                
                conn.commit()
                logger.info(f"Thread-Betreff aktualisiert: {thread_id}")
                
        except Exception as e:
            logger.error(f"Fehler beim Aktualisieren des Thread-Betreffs: {e}")
    
    def archive_old_conversations(self, days_old: int = 90):
        """Archiviert alte Konversationen"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Archiviere Konversationen
                cursor.execute('''
                    UPDATE conversation_contexts
                    SET status = 'archived'
                    WHERE last_activity < ? AND status != 'archived'
                ''', (cutoff_date.isoformat(),))
                
                archived_count = cursor.rowcount
                conn.commit()
                
                logger.info(f"{archived_count} Konversationen archiviert")
                return archived_count
                
        except Exception as e:
            logger.error(f"Fehler beim Archivieren: {e}")
            return 0
    
    def get_conversation_statistics(self) -> Dict[str, Any]:
        """Holt Statistiken über alle Konversationen"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Gesamtstatistiken
                cursor.execute('SELECT COUNT(*) FROM conversation_contexts')
                total_conversations = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM conversation_messages')
                total_messages = cursor.fetchone()[0]
                
                # Status-Verteilung
                cursor.execute('''
                    SELECT status, COUNT(*) 
                    FROM conversation_contexts 
                    GROUP BY status
                ''')
                status_distribution = dict(cursor.fetchall())
                
                # Intent-Verteilung
                cursor.execute('''
                    SELECT intent_type, COUNT(*) 
                    FROM conversation_messages 
                    WHERE intent_type IS NOT NULL 
                    GROUP BY intent_type 
                    ORDER BY COUNT(*) DESC 
                    LIMIT 10
                ''')
                intent_distribution = dict(cursor.fetchall())
                
                # Aktivste E-Mail-Adressen
                cursor.execute('''
                    SELECT email_address, COUNT(*) as message_count
                    FROM conversation_messages
                    GROUP BY email_address
                    ORDER BY message_count DESC
                    LIMIT 10
                ''')
                active_emails = [{"email": row[0], "count": row[1]} for row in cursor.fetchall()]
                
                return {
                    "total_conversations": total_conversations,
                    "total_messages": total_messages,
                    "status_distribution": status_distribution,
                    "intent_distribution": intent_distribution,
                    "most_active_emails": active_emails,
                    "generated_at": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Fehler beim Laden der Statistiken: {e}")
            return {}


# Test-Funktion für das Chat-Historie-System
def test_chat_history():
    """Testet das Chat-Historie-System"""
    chat_history = AdvancedChatHistory()
    
    # Test-Nachrichten erstellen
    test_messages = [
        ConversationMessage(
            message_id="msg_001",
            thread_id="thread_001",
            email_address="patient@example.com",
            subject="Terminanfrage",
            content="Hallo, ich brauche einen Termin für nächste Woche.",
            message_type=MessageType.INCOMING,
            intent_type="appointment",
            confidence=0.9,
            entities={"date": ["nächste Woche"]},
            context_type=ContextType.APPOINTMENT_BOOKING,
            timestamp=datetime.now(),
            extracted_name={"first_name": "Max", "last_name": "Mustermann", "full_name": "Max Mustermann"}
        ),
        ConversationMessage(
            message_id="msg_002",
            thread_id="thread_001",
            email_address="patient@example.com",
            subject="Re: Terminanfrage",
            content="Vielen Dank, der Termin am Montag um 10 Uhr passt mir gut.",
            message_type=MessageType.INCOMING,
            intent_type="appointment_confirm",
            confidence=0.95,
            entities={"date": ["Montag"], "time": ["10 Uhr"]},
            context_type=ContextType.APPOINTMENT_BOOKING,
            timestamp=datetime.now()
        )
    ]
    
    # Nachrichten speichern
    for message in test_messages:
        chat_history.store_message(message)
    
    # Historie abrufen
    history = chat_history.get_conversation_history("patient@example.com")
    print(f"Gespeicherte Nachrichten: {len(history)}")
    
    # Kontextuelle Zusammenfassung
    summary = chat_history.get_contextual_summary("patient@example.com")
    print(f"Zusammenfassung: {summary}")
    
    # Statistiken
    stats = chat_history.get_conversation_statistics()
    print(f"Statistiken: {stats}")


if __name__ == "__main__":
    test_chat_history()
