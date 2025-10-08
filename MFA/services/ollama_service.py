#!/usr/bin/env python3
"""
OLLAMA SERVICE
Enterprise-Level Integration mit Ollama LLM
"""

import requests
import logging
import time
import re
from datetime import datetime
from typing import Dict, Any, Optional
from utils.privacy import redact_text, contains_pii
from dataclasses import dataclass
from core.config import Config

logger = logging.getLogger(__name__)

@dataclass
class OllamaResponse:
    """Response-Struktur für Ollama"""
    response: str
    model: str
    created_at: datetime
    done: bool = True
    context: Optional[list] = None
    total_duration: Optional[float] = None
    load_duration: Optional[float] = None
    prompt_eval_count: Optional[int] = None
    prompt_eval_duration: Optional[float] = None
    eval_count: Optional[int] = None
    eval_duration: Optional[float] = None

class OllamaService:
    """Enterprise-Level Ollama Service"""
    
    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None, max_connections: int = 10):
        # Use config values by default so model can be set via .env
        self.base_url = base_url or getattr(Config, 'OLLAMA_BASE_URL', 'http://localhost:11434')
        self.model = model or getattr(Config, 'OLLAMA_MODEL', 'qwen2.5:14b-instruct')
        self.max_connections = max_connections

        # Connection-Pooling mit Adapter
        self.session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(pool_connections=max_connections, pool_maxsize=max_connections)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        self.session.timeout = self._get_adaptive_timeout()

    def _retry_with_backoff(self, func, max_retries: int = 5, backoff_factor: float = 1.5, exceptions: tuple = (requests.exceptions.RequestException,)):
        """Retry-Logik mit exponentiellem Backoff"""
        for attempt in range(max_retries):
            try:
                return func()
            except exceptions as e:
                if attempt == max_retries - 1:
                    logger.error(f"Alle {max_retries} Versuche fehlgeschlagen: {e}")
                    raise

                wait_time = backoff_factor ** attempt
                logger.warning(f"Ollama-Versuch {attempt + 1} fehlgeschlagen, warte {wait_time:.2f}s: {e}")
                time.sleep(wait_time)

    def generate_response(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> OllamaResponse:
        """Generiert eine KI-Antwort mit Retry-Logik"""
        def _ollama_call():
            # Erstelle den vollständigen Prompt mit Kontext
            full_prompt = self._build_prompt(prompt, context)

            # Ollama API-Aufruf
            response = self.session.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "max_tokens": 1000
                    }
                }
            )

            if response.status_code == 200:
                data = response.json()
                return OllamaResponse(
                    response=data.get("response", ""),
                    model=data.get("model", self.model),
                    created_at=datetime.now(),
                    done=data.get("done", True),
                    context=data.get("context"),
                    total_duration=data.get("total_duration"),
                    load_duration=data.get("load_duration"),
                    prompt_eval_count=data.get("prompt_eval_count"),
                    prompt_eval_duration=data.get("prompt_eval_duration"),
                    eval_count=data.get("eval_count"),
                    eval_duration=data.get("eval_duration")
                )
            else:
                logger.error(f"Ollama API-Fehler: {response.status_code}")
                raise requests.exceptions.RequestException(f"API Error: {response.status_code}")

        try:
            return self._retry_with_backoff(_ollama_call, max_retries=5, backoff_factor=1.5)
        except Exception as e:
            logger.error(f"Fehler bei Ollama-Aufruf nach allen Versuchen: {e}")
            # Bei KI-Fehlern: E-Mail in Queue legen statt Fallback senden
            # Das wird durch den aufrufenden Code gehandhabt
            raise e

    def generate_email_response(self, subject: str, body: str, sender_name: str = "", thread_id: str = "", sender_email: str = "", message_id: str = "", in_reply_to: str = "") -> str:
        """Generiert eine intelligente E-Mail-Antwort"""
        try:
            # Erstelle Kontext für die Antwort-Generierung
            context = {
                "email_subject": subject,
                "email_body": body,
                "sender_name": sender_name,
                "thread_id": thread_id,
                "sender_email": sender_email,
                "message_id": message_id,
                "in_reply_to": in_reply_to,
                "response_context": "medical_practice_email"
            }

            # Erstelle Prompt für E-Mail-Antwort
            prompt = f"""
Du bist ein intelligenter medizinischer Assistent für eine Hausarztpraxis.

E-Mail von: {sender_name or 'Patient/in'}
Betreff: {subject}
Inhalt: {body}

Bitte generiere eine professionelle, einfühlsame und hilfreiche Antwort auf Deutsch.

Wichtige Regeln:
- Sei professionell aber freundlich
- Antworte direkt auf die Anfrage des Patienten
- Verwende den Namen des Patienten wenn bekannt
- Bei Terminanfragen schlage konkrete Termine vor
- Bei medizinischen Fragen gib hilfreiche Ratschläge
- Bei Notfällen verweise an den Notruf 112
- Halte die Antwort prägnant aber vollständig

Antwort:
"""

            # Generiere Antwort mit Ollama
            ollama_response = self.generate_response(prompt, context)

            if ollama_response and ollama_response.response:
                response_text = ollama_response.response.strip()

                # Entferne mögliche Prompt-Echos
                if response_text.startswith("Antwort:"):
                    response_text = response_text[8:].strip()

                # Privacy enforcement: Prüfe ob die Antwort nach sensiblen Daten fragt
                # WICHTIG: Wir redaktieren NICHT die Antwort selbst (kein redact_text())
                # sondern verhindern nur, dass nach PII gefragt wird
                
                # If the original request was flagged as a privacy_request, override
                # the content with a privacy notice to avoid asking for PII.
                if context.get('intent') == 'privacy_request' or context.get('privacy_request'):
                    # Do not ask for or disclose PII via email
                    safe_note = "\n\nAus Datenschutzgründen kann die Praxis per E-Mail keine sensiblen personenbezogenen Daten anfordern oder mitteilen. Bitte nutzen Sie das sichere Patientenportal oder rufen Sie uns an, um vertrauliche Informationen zu übermitteln."
                    # Remove explicit asks for PII by appending the safe note
                    response_text = re.sub(r"(?i)(bitte\s+(senden|teilen|nennen|mitteilen)\s+ihre\s+(name|adresse|geburtsdatum|versichertennummer|personenbezogenen\s+daten)|teilen\s+sie\s+uns\s+(ihre|ihren)\s+(name|adresse|geburtsdatum)|nennen\s+sie\s+bitte\s+(ihre|ihren)\s+(name|adresse|geburtsdatum)).+", "", response_text)
                    response_text = response_text.strip() + safe_note

                return response_text
            else:
                logger.error("Keine Antwort von Ollama erhalten")
                raise Exception("Keine KI-Antwort erhalten")

        except Exception as e:
            logger.error(f"Fehler bei E-Mail-Antwort-Generierung: {e}")
            raise e

    def _build_prompt(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Baut den vollständigen Prompt mit Kontext"""
        system_prompt = """Du bist ein intelligenter medizinischer Assistent für eine Hausarztpraxis. 
        Antworte professionell, einfühlsam und hilfreich auf Deutsch.
        
        Wichtige Regeln:
        - Antworte immer auf Deutsch
        - Sei professionell aber freundlich
        - Bei medizinischen Notfällen verweise an Notruf 112
        - Für Terminbuchungen prüfe Verfügbarkeit
        - Speichere wichtige Informationen für spätere Referenz"""
        
        if context:
            context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
            return f"{system_prompt}\n\nKontext:\n{context_str}\n\nPatienten-Anfrage: {prompt}"
        else:
            return f"{system_prompt}\n\nPatienten-Anfrage: {prompt}"

    def _get_adaptive_timeout(self) -> int:
        """Berechnet adaptiven Timeout basierend auf Systemlast und Prompt-Komplexität"""
        import psutil
        import os

        # Basis-Timeout
        base_timeout = 30

        try:
            # CPU-Last-Faktor
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_factor = 1.0 + (cpu_percent / 100.0)  # 0-100% CPU = 1.0-2.0x Timeout

            # Memory-Faktor
            memory = psutil.virtual_memory()
            memory_factor = 1.0 + (memory.percent / 100.0)  # 0-100% RAM = 1.0-2.0x Timeout

            # Anzahl laufender Prozesse
            process_count = len(psutil.pids())
            process_factor = 1.0 + (process_count / 1000.0)  # Jeder 1000 Prozesse = +1s

            # Berechne adaptiven Timeout
            adaptive_timeout = base_timeout * cpu_factor * memory_factor * process_factor

            # Begrenze zwischen 5-120 Sekunden
            adaptive_timeout = max(5, min(120, adaptive_timeout))

            logger.debug(f"Adaptive Timeout berechnet: {adaptive_timeout:.1f}s (CPU: {cpu_percent:.1f}%, RAM: {memory.percent:.1f}%, Prozesse: {process_count})")

            return int(adaptive_timeout)

        except Exception as e:
            logger.warning(f"Fehler bei adaptiver Timeout-Berechnung: {e}, verwende Standard 30s")
            return 30

    def test_connection(self) -> bool:
        """Testet die Verbindung zu Ollama"""
        try:
            response = self.session.get(f"{self.base_url}/api/version", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Ollama-Verbindungstest fehlgeschlagen: {e}")
        return False

    # Compatibility stubs for older callers expecting persistence hooks
    def save_email_to_conversation(self, **kwargs) -> bool:
        """Compatibility stub: records email metadata (no-op here).

        In a full implementation this would persist to ConversationDB. Returning True
        to indicate the call succeeded and avoid AttributeError at runtime.
        """
        logger.debug(f"save_email_to_conversation called with keys: {list(kwargs.keys())}")
        return True

    def save_successful_response(self, subject: str, body: str, response: str) -> bool:
        """Compatibility stub: record successful response (no-op)."""
        logger.debug(f"save_successful_response called for subject: {subject[:60]}")
        return True

    def _create_fallback_response(self, prompt: str) -> OllamaResponse:
        """Erstellt eine Fallback-Antwort wenn Ollama nicht verfügbar ist"""
        fallback_response = """Vielen Dank für Ihre Nachricht. 
        
        Leider ist unser KI-System momentan nicht verfügbar. 
        Bitte kontaktieren Sie uns telefonisch unter der Praxisnummer 
        oder senden Sie uns eine E-Mail mit Ihrem Anliegen.
        
        Wir werden uns schnellstmöglich bei Ihnen melden.
        
        Mit freundlichen Grüßen
        Ihr Praxisteam"""
        
        return OllamaResponse(
            response=fallback_response,
            model="fallback",
            created_at=datetime.now(),
            done=True
        )

def get_ollama_service() -> OllamaService:
    """Factory-Funktion für OllamaService"""
    return OllamaService()

if __name__ == "__main__":
    # Test
    service = OllamaService()
    response = service.generate_response("Hallo, ich brauche einen Termin")
    print(f"Response: {response.response}")
