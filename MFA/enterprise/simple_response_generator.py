#!/usr/bin/env python3
"""
SIMPLE RESPONSE GENERATOR
Einfacher Response-Generator für das MFA System
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class SimpleResponseGenerator:
    """Einfacher Response-Generator"""
    
    def __init__(self):
        self.response_templates = {
            "appointment": """
Sehr geehrte/r {name},

vielen Dank für Ihre Terminanfrage. 

Wir haben Ihre Anfrage erhalten und werden uns schnellstmöglich bei Ihnen melden, um einen passenden Termin zu vereinbaren.

Bei dringenden Anliegen erreichen Sie uns telefonisch unter unserer Praxisnummer.

Mit freundlichen Grüßen
Ihr Praxisteam
""",
            "appointment_cancel": """
Sehr geehrte/r {name},

vielen Dank für Ihre Nachricht bezüglich der Terminabsage.

Ihr Termin wurde erfolgreich storniert. Gerne können Sie einen neuen Termin vereinbaren, wenn Sie möchten.

Bei Fragen stehen wir Ihnen gerne zur Verfügung.

Mit freundlichen Grüßen
Ihr Praxisteam
""",
            "emergency": """
Sehr geehrte/r {name},

vielen Dank für Ihre Nachricht.

Bei medizinischen Notfällen wenden Sie sich bitte sofort an den Notruf 112 oder fahren Sie zur nächsten Notaufnahme.

Für nicht-dringende Anliegen können Sie gerne einen Termin vereinbaren.

Mit freundlichen Grüßen
Ihr Praxisteam
""",
            "prescription_request": """
Sehr geehrte/r {name},

vielen Dank für Ihre Anfrage bezüglich eines Rezepts.

Bitte vereinbaren Sie einen Termin, damit wir Ihre Medikation überprüfen und ein neues Rezept ausstellen können.

Mit freundlichen Grüßen
Ihr Praxisteam
""",
            "sick_leave_certificate": """
Sehr geehrte/r {name},

vielen Dank für Ihre Anfrage bezüglich einer Krankmeldung.

Bitte vereinbaren Sie einen Termin, damit wir eine entsprechende Bescheinigung ausstellen können.

Mit freundlichen Grüßen
Ihr Praxisteam
""",
            "general_inquiry": """
Sehr geehrte/r {name},

vielen Dank für Ihre Nachricht.

Wir haben Ihre Anfrage erhalten und werden uns schnellstmöglich bei Ihnen melden.

Bei dringenden Anliegen erreichen Sie uns telefonisch.

Mit freundlichen Grüßen
Ihr Praxisteam
""",
            "kardiologe_appointment": """
Sehr geehrte/r {name},

vielen Dank für Ihre Anfrage bezüglich eines Kardiologen-Termins.

Wir werden Sie an einen geeigneten Kardiologen überweisen und uns um die Terminvereinbarung kümmern.

Sie erhalten in Kürze weitere Informationen.

Mit freundlichen Grüßen
Ihr Praxisteam
""",
            "endokrinologe_appointment": """
Sehr geehrte/r {name},

vielen Dank für Ihre Anfrage bezüglich eines Endokrinologen-Termins.

Wir werden Sie an einen geeigneten Endokrinologen überweisen und uns um die Terminvereinbarung kümmern.

Sie erhalten in Kürze weitere Informationen.

Mit freundlichen Grüßen
Ihr Praxisteam
""",
            "orthopaede_appointment": """
Sehr geehrte/r {name},

vielen Dank für Ihre Anfrage bezüglich eines Orthopäden-Termins.

Wir werden Sie an einen geeigneten Orthopäden überweisen und uns um die Terminvereinbarung kümmern.

Sie erhalten in Kürze weitere Informationen.

Mit freundlichen Grüßen
Ihr Praxisteam
""",
            "neurologe_appointment": """
Sehr geehrte/r {name},

vielen Dank für Ihre Anfrage bezüglich eines Neurologen-Termins.

Wir werden Sie an einen geeigneten Neurologen überweisen und uns um die Terminvereinbarung kümmern.

Sie erhalten in Kürze weitere Informationen.

Mit freundlichen Grüßen
Ihr Praxisteam
""",
            "preventive_care_inquiry": """
Sehr geehrte/r {name},

vielen Dank für Ihre Anfrage bezüglich der Vorsorgeuntersuchung.

Wir freuen uns, dass Sie sich um Ihre Gesundheit kümmern. Gerne vereinbaren wir einen Termin für die Vorsorgeuntersuchung.

