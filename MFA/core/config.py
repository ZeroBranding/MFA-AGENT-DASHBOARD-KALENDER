import os
from dotenv import load_dotenv

# Lade Umgebungsvariablen aus .env Datei
load_dotenv()

class Config:
    # Gmail IMAP/SMTP Konfiguration
    IMAP_SERVER = "imap.gmail.com"
    IMAP_PORT = 993
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587

    # Gmail Zugangsdaten (aus Umgebungsvariablen)
    EMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
    EMAIL_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")  # App-Password, nicht das normale Passwort!

    # Ollama Konfiguration
    OLLAMA_MODEL = "qwen2.5:14b-instruct"  # Qwen 2.5 14B Instruct (Produktion)
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    # E-Mail Signatur
    EMAIL_SIGNATURE = """
---
Eli5 Praxis
Maderweg 157
48157 Münster
---
"""

    # Grundlegende Einstellungen
    PROCESSED_EMAILS_FILE = "processed_emails.txt"  # Zum Verfolgen bearbeiteter E-Mails

    # Agent Konfiguration
    ENABLE_IMAP_IDLE = True  # IMAP IDLE für sofortige E-Mail-Benachrichtigung (empfohlen)
    CHECK_INTERVAL_SECONDS = 10  # Fallback: Wie oft E-Mails prüfen wenn IDLE nicht verfügbar (in Sekunden)
    MAX_RETRIES = 3  # Maximale Anzahl von Wiederholungsversuchen
    RETRY_DELAY_SECONDS = 5  # Verzögerung zwischen Wiederholungen

    # Termin-Integration
    ONLINE_BOOKING_URL = "https://termine.eli5-praxis.de"  # Ihr externer Terminkalender
    AUTO_ADD_BOOKING_LINK = True  # Automatisch Termin-Link in Antworten einfügen

    # Threading und Deduplizierung
    ENABLE_THREADING = True  # Thread-Erkennung aktivieren
    ENABLE_PERSISTENT_DEDUPE = True  # Persistente Deduplizierung (SQLite statt Textdatei)
    MAX_CONTEXT_EMAILS = 10  # Maximale Anzahl Kontext-E-Mails per Thread
    CLEANUP_OLD_EMAILS_DAYS = 90  # Alte E-Mails nach X Tagen löschen

    # Arztpraxis-Konfiguration
    PRACTICE_NAME = "Eli5 Praxis"  # Name der Arztpraxis
    PRACTICE_TYPE = "Hausarztpraxis"  # Typ der Praxis
    PRACTICE_LOCATION = "Maderweg 157, 48157 Münster"  # Adresse
    ENABLE_TOPIC_FILTER = True  # Nur praxisbezogene Anfragen beantworten
    MAX_THREAD_AGE_DAYS = 30  # Maximale Thread-Alter in Tagen

    # Logging Konfiguration
    LOG_LEVEL = "INFO"
    LOG_FILE = "email_agent.log"

    # E-Mail Verarbeitung
    AUTO_REPLY_SUBJECT_PREFIX = "Re: "

    @classmethod
    def validate_config(cls):
        """Überprüft, ob alle erforderlichen Konfigurationseinstellungen vorhanden sind"""
        required_vars = ["EMAIL_ADDRESS", "EMAIL_PASSWORD"]
        missing_vars = [var for var in required_vars if not getattr(cls, var)]

        if missing_vars:
            raise ValueError(f"Fehlende erforderliche Umgebungsvariablen: {', '.join(missing_vars)}")

        return True
