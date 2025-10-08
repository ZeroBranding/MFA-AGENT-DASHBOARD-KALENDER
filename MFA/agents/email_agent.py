"""
Basis E-Mail-Agent - minimale Version für Enhanced Agent
Mit IMAP IDLE Support für sofortige E-Mail-Benachrichtigung
"""

import imaplib
import smtplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
import threading
import time
import select
import socket
from typing import List, Tuple, Optional, Callable
from core.config import Config

logger = logging.getLogger(__name__)

class EmailAgent:
    """Basis E-Mail-Agent mit IMAP IDLE Support"""
    
    def __init__(self):
        self.imap_connection = None
        self.smtp_connection = None
        self.processed_emails = set()
        self.idle_thread = None
        self.idle_running = False
        self.idle_callback = None
        self._idle_lock = threading.Lock()

    def connect_imap(self) -> bool:
        """Stellt IMAP-Verbindung her"""
        try:
            self.imap_connection = imaplib.IMAP4_SSL(Config.IMAP_SERVER, Config.IMAP_PORT)
            self.imap_connection.login(Config.EMAIL_ADDRESS, Config.EMAIL_PASSWORD)
            logger.info("IMAP-Verbindung erfolgreich")
            return True
        except Exception as e:
            logger.error(f"IMAP-Fehler: {e}")
            return False

    def connect_smtp(self) -> bool:
        """Stellt SMTP-Verbindung her"""
        try:
            self.smtp_connection = smtplib.SMTP(Config.SMTP_SERVER, Config.SMTP_PORT)
            self.smtp_connection.starttls()
            self.smtp_connection.login(Config.EMAIL_ADDRESS, Config.EMAIL_PASSWORD)
            logger.info("SMTP-Verbindung erfolgreich")
            return True
        except Exception as e:
            logger.error(f"SMTP-Fehler: {e}")
            return False

    def disconnect(self):
        """Trennt Verbindungen"""
        if self.imap_connection:
            try:
                self.imap_connection.logout()
            except:
                pass
        if self.smtp_connection:
            try:
                self.smtp_connection.quit()
            except:
                pass

    def get_unread_emails(self) -> List[Tuple[str, dict]]:
        """Holt ungelesene E-Mails"""
        if not self.imap_connection:
            return []

        try:
            self.imap_connection.select('INBOX')
            status, messages = self.imap_connection.search(None, 'UNSEEN')
            if status != 'OK':
                return []

            email_ids = messages[0].split()
            unread_emails = []

            for email_id in email_ids:
                email_id_str = email_id.decode('utf-8')
                if email_id_str in self.processed_emails:
                    continue

                email_data = self._fetch_email_data(email_id)
                if email_data:
                    unread_emails.append((email_id_str, email_data))

            return unread_emails
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der E-Mails: {e}")
            return []

    def _fetch_email_data(self, email_id) -> Optional[dict]:
        """Holt E-Mail-Daten"""
        try:
            status, msg_data = self.imap_connection.fetch(email_id, '(RFC822)')
            if status != 'OK':
                return None

            email_body = msg_data[0][1]
            email_message = email.message_from_bytes(email_body)

            subject = self._decode_header(email_message.get('Subject', ''))
            sender = self._decode_header(email_message.get('From', ''))
            body = self._extract_email_body(email_message)

            return {
                'subject': subject,
                'sender': sender,
                'body': body,
                'message_id': email_message.get('Message-ID', ''),
                'in_reply_to': email_message.get('In-Reply-To', ''),
                'references': email_message.get('References', ''),
                'date': email_message.get('Date', '')
            }
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der E-Mail: {e}")
            return None

    def _decode_header(self, header: str) -> str:
        """Dekodiert E-Mail-Header"""
        if not header:
            return ''
        try:
            decoded_parts = email.header.decode_header(header)
            decoded_string = ''
            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    decoded_string += part.decode(encoding or 'utf-8', errors='ignore')
                else:
                    decoded_string += str(part)
            return decoded_string
        except:
            return header

    def _extract_email_body(self, email_message) -> str:
        """Extrahiert E-Mail-Text"""
        body = ''
        if email_message.is_multipart():
            for part in email_message.walk():
                if part.get_content_type() == 'text/plain':
                    charset = part.get_content_charset() or 'utf-8'
                    try:
                        body += part.get_payload(decode=True).decode(charset, errors='ignore')
                    except:
                        body += str(part.get_payload())
                    break
        else:
            charset = email_message.get_content_charset() or 'utf-8'
            try:
                body = email_message.get_payload(decode=True).decode(charset, errors='ignore')
            except:
                body = str(email_message.get_payload())
        return body.strip()

    def send_reply(self, original_email_data: dict, reply_body: str) -> bool:
        """Sendet Antwort-E-Mail"""
        try:
            reply_subject = f"Re: {original_email_data['subject']}"
            if reply_subject.startswith("Re: Re:"):
                reply_subject = original_email_data['subject']

            msg = MIMEMultipart()
            msg['From'] = Config.EMAIL_ADDRESS
            msg['To'] = self._extract_email_address(original_email_data['sender'])
            msg['Subject'] = reply_subject
            msg['In-Reply-To'] = original_email_data.get('message_id', '')
            msg['References'] = original_email_data.get('message_id', '')

            msg.attach(MIMEText(reply_body, 'plain', 'utf-8'))

            self.smtp_connection.sendmail(
                Config.EMAIL_ADDRESS,
                msg['To'],
                msg.as_string()
            )

            logger.info(f"Antwort gesendet an: {msg['To']}")
            return True
        except Exception as e:
            logger.error(f"Fehler beim Senden: {e}")
            return False

    def _extract_email_address(self, sender_field: str) -> str:
        """Extrahiert E-Mail-Adresse"""
        if '<' in sender_field and '>' in sender_field:
            return sender_field.split('<')[1].split('>')[0].strip()
        return sender_field.strip()

    def _save_processed_email(self, email_id: str):
        """Speichert bearbeitete E-Mail"""
        self.processed_emails.add(email_id)

    def process_emails(self) -> int:
        """Verarbeitet E-Mails - Basis-Implementierung"""
        return 0  # Wird von Enhanced Agent überschrieben
    
    def start_idle_mode(self, callback: Callable[[], None]):
        """
        Startet IMAP IDLE Modus für sofortige E-Mail-Benachrichtigung
        
        Args:
            callback: Funktion die bei neuer E-Mail aufgerufen wird
        """
        if self.idle_running:
            logger.warning("IDLE-Modus läuft bereits")
            return
        
        self.idle_callback = callback
        self.idle_running = True
        self.idle_thread = threading.Thread(target=self._idle_loop, daemon=True)
        self.idle_thread.start()
        logger.info("⚡ IMAP IDLE-Modus gestartet - Wartet auf neue E-Mails...")
    
    def stop_idle_mode(self):
        """Stoppt IMAP IDLE Modus"""
        self.idle_running = False
        if self.idle_thread:
            self.idle_thread.join(timeout=5)
        logger.info("IMAP IDLE-Modus gestoppt")
    
    def _idle_loop(self):
        """
        Hauptschleife für IMAP IDLE - Bombensicher mit intelligentem Reconnect
        
        Reconnect-Strategie:
        1. Verbindung verloren → Warte 10 Sekunden, dann Reconnect
        2. Wenn fehlgeschlagen → 3x alle 3 Minuten versuchen
        3. Danach → Weiter alle 3 Minuten (permanent)
        
        Funktioniert auch nach Router-Neustart!
        """
        # Intelligente Reconnect-Delays
        reconnect_attempts = 0
        first_reconnect_delay = 10  # 10 Sekunden beim ersten Versuch
        subsequent_reconnect_delay = 180  # 3 Minuten bei weiteren Versuchen
        max_fast_attempts = 3  # Nach 3 Versuchen permanent alle 3 Min
        
        idle_timeout = 29 * 60  # 29 Minuten (Gmail-Limit: 30 Min)
        
        while self.idle_running:
            try:
                # Stelle sicher dass Verbindung besteht
                if not self.imap_connection:
                    reconnect_attempts += 1
                    
                    # Bestimme Reconnect-Delay basierend auf Versuchen
                    if reconnect_attempts == 1:
                        # Erster Versuch: 10 Sekunden
                        delay = first_reconnect_delay
                        logger.warning(f"🔄 IDLE: Verbindung verloren! Reconnect in {delay} Sekunden... (Versuch {reconnect_attempts})")
                    elif reconnect_attempts <= max_fast_attempts:
                        # Versuche 2-4: 3 Minuten
                        delay = subsequent_reconnect_delay
                        logger.warning(f"🔄 IDLE: Reconnect-Versuch {reconnect_attempts} in {delay//60} Minuten...")
                    else:
                        # Ab Versuch 5: Permanent alle 3 Minuten
                        delay = subsequent_reconnect_delay
                        logger.warning(f"🔄 IDLE: Langzeit-Reconnect (Versuch {reconnect_attempts}) in {delay//60} Minuten...")
                    
                    time.sleep(delay)
                    
                    # Versuche Reconnect
                    logger.info(f"🔌 IDLE: Versuche Verbindung wiederherzustellen... (Versuch {reconnect_attempts})")
                    if not self.connect_imap():
                        logger.error(f"❌ IDLE: Reconnect fehlgeschlagen (Versuch {reconnect_attempts})")
                        continue
                    
                    # Erfolgreicher Reconnect!
                    logger.info(f"✅ IDLE: Verbindung wiederhergestellt nach {reconnect_attempts} Versuchen!")
                    reconnect_attempts = 0  # Reset Counter bei Erfolg
                
                # Wähle INBOX
                with self._idle_lock:
                    self.imap_connection.select('INBOX')
                    
                    # Starte IDLE
                    tag = self.imap_connection._new_tag().decode()
                    self.imap_connection.send(b'%s IDLE\r\n' % tag.encode())
                    
                    # Warte auf Response
                    response = self.imap_connection.readline().decode('utf-8', errors='ignore').strip()
                    if '+ idling' not in response.lower() and 'waiting' not in response.lower():
                        logger.warning(f"IDLE Start fehlgeschlagen: {response}")
                        time.sleep(5)
                        continue
                    
                    logger.debug("📬 IDLE aktiv - Warte auf neue Nachrichten...")
                
                # Warte auf Benachrichtigung oder Timeout
                start_time = time.time()
                notification_received = False
                
                while self.idle_running and (time.time() - start_time) < idle_timeout:
                    try:
                        # Check ob Daten verfügbar sind (100ms Timeout für schnelle Reaktion)
                        readable, _, _ = select.select([self.imap_connection.socket()], [], [], 0.1)
                        
                        if readable:
                            # Neue Nachricht!
                            with self._idle_lock:
                                response = self.imap_connection.readline().decode('utf-8', errors='ignore').strip()
                                
                                # Prüfe ob es eine EXISTS oder RECENT Benachrichtigung ist
                                if 'EXISTS' in response or 'RECENT' in response:
                                    logger.info(f"⚡ NEUE E-MAIL ERKANNT! - {response}")
                                    notification_received = True
                                    break
                    
                    except Exception as e:
                        logger.debug(f"IDLE-Schleife Fehler: {e}")
                        break
                
                # Beende IDLE
                try:
                    with self._idle_lock:
                        self.imap_connection.send(b'DONE\r\n')
                        # Lese verbleibende Responses
                        while True:
                            try:
                                line = self.imap_connection.readline().decode('utf-8', errors='ignore').strip()
                                if not line or 'OK IDLE' in line or tag in line:
                                    break
                            except:
                                break
                
                except Exception as e:
                    logger.debug(f"IDLE-Beenden Fehler: {e}")
                
                # Wenn neue E-Mail erkannt, rufe Callback auf
                if notification_received and self.idle_callback:
                    logger.info("🚀 Verarbeite neue E-Mail(s) SOFORT...")
                    try:
                        self.idle_callback()
                    except Exception as e:
                        logger.error(f"IDLE-Callback Fehler: {e}")
                
                # Kurze Pause vor erneutem IDLE (für Stabilität)
                time.sleep(0.5)
            
            except imaplib.IMAP4.abort as e:
                logger.warning(f"❌ IDLE: Verbindung abgebrochen (IMAP4.abort) - {e}")
                # Verbindung sauber trennen
                try:
                    if self.imap_connection:
                        try:
                            self.imap_connection.close()
                        except:
                            pass
                        try:
                            self.imap_connection.logout()
                        except:
                            pass
                except:
                    pass
                finally:
                    self.imap_connection = None
                # Reconnect wird von der Hauptschleife gehandhabt (intelligente Delays)
            
            except socket.error as e:
                logger.warning(f"❌ IDLE: Netzwerk-Fehler (Socket) - {e}")
                # Bei Netzwerk-Fehlern (z.B. Router-Neustart)
                try:
                    if self.imap_connection:
                        try:
                            self.imap_connection.close()
                        except:
                            pass
                        try:
                            self.imap_connection.logout()
                        except:
                            pass
                except:
                    pass
                finally:
                    self.imap_connection = None
                logger.info("🔄 Netzwerk-Problem erkannt - Intelligenter Reconnect startet...")
            
            except Exception as e:
                logger.error(f"❌ IDLE: Unerwarteter Fehler - {type(e).__name__}: {e}")
                # Bei allen anderen Fehlern
                try:
                    if self.imap_connection:
                        try:
                            self.imap_connection.close()
                        except:
                            pass
                        try:
                            self.imap_connection.logout()
                        except:
                            pass
                except:
                    pass
                finally:
                    self.imap_connection = None
        
        logger.info("IDLE-Schleife beendet")

