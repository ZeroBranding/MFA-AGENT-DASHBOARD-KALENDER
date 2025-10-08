#!/usr/bin/env python3
"""
CONVERSATION DATABASE
Datenbank für Konversations-Historie und Patienten-Interaktionen
"""

import sqlite3
import logging
import json
import hashlib
import re
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class ConversationEntry:
    """Konversations-Eintrag"""
    conversation_id: str
    email_address: str
    subject: str
    incoming_message: str
    outgoing_response: str
    intent_type: str
    confidence: float
    timestamp: datetime
    thread_id: str = ""

class ConversationDB:
    """Datenbank für Konversations-Management"""

    def __init__(self, db_path: str = "conversations.db"):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Initialisiert die Konversations-Datenbank"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Konversations-Tabelle
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS conversations (
                        conversation_id TEXT PRIMARY KEY,
                        email_address TEXT NOT NULL,
                        subject TEXT NOT NULL,
                        incoming_message TEXT NOT NULL,
                        outgoing_response TEXT NOT NULL,
                        intent_type TEXT NOT NULL,
                        confidence REAL DEFAULT 0.0,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        thread_id TEXT DEFAULT ''
                    )
                ''')

                # Indizes für Performance
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_email ON conversations(email_address)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON conversations(timestamp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_thread ON conversations(thread_id)')

                conn.commit()
                logger.info("Konversations-Datenbank initialisiert")

        except Exception as e:
            logger.error(f"Fehler bei Datenbank-Initialisierung: {e}")
            raise

    def save_conversation(self, entry: ConversationEntry) -> bool:
        """Speichert eine Konversation"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO conversations
                    (conversation_id, email_address, subject, incoming_message, outgoing_response,
                     intent_type, confidence, timestamp, thread_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    entry.conversation_id,
                    entry.email_address,
                    entry.subject,
                    entry.incoming_message,
                    entry.outgoing_response,
                    entry.intent_type,
                    entry.confidence,
                    entry.timestamp.isoformat(),
                    entry.thread_id
                ))

                conn.commit()
                logger.info(f"Konversation gespeichert: {entry.conversation_id}")
                return True

        except Exception as e:
            logger.error(f"Fehler beim Speichern der Konversation: {e}")
            return False

    def get_conversations_for_email(self, email_address: str, limit: int = 10) -> List[ConversationEntry]:
        """Holt alle Konversationen für eine E-Mail-Adresse"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT conversation_id, email_address, subject, incoming_message, outgoing_response,
                           intent_type, confidence, timestamp, thread_id
                    FROM conversations
                    WHERE email_address = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (email_address, limit))

                conversations = []
                for row in cursor.fetchall():
                    conversations.append(ConversationEntry(
                        conversation_id=row[0],
                        email_address=row[1],
                        subject=row[2],
                        incoming_message=row[3],
                        outgoing_response=row[4],
                        intent_type=row[5],
                        confidence=row[6],
                        timestamp=datetime.fromisoformat(row[7]),
                        thread_id=row[8]
                    ))

                return conversations

        except Exception as e:
            logger.error(f"Fehler beim Laden der Konversationen: {e}")
            return []

    def get_conversation_thread(self, thread_id: str) -> List[ConversationEntry]:
        """Holt alle Konversationen eines Threads"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT conversation_id, email_address, subject, incoming_message, outgoing_response,
                           intent_type, confidence, timestamp, thread_id
                    FROM conversations
                    WHERE thread_id = ?
                    ORDER BY timestamp ASC
                ''', (thread_id,))

                conversations = []
                for row in cursor.fetchall():
                    conversations.append(ConversationEntry(
                        conversation_id=row[0],
                        email_address=row[1],
                        subject=row[2],
                        incoming_message=row[3],
                        outgoing_response=row[4],
                        intent_type=row[5],
                        confidence=row[6],
                        timestamp=datetime.fromisoformat(row[7]),
                        thread_id=row[8]
                    ))

                return conversations

        except Exception as e:
            logger.error(f"Fehler beim Laden des Threads: {e}")
            return []

    def get_recent_conversations(self, limit: int = 50) -> List[ConversationEntry]:
        """Holt die letzten Konversationen"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT conversation_id, email_address, subject, incoming_message, outgoing_response,
                           intent_type, confidence, timestamp, thread_id
                    FROM conversations
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (limit,))

                conversations = []
                for row in cursor.fetchall():
                    conversations.append(ConversationEntry(
                        conversation_id=row[0],
                        email_address=row[1],
                        subject=row[2],
                        incoming_message=row[3],
                        outgoing_message=row[4],
                        intent_type=row[5],
                        confidence=row[6],
                        timestamp=datetime.fromisoformat(row[7]),
                        thread_id=row[8]
                    ))

                return conversations

        except Exception as e:
            logger.error(f"Fehler beim Laden der letzten Konversationen: {e}")
            return []

    def get_conversation_stats(self) -> Dict[str, Any]:
        """Gibt Statistiken über die Konversationen zurück"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Gesamtanzahl
                cursor.execute('SELECT COUNT(*) FROM conversations')
                total_conversations = cursor.fetchone()[0]

                # Einzigartige E-Mail-Adressen
                cursor.execute('SELECT COUNT(DISTINCT email_address) FROM conversations')
                unique_emails = cursor.fetchone()[0]

                # Intents nach Häufigkeit
                cursor.execute('''
                    SELECT intent_type, COUNT(*) as count
                    FROM conversations
                    GROUP BY intent_type
                    ORDER BY count DESC
                    LIMIT 10
                ''')
                intent_stats = {row[0]: row[1] for row in cursor.fetchall()}

                return {
                    "total_conversations": total_conversations,
                    "unique_emails": unique_emails,
                    "top_intents": intent_stats,
                    "generated_at": datetime.now().isoformat()
                }

        except Exception as e:
            logger.error(f"Fehler beim Laden der Statistiken: {e}")
            return {"error": str(e)}

    def generate_thread_id(self, email_address: str, subject: str, content: str) -> str:
        """Generiert eine eindeutige Thread-ID basierend auf E-Mail-Adresse und Inhalt"""
        # Normalisiere Subject (entferne Re: Fwd: etc.)
        normalized_subject = re.sub(r'^(re:|fwd?:|aw:)\s*', '', subject, flags=re.IGNORECASE).strip()

        # Erstelle Hash aus E-Mail-Adresse und normalisiertem Subject
        hash_input = f"{email_address}:{normalized_subject}"
        thread_hash = hashlib.md5(hash_input.encode()).hexdigest()[:16]

        return f"thread_{thread_hash}"
