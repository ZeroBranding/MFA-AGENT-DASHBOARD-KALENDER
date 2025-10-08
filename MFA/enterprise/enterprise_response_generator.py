#!/usr/bin/env python3
"""
ENTERPRISE-LEVEL KI-ANTWORT-GENERATOR
Personalisierte, kontextsensitive E-Mail-Antworten für medizinische Praxen
"""

import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ResponseTone(Enum):
    """Antwort-Tonarten"""
    PROFESSIONAL = "professional"
    EMPATHETIC = "empathetic"
    URGENT = "urgent"
    FRIENDLY = "friendly"
    FORMAL = "formal"

class ResponseType(Enum):
    """Antwort-Typen"""
    APPOINTMENT_CONFIRMATION = "appointment_confirmation"
    APPOINTMENT_SUGGESTION = "appointment_suggestion"
    APPOINTMENT_CANCELLATION = "appointment_cancellation"
    STATUS_INQUIRY = "status_inquiry"
    MEDICAL_ADVICE = "medical_advice"
    SPECIALIST_REFERRAL = "specialist_referral"
    EMERGENCY_RESPONSE = "emergency_response"
    GENERAL_RESPONSE = "general_response"
    HAUSARZT_PRAXIS_INQUIRY = "hausarzt_praxis_inquiry"  # NEU: Hausarzt-Praxis-Anfragen

@dataclass
class PatientProfile:
    """Patienten-Profil für personalisierte Antworten"""
    email: str
    name: str = ""
    age_group: str = "unknown"  # child, adult, senior
    language_preference: str = "de"
    communication_style: str = "formal"  # formal, friendly, direct
    medical_history: List[str] = None
    previous_interactions: int = 0
    last_contact: Optional[datetime] = None

    def __post_init__(self):
        if self.medical_history is None:
            self.medical_history = []

@dataclass
class ResponseContext:
    """Kontext für die Antwort-Generierung"""
    intent_type: str
    urgency_level: str
    entities: Dict[str, List[str]]
    subject: str = ""
    body: str = ""
    sender_email: str = ""
    confidence: float = 0.0
    context_info: Dict[str, Any] = None
    calendar_info: Dict[str, Any] = None
    patient_info: Dict[str, Any] = None
    patient_profile: Any = None  # Backward compatibility
    tone: ResponseTone = ResponseTone.PROFESSIONAL
    response_type: ResponseType = ResponseType.GENERAL_RESPONSE

    def __post_init__(self):
        if self.context_info is None:
            self.context_info = {}
        if self.calendar_info is None:
            self.calendar_info = {}
        if self.patient_info is None:
            self.patient_info = {}

        # Synchronisiere patient_profile mit patient_info für backward compatibility
        if self.patient_profile is not None and not self.patient_info:
            self.patient_info = {"profile": self.patient_profile}

