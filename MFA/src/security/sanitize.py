"""
Input-Sanitizing und PII-Redaktion für E-Mail-Inhalte
Entfernt HTML-Tags und redigiert persönliche Informationen
"""

import re

def strip_html(input_text: str) -> str:
    """Entfernt HTML-Tags aus Text"""
    return re.sub(r'<[^>]*>', ' ', input_text).replace('  ', ' ').strip()

def redact_pii(input_text: str) -> str:
    """Redigiert persönliche Informationen"""
    # E-Mail-Adressen redigieren
    input_text = re.sub(r'\b[\w.%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b', '[email:redacted]', input_text)
    
    # Telefonnummern redigieren
    input_text = re.sub(r'\b(\+?49|0)[1-9]\d{7,}\b', '[phone:redacted]', input_text)
    
    # Geburtsdaten redigieren
    input_text = re.sub(r'\b(0[1-9]|[12]\d|3[01])\.(0[1-9]|1[0-2])\.(19|20)\d{2}\b', '[dob:redacted]', input_text)
    
    return input_text

def sanitize_inbound_email(html_or_text: str) -> str:
    """Sanitized eingehende E-Mail-Inhalte"""
    return redact_pii(strip_html(html_or_text))
