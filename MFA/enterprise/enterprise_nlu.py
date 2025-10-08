#!/usr/bin/env python3
"""
ENTERPRISE-LEVEL NLU (NATURAL LANGUAGE UNDERSTANDING) COMPONENT
Erweiterte Intent-Erkennung und Entity Recognition für medizinische E-Mails
"""

import re
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from dateutil import parser as date_parser
from dateutil.relativedelta import relativedelta

logger = logging.getLogger(__name__)

class EntityType(Enum):
    """Entity-Typen für NLU"""
    DATE = "date"
    TIME = "time"
    DURATION = "duration"
    NUMBER = "number"
    PERSON = "person"
    MEDICAL_CONDITION = "medical_condition"
    MEDICATION = "medication"
    SYMPTOM = "symptom"
    SPECIALIST = "specialist"
    URGENCY_LEVEL = "urgency_level"

class UrgencyLevel(Enum):
    """Dringlichkeitsstufen"""
    ROUTINE = "routine"
    URGENT = "urgent"
    EMERGENCY = "emergency"

class NLUResult:
    """Ergebnis der NLU-Analyse"""
    def __init__(self):
        self.intent_type: str = "unknown"
        self.confidence: float = 0.0
        self.entities: Dict[EntityType, List[str]] = {}
        self.urgency_level: UrgencyLevel = UrgencyLevel.ROUTINE
        self.requires_immediate_attention: bool = False
        self.action_required: Optional[str] = None
        self.context_info: Dict[str, Any] = {}

