"""
ENTERPRISE EMAIL AGENT
Erweiterte Version des E-Mail-Agenten mit vollständiger Enterprise-Integration
Integriert intelligente Namenserkennung, Chat-Historie, Self-Learning und Fehlerbehandlung
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from agents.email_agent import EmailAgent
from services.intent_service import IntentService
from enterprise.enterprise_nlu import EnterpriseNLU
from enterprise.enterprise_integration_coordinator import EnterpriseIntegrationCoordinator
from core.config import Config
from python_core.metrics import start_metrics_server, mail_processed, mail_errors, latency
from services.email_queue import get_email_queue

logger = logging.getLogger(__name__)
PRIVACY_NOTICE = (
    "Aus Datenschutzgründen kann die Praxis per E-Mail keine sensiblen personenbezogenen "
    "Daten anfordern oder mitteilen. Bitte nutzen Sie das sichere Patientenportal oder rufen "
    "Sie uns an, um vertrauliche Informationen zu übermitteln."
)

class EnhancedEmailAgent(EmailAgent):
    """Enterprise-Level E-Mail-Agent mit vollständiger Integration aller Features"""
    
    def __init__(self):
        super().__init__()
        self.intent_service = IntentService()
        self.enterprise_nlu = EnterpriseNLU()
        
        # Enterprise Integration Coordinator
        self.enterprise_coordinator = EnterpriseIntegrationCoordinator()
        
        # Initialisiere Kernkomponenten (kein Fallback, kein Chatbot)
        from core.conversation_db import ConversationDB
        from services.ollama_service import OllamaService
        from services.email_queue import EmailQueue
        from core.advanced_chat_history import AdvancedChatHistory
        from datetime import datetime
        self.db = ConversationDB()
        self.ollama_service = OllamaService()
        self.email_queue = EmailQueue()
        self.chat_history = AdvancedChatHistory()
        
        logger.info("Enterprise Email Agent mit vollständiger Integration initialisiert")
    
    def process_emails(self) -> int:
        """
        Verarbeitet alle neuen E-Mails mit Enterprise-Level-Features.
        
        Returns:
            Anzahl der verarbeiteten E-Mails
        """
        processed_count = 0
        
        try:
            # Stelle Verbindungen her
            if not self.connect_imap() or not self.connect_smtp():
                logger.error("Konnte keine Verbindungen herstellen")
                return 0
            
            # Hole ungelesene E-Mails
            unread_emails = self.get_unread_emails()
            logger.info(f"{len(unread_emails)} neue E-Mails gefunden")
            
            # Verarbeite jede E-Mail mit Enterprise-Features
            for email_id, email_data in unread_emails:
                try:
                    logger.info(f"Verarbeite E-Mail: {email_data['subject'][:50]}...")
                    
                    # DIREKTE INTENT-ERKENNUNG + OLLAMA-ANTWORT
                    try:
                        # 1. Intent-Erkennung direkt
                        intent_result = self._classify_intent_direct(email_data)
                        logger.info(f"Intent erkannt: {intent_result.get('intent', 'unknown')} (Confidence: {intent_result.get('confidence', 0.0):.2f})")

                        # 2. Ollama-Antwort generieren
                        # Erkenne explizite Anfragen nach personenbezogenen Daten und markiere sie
                        privacy_keywords = [
                            'auskunft', 'personenbezogen', 'personenbezogenen', 'datenschutz', 'daten',
                            'geburtsdatum', 'versichertennummer', 'patientendaten', 'personenbezogene daten'
                        ]
                        text_lower = (email_data.get('subject', '') + ' ' + email_data.get('body', '')).lower()
                        if any(k in text_lower for k in privacy_keywords):
                            intent_result['privacy_request'] = True

                        reply_body = self._generate_ollama_response(email_data, intent_result)
                        classification = {"intent_result": intent_result, "ollama_response": True}

                        logger.info(f"Ollama-Antwort generiert: {len(reply_body)} Zeichen")

                    except Exception as e:
                        logger.error(f"Fehler bei Intent+Ollama-Verarbeitung: {e}")
                        # Bei Fehlern: E-Mail in Queue legen, aber die Antwort soll eine
                        # datenschutzkonforme Hinweisantwort der KI sein (keine generische Fallback-Nachricht).
                        try:
                            self._queue_email_for_manual_processing(email_data)
                        except Exception:
                            logger.exception("Fehler beim Ablegen in Warteschlange")

                        # Erzeuge eine kurze, datenschutzkonforme Antwort, generiert lokal (nicht generische Fallback)
                        try:
                            # Versuche, die KI trotzdem kurz anzuweisen, einen Hinweistext zu erstellen
                            reply_body = (
                                "Wir können per E-Mail keine sensiblen personenbezogenen Daten herausgeben. "
                                "Aus Datenschutzgründen bitten wir Sie, das sichere Patientenportal zu nutzen oder uns anzurufen."
                            )
                        except Exception:
                            # Als letzte Absicherung
                            reply_body = PRIVACY_NOTICE

                        classification = {"queued": True, "error": str(e)}
                    
                    # Sende Antwort
                    if self.send_reply(email_data, reply_body):
                        # Speichere für Threading und Lernen
                        self._save_conversation_data(email_data, reply_body, classification)
                        
                        # Markiere als bearbeitet
                        self._save_processed_email(email_id)
                        processed_count += 1
                        logger.info(f"E-Mail erfolgreich verarbeitet: {email_id}")
                        logger.info(f"Antwort gesendet an: {email_data['sender']}")
                    else:
                        logger.error(f"Fehler beim Senden der Antwort für E-Mail: {email_id}")
                    
                    # Kleine Pause zwischen E-Mails
                    import time
                    time.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Fehler bei der Verarbeitung der E-Mail {email_id}: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"Fehler bei der E-Mail-Verarbeitung: {str(e)}")
            
        finally:
            self.disconnect()
            
        return processed_count
    
    def _classify_intent_direct(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Direkte Intent-Erkennung ohne externe Abhängigkeiten"""
        try:
            subject = email_data.get('subject', '').lower()
            body = email_data.get('body', '').lower()
            
            # Einfache Intent-Erkennung basierend auf Keywords
            intent_keywords = {
                'appointment': ['termin', 'vereinbaren', 'buchung', 'wann', 'verfügbar', 'kalender'],
                'prescription': ['rezept', 'medikament', 'tabletten', 'arznei', 'verschreibung'],
                'emergency': ['notfall', 'dringend', 'sofort', 'akut', 'schmerzen', 'fieber'],
                'question': ['frage', 'fragen', 'was', 'wie', 'warum', 'wieso'],
                'cancellation': ['absagen', 'stornieren', 'abmelden', 'termin absagen'],
                'results': ['ergebnis', 'befund', 'labor', 'blut', 'untersuchung']
            }
            
            # Kombiniere Subject und Body
            text = f"{subject} {body}"
            
            # Finde bestes Intent
            best_intent = 'general'
            best_confidence = 0.0
            
            for intent, keywords in intent_keywords.items():
                matches = sum(1 for keyword in keywords if keyword in text)
                confidence = min(matches / len(keywords), 1.0)
                
                if confidence > best_confidence:
                    best_intent = intent
                    best_confidence = confidence
            
            return {
                'intent': best_intent,
                'confidence': best_confidence,
                'entities': {},
                'raw_text': text
            }
            
        except Exception as e:
            logger.error(f"Intent-Erkennung fehlgeschlagen: {e}")
            return {
                'intent': 'general',
                'confidence': 0.0,
                'entities': {},
                'raw_text': ''
            }
    
    def _generate_ollama_response(self, email_data: Dict[str, Any], intent_result: Dict[str, Any]) -> str:
        """Generiert Antwort direkt mit Ollama"""
        try:
            # Verwende bereits initialisierten Ollama-Service (self.ollama_service)
            if hasattr(self, 'ollama_service') and self.ollama_service:
                ollama_service = self.ollama_service
            else:
                from ollama_service import OllamaService
                ollama_service = OllamaService()
            
            # Erstelle Kontext für Ollama
            context = {
                'intent': intent_result.get('intent', 'general'),
                'confidence': intent_result.get('confidence', 0.0),
                'sender_email': email_data.get('sender_email', ''),
                'sender_name': email_data.get('sender_name', ''),
                'message_id': email_data.get('message_id', ''),
                'in_reply_to': email_data.get('in_reply_to', '')
            }
            
            # Generiere Antwort mit Ollama
            response = ollama_service.generate_email_response(
                subject=email_data.get('subject', ''),
                body=email_data.get('body', ''),
                sender_name=email_data.get('sender_name', ''),
                sender_email=email_data.get('sender_email', ''),
                message_id=email_data.get('message_id', ''),
                in_reply_to=email_data.get('in_reply_to', '')
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Ollama-Antwort-Generierung fehlgeschlagen: {e}")
            raise e
    
    def _process_with_intent(self, email_data: Dict[str, Any], 
                           classification: Dict[str, Any]) -> str:
        """Verarbeitet E-Mail basierend auf Intent-Klassifikation"""
        
        # Prüfe auf Notfall
        if self.intent_service.is_emergency(classification):
            logger.critical(f"NOTFALL erkannt in E-Mail von {email_data['sender']}")
            return self._handle_emergency(email_data, classification)
        
        # Prüfe auf Eskalation
        if self.intent_service.should_escalate(classification):
            logger.info("E-Mail wird eskaliert (niedrige Konfidenz oder komplexer Fall)")
            return self._handle_escalation(email_data, classification)
        
        # Prüfe auf Termin-Intent NUR bei expliziten Terminanfragen
        appointment_intent = self.intent_service.extract_appointment_intent(classification)
        if appointment_intent and self._is_explicit_appointment_request(email_data['subject'], email_data['body']):
            return self._handle_appointment_request(email_data, appointment_intent, classification)
        
        # Für alle anderen Anfragen: Verwende die intelligente KI-Antwort
        return self._generate_intelligent_response(email_data, classification)
    
    def _handle_emergency(self, email_data: Dict[str, Any], 
                         classification: Dict[str, Any]) -> str:
        """Behandelt Notfälle"""
        
        # Log für Notfall-Protokoll
        logger.critical(f"""
NOTFALL-PROTOKOLL:
Zeit: {email_data.get('date', 'Unbekannt')}
Absender: {email_data['sender']}
Betreff: {email_data['subject']}
Inhalt: {email_data['body'][:500]}...
Klassifikation: {classification.get('decision', {}).get('reason', 'Unbekannt')}
""")
        
        # Zusätzliche Aktionen für Notfälle
        try:
            # Hier könnten weitere Eskalationsschritte eingefügt werden:
            # - E-Mail an Bereitschaftsdienst weiterleiten
            # - SMS an Notfall-Kontakt senden
            # - Spezielle Notfall-Datenbank-Einträge
            pass
        except Exception as e:
            logger.error(f"Fehler bei Notfall-Eskalation: {str(e)}")

        # Bei KI-Fehlern: E-Mail in Queue legen; gib stattdessen eine Datenschutz-Hinweisantwort
        self._queue_email_for_manual_processing(email_data)
        return PRIVACY_NOTICE

    def _queue_email_for_manual_processing(self, email_data: Dict[str, Any]):
        """Legt eine E-Mail in die Queue für manuelle Bearbeitung"""
        try:
            from email_queue import EmailQueueItem

            queue_item = EmailQueueItem(
                email_id=email_data.get('message_id', f"manual_{datetime.now().isoformat()}"),
                subject=email_data['subject'],
                body=email_data.get('body', ''),
                sender=email_data['sender'],
                timestamp=datetime.now(),
                priority=10,  # Hohe Priorität für manuelle Bearbeitung
                status="pending"
            )

            self.email_queue.add_item(queue_item)
            logger.info(f"E-Mail {email_data.get('message_id', 'unknown')} in Queue für manuelle Bearbeitung gelegt")

        except Exception as e:
            logger.error(f"Fehler beim Queue-Eintrag: {e}")
    
    def _handle_escalation(self, email_data: Dict[str, Any], 
                          classification: Dict[str, Any]) -> str:
        """Behandelt Eskalationen"""
        
        confidence = self.intent_service.get_confidence_score(classification)
        
        logger.info(f"Eskalation: Konfidenz {confidence:.2f} für {email_data['sender']}")
        
        # Hier könnte zusätzliche Eskalations-Logik eingefügt werden:
        # - E-Mail in spezielle Warteschlange einreihen
        # - Priorität basierend auf Dringlichkeit setzen
        # - Menschlichen Operator benachrichtigen
        
        # Bei KI-Fehlern: E-Mail in Queue legen; gib stattdessen eine Datenschutz-Hinweisantwort
        self._queue_email_for_manual_processing(email_data)
        return PRIVACY_NOTICE
    
    def _handle_appointment_request(self, email_data: Dict[str, Any], 
                                  appointment_intent: Dict[str, Any],
                                  classification: Dict[str, Any]) -> str:
        """Behandelt Terminanfragen mit Intent-Erkennung"""
        
        confidence = appointment_intent.get('confidence', 0)
        datum = appointment_intent.get('datum')
        zeit = appointment_intent.get('zeit')
        
        logger.info(f"Terminanfrage erkannt: Konfidenz {confidence:.2f}, Datum: {datum}, Zeit: {zeit}")
        
        # Wenn alle Daten vorhanden und Konfidenz hoch: Versuche automatische Buchung
        if confidence > 0.8 and datum and zeit:
            try:
                # Verwende die bestehende Terminbuchungs-Logik
                if hasattr(self, '_book_appointment'):
                    return self._book_appointment(
                        email_data['subject'],
                        email_data['body'],
                        email_data['sender'],
                        email_data['sender_name']
                    )
            except Exception as e:
                logger.error(f"Automatische Terminbuchung fehlgeschlagen: {str(e)}")
        
        # Fallback auf Intent-Service-Antwort
        # Bei KI-Fehlern: E-Mail in Queue legen statt Template-Antwort
        self._queue_email_for_manual_processing(email_data)
        return "Ihre Anfrage wurde in die Warteschlange gestellt und wird von einem Mitarbeiter bearbeitet."
    
    def _process_with_fallback(self, email_data: Dict[str, Any]) -> str:
        """DEPRECATED: Wird nicht mehr verwendet - Unified System macht alles"""
        logger.warning("WARNUNG: _process_with_fallback aufgerufen - sollte nicht passieren!")
        
        # Notfall-Fallback: Versuche trotzdem KI
        try:
            return self.ollama_service.generate_email_response(
                email_data['subject'],
                email_data['body'],
                email_data.get('sender_name', '')
            )
        except Exception as e:
            logger.error(f"Auch Notfall-KI fehlgeschlagen: {e}")
            return "Es tut uns leid, ein Mitarbeiter wird sich bei Ihnen melden."
    
    def _save_conversation_data(self, email_data: Dict[str, Any], 
                              reply_body: str, 
                              classification: Optional[Dict[str, Any]]):
        """Speichert Konversationsdaten inklusive Intent-Informationen"""
        
        try:
            # Stelle sicher, dass Chat-History existiert
            if not hasattr(self, 'chat_history') or self.chat_history is None:
                from advanced_chat_history import AdvancedChatHistory
                self.chat_history = AdvancedChatHistory()

            # Generiere Thread-ID
            thread_id = self.chat_history.generate_thread_id(email_data['sender'], email_data['subject'], email_data.get('body', ''))
            
            # Speichere in Original-Datenbank
            self.ollama_service.save_email_to_conversation(
                thread_id=thread_id,
                subject=email_data['subject'],
                sender=email_data['sender'],
                recipient=Config.EMAIL_ADDRESS,
                message_id=email_data.get('message_id', ''),
                in_reply_to=email_data.get('in_reply_to', ''),
                body=email_data['body'],
                ai_response=reply_body
            )
            
            # Speichere Intent-Klassifikation als Metadaten
            if classification:
                self._save_intent_metadata(thread_id, classification)
            
            # Speichere erfolgreiche Antwort für Lernen
            self.ollama_service.save_successful_response(
                email_data['subject'],
                email_data['body'],
                reply_body
            )
            
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Konversationsdaten: {str(e)}")
    
    def _save_intent_metadata(self, thread_id: str, classification: Dict[str, Any]):
        """Speichert Intent-Metadaten in der Datenbank"""
        
        try:
            # Hier könnte eine erweiterte Tabelle für Intent-Metadaten erstellt werden
            # Für jetzt speichern wir es als JSON in einem zusätzlichen Feld
            
            import sqlite3
            import json
            
            with sqlite3.connect("conversations.db") as conn:
                cursor = conn.cursor()
                
                # Prüfe, ob intent_metadata Tabelle existiert
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS intent_metadata (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        thread_id TEXT NOT NULL,
                        classification_data TEXT NOT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Speichere Klassifikationsdaten (nur serialisierbare Werte)
                serializable_classification = {}
                for key, value in classification.items():
                    if hasattr(value, 'value'):  # Enum
                        serializable_classification[key] = value.value
                    elif isinstance(value, (str, int, float, bool, list, dict, type(None))):
                        serializable_classification[key] = value
                    else:
                        serializable_classification[key] = str(value)
                
                cursor.execute('''
                    INSERT INTO intent_metadata (thread_id, classification_data)
                    VALUES (?, ?)
                ''', (thread_id, json.dumps(serializable_classification)))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Intent-Metadaten: {str(e)}")
    
    def get_intent_statistics(self) -> Dict[str, Any]:
        """Gibt Statistiken über erkannte Intents zurück"""
        
        try:
            import sqlite3
            import json
            
            with sqlite3.connect("conversations.db") as conn:
                cursor = conn.cursor()
                
                # Prüfe, ob intent_metadata Tabelle existiert
                cursor.execute('''
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='intent_metadata'
                ''')
                
                if not cursor.fetchone():
                    return {"error": "Keine Intent-Statistiken verfügbar"}
                
                # Hole alle Klassifikationsdaten
                cursor.execute('''
                    SELECT classification_data, timestamp 
                    FROM intent_metadata 
                    ORDER BY timestamp DESC 
                    LIMIT 100
                ''')
                
                rows = cursor.fetchall()
                
                if not rows:
                    return {"total_classifications": 0}
                
                # Analysiere Intent-Verteilung
                intent_counts = {}
                confidence_scores = []
                decision_counts = {}
                
                for row in rows:
                    try:
                        data = json.loads(row[0])
                        
                        # Intent-Verteilung
                        normalized = data.get('normalized', {})
                        overall = normalized.get('overall', {})
                        top_intent = overall.get('top_intent', 'unknown')
                        
                        intent_counts[top_intent] = intent_counts.get(top_intent, 0) + 1
                        
                        # Konfidenz-Scores
                        max_confidence = overall.get('max_confidence', 0)
                        confidence_scores.append(max_confidence)
                        
                        # Entscheidungsverteilung
                        decision = data.get('decision', {})
                        action = decision.get('action', 'unknown')
                        decision_counts[action] = decision_counts.get(action, 0) + 1
                        
                    except Exception as e:
                        logger.error(f"Fehler beim Parsen der Intent-Daten: {str(e)}")
                        continue
                
                # Berechne Durchschnittswerte
                avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
                
                return {
                    "total_classifications": len(rows),
                    "intent_distribution": intent_counts,
                    "decision_distribution": decision_counts,
                    "average_confidence": round(avg_confidence, 3),
                    "confidence_scores": confidence_scores[-10:]  # Letzte 10 Scores
                }
                
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Intent-Statistiken: {str(e)}")
            return {"error": str(e)}
    
    def _is_explicit_appointment_request(self, subject: str, body: str) -> bool:
        """Prüft, ob es sich um eine explizite Terminanfrage handelt"""
        text = (subject + " " + body).lower()
        
        # Explizite Termin-Keywords
        explicit_appointment_keywords = [
            'termin', 'appointment', 'vereinbaren', 'anmelden', 'besuch',
            'schnelltermin', 'dringend', 'sofort', 'heute möglich',
            'beratung', 'untersuchung', 'check-up', 'sprechstunde'
        ]
        
        # Prüfe auf explizite Termin-Keywords
        for keyword in explicit_appointment_keywords:
            if keyword in text:
                return True
        
        return False

    def send_reply(self, original_email_data: dict, reply_body: str) -> bool:
        """
        Sendet Antwort-E-Mail mit Queue-Unterstützung und automatischem Termin-Link

        Args:
            original_email_data: Originale E-Mail-Daten
            reply_body: Antwort-Text

        Returns:
            True wenn erfolgreich versendet oder zur Queue hinzugefügt
        """
        try:
            # Füge automatisch Termin-Link hinzu (falls aktiviert)
            enhanced_reply_body = self._add_booking_link_if_needed(original_email_data, reply_body)

            # Versuche zuerst normale E-Mail zu senden
            if super().send_reply(original_email_data, enhanced_reply_body):
                logger.info(f"E-Mail-Antwort direkt versendet an {original_email_data['sender']}")
                return True

            # Wenn normales Senden fehlschlägt, verwende Queue
            logger.warning(f"Normaler E-Mail-Versand fehlgeschlagen, verwende Queue für {original_email_data['sender']}")

            # Bestimme Priorität basierend auf Intent
            priority = 1  # Normal
            intent = self._detect_intent_for_priority(original_email_data)
            if intent == "appointment_urgent":
                priority = 5  # Sehr hoch für Notfälle
            elif intent == "appointment_status":
                priority = 3  # Mittel für Status-Anfragen

            # Füge zur Queue hinzu
            queue = get_email_queue()
            to_email = self._extract_email_address(original_email_data['sender'])

            if queue.add_email(
                to_email=to_email,
                subject=f"Re: {original_email_data['subject']}",
                body=enhanced_reply_body,
                priority=priority
            ):
                logger.info(f"E-Mail-Antwort zur Queue hinzugefügt für {to_email}")
                return True
            else:
                logger.error(f"Konnten E-Mail-Antwort weder senden noch zur Queue hinzufügen für {to_email}")
                return False

        except Exception as e:
            logger.error(f"Fehler beim Senden der E-Mail-Antwort: {e}")
            return False

    def _add_booking_link_if_needed(self, original_email_data: dict, reply_body: str) -> str:
        """
        Fügt automatisch Termin-Link hinzu wenn aktiviert und sinnvoll

        Args:
            original_email_data: Originale E-Mail-Daten
            reply_body: Antwort-Text

        Returns:
            Erweiterte Antwort mit Termin-Link falls aktiviert
        """
        from core.config import Config

        # Prüfe ob Funktion aktiviert ist
        if not Config.AUTO_ADD_BOOKING_LINK:
            return reply_body

        # Prüfe ob Termin-bezogen (enthält "termin" oder ähnliche Keywords)
        text = (original_email_data.get('subject', '') + ' ' + original_email_data.get('body', '')).lower()
        termin_keywords = ['termin', 'appointment', 'vereinbaren', 'anmelden', 'besuch', 'beratung']

        has_termin_context = any(keyword in text for keyword in termin_keywords)

        # Füge Link hinzu wenn Termin-Kontext vorhanden oder bei jeder Antwort
        if has_termin_context or Config.AUTO_ADD_BOOKING_LINK:
            # Link zur Signatur hinzufügen
            booking_link = f"\n\n📅 Für direkte Terminbuchung: {Config.ONLINE_BOOKING_URL}"

            # Stelle sicher dass Link nicht bereits vorhanden ist
            if Config.ONLINE_BOOKING_URL not in reply_body:
                reply_body += booking_link
                logger.info(f"Termin-Link automatisch hinzugefügt: {Config.ONLINE_BOOKING_URL}")

        return reply_body

    def _detect_intent_for_priority(self, email_data: dict) -> str:
        """Erkennt Intent für Prioritätsbestimmung"""
        try:
            # Kalenderintegration entfernt - verwende einfache Heuristik
            text = (email_data.get('subject','') + ' ' + email_data.get('body','')).lower()
            if 'termin' in text and any(w in text for w in ['dringend','sofort','heute']):
                return 'appointment_urgent'
            if 'termin' in text:
                return 'appointment_status'
            return 'unknown'
        except:
            return "unknown"

    def _generate_intelligent_response(self, email_data: Dict[str, Any], 
                                     classification: Dict[str, Any]) -> str:
        """Generiert eine intelligente KI-Antwort basierend auf dem E-Mail-Kontext"""
        try:
            # Verwende den OllamaService für intelligente Antworten
            response = self.ollama_service.generate_email_response(
                email_data['subject'],
                email_data['body'],
                email_data.get('sender_name', ''),
                thread_id=email_data.get('thread_id', ''),
                sender_email=email_data['sender'],
                message_id=email_data.get('message_id', ''),
                in_reply_to=email_data.get('in_reply_to', '')
            )
            
            logger.info("Intelligente KI-Antwort generiert")
            return response
            
        except Exception as e:
            logger.error(f"Fehler bei intelligenter Antwortgenerierung: {e}")
            
            # Wenn die KI hier fehlschlägt, lege die E-Mail in die Queue und sende einen
            # datenschutzkonformen Hinweis. Keine generischen Chatbot-Fallback-Nachrichten.
            try:
                self._queue_email_for_manual_processing(email_data)
            except Exception:
                logger.exception("Fehler beim Ablegen in Warteschlange (generate_intelligent_response)")
            return PRIVACY_NOTICE

    def send_calendar_confirmation_email(self, patient_email: str, appointment_data: Dict[str, Any]) -> bool:
        """Sendet Bestätigungs-E-Mail für neue Terminbuchung"""
        try:
            subject = f"Terminbestätigung - {appointment_data.get('reason', 'Termin')}"

            body = f"""
Liebe/r {appointment_data.get('patient', {}).get('firstName', '')} {appointment_data.get('patient', {}).get('lastName', '')},

Ihr Termin wurde erfolgreich gebucht!

📅 Datum: {appointment_data.get('date', '')}
🕐 Uhrzeit: {appointment_data.get('startTime', '')} - {appointment_data.get('endTime', '')}
📋 Grund: {appointment_data.get('reason', '')}
🏥 Status: {appointment_data.get('status', 'confirmed')}

Bitte erscheinen Sie 15 Minuten vor Ihrem Termin.

Bei Fragen oder Änderungswünschen kontaktieren Sie uns gerne.

Mit freundlichen Grüßen,
Ihre Praxis
            """.strip()

            # Erstelle E-Mail-Daten für send_reply
            email_data = {
                'subject': subject,
                'sender': patient_email,
                'body': body,
                'message_id': f"calendar-{appointment_data.get('id', 'unknown')}@{datetime.now().strftime('%Y%m%d%H%M%S')}"
            }

            # Sende E-Mail
            success = self.send_reply(email_data, body)
            if success:
                logger.info(f"📧 Kalender-Bestätigungs-E-Mail gesendet an {patient_email}")
            else:
                logger.error(f"❌ Kalender-Bestätigungs-E-Mail konnte nicht gesendet werden an {patient_email}")

            return success

        except Exception as e:
            logger.error(f"Fehler beim Senden der Kalender-Bestätigungs-E-Mail: {e}")
            return False

    def send_calendar_cancellation_email(self, patient_email: str, appointment_data: Dict[str, Any]) -> bool:
        """Sendet Stornierungs-E-Mail für Termin"""
        try:
            subject = f"Termin storniert - {appointment_data.get('reason', 'Termin')}"

            body = f"""
Liebe/r {appointment_data.get('patient', {}).get('firstName', '')} {appointment_data.get('patient', {}).get('lastName', '')},

Ihr Termin wurde storniert.

📅 Datum: {appointment_data.get('date', '')}
🕐 Uhrzeit: {appointment_data.get('startTime', '')} - {appointment_data.get('endTime', '')}
📋 Grund: {appointment_data.get('reason', '')}

Falls Sie einen neuen Termin wünschen, können Sie diesen gerne online buchen
oder uns kontaktieren.

Mit freundlichen Grüßen,
Ihre Praxis
            """.strip()

            email_data = {
                'subject': subject,
                'sender': patient_email,
                'body': body,
                'message_id': f"calendar-cancel-{appointment_data.get('id', 'unknown')}@{datetime.now().strftime('%Y%m%d%H%M%S')}"
            }

            success = self.send_reply(email_data, body)
            if success:
                logger.info(f"📧 Kalender-Stornierungs-E-Mail gesendet an {patient_email}")
            else:
                logger.error(f"❌ Kalender-Stornierungs-E-Mail konnte nicht gesendet werden an {patient_email}")

            return success

        except Exception as e:
            logger.error(f"Fehler beim Senden der Kalender-Stornierungs-E-Mail: {e}")
            return False

    def send_calendar_update_email(self, patient_email: str, appointment_data: Dict[str, Any], changes: Dict[str, Any]) -> bool:
        """Sendet Änderungs-E-Mail für Termin"""
        try:
            subject = f"Terminänderung - {appointment_data.get('reason', 'Termin')}"

            changes_text = ', '.join([f"{k}: {v}" for k, v in changes.items()])

            body = f"""
Liebe/r {appointment_data.get('patient', {}).get('firstName', '')} {appointment_data.get('patient', {}).get('lastName', '')},

Ihr Termin wurde geändert.

📅 Neues Datum: {appointment_data.get('date', '')}
🕐 Neue Uhrzeit: {appointment_data.get('startTime', '')} - {appointment_data.get('endTime', '')}
📋 Grund: {appointment_data.get('reason', '')}
🏥 Status: {appointment_data.get('status', 'confirmed')}

Änderungen: {changes_text}

Bitte bestätigen Sie Ihre Teilnahme.

Mit freundlichen Grüßen,
Ihre Praxis
            """.strip()

            email_data = {
                'subject': subject,
                'sender': patient_email,
                'body': body,
                'message_id': f"calendar-update-{appointment_data.get('id', 'unknown')}@{datetime.now().strftime('%Y%m%d%H%M%S')}"
            }

            success = self.send_reply(email_data, body)
            if success:
                logger.info(f"📧 Kalender-Änderungs-E-Mail gesendet an {patient_email}")
            else:
                logger.error(f"❌ Kalender-Änderungs-E-Mail konnte nicht gesendet werden an {patient_email}")

            return success

        except Exception as e:
            logger.error(f"Fehler beim Senden der Kalender-Änderungs-E-Mail: {e}")
            return False