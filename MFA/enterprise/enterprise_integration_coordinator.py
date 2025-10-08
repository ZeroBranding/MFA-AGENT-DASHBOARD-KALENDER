#!/usr/bin/env python3
"""
ENTERPRISE INTEGRATION COORDINATOR
Zentrale Koordination aller Enterprise-Komponenten
Integriert intelligente Namenserkennung, Chat-Historie, Self-Learning und Fehlerbehandlung
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import json

# Import aller Enterprise-Komponenten
from utils.intelligent_name_extractor import IntelligentNameExtractor, ExtractedName, NameConfidence
from enterprise.enterprise_error_handling import EnterpriseErrorHandler
from core.advanced_chat_history import AdvancedChatHistory, ConversationMessage, MessageType, ContextType
from utils.self_learning_system import SelfLearningSystem, LearningExample, LearningType, LearningSource
from enterprise.enterprise_nlu import EnterpriseNLU, NLUResult
from enterprise.enterprise_response_generator import EnterpriseResponseGenerator, ResponseContext, ResponseType
from agents.patient_management_agent import PatientManagementAgent, PatientProfile

logger = logging.getLogger(__name__)

@dataclass
class EnterpriseEmailContext:
    """Erweiterter Kontext für E-Mail-Verarbeitung"""
    email_data: Dict[str, Any]
    nlu_result: NLUResult
    extracted_name: Optional[ExtractedName]
    conversation_history: List[ConversationMessage]
    patient_profile: Optional[PatientProfile]
    context_summary: Dict[str, Any]
    learning_opportunities: List[LearningExample]
    error_context: Optional[str] = None

class EnterpriseIntegrationCoordinator:
    """
    Zentrale Koordination aller Enterprise-Komponenten
    Orchestriert intelligente Namenserkennung, Chat-Historie, Self-Learning und Fehlerbehandlung
    """
    
    def __init__(self):
        """Initialisiert den Enterprise Integration Coordinator"""
        self.name_extractor = IntelligentNameExtractor()
        self.chat_history = AdvancedChatHistory()
        self.learning_system = SelfLearningSystem()
        self.error_handler = EnterpriseErrorHandler()
        self.enterprise_nlu = EnterpriseNLU()
        self.response_generator = EnterpriseResponseGenerator()
        self.patient_manager = PatientManagementAgent()
        
        logger.info("Enterprise Integration Coordinator initialisiert")
    
    async def process_email_enterprise(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verarbeitet eine E-Mail mit allen Enterprise-Features
        
        Args:
            email_data: E-Mail-Daten (subject, body, sender, etc.)
            
        Returns:
            Verarbeitungsergebnis mit Antwort und Metadaten
        """
        try:
            # 1. Erstelle Enterprise-Kontext
            context = await self._create_enterprise_context(email_data)
            
            # 2. Intelligente Namenserkennung
            await self._process_name_extraction(context)
            
            # 3. Chat-Historie laden und analysieren
            await self._process_chat_history(context)
            
            # 4. NLU-Analyse mit Kontext
            await self._process_nlu_analysis(context)
            
            # 5. Patientenprofil aktualisieren
            await self._process_patient_profile(context)
            
            # 6. Response-Generierung mit Kontext
            response = await self._process_response_generation(context)
            
            # 7. Self-Learning-Integration
            await self._process_learning_integration(context, response)
            
            # 8. Chat-Historie aktualisieren
            await self._update_chat_history(context, response)
            
            return {
                "success": True,
                "response": response,
                "context": {
                    "extracted_name": asdict(context.extracted_name) if context.extracted_name else None,
                    "conversation_count": len(context.conversation_history),
                    "patient_known": context.patient_profile is not None,
                    "intent_confidence": context.nlu_result.confidence,
                    "learning_examples": len(context.learning_opportunities)
                },
                "metadata": {
                    "processing_time": datetime.now().isoformat(),
                    "enterprise_features_used": [
                        "intelligent_name_extraction",
                        "chat_history_analysis",
                        "self_learning",
                        "error_handling",
                        "context_aware_responses"
                    ]
                }
            }
            
        except Exception as e:
            logger.error(f"Enterprise-Verarbeitung fehlgeschlagen: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _create_enterprise_context(self, email_data: Dict[str, Any]) -> EnterpriseEmailContext:
        """Erstellt einen erweiterten Enterprise-Kontext"""
        return EnterpriseEmailContext(
            email_data=email_data,
            nlu_result=None,
            extracted_name=None,
            conversation_history=[],
            patient_profile=None,
            context_summary={},
            learning_opportunities=[]
        )
    
    async def _process_name_extraction(self, context: EnterpriseEmailContext):
        """Verarbeitet intelligente Namenserkennung"""
        try:
            email_content = f"{context.email_data.get('subject', '')} {context.email_data.get('body', '')}"
            sender_email = context.email_data.get('sender', '')
            
            # Lade Chat-Historie für Kontext
            previous_context = self.chat_history.get_conversation_history(sender_email, limit=5)
            
            # Extrahiere Namen
            extracted_name = self.name_extractor.extract_name_from_email(
                email_content=email_content,
                sender_email=sender_email,
                subject=context.email_data.get('subject', ''),
                previous_context=[asdict(msg) for msg in previous_context]
            )
            
            context.extracted_name = extracted_name
            
            if extracted_name:
                logger.info(f"Name extrahiert: {extracted_name.full_name} (Vertrauen: {extracted_name.confidence.value})")
            
        except Exception as e:
            logger.error(f"Name-Extraktion fehlgeschlagen: {e}")
    
    async def _process_chat_history(self, context: EnterpriseEmailContext):
        """Verarbeitet Chat-Historie und Kontextanalyse"""
        try:
            sender_email = context.email_data.get('sender', '')
            
            # Lade Konversationshistorie
            context.conversation_history = self.chat_history.get_conversation_history(sender_email, limit=10)
            
            # Erstelle Kontext-Zusammenfassung
            context.context_summary = self.chat_history.get_contextual_summary(sender_email)
            
            # Analysiere Konversationskontext
            email_content = f"{context.email_data.get('subject', '')} {context.email_data.get('body', '')}"
            context_type = self.chat_history.analyze_conversation_context(email_content, sender_email)
            
            logger.info(f"Chat-Historie geladen: {len(context.conversation_history)} Nachrichten")
            
        except Exception as e:
            logger.error(f"Chat-Historie-Verarbeitung fehlgeschlagen: {e}")
    
    async def _process_nlu_analysis(self, context: EnterpriseEmailContext):
        """Verarbeitet NLU-Analyse mit Kontext"""
        try:
            # Führe NLU-Analyse durch
            nlu_result = self.enterprise_nlu.analyze_email(
                subject=context.email_data.get('subject', ''),
                body=context.email_data.get('body', ''),
                sender_email=context.email_data.get('sender', '')
            )
            
            context.nlu_result = nlu_result
            
            # Erstelle Lernbeispiel für Self-Learning
            learning_example = LearningExample(
                example_id=f"nlu_{int(datetime.now().timestamp())}",
                learning_type=LearningType.INTENT_CLASSIFICATION,
                input_text=f"{context.email_data.get('subject', '')} {context.email_data.get('body', '')}",
                expected_output=nlu_result.intent_type,
                actual_output=nlu_result.intent_type,  # Wird später durch Feedback aktualisiert
                confidence=nlu_result.confidence,
                source=LearningSource.SUCCESSFUL_INTERACTION,
                timestamp=datetime.now(),
                context={"sender": context.email_data.get('sender', '')}
            )
            
            context.learning_opportunities.append(learning_example)
            
            logger.info(f"NLU-Analyse abgeschlossen: {nlu_result.intent_type} (Vertrauen: {nlu_result.confidence:.2f})")
            
        except Exception as e:
            logger.error(f"NLU-Analyse fehlgeschlagen: {e}")
    
    async def _process_patient_profile(self, context: EnterpriseEmailContext):
        """Verarbeitet und aktualisiert Patientenprofil"""
        try:
            sender_email = context.email_data.get('sender', '')
            
            # Hole bestehendes Profil
            patient_profile = self.patient_manager.get_profile_by_email(sender_email)
            
            # Aktualisiere mit extrahiertem Namen
            if context.extracted_name and context.extracted_name.full_name:
                if patient_profile:
                    # Aktualisiere bestehendes Profil
                    patient_profile.name = context.extracted_name.full_name
                    patient_profile.updated_at = datetime.now()
                    self.patient_manager.create_or_update_profile(sender_email, {"name": context.extracted_name.full_name, "email": sender_email})
                else:
                    # Erstelle neues Profil
                    profile_data = {
                        "name": context.extracted_name.full_name,
                        "email": sender_email,
                        "last_contact": datetime.now(),
                        "communication_style": "formal"  # Default
                    }
                    patient_profile = self.patient_manager.create_or_update_profile(sender_email, profile_data)
            
            context.patient_profile = patient_profile
            
            if patient_profile:
                logger.info(f"Patientenprofil aktualisiert: {patient_profile.name}")
            
        except Exception as e:
            logger.error(f"Patientenprofil-Verarbeitung fehlgeschlagen: {e}")
    
    async def _process_response_generation(self, context: EnterpriseEmailContext) -> str:
        """Verarbeitet Response-Generierung mit Kontext"""
        try:
            # Erstelle Response-Kontext
            response_context = ResponseContext(
                subject=context.email_data.get('subject', ''),
                body=context.email_data.get('body', ''),
                sender_email=context.email_data.get('sender', ''),
                intent_type=context.nlu_result.intent_type if context.nlu_result else "unknown",
                confidence=context.nlu_result.confidence if context.nlu_result else 0.0,
                urgency_level=context.nlu_result.urgency_level if context.nlu_result else "routine",
                entities=context.nlu_result.entities if context.nlu_result else {},
                context_info=context.nlu_result.context_info if context.nlu_result else {},
                calendar_info={},
                patient_info={
                    "name": context.extracted_name.full_name if context.extracted_name else "",
                    "email": context.email_data.get('sender', ''),
                    "profile": context.patient_profile
                }
            )
            
            # Generiere Response
            response = self.response_generator.generate_response(response_context)
            
            # Erstelle Lernbeispiel für Response-Qualität
            learning_example = LearningExample(
                example_id=f"response_{int(datetime.now().timestamp())}",
                learning_type=LearningType.RESPONSE_GENERATION,
                input_text=f"{context.email_data.get('subject', '')} {context.email_data.get('body', '')}",
                expected_output=response,
                actual_output=response,
                confidence=0.8,  # Wird durch Feedback aktualisiert
                source=LearningSource.SUCCESSFUL_INTERACTION,
                timestamp=datetime.now(),
                context={"intent": context.nlu_result.intent_type if context.nlu_result else "unknown"}
            )
            
            context.learning_opportunities.append(learning_example)
            
            logger.info("Response generiert mit Enterprise-Kontext")
            return response
            
        except Exception as e:
            logger.error(f"Response-Generierung fehlgeschlagen: {e}")
            raise e
    
    async def _process_learning_integration(self, context: EnterpriseEmailContext, response: str):
        """Verarbeitet Self-Learning-Integration"""
        try:
            # Füge alle Lernbeispiele hinzu
            for learning_example in context.learning_opportunities:
                self.learning_system.add_learning_example(learning_example)
            
            # Speichere Modelle
            self.learning_system.save_models()
            
            logger.info(f"Self-Learning: {len(context.learning_opportunities)} Beispiele verarbeitet")
            
        except Exception as e:
            logger.error(f"Learning-Integration fehlgeschlagen: {e}")
    
    async def _update_chat_history(self, context: EnterpriseEmailContext, response: str):
        """Aktualisiert Chat-Historie mit neuer Nachricht"""
        try:
            # Erstelle Thread-ID
            thread_id = self.chat_history.generate_thread_id(
                context.email_data.get('sender', ''),
                context.email_data.get('subject', ''),
                context.email_data.get('body', '')
            )
            
            # Erstelle Nachricht für Historie
            message = ConversationMessage(
                message_id=f"msg_{int(datetime.now().timestamp())}",
                thread_id=thread_id,
                email_address=context.email_data.get('sender', ''),
                subject=context.email_data.get('subject', ''),
                content=context.email_data.get('body', ''),
                message_type=MessageType.INCOMING,
                intent_type=context.nlu_result.intent_type if context.nlu_result else "unknown",
                confidence=context.nlu_result.confidence if context.nlu_result else 0.0,
                entities=context.nlu_result.entities if context.nlu_result else {},
                context_type=ContextType.APPOINTMENT_BOOKING,  # Wird durch Analyse bestimmt
                timestamp=datetime.now(),
                is_processed=True,
                response_generated=True,
                extracted_name=asdict(context.extracted_name) if context.extracted_name else None,
                sentiment="neutral",  # Wird durch Sentiment-Analyse bestimmt
                urgency_level=context.nlu_result.urgency_level if context.nlu_result else "routine"
            )
            
            # Speichere Nachricht
            self.chat_history.store_message(message)
            
            logger.info("Chat-Historie aktualisiert")
            
        except Exception as e:
            logger.error(f"Chat-Historie-Update fehlgeschlagen: {e}")
    
    
    def get_enterprise_statistics(self) -> Dict[str, Any]:
        """Holt umfassende Enterprise-Statistiken"""
        try:
            stats = {
                "name_extraction": {
                    "total_extractions": 0,  # Wird aus Datenbank geladen
                    "success_rate": 0.0
                },
                "chat_history": self.chat_history.get_conversation_statistics(),
                "learning_system": self.learning_system.get_learning_statistics(),
                "error_handling": self.error_handler.get_error_statistics(),
                "generated_at": datetime.now().isoformat()
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Statistiken-Laden fehlgeschlagen: {e}")
            return {"error": "Fehler beim Laden der Statistiken"}
    
    def get_name_for_appointment(self, email: str, email_content: str = "") -> Tuple[bool, str, str]:
        """Holt oder extrahiert Namen für Terminbuchung"""
        try:
            has_full_name, first_name, last_name = self.name_extractor.get_name_for_appointment(email, email_content)
            
            if not has_full_name and first_name:
                # Nur Vorname vorhanden - generiere Nachfrage
                return False, first_name, ""
            elif not has_full_name and not first_name:
                # Kein Name vorhanden - generiere Nachfrage
                return False, "", ""
            else:
                # Vollständiger Name vorhanden
                return True, first_name, last_name
                
        except Exception as e:
            logger.error(f"Name-für-Termin fehlgeschlagen: {e}")
            return False, "", ""
    
    def ask_for_missing_name_part(self, email: str, current_name: str, missing_part: str) -> str:
        """Generiert eine höfliche Nachfrage nach fehlenden Namensbestandteilen"""
        return self.name_extractor.ask_for_missing_name_part(email, current_name, missing_part)


# Test-Funktion für den Enterprise Integration Coordinator
def test_enterprise_integration():
    """Testet den Enterprise Integration Coordinator"""
    coordinator = EnterpriseIntegrationCoordinator()
    
    # Test-E-Mail
    test_email = {
        "subject": "Terminanfrage",
        "body": "Hallo, ich bin Max Mustermann und brauche einen Termin für nächste Woche.",
        "sender": "max.mustermann@example.com",
        "message_id": "test_001"
    }
    
    # Verarbeite E-Mail
    result = asyncio.run(coordinator.process_email_enterprise(test_email))
    print(f"Verarbeitungsergebnis: {result['success']}")
    
    # Zeige Statistiken
    stats = coordinator.get_enterprise_statistics()
    print(f"Enterprise-Statistiken: {json.dumps(stats, indent=2, default=str)}")


if __name__ == "__main__":
    test_enterprise_integration()