class EnterpriseNLU:
    """Enterprise-Level NLU für medizinische E-Mail-Verarbeitung"""

    def __init__(self):
        """Initialisiert das NLU-System"""
        self._load_medical_knowledge()
        self._load_time_patterns()
        self._load_urgency_indicators()

    def _load_medical_knowledge(self):
        """Lädt medizinisches Wissensbasis"""
        # Symptome und Bedingungen
        self.medical_conditions = {
            'schmerzen': ['kopfschmerzen', 'bauchschmerzen', 'rückenschmerzen', 'gelenkschmerzen', 'zahnschmerzen'],
            'infektionen': ['erkältung', 'grippe', 'husten', 'schnupfen', 'fieber'],
            'verdauung': ['durchfall', 'verstopfung', 'übelkeit', 'erbrechen'],
            'haut': ['ausschlag', 'ekzem', 'akne', 'wunde'],
            'psychisch': ['depression', 'angst', 'stress', 'schlafstörung']
        }

        # Medikamente
        self.medications = [
            'paracetamol', 'ibuprofen', 'aspirin', 'antibiotika', 'insulin',
            'blutdruckmedikament', 'cholesterolmedikament', 'antidepressiva'
        ]

        # Fachärzte
        self.specialists = {
            'zahnarzt': ['zahn', 'zähne', 'kiefer', 'kieferorthopäde'],
            'dermatologe': ['haut', 'ausschlag', 'ekzem'],
            'neurologe': ['kopf', 'migräne', 'schwindel', 'taubheitsgefühl'],
            'orthopäde': ['gelenk', 'knochen', 'rücken', 'arthritis'],
            'gynäkologe': ['frau', 'schwanger', 'menstruation', 'wechseljahr'],
            'psychiater': ['depression', 'angst', 'psychose', 'therapie'],
            'kardiologe': ['herz', 'blutdruck', 'cholesterol'],
            'endokrinologe': ['diabetes', 'schilddrüse', 'hormon']
        }

    def _load_time_patterns(self):
        """Lädt Zeitmuster für bessere Erkennung"""
        self.time_patterns = {
            'absolute_dates': [
                r'\b(\d{1,2})\.(\d{1,2})\.(\d{4})\b',  # DD.MM.YYYY
                r'\b(\d{4})-(\d{1,2})-(\d{1,2})\b',   # YYYY-MM-DD
                r'\b(\d{1,2})/(\d{1,2})/(\d{4})\b',   # MM/DD/YYYY
            ],
            'relative_dates': [
                r'\b(heute|morgen|übermorgen)\b',
                r'\b(nächste|kommende)\s+(woche|wochen|monat|monate|jahr|jahre)\b',
                r'\b(in)\s+(\d+)\s+(tag|tagen|wochen?|monat|monaten|jahr|jahren)\b',
            ],
            'weekdays': [
                r'\b(montag|dienstag|mittwoch|donnerstag|freitag|samstag|sonntag)\b',
            ],
            'times': [
                r'\b(\d{1,2}):(\d{2})\b',  # HH:MM
                r'\b(\d{1,2})\s*(uhr|am|pm)\b',  # 14 Uhr, 2 PM
            ],
            'time_preferences': [
                r'\b(vormittag|früh|am morgen)\b',
                r'\b(nachmittag|spät|am abend)\b',
                r'\b(mittag|mittags)\b',
            ]
        }

    def _load_urgency_indicators(self):
        """Lädt Dringlichkeits-Indikatoren"""
        self.urgency_keywords = {
            UrgencyLevel.EMERGENCY: [
                'notfall', 'akut', 'sofort', 'dringend', 'lebensbedrohlich',
                'schwer verletzt', 'bewusstlos', 'atemnot', 'herzinfarkt',
                'schlaganfall', 'starke blutung', 'vergiftung', 'anaphylaxie',
                'krampfanfall', 'ohnmacht', 'koma', 'tod'
            ],
            UrgencyLevel.URGENT: [
                'starke schmerzen', 'hohes fieber', 'erbrechen', 'durchfall stark',
                'schwindel', 'kurzatmigkeit', 'brustschmerz', 'bauchschmerz stark',
                'kopfschmerz migräne', 'gelenkschmerz', 'hautausschlag schlimm'
            ],
            UrgencyLevel.ROUTINE: [
                'schmerzen', 'fieber', 'husten', 'schnupfen', 'müdigkeit',
                'schlafstörung', 'stress', 'depression', 'angst'
            ]
        }

    def analyze_email(self, subject: str, body: str, sender_email: str = "") -> NLUResult:
        """
        Analysiert eine E-Mail mit Enterprise-Level NLU

        Args:
            subject: E-Mail-Betreff
            body: E-Mail-Text
            sender_email: Absender-E-Mail

        Returns:
            NLUResult mit umfassender Analyse
        """
        result = NLUResult()

        # Kombiniere Subject und Body für Analyse
        full_text = f"{subject} {body}".lower()

        try:
            # 1. Entity Recognition
            result.entities = self._extract_entities(full_text)

            # 2. Intent Recognition (verbessert)
            result.intent_type, result.confidence = self._classify_intent_enhanced(full_text, result.entities)

            # 3. Urgency Assessment
            result.urgency_level = self._assess_urgency(full_text)

            # 4. Action Requirements
            result.action_required = self._determine_action(result.intent_type, result.entities, result.urgency_level)

            # 5. Immediate Attention Flag
            result.requires_immediate_attention = self._requires_immediate_attention(
                result.urgency_level, result.entities
            )

            # 6. Context Information
            result.context_info = self._extract_context_info(full_text, result.entities)

        except Exception as e:
            logger.error(f"NLU-Analyse fehlgeschlagen: {e}")
            result.intent_type = "unknown"
            result.confidence = 0.1

        return result

    def _extract_entities(self, text: str) -> Dict[EntityType, List[str]]:
        """Extrahiert Entities aus dem Text"""
        entities = {entity_type: [] for entity_type in EntityType}

        # Datums-Erkennung
        entities[EntityType.DATE] = self._extract_dates(text)

        # Uhrzeit-Erkennung
        entities[EntityType.TIME] = self._extract_times(text)

        # Zahlen-Erkennung
        entities[EntityType.NUMBER] = self._extract_numbers(text)

        # Medizinische Bedingungen
        entities[EntityType.MEDICAL_CONDITION] = self._extract_medical_conditions(text)

        # Medikamente
        entities[EntityType.MEDICATION] = self._extract_medications(text)

        # Symptome
        entities[EntityType.SYMPTOM] = self._extract_symptoms(text)

        # Fachärzte
        entities[EntityType.SPECIALIST] = self._extract_specialists(text)

        return entities

    def _extract_dates(self, text: str) -> List[str]:
        """Extrahiert Datumsangaben"""
        dates = []

        # Absolute Datumsangaben
        for pattern in self.time_patterns['absolute_dates']:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if len(match) == 3:
                    day, month, year = match
                    dates.append(f"{day.zfill(2)}.{month.zfill(2)}.{year}")

        # Relative Datumsangaben
        for pattern in self.time_patterns['relative_dates']:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, str):
                    dates.append(match.lower())
                else:
                    # Handle tuple matches from regex groups
                    dates.append(match[0].lower() if match else "")

        # Wochentage
        for pattern in self.time_patterns['weekdays']:
            matches = re.findall(pattern, text, re.IGNORECASE)
            dates.extend([m.lower() for m in matches if isinstance(m, str)])

        return list(set(dates))

    def _extract_times(self, text: str) -> List[str]:
        """Extrahiert Uhrzeitangaben"""
        times = []

        # Uhrzeit-Patterns
        for pattern in self.time_patterns['times']:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if len(match) == 2:
                    hour, minute = match
                    times.append(f"{hour.zfill(2)}:{minute.zfill(2)}")
                elif isinstance(match, str):
                    # Handle string matches
                    times.append(match.lower())

        # Zeitpräferenzen
        for pattern in self.time_patterns['time_preferences']:
            matches = re.findall(pattern, text, re.IGNORECASE)
            times.extend([m.lower() for m in matches if isinstance(m, str)])

        return list(set(times))

    def _extract_numbers(self, text: str) -> List[str]:
        """Extrahiert Zahlen"""
        numbers = re.findall(r'\b\d+\b', text)
        return list(set(numbers))

    def _extract_medical_conditions(self, text: str) -> List[str]:
        """Extrahiert medizinische Bedingungen"""
        conditions = []
        for category, keywords in self.medical_conditions.items():
            for keyword in keywords:
                if keyword in text:
                    conditions.append(keyword)
        return list(set(conditions))

    def _extract_medications(self, text: str) -> List[str]:
        """Extrahiert Medikamenten-Erwähnungen"""
        medications = []
        for medication in self.medications:
            if medication in text:
                medications.append(medication)
        return list(set(medications))

    def _extract_symptoms(self, text: str) -> List[str]:
        """Extrahiert Symptom-Erwähnungen"""
        symptoms = []
        for category, keywords in self.medical_conditions.items():
            for keyword in keywords:
                if keyword in text:
                    symptoms.append(keyword)
        return list(set(symptoms))

    def _extract_specialists(self, text: str) -> List[str]:
        """Extrahiert Facharzt-Erwähnungen"""
        specialists = []
        for specialist, keywords in self.specialists.items():
            for keyword in keywords:
                if keyword in text:
                    specialists.append(specialist)
                    break
        return list(set(specialists))

    def _classify_intent_enhanced(self, text: str, entities: Dict[EntityType, List[str]]) -> Tuple[str, float]:
        """
        Erweiterte Intent-Klassifikation mit Entity-Analyse
        Args:
            text: E-Mail-Text
            entities: Erkannte Entities
        Returns:
            Tuple von (intent_type, confidence)
        """
        text_lower = text.lower()

        # Notfall-Intent (höchste Priorität)
        if self._is_emergency_intent(text_lower):
            return "emergency", 0.95

        # Termin-Bestätigung (hohe Priorität)
        if self._is_appointment_confirm_intent(text_lower, entities):
            return "appointment_confirm", 0.9

        # Termin-Absage (hohe Priorität)
        if self._is_appointment_cancel_intent(text_lower, entities):
            return "appointment_cancel", 0.9

        # Facharzt-Intent (hohe Priorität)
        specialist_intent = self._detect_specialist_intent(text_lower, entities)
        if specialist_intent:
            return specialist_intent, 0.9

        # Medikamenten-Intent (höhere Priorität)
        medication_intent = self._classify_medication_intents(text_lower, entities)
        if medication_intent:
            return medication_intent, 0.9

        # Dokumenten-Intent
        document_intent = self._classify_document_intents(text_lower, entities)
        if document_intent:
            return document_intent, 0.8

        # Follow-up Intent
        followup_intent = self._classify_followup_intents(text_lower, entities)
        if followup_intent:
            return followup_intent, 0.8

        # Hausarzt-Praxis-Intent (spezifisch prüfen - VOR sick_leave_certificate)
        hausarzt_keywords = [
            'hausarzt', 'allgemeinarzt', 'praxis', 'arzt', 'untersuchung',
            'blutabnahme', 'impfung', 'vorsorge', 'check-up', 'gesundheitscheck',
            'allgemeine untersuchung', 'hausarzt termin', 'arzttermin'
        ]
        if any(keyword in text_lower for keyword in hausarzt_keywords):
            return "hausarzt_praxis_inquiry", 0.9

        # Administrative Intents (andere - NACH Hausarzt-Prüfung)
        admin_intent = self._classify_administrative_intents(text_lower, entities)
        if admin_intent:
            return admin_intent, 0.8

        # Generische Termin-Intent (NUR wenn nichts Spezifischeres passt)
        if self._is_appointment_intent(text_lower, entities):
            return "appointment", 0.85

        # Basis-Intent-Klassifikation
        return self._basic_intent_classification(text_lower)

    def _is_emergency_intent(self, text: str) -> bool:
        """Prüft auf Notfall-Intent"""
        emergency_keywords = [
            'notfall', 'akut', 'schwer verletzt', 'bewusstlos', 'atemnot',
            'herzinfarkt', 'schlaganfall', 'starke blutung', 'vergiftung',
            'sofort hilfe', 'lebensgefahr'
        ]
        return any(keyword in text for keyword in emergency_keywords)

    def _is_appointment_intent(self, text: str, entities: Dict[EntityType, List[str]]) -> bool:
        """Prüft auf generische Termin-Anfrage (NICHT Bestätigung/Absage)"""
        # Spezifische Keywords für generische Terminanfragen
        generic_appointment_keywords = [
            'termin vereinbaren', 'appointment machen', 'besuch termin',
            'wann kann ich', 'hätte gerne einen termin', 'brauche einen termin',
            'termin anmelden', 'termin buchen', 'termin planen',
            'termin möchten', 'termin brauchen', 'termin suche'
        ]

        # Prüfe, ob es sich um eine generische Anfrage handelt
        has_generic_keywords = any(keyword in text for keyword in generic_appointment_keywords)

        # Prüfe NICHT auf Bestätigungs-/Absage-Keywords
        confirmation_keywords = ['bestätigen', 'zusagen', 'passt mir', 'nehme ich', 'ok', 'ja', 'einverstanden']
        cancellation_keywords = ['absagen', 'stornieren', 'absage', 'stornierung', 'nicht kommen', 'kann nicht']

        has_confirmation = any(keyword in text for keyword in confirmation_keywords)
        has_cancellation = any(keyword in text for keyword in cancellation_keywords)

        # Nur als generischer Termin-Intent klassifizieren, wenn:
        # 1. Generische Keywords vorhanden UND
        # 2. KEINE Bestätigungs-/Absage-Keywords vorhanden
        return has_generic_keywords and not has_confirmation and not has_cancellation

    def _is_appointment_confirm_intent(self, text: str, entities: Dict[EntityType, List[str]]) -> bool:
        """Prüft auf Termin-Bestätigungs-Intent"""
        confirmation_keywords = ['bestätigen', 'zusagen', 'passt mir', 'nehme ich', 'ok', 'ja', 'einverstanden', 'buchen']
        has_appointment_context = any(keyword in text for keyword in ['termin', 'appointment'])
        return any(keyword in text for keyword in confirmation_keywords) and has_appointment_context

    def _is_appointment_cancel_intent(self, text: str, entities: Dict[EntityType, List[str]]) -> bool:
        """Prüft auf Termin-Absage-Intent"""
        cancellation_keywords = ['absagen', 'stornieren', 'absage', 'stornierung', 'nicht kommen', 'kann nicht', 'muss absagen']
        has_appointment_context = any(keyword in text for keyword in ['termin', 'appointment'])
        return any(keyword in text for keyword in cancellation_keywords) and has_appointment_context

    def _detect_specialist_intent(self, text: str, entities: Dict[EntityType, List[str]]) -> Optional[str]:
        """Erkennt spezifische Facharzt-Intents"""
        # Prüfe auf spezifische Facharzt-Kombinationen
        specialist_entities = entities.get(EntityType.SPECIALIST, [])

        # Zahnarzt-spezifische Keywords
        zahnarzt_keywords = ['zahn', 'zähne', 'kiefer', 'kieferorthopäde', 'zahnschmerzen', 'füllung']
        if any(keyword in text for keyword in zahnarzt_keywords):
            return "zahnarzt_appointment"

        # Dermatologe-spezifische Keywords
        dermatologe_keywords = ['haut', 'ausschlag', 'ekzem', 'akne', 'wunde', 'pickel']
        if any(keyword in text for keyword in dermatologe_keywords):
            return "dermatologe_appointment"

        # Neurologe-spezifische Keywords
        neurologe_keywords = ['kopf', 'migräne', 'schwindel', 'taubheitsgefühl', 'kopfschmerzen']
        if any(keyword in text for keyword in neurologe_keywords):
            return "neurologe_appointment"

        # Orthopäde-spezifische Keywords
        orthopaede_keywords = ['gelenk', 'knochen', 'rücken', 'arthritis', 'bruch']
        if any(keyword in text for keyword in orthopaede_keywords):
            return "orthopaede_appointment"

        # Gynäkologe-spezifische Keywords
        gynaekologe_keywords = ['frau', 'schwanger', 'menstruation', 'wechseljahr', 'gynäko']
        if any(keyword in text for keyword in gynaekologe_keywords):
            return "gynaekologe_appointment"

        # Psychiater-spezifische Keywords
        psychiater_keywords = ['depression', 'angst', 'psychose', 'therapie', 'psychisch']
        if any(keyword in text for keyword in psychiater_keywords):
            return "psychiater_appointment"

        # Kardiologe-spezifische Keywords
        kardiologe_keywords = ['herz', 'blutdruck', 'cholesterol', 'herzschmerz']
        if any(keyword in text for keyword in kardiologe_keywords):
            return "kardiologe_appointment"

        # Endokrinologe-spezifische Keywords
        endokrinologe_keywords = ['diabetes', 'schilddrüse', 'hormon', 'zucker']
        if any(keyword in text for keyword in endokrinologe_keywords):
            return "endokrinologe_appointment"

        return None

    def _classify_medication_intents(self, text: str, entities: Dict[EntityType, List[str]]) -> Optional[str]:
        """Klassifiziert Medikamenten-bezogene Intents"""
        medication_entities = entities.get(EntityType.MEDICATION, [])

        # Rezept-Anfrage
        prescription_keywords = ['rezept', 'verschreibung', 'neues medikament', 'brauche rezept']
        if any(keyword in text for keyword in prescription_keywords):
            return "prescription_request"

        # Medikamenten-Nachfüllung
        refill_keywords = ['nachfüllen', 'rezept verlängern', 'medikament nachbestellen', 'mehr', 'auffüllen', 'nachbestellen', 'verlängern']
        if any(keyword in text for keyword in refill_keywords):
            return "medication_refill"

        # Nebenwirkungen melden
        side_effect_keywords = ['nebenwirkung', 'unverträglichkeit', 'vertrage nicht', 'schlecht']
        if any(keyword in text for keyword in side_effect_keywords):
            return "side_effect_report"

        # Wechselwirkungen prüfen
        interaction_keywords = ['wechselwirkung', 'verträgt sich mit', 'kombinieren', 'zusammen']
        if any(keyword in text for keyword in interaction_keywords) and len(medication_entities) > 1:
            return "medication_interaction_check"

        # Allgemeine Medikamenten-Frage
        if medication_entities:
            return "medication_inquiry"

        return None

    def _classify_document_intents(self, text: str, entities: Dict[EntityType, List[str]]) -> Optional[str]:
        """Klassifiziert Dokumenten-bezogene Intents"""
        # Rezept-Anfrage
        prescription_keywords = ['rezept benötigt', 'medikamentenrezept', 'arzneimittelverschreibung']
        if any(keyword in text for keyword in prescription_keywords):
            return "prescription_needed"

        # Facharzt-Überweisung
        referral_keywords = ['überweisung', 'facharztüberweisung', 'weisung zum', 'empfehlung']
        if any(keyword in text for keyword in referral_keywords):
            return "specialist_referral"

        # Krankschreibung
        sick_leave_keywords = ['krankschreibung', 'arbeitsunfähigkeit', 'gelber schein', 'au']
        if any(keyword in text for keyword in sick_leave_keywords):
            # Nur wenn es NICHT um Termine oder allgemeine Arztbesuche geht
            if not any(keyword in text for keyword in ['termin', 'appointment', 'vereinbaren', 'anmelden', 'besuch']):
                return "sick_leave_certificate"

        # Befunde/Laborergebnisse
        test_result_keywords = ['befund', 'untersuchungsergebnis', 'laborwerte', 'ergebnis']
        if any(keyword in text for keyword in test_result_keywords):
            return "test_results_inquiry"

        return None

    def _classify_followup_intents(self, text: str, entities: Dict[EntityType, List[str]]) -> Optional[str]:
        """Klassifiziert Follow-up und Nachsorge-Intents"""
        # Follow-up Termin
        followup_keywords = ['nachuntersuchung', 'kontrolle', 'wieder vorstellen', 'nachsorge']
        if any(keyword in text for keyword in followup_keywords):
            return "follow_up_appointment"

        # Behandlungsupdate
        treatment_keywords = ['behandlung', 'therapie', 'fortschritt', 'verbesserung']
        if any(keyword in text for keyword in treatment_keywords):
            return "treatment_update"

        # Chronische Erkrankungen
        chronic_keywords = ['chronisch', 'dauerhaft', 'langfristig', 'management']
        if any(keyword in text for keyword in chronic_keywords):
            return "chronic_condition_management"

        # Vorsorge
        preventive_keywords = ['vorsorge', 'prävention', 'screening']
        if any(keyword in text for keyword in preventive_keywords):
            # Nur wenn es NICHT um eine allgemeine Hausarzt-Untersuchung geht
            if not any(keyword in text for keyword in ['hausarzt', 'allgemeinarzt', 'praxis']):
                return "preventive_care_inquiry"

        return None

    def _classify_administrative_intents(self, text: str, entities: Dict[EntityType, List[str]]) -> Optional[str]:
        """Klassifiziert administrative Intents"""
        # Abrechnung
        billing_keywords = ['rechnung', 'kosten', 'bezahlung', 'abrechnung']
        if any(keyword in text for keyword in billing_keywords):
            return "billing_inquiry"

        # Versicherung
        insurance_keywords = ['versicherung', 'karte', 'chipkarte', 'kostenübernahme']
        if any(keyword in text for keyword in insurance_keywords):
            return "insurance_verification"

        # Krankenakte
        records_keywords = ['akte', 'unterlagen', 'historie', 'vorgeschichte']
        if any(keyword in text for keyword in records_keywords):
            return "medical_records_request"

        # Neue Patienten-Anmeldung
        registration_keywords = ['anmelden', 'registrieren', 'neu hier', 'erstmals']
        if any(keyword in text for keyword in registration_keywords):
            return "new_patient_registration"

        # Hausarzt-Praxis-spezifische Anfragen
        hausarzt_keywords = [
            'hausarzt', 'allgemeinarzt', 'praxis', 'arzt', 'untersuchung',
            'blutabnahme', 'impfung', 'vorsorge', 'check-up', 'gesundheitscheck',
            'allgemeine untersuchung', 'hausarzt termin', 'arzttermin'
        ]
        if any(keyword in text for keyword in hausarzt_keywords):
            return "hausarzt_praxis_inquiry"

        return None

    def _basic_intent_classification(self, text: str) -> Tuple[str, float]:
        """Basis-Intent-Klassifikation (von existierendem System klonen)"""
        # Notfall-Keywords (höchste Priorität)
        emergency_keywords = [
            'notfall', 'akut', 'schwer verletzt', 'bewusstlos', 'atemnot',
            'herzinfarkt', 'schlaganfall', 'starke blutung', 'vergiftung'
        ]

        if any(keyword in text for keyword in emergency_keywords):
            return "emergency", 0.95

        # Termin-Keywords
        appointment_keywords = [
            'termin', 'appointment', 'vereinbaren', 'anmelden', 'besuch',
            'sprechstunde', 'beratung', 'untersuchung', 'check-up'
        ]

        if any(keyword in text for keyword in appointment_keywords):
            return "appointment", 0.85

        # Bestätigungs-Keywords
        confirm_keywords = [
            'bestätigen', 'zusagen', 'passt mir', 'nehme ich', 'ok',
            'termin 1', 'termin 2', 'termin 3', 'ja', 'einverstanden'
        ]

        if any(keyword in text for keyword in confirm_keywords):
            return "appointment_confirm", 0.8

        # Absage-Keywords
        cancel_keywords = [
            'absagen', 'stornieren', 'absage', 'stornierung', 'nicht kommen',
            'kann nicht', 'muss absagen', 'terminabsage'
        ]

        if any(keyword in text for keyword in cancel_keywords):
            return "appointment_cancel", 0.85

        # Status-Keywords
        status_keywords = [
            'meine termine', 'mein termin', 'termin status', 'wann habe ich termin'
        ]

        if any(keyword in text for keyword in status_keywords):
            return "status_check", 0.8

        # Medizinische Keywords
        medical_keywords = [
            'schmerzen', 'fieber', 'erkältung', 'medikament', 'behandlung',
            'untersuchung', 'therapie', 'arzt', 'medizin', 'gesundheit'
        ]

        if any(keyword in text for keyword in medical_keywords):
            return "medical_question", 0.75

        return "general_inquiry", 0.5

    def _assess_urgency(self, text: str) -> UrgencyLevel:
        """Bewertet die Dringlichkeit"""
        for level, keywords in self.urgency_keywords.items():
            if any(keyword in text for keyword in keywords):
                return level
        return UrgencyLevel.ROUTINE

    def _determine_action(self, intent_type: str, entities: Dict[EntityType, List[str]],
                         urgency_level: UrgencyLevel) -> Optional[str]:
        """Bestimmt erforderliche Aktion"""
        if urgency_level == UrgencyLevel.EMERGENCY:
            return "call_emergency_services"

        if intent_type == "appointment":
            if entities[EntityType.DATE] or entities[EntityType.TIME]:
                return "create_appointment_request"
            else:
                return "request_appointment_details"

        if intent_type == "appointment_confirm":
            return "confirm_appointment"

        if intent_type == "appointment_cancel":
            return "cancel_appointment"

        if intent_type == "status_check":
            return "get_appointment_status"

        if intent_type == "specialist_referral":
            return "refer_to_specialist"

        if intent_type == "medication_inquiry":
            return "provide_medication_info"

        return None

    def _requires_immediate_attention(self, urgency_level: UrgencyLevel,
                                    entities: Dict[EntityType, List[str]]) -> bool:
        """Prüft, ob sofortige Aufmerksamkeit erforderlich ist"""
        if urgency_level == UrgencyLevel.EMERGENCY:
            return True

        # Starke Symptome
        strong_symptoms = ['starke schmerzen', 'hohes fieber', 'atemnot', 'brustschmerz']
        if any(symptom in entities[EntityType.SYMPTOM] for symptom in strong_symptoms):
            return True

        return False

    def _extract_context_info(self, text: str, entities: Dict[EntityType, List[str]]) -> Dict[str, Any]:
        """Extrahiert Kontext-Informationen"""
        context = {}

        # Patienten-Informationen (falls verfügbar)
        context['has_patient_history'] = False  # Würde aus Datenbank kommen

        # Gesprächskontext
        context['is_follow_up'] = 're:' in text or 'aw:' in text

        # Kommunikationspräferenzen
        context['prefers_phone'] = 'telefon' in text or 'anrufen' in text

        # Zeitdruck-Indikatoren
        context['time_pressure'] = any(word in text for word in ['sofort', 'dringend', 'schnell'])

        return context
