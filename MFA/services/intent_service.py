#!/usr/bin/env python3
"""
INTENT SERVICE
Legacy Intent-Service als Fallback für das Enterprise-System
"""

import logging
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class IntentResult:
    """Ergebnis der Intent-Klassifikation"""
    intent_type: str
    confidence: float
    entities: Dict[str, List[str]]
    action_required: str
    urgency_level: str

class IntentService:
    """Legacy Intent-Service als Fallback"""
    
    def __init__(self):
        self.intent_keywords = {
            "medication_inquiry": ["medikament", "medizin", "rezept", "verschreibung"],
            "emergency": ["notfall", "akut", "schwer verletzt", "bewusstlos", "atemnot"],
            "general_question": ["frage", "hilfe", "information", "beratung"]
        }
        
        self.action_mapping = {
            "medication_inquiry": "provide_medication_info",
            "emergency": "call_emergency_services",
            "general_question": "provide_general_info"
        }
    
    def classify_intent(self, subject: str, body: str, sender: str) -> IntentResult:
        """Klassifiziert Intent basierend auf E-Mail-Inhalt"""
        try:
            full_text = f"{subject} {body}".lower()
            
            # Finde den besten Intent
            best_intent = "general_question"
            best_confidence = 0.1
            
            for intent_type, keywords in self.intent_keywords.items():
                matches = sum(1 for keyword in keywords if keyword in full_text)
                if matches > 0:
                    confidence = min(0.9, 0.3 + (matches * 0.2))
                    if confidence > best_confidence:
                        best_intent = intent_type
                        best_confidence = confidence
            
            # Bestimme Dringlichkeit
            urgency_level = "routine"
            if best_intent == "emergency":
                urgency_level = "critical"
            elif any(word in full_text for word in ["dringend", "schnell", "sofort"]):
                urgency_level = "urgent"
            
            # Extrahiere einfache Entities
            entities = self._extract_simple_entities(full_text)
            
            return IntentResult(
                intent_type=best_intent,
                confidence=best_confidence,
                entities=entities,
                action_required=self.action_mapping.get(best_intent, "provide_general_info"),
                urgency_level=urgency_level
            )
                
        except Exception as e:
            logger.error(f"Fehler bei Intent-Klassifikation: {e}")
            return IntentResult(
                intent_type="general_question",
                confidence=0.1,
                entities={},
                action_required="provide_general_info",
                urgency_level="routine"
            )
    
    def _extract_simple_entities(self, text: str) -> Dict[str, List[str]]:
        """Extrahiert einfache Entities"""
        entities = {
            "date": [],
            "time": [],
            "symptom": [],
            "medication": []
        }
        
        # Einfache Datum-Erkennung
        date_keywords = ["montag", "dienstag", "mittwoch", "donnerstag", "freitag", "morgen", "heute", "nächste woche"]
        for keyword in date_keywords:
            if keyword in text:
                entities["date"].append(keyword)
        
        # Einfache Zeit-Erkennung
        time_keywords = ["morgens", "nachmittags", "abends", "8 uhr", "9 uhr", "10 uhr"]
        for keyword in time_keywords:
            if keyword in text:
                entities["time"].append(keyword)
        
        # Einfache Symptom-Erkennung
        symptom_keywords = ["schmerzen", "fieber", "husten", "kopfschmerzen", "bauchschmerzen"]
        for keyword in symptom_keywords:
            if keyword in text:
                entities["symptom"].append(keyword)
        
        # Einfache Medikamenten-Erkennung
        medication_keywords = ["ibuprofen", "paracetamol", "aspirin", "antibiotika"]
        for keyword in medication_keywords:
            if keyword in text:
                entities["medication"].append(keyword)
        
        return entities

    # Compatibility helper methods used elsewhere in the system
    def _sanitize_text(self, text: str) -> str:
        """Einfacher Text-Sanitizer"""
        try:
            return text.replace('\r', ' ').replace('\n', ' ').strip()
        except:
            return text

    def _fallback_classification(self, subject: str, body: str) -> IntentResult:
        """Einfacher Fallback, falls komplexere Klassifikation fehlt"""
        return self.classify_intent(subject, body, '')