Mit freundlichen Grüßen
Ihr Praxisteam
""",
            "medical_question": """
Sehr geehrte/r {name},

vielen Dank für Ihre medizinische Frage.

Wir haben Ihre Anfrage erhalten und werden uns schnellstmöglich bei Ihnen melden.

Bei dringenden medizinischen Anliegen erreichen Sie uns telefonisch.

Mit freundlichen Grüßen
Ihr Praxisteam
""",
            "specialist_referral": """
Sehr geehrte/r {name},

vielen Dank für Ihre Anfrage bezüglich einer Überweisung.

Wir werden die entsprechende Überweisung ausstellen und uns um die Weiterleitung kümmern.

Sie erhalten in Kürze weitere Informationen.

Mit freundlichen Grüßen
Ihr Praxisteam
""",
            "test_results_inquiry": """
Sehr geehrte/r {name},

vielen Dank für Ihre Anfrage bezüglich Ihrer Untersuchungsergebnisse.

Wir prüfen Ihre Ergebnisse und werden uns schnellstmöglich bei Ihnen melden.

Mit freundlichen Grüßen
Ihr Praxisteam
""",
            "chronic_condition_management": """
Sehr geehrte/r {name},

vielen Dank für Ihre Nachricht bezüglich Ihrer chronischen Erkrankung.

Wir werden Ihre Anfrage prüfen und uns schnellstmöglich bei Ihnen melden, um die weitere Behandlung zu besprechen.

Mit freundlichen Grüßen
Ihr Praxisteam
""",
            "insurance_verification": """
Sehr geehrte/r {name},

vielen Dank für Ihre Anfrage bezüglich Ihrer Versicherung.

Wir prüfen Ihre Versicherungsdaten und werden uns schnellstmöglich bei Ihnen melden.

Mit freundlichen Grüßen
Ihr Praxisteam
""",
            "billing_inquiry": """
Sehr geehrte/r {name},

vielen Dank für Ihre Anfrage bezüglich Ihrer Rechnung.

Wir prüfen Ihre Anfrage und werden uns schnellstmöglich bei Ihnen melden.

Bei Fragen stehen wir Ihnen gerne zur Verfügung.

Mit freundlichen Grüßen
Ihr Praxisteam
""",
            "medical_records_request": """
Sehr geehrte/r {name},

vielen Dank für Ihre Anfrage bezüglich Ihrer Patientenakte.

Wir prüfen Ihre Anfrage und werden uns schnellstmöglich bei Ihnen melden.

Mit freundlichen Grüßen
Ihr Praxisteam
""",
            "appointment_confirm": """
Sehr geehrte/r {name},

vielen Dank für Ihre Terminbestätigung.

Ihr Termin ist bestätigt. Wir freuen uns auf Ihren Besuch.

Bei Fragen stehen wir Ihnen gerne zur Verfügung.

Mit freundlichen Grüßen
Ihr Praxisteam
""",
            "hausarzt_praxis_inquiry": """
Sehr geehrte/r {name},

vielen Dank für Ihre Anfrage an unsere Hausarztpraxis.

Wir haben Ihre Nachricht erhalten und werden uns schnellstmöglich bei Ihnen melden.

Bei dringenden Anliegen erreichen Sie uns telefonisch.

Mit freundlichen Grüßen
Ihr Praxisteam
"""
        }
    
    def generate_response(self, context: Dict[str, Any]) -> str:
        """Generiert eine einfache Antwort"""
        try:
            intent = context.get("intent_type", "general_inquiry")
            sender_name = context.get("sender_name", "Patient/in")
            
            # Wähle passende Vorlage
            template = self.response_templates.get(intent, self.response_templates["general_inquiry"])
            
            # Personalisiere Antwort
            response = template.format(name=sender_name)
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"Fehler bei Response-Generierung: {e}")
            return """
Sehr geehrte/r Patient/in,

vielen Dank für Ihre Nachricht.

Wir haben Ihre Anfrage erhalten und werden uns schnellstmöglich bei Ihnen melden.

Mit freundlichen Grüßen
Ihr Praxisteam
"""

def get_simple_response_generator() -> SimpleResponseGenerator:
    """Factory-Funktion"""
    return SimpleResponseGenerator()

if __name__ == "__main__":
    # Test
    generator = SimpleResponseGenerator()
    context = {
        "intent_type": "appointment",
        "sender_name": "Max Mustermann"
    }
    response = generator.generate_response(context)
    print(response)