class EnterpriseResponseGenerator:
    """Enterprise-Level KI-Antwort-Generator"""

    def __init__(self):
        """Initialisiert den Antwort-Generator"""
        self._load_response_templates()
        self._load_medical_knowledge()
        self._load_personalization_rules()

    def _load_response_templates(self):
        """Lädt Antwort-Templates"""
        self.response_templates = {
            ResponseType.APPOINTMENT_SUGGESTION: {
                'structure': [
                    'greeting',
                    'acknowledgment',
                    'appointment_suggestions',
                    'instructions',
                    'closing'
                ],
                'tone_adjustments': {
                    ResponseTone.PROFESSIONAL: {
                        'greeting': 'Sehr geehrte/r {patient_name},',
                        'acknowledgment': 'vielen Dank für Ihre Terminanfrage.',
                        'closing': 'Mit freundlichen Grüßen\nIhr Praxis-Team'
                    },
                    ResponseTone.EMPATHETIC: {
                        'greeting': 'Liebe/r {patient_name},',
                        'acknowledgment': 'ich verstehe, dass Sie einen Termin benötigen.',
                        'closing': 'Herzliche Grüße\nIhr Praxis-Team'
                    }
                }
            },
            ResponseType.APPOINTMENT_CONFIRMATION: {
                'structure': [
                    'greeting',
                    'confirmation',
                    'appointment_details',
                    'preparation_instructions',
                    'closing'
                ],
                'tone_adjustments': {
                    ResponseTone.PROFESSIONAL: {
                        'greeting': 'Sehr geehrte/r {patient_name},',
                        'confirmation': 'Ihr Termin wurde erfolgreich gebucht.',
                        'closing': 'Mit freundlichen Grüßen\nIhr Praxis-Team'
                    }
                }
            },
            ResponseType.EMERGENCY_RESPONSE: {
                'structure': [
                    'urgent_greeting',
                    'immediate_action',
                    'contact_info',
                    'urgent_closing'
                ],
                'tone_adjustments': {
                    ResponseTone.URGENT: {
                        'urgent_greeting': 'ACHTUNG - NOTFALL',
                        'immediate_action': 'Notfall erkannt - wird an Arzt eskaliert.',
                        'urgent_closing': 'Dringende medizinische Hilfe erforderlich!'
                    }
                }
            },
            # NEUE FACHARZT-RESPONSE-TEMPLATES
            ResponseType.SPECIALIST_REFERRAL: {
                'structure': [
                    'greeting',
                    'specialist_acknowledgment',
                    'referral_process',
                    'next_steps',
                    'closing'
                ],
                'tone_adjustments': {
                    ResponseTone.PROFESSIONAL: {
                        'greeting': 'Sehr geehrte/r {patient_name},',
                        'specialist_acknowledgment': 'Vielen Dank für Ihre Anfrage bezüglich eines Facharzt-Termins.',
                        'referral_process': 'Wir werden eine Überweisung zu einem geeigneten {specialist_type} veranlassen.',
                        'next_steps': 'Sie erhalten in den nächsten Tagen einen Termin bei dem entsprechenden Facharzt.',
                        'closing': 'Mit freundlichen Grüßen\nIhr Praxis-Team'
                    }
                }
            },
            # GENERAL RESPONSE TEMPLATE (für neue Intent-Typen)
            ResponseType.GENERAL_RESPONSE: {
                'structure': [
                    'greeting',
                    'acknowledgment',
                    'general_info',
                    'closing'
                ],
                'tone_adjustments': {
                    ResponseTone.PROFESSIONAL: {
                        'greeting': 'Sehr geehrte/r {patient_name},',
                        'acknowledgment': 'Vielen Dank für Ihre Nachricht.',
                        'general_info': 'Wir werden Ihre Anfrage bearbeiten und uns bald bei Ihnen melden.',
                        'closing': 'Mit freundlichen Grüßen\nIhr Praxis-Team'
                    },
                    ResponseTone.EMPATHETIC: {
                        'greeting': 'Liebe/r {patient_name},',
                        'acknowledgment': 'Ich verstehe Ihre Anfrage.',
                        'general_info': 'Wir kümmern uns darum und melden uns bei Ihnen.',
                        'closing': 'Herzliche Grüße\nIhr Praxis-Team'
                    }
                }
            },
            # HAUSARZT-PRAXIS-RESPONSE-TEMPLATE (NEU)
            ResponseType.HAUSARZT_PRAXIS_INQUIRY: {
                'structure': [
                    'greeting',
                    'hausarzt_acknowledgment',
                    'services_overview',
                    'appointment_suggestion',
                    'closing'
                ],
                'tone_adjustments': {
                    ResponseTone.PROFESSIONAL: {
                        'greeting': 'Sehr geehrte/r {patient_name},',
                        'hausarzt_acknowledgment': 'Vielen Dank für Ihre Anfrage bezüglich unserer Hausarzt-Praxis.',
                        'services_overview': 'Als Hausarztpraxis bieten wir umfassende medizinische Betreuung für alle Altersgruppen.',
                        'appointment_suggestion': 'Für eine persönliche Beratung oder Untersuchung vereinbaren Sie bitte einen Termin.',
                        'closing': 'Mit freundlichen Grüßen\nIhr Hausarzt-Team\nEli5 Hausarztpraxis'
                    },
                    ResponseTone.EMPATHETIC: {
                        'greeting': 'Liebe/r {patient_name},',
                        'hausarzt_acknowledgment': 'Ich freue mich über Ihr Interesse an unserer Hausarzt-Praxis.',
                        'services_overview': 'Wir kümmern uns um Ihre Gesundheit - von der Vorsorge bis zur Behandlung.',
                        'appointment_suggestion': 'Lassen Sie uns gemeinsam Ihre Gesundheit im Blick behalten.',
                        'closing': 'Herzliche Grüße\nIhr Hausarzt-Team\nEli5 Hausarztpraxis'
                    }
                }
            },
            # MEDIKAMENTEN-RESPONSE-TEMPLATES
            ResponseType.MEDICAL_ADVICE: {
                'structure': [
                    'greeting',
                    'medication_acknowledgment',
                    'medication_info',
                    'side_effects_warning',
                    'closing'
                ],
                'tone_adjustments': {
                    ResponseTone.PROFESSIONAL: {
                        'greeting': 'Sehr geehrte/r {patient_name},',
                        'medication_acknowledgment': 'Bezüglich Ihrer Medikamenten-Anfrage:',
                        'medication_info': 'Informationen zu {medication_name}: {medication_details}',
                        'side_effects_warning': 'Bitte beachten Sie mögliche Nebenwirkungen und Wechselwirkungen.',
                        'closing': 'Bei Fragen stehen wir gerne zur Verfügung.'
                    }
                }
            },
            # DOKUMENTEN-RESPONSE-TEMPLATES
            ResponseType.STATUS_INQUIRY: {
                'structure': [
                    'greeting',
                    'document_request_acknowledgment',
                    'processing_info',
                    'timeline',
                    'closing'
                ],
                'tone_adjustments': {
                    ResponseTone.PROFESSIONAL: {
                        'greeting': 'Sehr geehrte/r {patient_name},',
                        'document_request_acknowledgment': 'Vielen Dank für Ihre Anfrage nach {document_type}.',
                        'processing_info': 'Wir bearbeiten Ihre Anfrage und werden Ihnen die Unterlagen zusenden.',
                        'timeline': 'Sie erhalten die Dokumente innerhalb der nächsten 3-5 Werktage.',
                        'closing': 'Mit freundlichen Grüßen\nIhr Praxis-Team'
                    }
                }
            }
        }

    def _load_medical_knowledge(self):
        """Lädt medizinisches Wissensbasis"""
        self.medical_advice = {
            'symptoms': {
                'kopfschmerzen': {
                    'routine': 'Bleiben Sie hydriert und ruhen Sie sich aus.',
                    'urgent': 'Starke Kopfschmerzen erkannt - wird an Arzt eskaliert.'
                },
                'fieber': {
                    'routine': 'Überwachen Sie Ihre Temperatur und trinken Sie viel.',
                    'urgent': 'Hohes Fieber (>39°C) erfordert sofortige Behandlung.'
                }
            },
            'preparation': {
                'blood_test': 'Kommen Sie nüchtern (nicht essen ab Mitternacht).',
                'vaccination': 'Bringen Sie Ihren Impfpass mit.',
                'consultation': 'Bringen Sie alle relevanten Unterlagen mit.'
            }
        }

    def _load_personalization_rules(self):
        """Lädt Personalisierungs-Regeln"""
        self.personalization_rules = {
            'age_groups': {
                'child': {
                    'tone': ResponseTone.FRIENDLY,
                    'language': 'einfach',
                    'details': 'weniger technisch'
                },
                'adult': {
                    'tone': ResponseTone.PROFESSIONAL,
                    'language': 'standard',
                    'details': 'normal'
                },
                'senior': {
                    'tone': ResponseTone.EMPATHETIC,
                    'language': 'klar',
                    'details': 'mehr Erklärungen'
                }
            },
            'communication_styles': {
                'formal': {
                    'greeting': 'Sehr geehrte/r {patient_name},',
                    'closing': 'Mit freundlichen Grüßen'
                },
                'friendly': {
                    'greeting': 'Hallo {patient_name},',
                    'closing': 'Viele Grüße'
                },
                'direct': {
                    'greeting': '{patient_name},',
                    'closing': 'Beste Grüße'
                }
            }
        }

    def generate_response(self, context: ResponseContext) -> str:
        """
        Generiert eine personalisierte E-Mail-Antwort

        Args:
            context: Kontext für die Antwort-Generierung

        Returns:
            Vollständige E-Mail-Antwort
        """
        try:
            # Bestimme optimalen Antwort-Typ
            response_type = self._determine_response_type(context)

            # Passe Ton an Patienten-Profil an
            optimal_tone = self._determine_optimal_tone(context)

            # Generiere strukturierte Antwort
            response_parts = self._generate_response_parts(context, response_type, optimal_tone)

            # Kombiniere zu vollständiger Antwort
            full_response = self._assemble_response(response_parts, context)

            # Personalisierung anwenden
            personalized_response = self._apply_personalization(full_response, context)

            return personalized_response

        except Exception as e:
            logger.error(f"Antwort-Generierung fehlgeschlagen: {e}")
            raise e

    def _determine_response_type(self, context: ResponseContext) -> ResponseType:
        """Bestimmt den optimalen Antwort-Typ"""
        intent = context.intent_type

        print(f"DEBUG: Bestimme Response-Typ für Intent: {intent}")

        if intent == "emergency":
            print("DEBUG: Emergency Response")
            return ResponseType.EMERGENCY_RESPONSE
        elif intent in ["appointment", "appointment_inquiry"]:
            print("DEBUG: Appointment Response")
            # Prüfe ob bereits Termine vorhanden sind
            if context.calendar_info.get('has_appointments', False):
                print("DEBUG: Appointment Confirmation")
                return ResponseType.APPOINTMENT_CONFIRMATION
            else:
                print("DEBUG: Appointment Suggestion")
                return ResponseType.APPOINTMENT_SUGGESTION
        elif intent == "appointment_confirm":
            print("DEBUG: Appointment Confirm")
            return ResponseType.APPOINTMENT_CONFIRMATION
        elif intent == "appointment_cancel":
            print("DEBUG: Appointment Cancellation")
            return ResponseType.APPOINTMENT_CANCELLATION
        elif intent == "status_check":
            print("DEBUG: Status Inquiry")
            return ResponseType.STATUS_INQUIRY
        # Facharzt-Intents (NEU)
        elif intent.startswith("zahnarzt_") or intent.startswith("dermatologe_") or \
             intent.startswith("neurologe_") or intent.startswith("orthopaede_") or \
             intent.startswith("gynaekologe_") or intent.startswith("psychiater_") or \
             intent.startswith("kardiologe_") or intent.startswith("endokrinologe_"):
            print(f"DEBUG: Specialist Appointment: {intent}")
            return ResponseType.SPECIALIST_REFERRAL

        # Medikamenten-Intents (NEU)
        elif intent in ["prescription_request", "medication_refill", "medication_inquiry",
                       "side_effect_report", "medication_interaction_check"]:
            print(f"DEBUG: Medication Intent: {intent}")
            return ResponseType.MEDICAL_ADVICE

        # Dokumenten-Intents (NEU)
        elif intent in ["prescription_needed", "specialist_referral", "sick_leave_certificate",
                       "test_results_inquiry", "medical_records_request"]:
            print(f"DEBUG: Document Intent: {intent}")
            return ResponseType.STATUS_INQUIRY

        # Follow-up Intents (NEU)
        elif intent in ["follow_up_appointment", "treatment_update", "chronic_condition_management",
                       "preventive_care_inquiry"]:
            print(f"DEBUG: Follow-up Intent: {intent}")
            return ResponseType.APPOINTMENT_SUGGESTION

        # Hausarzt-Praxis-Intent (NEU)
        elif intent == "hausarzt_praxis_inquiry":
            print(f"DEBUG: Hausarzt-Praxis Intent: {intent}")
            return ResponseType.HAUSARZT_PRAXIS_INQUIRY

        # Administrative Intents (NEU)
        elif intent in ["billing_inquiry", "insurance_verification", "new_patient_registration"]:
            print(f"DEBUG: Administrative Intent: {intent}")
            return ResponseType.GENERAL_RESPONSE

        else:
            print(f"DEBUG: General Response for intent: {intent}")
            return ResponseType.GENERAL_RESPONSE

    def _determine_optimal_tone(self, context: ResponseContext) -> ResponseTone:
        """Bestimmt den optimalen Ton basierend auf Kontext"""
        patient = context.patient_info.get('profile') if context.patient_info else None

        # Basis-Ton basierend auf Dringlichkeit
        if context.urgency_level == "emergency":
            return ResponseTone.URGENT
        elif context.urgency_level == "urgent":
            return ResponseTone.PROFESSIONAL

        # Anpassung an Patienten-Profil
        age_tone = self.personalization_rules['age_groups'].get(patient.age_group, {}).get('tone', ResponseTone.PROFESSIONAL)
        if age_tone:
            return age_tone

        return ResponseTone.PROFESSIONAL

    def _generate_response_parts(self, context: ResponseContext, response_type: ResponseType, tone: ResponseTone) -> Dict[str, str]:
        """Generiert die einzelnen Teile der Antwort"""
        parts = {}

        try:
            template = self.response_templates.get(response_type)
            if template is None:
                print(f"DEBUG: Kein Template für {response_type}, verwende APPOINTMENT_SUGGESTION als Fallback")
                template = self.response_templates[ResponseType.APPOINTMENT_SUGGESTION]
            tone_adjustments = template.get('tone_adjustments', {}).get(tone, {})

            print(f"DEBUG: Template für {response_type}: {template}")
            print(f"DEBUG: Tone adjustments: {tone_adjustments}")

            for part_name in template.get('structure', []):
                print(f"DEBUG: Generiere Part: {part_name}")
                parts[part_name] = self._generate_part(part_name, context, tone_adjustments)
                print(f"DEBUG: Part {part_name} generiert: {parts[part_name][:100]}")

        except Exception as e:
            print(f"DEBUG: Fehler bei Response-Parts-Generierung: {e}")
            raise

        return parts

    def _generate_part(self, part_name: str, context: ResponseContext, tone_adjustments: Dict[str, str]) -> str:
        """Generiert einen einzelnen Antwort-Teil"""
        patient = context.patient_info.get('profile') if context.patient_info else None
        patient_name = patient.name if patient else "Patient/in"

        # Verwende Ton-Anpassungen falls verfügbar
        if part_name in tone_adjustments:
            content = tone_adjustments[part_name]
        else:
            content = self._get_default_part_content(part_name, context)

        # Personalisierung
        content = content.format(
            patient_name=patient_name,
            **context.calendar_info,
            **context.entities
        )

        return content

    def _get_default_part_content(self, part_name: str, context: ResponseContext) -> str:
        """Gibt Standard-Inhalte für Antwort-Teile"""
        defaults = {
            'greeting': 'Sehr geehrte/r {patient_name},',
            'acknowledgment': 'vielen Dank für Ihre Nachricht.',
            'appointment_suggestions': 'Hier sind die verfügbaren Termine:\n{appointment_list}',
            'instructions': 'Bitte antworten Sie mit der gewünschten Termin-Nummer.',
            'closing': 'Mit freundlichen Grüßen\nIhr Praxis-Team',
            'urgent_greeting': 'DRINGEND - NOTFALL',
            'immediate_action': 'Notfall erkannt - wird an Arzt eskaliert.',
            'contact_info': 'Praxis-Telefon: 0251-123456',
            'urgent_closing': 'Medizinische Notfallhilfe erforderlich!'
        }

        return defaults.get(part_name, f'[{part_name}]')

    def _assemble_response(self, parts: Dict[str, str], context: ResponseContext) -> str:
        """Setzt die Antwort-Teile zusammen"""
        response_lines = []

        for part_name in parts:
            content = parts[part_name]
            if content and content.strip():
                response_lines.append(content.strip())

        return '\n\n'.join(response_lines)

    def _apply_personalization(self, response: str, context: ResponseContext) -> str:
        """Wendet Personalisierung auf die Antwort an"""
        patient = context.patient_info.get('profile') if context.patient_info else None

        # Sprach-Anpassung
        if patient.language_preference != "de":
            response = self._translate_response(response, patient.language_preference)

        # Kommunikationsstil-Anpassung
        response = self._apply_communication_style(response, patient.communication_style)

        # Medizinische Historie einbeziehen
        if patient.medical_history:
            response = self._include_medical_context(response, patient.medical_history)

        # Gesprächs-Historie berücksichtigen
        if context.conversation_history:
            response = self._include_conversation_context(response, context.conversation_history)

        return response

    def _translate_response(self, response: str, target_language: str) -> str:
        """Übersetzt die Antwort (vereinfacht)"""
        # Vereinfachte Übersetzung - in echtem System würde hier eine professionelle Übersetzung stehen
        translations = {
            'de': response,  # Original ist Deutsch
            'en': response.replace('geehrte/r', 'dear').replace('vielen Dank', 'thank you')
        }

        return translations.get(target_language, response)

    def _apply_communication_style(self, response: str, style: str) -> str:
        """Passt Kommunikationsstil an"""
        style_rules = self.personalization_rules['communication_styles'].get(style, {})

        # Ersetze Begrüßung und Abschluss
        for key, replacement in style_rules.items():
            if key == 'greeting' and response.startswith('Sehr geehrte/r'):
                response = replacement + response[13:]  # Entferne alte Begrüßung
            elif key == 'closing' and 'Mit freundlichen Grüßen' in response:
                response = response.replace('Mit freundlichen Grüßen\nIhr Praxis-Team', replacement + '\nIhr Praxis-Team')

        return response

    def _include_medical_context(self, response: str, medical_history: List[str]) -> str:
        """Bezieht medizinische Historie ein"""
        if medical_history:
            context_line = f"\n\nBasierend auf Ihrer Krankengeschichte ({', '.join(medical_history[:2])}):"
            response += context_line

        return response

    def _include_conversation_context(self, response: str, conversation_history: List[Dict[str, Any]]) -> str:
        """Bezieht Gesprächs-Kontext ein"""
        if len(conversation_history) > 1:
            recent_topics = [msg.get('subject', '') for msg in conversation_history[-3:]]
            if recent_topics:
                context_line = f"\n\nBezüglich unserer vorherigen Korrespondenz ({', '.join(recent_topics)}):"
                response += context_line

        return response


    def create_response_context(self, nlu_result: Dict[str, Any], patient_email: str = "",
                              conversation_history: List[Dict[str, Any]] = None) -> ResponseContext:
        """Erstellt ResponseContext aus NLU-Ergebnis"""
        if conversation_history is None:
            conversation_history = []

        # Bestimme Patienten-Profil (vereinfacht - in echtem System aus Datenbank)
        # Erzeuge vereinfachtes temporäres Profil, kompatibel mit PatientManagementAgent
        patient_profile = PatientProfile(
            email=patient_email,
            name=self._extract_patient_name(nlu_result),
            communication_style="formal",
            age_group="adult"  # Standardwert
        )

        # Bestimme Dringlichkeitsstufe
        urgency_level = nlu_result.get('classification_data', {}).get('urgency_level', 'routine')

        return ResponseContext(
            intent_type=nlu_result.get('intent_type', 'unknown'),
            urgency_level=urgency_level,
            entities=nlu_result.get('classification_data', {}).get('entities', {}),
            patient_info={"profile": patient_profile},
            conversation_history=conversation_history,
            calendar_info={},  # Würde aus Kalender-System kommen
            tone=ResponseTone.PROFESSIONAL,
            response_type=ResponseType.GENERAL_RESPONSE
        )

    def _extract_patient_name(self, nlu_result: Dict[str, Any]) -> str:
        """Extrahiert Patienten-Namen aus NLU-Ergebnis"""
        try:
            # Versuche echte Namenserkennung
            from intelligent_name_extractor import IntelligentNameExtractor
            extractor = IntelligentNameExtractor()

            # Extrahiere aus verschiedenen Quellen
            email_body = nlu_result.get('email_body', '')
            email_subject = nlu_result.get('email_subject', '')
            sender_email = nlu_result.get('sender_email', '')

            # Einfache Namenserkennung aus E-Mail-Inhalt
            name_result = extractor.extract_name_from_email(email_body, sender_email)

            if name_result and name_result.full_name:
                return name_result.full_name

            # Fallback: Extrahiere Namen aus E-Mail-Adresse
            if '@' in sender_email:
                local_part = sender_email.split('@')[0]
                # Einfache Heuristik für Namen in E-Mail-Adressen
                if '.' in local_part:
                    parts = local_part.split('.')
                    if len(parts) >= 2:
                        return f"{parts[0].capitalize()} {parts[1].capitalize()}"

                return local_part.capitalize()

            # Letzter Fallback
            return "Patient/in"

        except Exception as e:
            logger.warning(f"Namenserkennung fehlgeschlagen: {e}")
            return "Patient/in"
