import re
import hashlib

PII_PATTERNS = [
    # emails
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    # phone numbers (simple)
    re.compile(r"\b\+?\d[\d\s\-()]{6,}\d\b"),
    # dates like DD.MM.YYYY or YYYY-MM-DD
    re.compile(r"\b\d{1,2}[\./-]\d{1,2}[\./-]\d{2,4}\b"),
    re.compile(r"\b\d{4}-\d{1,2}-\d{1,2}\b"),
    # simple street address pattern: StreetName 12
    re.compile(r"\b[A-Za-zÄÖÜäöüß][A-Za-zäöüß\.\s]+\s\d{1,4}[a-zA-Z]?\b")
]


def hash_owner(email: str) -> str:
    if not email:
        return ''
    return hashlib.sha256(email.encode('utf-8')).hexdigest()


def redact_text(text: str) -> str:
    if not text:
        return text
    redacted = text
    for pat in PII_PATTERNS:
        redacted = pat.sub('[REDACTED_PII]', redacted)
    return redacted


def contains_pii(text: str) -> bool:
    if not text:
        return False
    for pat in PII_PATTERNS:
        if pat.search(text):
            return True
    return False


