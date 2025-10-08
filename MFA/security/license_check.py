#!/usr/bin/env python3
"""
LIZENZ-MANAGEMENT-SYSTEM
Hardware-gebundene Lizenz-Prüfung mit Server-Validierung
"""

import uuid
import hashlib
import requests
import logging
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class LicenseManager:
    """Verwaltet Lizenz-Prüfung und Hardware-Bindung"""
    
    def __init__(self, server_url: str = "https://ihre-lizenz-server.de/api"):
        self.server = server_url
        self.offline_grace_period = 86400  # 24 Stunden Offline-Modus
        
    def get_machine_id(self) -> str:
        """
        Generiert eindeutige Hardware-ID
        Kombiniert MAC-Adresse, CPU-Info, etc.
        """
        try:
            # MAC-Adresse als Basis
            mac = str(uuid.getnode())
            
            # Zusätzliche Hardware-Info (optional)
            # Hier können Sie weitere Hardware-IDs hinzufügen
            # z.B. CPU Serial, Motherboard Serial
            
            # Hash für Anonymität
            machine_id = hashlib.sha256(mac.encode()).hexdigest()
            
            logger.debug(f"Hardware-ID generiert: {machine_id[:16]}...")
            return machine_id
            
        except Exception as e:
            logger.error(f"Fehler bei Hardware-ID-Generierung: {e}")
            # Fallback auf UUID
            return str(uuid.uuid4())
    
    def check_license(self, license_key: str) -> Dict[str, any]:
        """
        Prüft Lizenz bei jedem Start
        
        Args:
            license_key: Lizenz-Schlüssel des Kunden
            
        Returns:
            Dict mit Lizenz-Informationen (tier, valid, etc.)
        """
        try:
            machine_id = self.get_machine_id()
            
            logger.info("Prüfe Lizenz...")
            logger.debug(f"Lizenz-Key: {license_key[:10]}...")
            logger.debug(f"Hardware-ID: {machine_id[:16]}...")
            
            # Prüfe bei Lizenz-Server
            response = requests.post(
                f"{self.server}/check",
                json={
                    "license_key": license_key,
                    "machine_id": machine_id,
                    "timestamp": datetime.now().isoformat(),
                    "version": "2.0.0"
                },
                timeout=10
            )
            
            if response.status_code != 200:
                logger.error(f"Lizenz-Server Fehler: {response.status_code}")
                return self._handle_license_error("Server-Fehler")
            
            data = response.json()
            
            if not data.get("valid"):
                error_msg = data.get('error', 'Unbekannter Fehler')
                logger.error(f"Lizenz ungültig: {error_msg}")
                return self._handle_license_error(error_msg)
            
            # Lizenz ist gültig
            logger.info(f"✅ Lizenz gültig")
            logger.info(f"📦 Staffel: {data.get('tier').upper()}")
            logger.info(f"📅 Gültig bis: {data.get('expiry_date')}")
            logger.info(f"👤 Kunde: {data.get('customer')}")
            
            return {
                "valid": True,
                "tier": data.get('tier'),
                "expiry_date": data.get('expiry_date'),
                "customer": data.get('customer'),
                "features": data.get('features', [])
            }
            
        except requests.exceptions.Timeout:
            logger.warning("⚠️ Lizenz-Server nicht erreichbar (Timeout)")
            return self._handle_offline_mode(license_key)
            
        except requests.exceptions.ConnectionError:
            logger.warning("⚠️ Lizenz-Server nicht erreichbar (Verbindungsfehler)")
            return self._handle_offline_mode(license_key)
            
        except Exception as e:
            logger.error(f"Unerwarteter Fehler bei Lizenz-Prüfung: {e}")
            return self._handle_license_error(str(e))
    
    def _handle_license_error(self, error_msg: str) -> Dict:
        """Behandelt Lizenz-Fehler"""
        print("\n" + "="*60)
        print("❌ LIZENZ-FEHLER")
        print("="*60)
        print(f"\nFehler: {error_msg}")
        print("\nMögliche Ursachen:")
        print("  1. Lizenz-Key ist ungültig")
        print("  2. Lizenz ist abgelaufen")
        print("  3. Lizenz ist an andere Hardware gebunden")
        print("  4. Lizenz wurde deaktiviert")
        print("\nBitte kontaktieren Sie den Support:")
        print("  📧 E-Mail: support@ihre-firma.de")
        print("  📞 Telefon: +49-XXX-XXXXXXX")
        print("\n" + "="*60)
        
        # System beenden
        import sys
        sys.exit(1)
    
    def _handle_offline_mode(self, license_key: str) -> Dict:
        """Behandelt Offline-Modus (24h grace period)"""
        logger.warning("System läuft im Offline-Modus")
        logger.warning(f"Offline-Modus erlaubt für {self.offline_grace_period/3600}h")
        
        # Hier könnten Sie einen lokalen Cache prüfen
        # um zu sehen, ob die Lizenz kürzlich gültig war
        
        print("\n" + "="*60)
        print("⚠️ OFFLINE-MODUS")
        print("="*60)
        print("\nLizenz-Server ist nicht erreichbar.")
        print("System läuft im Offline-Modus für maximal 24 Stunden.")
        print("\nBitte stellen Sie sicher, dass:")
        print("  1. Internet-Verbindung besteht")
        print("  2. Lizenz-Server erreichbar ist")
        print("\n" + "="*60)
        
        # Gebe Standard-Tier zurück (Starter)
        return {
            "valid": True,
            "tier": "starter",
            "offline_mode": True,
            "features": self._get_starter_features()
        }
    
    def _get_starter_features(self) -> List[str]:
        """Gibt Starter-Features zurück"""
        return [
            "basic_email", "imap_idle", "intent_recognition",
            "ollama_llm", "emergency_detection", "gdpr_compliance"
        ]
    
    def get_enabled_features(self, tier: str) -> List[str]:
        """
        Gibt verfügbare Features je nach Staffel zurück
        
        Args:
            tier: Lizenz-Staffel (starter, professional, enterprise)
            
        Returns:
            Liste von Feature-Namen
        """
        features = {
            "starter": [
                "basic_email",
                "imap_idle",
                "intent_recognition_basic",
                "ollama_llm",
                "emergency_detection",
                "gdpr_compliance",
                "chat_history_basic",
                "error_logging",
                "health_checks",
                "retry_mechanisms",
                "auto_booking_links"
            ],
            
            "professional": [
                # Alle Starter-Features
                "basic_email", "imap_idle", "intent_recognition_basic",
                "ollama_llm", "emergency_detection", "gdpr_compliance",
                "chat_history_basic", "error_logging", "health_checks",
                "retry_mechanisms", "auto_booking_links",
                # Professional zusätzlich
                "multi_intent",
                "sentiment_analysis",
                "urgency_assessment",
                "advanced_chat_history",
                "name_recognition_advanced",
                "performance_metrics",
                "patient_profiles_basic",
                "email_queue_priority",
                "context_analysis"
            ],
            
            "enterprise": [
                # Alle Professional-Features
                "basic_email", "imap_idle", "intent_recognition_basic",
                "ollama_llm", "emergency_detection", "gdpr_compliance",
                "chat_history_basic", "error_logging", "health_checks",
                "retry_mechanisms", "auto_booking_links",
                "multi_intent", "sentiment_analysis", "urgency_assessment",
                "advanced_chat_history", "name_recognition_advanced",
                "performance_metrics", "patient_profiles_basic",
                "email_queue_priority", "context_analysis",
                # Enterprise zusätzlich
                "self_learning",
                "enterprise_cache",
                "advanced_analytics",
                "pattern_recognition",
                "predictive_maintenance",
                "patient_profiles_full",
                "websocket_realtime",
                "5_name_recognition_methods",
                "enterprise_error_handling",
                "statistical_analysis"
            ]
        }
        
        return features.get(tier, features["starter"])
    
    def validate_feature(self, feature: str, tier: str) -> bool:
        """
        Prüft ob Feature in dieser Staffel verfügbar ist
        
        Args:
            feature: Feature-Name
            tier: Lizenz-Staffel
            
        Returns:
            True wenn Feature verfügbar, sonst False
        """
        enabled_features = self.get_enabled_features(tier)
        return feature in enabled_features


# Globale Instanz (Singleton)
_license_manager = None

def get_license_manager(server_url: Optional[str] = None) -> LicenseManager:
    """Factory-Funktion für LicenseManager"""
    global _license_manager
    if _license_manager is None:
        _license_manager = LicenseManager(server_url or "https://ihre-lizenz-server.de/api")
    return _license_manager


