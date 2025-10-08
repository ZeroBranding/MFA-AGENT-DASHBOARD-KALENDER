#!/usr/bin/env python3
"""
EMAIL QUEUE
E-Mail-Warteschlange für das Enterprise-System
"""

import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class EmailQueueItem:
    """E-Mail-Warteschlangen-Element"""
    email_id: str
    subject: str
    body: str
    sender: str
    timestamp: datetime
    priority: int = 0
    retry_count: int = 0
    max_retries: int = 3
    status: str = "pending"  # pending, processing, completed, failed

class EmailQueue:
    """E-Mail-Warteschlange"""
    
    def __init__(self, queue_file: str = "email_queue.json"):
        self.queue_file = Path(queue_file)
        self.queue: List[EmailQueueItem] = []
        self._load_queue()
    
    def _load_queue(self):
        """Lädt die Warteschlange aus der Datei"""
        try:
            if self.queue_file.exists():
                with open(self.queue_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.queue = [
                        EmailQueueItem(
                            email_id=item['email_id'],
                            subject=item['subject'],
                            body=item['body'],
                            sender=item['sender'],
                            timestamp=datetime.fromisoformat(item['timestamp']),
                            priority=item.get('priority', 0),
                            retry_count=item.get('retry_count', 0),
                            max_retries=item.get('max_retries', 3),
                            status=item.get('status', 'pending')
                        )
                        for item in data
                    ]
        except Exception as e:
            logger.error(f"Fehler beim Laden der E-Mail-Warteschlange: {e}")
            self.queue = []
    
    def _save_queue(self):
        """Speichert die Warteschlange in die Datei"""
        try:
            data = [
                {
                    'email_id': item.email_id,
                    'subject': item.subject,
                    'body': item.body,
                    'sender': item.sender,
                    'timestamp': item.timestamp.isoformat(),
                    'priority': item.priority,
                    'retry_count': item.retry_count,
                    'max_retries': item.max_retries,
                    'status': item.status
                }
                for item in self.queue
            ]
            with open(self.queue_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Fehler beim Speichern der E-Mail-Warteschlange: {e}")
    
    def add_email(self, email_id: str, subject: str, body: str, sender: str, priority: int = 0) -> bool:
        """Fügt eine E-Mail zur Warteschlange hinzu"""
        try:
            # Prüfe, ob E-Mail bereits existiert
            if any(item.email_id == email_id for item in self.queue):
                logger.warning(f"E-Mail {email_id} bereits in der Warteschlange")
                return False
            
            item = EmailQueueItem(
                email_id=email_id,
                subject=subject,
                body=body,
                sender=sender,
                timestamp=datetime.now(),
                priority=priority
            )
            
            self.queue.append(item)
            self._save_queue()
            logger.info(f"E-Mail {email_id} zur Warteschlange hinzugefügt")
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim Hinzufügen der E-Mail zur Warteschlange: {e}")
            return False
    
    def get_next_email(self) -> Optional[EmailQueueItem]:
        """Holt die nächste E-Mail aus der Warteschlange"""
        try:
            # Sortiere nach Priorität und Zeitstempel
            pending_emails = [item for item in self.queue if item.status == "pending"]
            if not pending_emails:
                return None
            
            # Sortiere nach Priorität (höher = wichtiger) und dann nach Zeitstempel
            pending_emails.sort(key=lambda x: (-x.priority, x.timestamp))
            
            return pending_emails[0]
            
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der nächsten E-Mail: {e}")
            return None
    
    def mark_processing(self, email_id: str) -> bool:
        """Markiert eine E-Mail als in Bearbeitung"""
        try:
            for item in self.queue:
                if item.email_id == email_id:
                    item.status = "processing"
                    self._save_queue()
                    return True
            return False
        except Exception as e:
            logger.error(f"Fehler beim Markieren der E-Mail als in Bearbeitung: {e}")
            return False
    
    def mark_completed(self, email_id: str) -> bool:
        """Markiert eine E-Mail als abgeschlossen"""
        try:
            for item in self.queue:
                if item.email_id == email_id:
                    item.status = "completed"
                    self._save_queue()
                    return True
            return False
        except Exception as e:
            logger.error(f"Fehler beim Markieren der E-Mail als abgeschlossen: {e}")
            return False
    
    def mark_failed(self, email_id: str) -> bool:
        """Markiert eine E-Mail als fehlgeschlagen"""
        try:
            for item in self.queue:
                if item.email_id == email_id:
                    item.retry_count += 1
                    if item.retry_count >= item.max_retries:
                        item.status = "failed"
                    else:
                        item.status = "pending"  # Für erneuten Versuch
                    self._save_queue()
                    return True
            return False
        except Exception as e:
            logger.error(f"Fehler beim Markieren der E-Mail als fehlgeschlagen: {e}")
            return False
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Gibt den Status der Warteschlange zurück"""
        try:
            status_counts = {}
            for item in self.queue:
                status_counts[item.status] = status_counts.get(item.status, 0) + 1
            
            return {
                "total_emails": len(self.queue),
                "status_counts": status_counts,
                "pending_count": len([item for item in self.queue if item.status == "pending"]),
                "processing_count": len([item for item in self.queue if item.status == "processing"]),
                "completed_count": len([item for item in self.queue if item.status == "completed"]),
                "failed_count": len([item for item in self.queue if item.status == "failed"])
            }
        except Exception as e:
            logger.error(f"Fehler beim Abrufen des Warteschlangen-Status: {e}")
            return {"error": str(e)}

# Globale Warteschlangen-Instanz
_email_queue_instance: Optional[EmailQueue] = None

def get_email_queue() -> EmailQueue:
    """Gibt die globale E-Mail-Warteschlangen-Instanz zurück"""
    global _email_queue_instance
    if _email_queue_instance is None:
        _email_queue_instance = EmailQueue()
    return _email_queue_instance
