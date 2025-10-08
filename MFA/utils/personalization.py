"""
personalization.py
Leichte Utilities zur Personalisierung von Antworten.
"""
from enterprise.enterprise_response_generator import PatientProfile


def make_temp_profile(email: str, name: str = "") -> PatientProfile:
    """Erstellt ein temporäres PatientProfile-Objekt zur Personalisierung."""
    return PatientProfile(email=email, name=name)


def apply_basic_personalization(text: str, profile: PatientProfile) -> str:
    """Einfache Personalisierung: Namen einsetzen, Sprache/Style beachten."""
    if not profile:
        return text
    try:
        name = profile.name or profile.email.split('@')[0].capitalize()
        return text.replace('{patient_name}', name)
    except Exception:
        return text


