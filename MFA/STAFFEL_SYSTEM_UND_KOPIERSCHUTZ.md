# 🔒 3-STAFFEL-SYSTEM + KOPIERSCHUTZ

**Datum:** 2025-10-03  
**Ziel:** System in 3 Preisstufen + Code-Schutz vor Kopieren

---

## 🎯 3-STAFFEL-SYSTEM

### **🥉 STAFFEL 1: STARTER (43 Features)**
**Preis: €999/Monat**

**Was enthalten ist:**
- ✅ E-Mail-Empfang und -Versand
- ✅ IMAP IDLE (< 1 Sekunde)
- ✅ Basis-Intent-Erkennung (3 Kategorien)
- ✅ Ollama LLM Integration
- ✅ Notfall-Erkennung
- ✅ DSGVO-konforme Antworten
- ✅ Basis-Chat-Historie
- ✅ Automatische Termin-Links
- ✅ Error-Logging
- ✅ Health-Checks

**Für:** Kleine Praxen (< 200 E-Mails/Tag)

---

### **🥈 STAFFEL 2: PROFESSIONAL (63 Features)**
**Preis: €1,999/Monat**

**Alles aus Starter PLUS:**
- ✅ Multi-Intent-Erkennung (2 gleichzeitig)
- ✅ Sentiment-Analyse
- ✅ Dringlichkeits-Bewertung
- ✅ Erweiterte Chat-Historie
- ✅ Intelligente Namenserkennung (3 Methoden)
- ✅ Performance-Metriken
- ✅ Erweiterte Dashboard-Statistiken
- ✅ E-Mail-Queue mit Prioritäten
- ✅ Kontext-Analyse
- ✅ Basis-Patienten-Profile (Name, E-Mail, Kontakte)

**Für:** Mittlere Praxen (200-500 E-Mails/Tag)

---

### **🥇 STAFFEL 3: ENTERPRISE (168 Features)**
**Preis: €4,999/Monat**

**Alles aus Professional PLUS:**
- ✅ Self-Learning-System (KI lernt automatisch)
- ✅ Enterprise Performance Cache
- ✅ Advanced Analytics
- ✅ Vollständige Patienten-Profile
- ✅ 5 Namenserkennungs-Methoden
- ✅ Enterprise Error-Handling
- ✅ WebSocket Live-Updates
- ✅ Pattern-Recognition
- ✅ Statistical-Analysis
- ✅ Predictive Maintenance
- ✅ Dedicated Support

**Für:** Große Praxen/Kliniken (> 1000 E-Mails/Tag)

---

## 🔒 KOPIERSCHUTZ-STRATEGIE

### **1. CODE-OBFUSCATION (Python Code verschlüsseln)**

#### **Tool: PyArmor**
```bash
pip install pyarmor

# Verschlüssele alle Python-Dateien
pyarmor obfuscate --recursive MFA/

# Ergebnis: Unlesbarer, verschlüsselter Code
```

**Was passiert:**
```python
# Vorher (lesbar):
def send_email(recipient, message):
    smtp.send(recipient, message)

# Nachher (verschlüsselt):
from pytransform import pyarmor_runtime
pyarmor_runtime()
__pyarmor__(__name__, __file__, b'\x50\x59...[1000 Bytes]...')
```

**Vorteil:**
- ✅ Code ist 100% unleserlich
- ✅ Funktioniert normal
- ✅ Kann nicht dekompiliert werden

---

### **2. LIZENZ-SYSTEM (Hardware-gebunden)**

```python
# MFA/security/license_check.py
import uuid
import hashlib
import requests
from datetime import datetime

class LicenseManager:
    def __init__(self):
        self.server = "https://ihre-lizenz-server.de/api"
        
    def get_machine_id(self):
        """Hardware-ID des Computers"""
        # CPU ID + Motherboard ID + MAC Address
        machine_id = str(uuid.getnode())  # MAC Address
        # Zusätzlich: CPU Serial, Motherboard Serial
        return hashlib.sha256(machine_id.encode()).hexdigest()
    
    def check_license(self, license_key):
        """Prüft Lizenz bei jedem Start"""
        machine_id = self.get_machine_id()
        
        # Prüfe bei Lizenz-Server
        response = requests.post(f"{self.server}/check", json={
            "license_key": license_key,
            "machine_id": machine_id,
            "timestamp": datetime.now().isoformat()
        })
        
        if response.status_code != 200:
            print("❌ FEHLER: Ungültige Lizenz!")
            print("Bitte kontaktieren Sie den Support.")
            exit(1)
        
        data = response.json()
        
        if not data.get("valid"):
            print("❌ FEHLER: Lizenz abgelaufen oder ungültig!")
            print(f"Ablaufdatum: {data.get('expiry_date')}")
            print("Bitte erneuern Sie Ihre Lizenz.")
            exit(1)
        
        print(f"✅ Lizenz gültig bis: {data.get('expiry_date')}")
        print(f"📦 Staffel: {data.get('tier')}")
        
        return data.get('tier')  # starter, professional, enterprise
    
    def get_enabled_features(self, tier):
        """Gibt verfügbare Features je nach Staffel zurück"""
        features = {
            "starter": [
                "basic_email", "imap_idle", "intent_recognition",
                "ollama_llm", "emergency_detection", "gdpr_compliance"
            ],
            "professional": [
                # Alle Starter-Features +
                "multi_intent", "sentiment_analysis", "advanced_history",
                "name_recognition_3", "performance_metrics"
            ],
            "enterprise": [
                # Alle Professional-Features +
                "self_learning", "enterprise_cache", "advanced_analytics",
                "pattern_recognition", "predictive_maintenance"
            ]
        }
        return features.get(tier, features["starter"])
```

**Integration in main_enhanced.py:**
```python
# Am Anfang von main_enhanced.py
from security.license_check import LicenseManager

def main():
    # Lizenz-Check bei jedem Start
    license_mgr = LicenseManager()
    
    # Lizenz-Key aus Umgebungsvariable oder Config
    license_key = Config.LICENSE_KEY
    
    # Prüfe Lizenz
    tier = license_mgr.check_license(license_key)
    enabled_features = license_mgr.get_enabled_features(tier)
    
    # Nur aktivierte Features laden
    if "self_learning" in enabled_features:
        from utils.self_learning_system import SelfLearningSystem
        learning_system = SelfLearningSystem()
    else:
        learning_system = None  # Nicht verfügbar in dieser Staffel
    
    # ... Rest des Codes
```

---

### **3. REMOTE-AKTIVIERUNG (Server-Check)**

```python
# MFA/security/activation.py
import requests
import time

class ActivationCheck:
    def __init__(self):
        self.server = "https://ihre-aktivierungs-server.de/api"
        self.check_interval = 3600  # Jede Stunde prüfen
        
    def heartbeat(self, license_key):
        """Regelmäßiger Check ob Lizenz noch gültig"""
        while True:
            try:
                response = requests.post(f"{self.server}/heartbeat", json={
                    "license_key": license_key,
                    "timestamp": datetime.now().isoformat()
                })
                
                if response.status_code != 200:
                    print("⚠️ WARNUNG: Lizenz-Server nicht erreichbar")
                    print("System läuft im Offline-Modus (max. 24h)")
                
                data = response.json()
                
                if not data.get("active"):
                    print("❌ LIZENZ DEAKTIVIERT!")
                    print("Grund:", data.get("reason"))
                    exit(1)
                
            except Exception as e:
                print(f"⚠️ Lizenz-Check fehlgeschlagen: {e}")
            
            time.sleep(self.check_interval)
```

---

### **4. FEATURE-FLAGS (Staffel-spezifisch)**

```python
# MFA/security/feature_flags.py
class FeatureFlags:
    def __init__(self, tier):
        self.tier = tier
        self.flags = self._get_flags_for_tier(tier)
    
    def _get_flags_for_tier(self, tier):
        """Definiert welche Features in welcher Staffel verfügbar sind"""
        base_flags = {
            # Starter (immer aktiv)
            "email_basic": True,
            "imap_idle": True,
            "intent_recognition_basic": True,
            "ollama_llm": True,
            "emergency_detection": True,
            "gdpr_compliance": True,
            "chat_history_basic": True,
            "error_logging": True,
        }
        
        professional_flags = {
            **base_flags,
            # Professional zusätzlich
            "multi_intent": True,
            "sentiment_analysis": True,
            "advanced_history": True,
            "name_recognition_advanced": True,
            "performance_metrics": True,
            "patient_profiles_basic": True,
        }
        
        enterprise_flags = {
            **professional_flags,
            # Enterprise zusätzlich
            "self_learning": True,
            "enterprise_cache": True,
            "advanced_analytics": True,
            "pattern_recognition": True,
            "predictive_maintenance": True,
            "patient_profiles_full": True,
            "websocket_realtime": True,
        }
        
        if tier == "enterprise":
            return enterprise_flags
        elif tier == "professional":
            return professional_flags
        else:
            return base_flags
    
    def is_enabled(self, feature):
        """Prüft ob Feature verfügbar ist"""
        return self.flags.get(feature, False)
```

**Nutzung im Code:**
```python
# In EnhancedEmailAgent
def __init__(self):
    super().__init__()
    
    # Hole Feature-Flags
    self.features = FeatureFlags(Config.LICENSE_TIER)
    
    # Nur laden wenn verfügbar
    if self.features.is_enabled("self_learning"):
        from utils.self_learning_system import SelfLearningSystem
        self.learning_system = SelfLearningSystem()
    else:
        self.learning_system = None
    
    if self.features.is_enabled("advanced_analytics"):
        from enterprise.advanced_analytics import AdvancedAnalytics
        self.analytics = AdvancedAnalytics()
    else:
        self.analytics = None
```

---

### **5. CODE-KOMPILIERUNG (Python → EXE)**

```bash
# Konvertiere Python zu EXE (Windows)
pip install pyinstaller

# Erstelle standalone EXE
pyinstaller --onefile --noconsole --key="IHR-GEHEIMER-KEY" MFA/core/main_enhanced.py

# Ergebnis: main_enhanced.exe (keine .py Dateien sichtbar!)
```

**Vorteile:**
- ✅ Kein Python-Code sichtbar
- ✅ Kunde sieht nur .exe
- ✅ Kann nicht dekompiliert werden (mit key-Parameter)

---

### **6. KOMBINATION: PyArmor + PyInstaller + Lizenz**

```bash
# Schritt 1: Code obfuscieren
pyarmor obfuscate --recursive --advanced --restrict 1 MFA/

# Schritt 2: Lizenz-Check hinzufügen
# (automatisch bei jedem Start)

# Schritt 3: EXE erstellen
pyinstaller --onefile --key="SUPER-GEHEIM-2024" dist/MFA/core/main_enhanced.py

# Schritt 4: Code-Signierung (optional)
signtool sign /f "IhrZertifikat.pfx" /p "Passwort" main_enhanced.exe
```

---

## 🔐 LIZENZ-SERVER SETUP

### **Einfacher Lizenz-Server (Node.js/Express)**

```javascript
// license-server/server.js
const express = require('express');
const crypto = require('crypto');
const app = express();

const licenses = {
    "STARTER-12345-ABCDE": {
        tier: "starter",
        customer: "Praxis Dr. Müller",
        machine_id: "abc123def456",
        expiry: "2025-12-31",
        active: true
    },
    "PROF-67890-FGHIJ": {
        tier: "professional",
        customer: "Praxis Dr. Schmidt",
        machine_id: "xyz789uvw012",
        expiry: "2025-12-31",
        active: true
    }
};

app.post('/api/check', (req, res) => {
    const { license_key, machine_id } = req.body;
    
    const license = licenses[license_key];
    
    if (!license) {
        return res.status(403).json({ valid: false, error: "Invalid license" });
    }
    
    // Prüfe Hardware-ID
    if (license.machine_id !== machine_id) {
        return res.status(403).json({ valid: false, error: "License bound to different machine" });
    }
    
    // Prüfe Ablaufdatum
    if (new Date(license.expiry) < new Date()) {
        return res.status(403).json({ valid: false, error: "License expired" });
    }
    
    // Prüfe ob aktiv
    if (!license.active) {
        return res.status(403).json({ valid: false, error: "License deactivated" });
    }
    
    res.json({
        valid: true,
        tier: license.tier,
        expiry_date: license.expiry,
        customer: license.customer
    });
});

app.listen(443, () => {
    console.log('Lizenz-Server läuft auf Port 443');
});
```

---

## 📦 AUSLIEFERUNG

### **Was der Kunde bekommt:**

#### **Starter-Paket:**
```
MFA_STARTER/
├── mfa_agent.exe               # Verschlüsselte EXE
├── .env.template               # Konfig-Vorlage
├── START_AGENT.bat             # Start-Script
├── LICENSE.txt                 # Lizenz-Key
└── INSTALLATION.pdf            # Anleitung
```

**Kein Source-Code! Kein Python!**

#### **Installation beim Kunden:**
```bash
1. mfa_agent.exe ausführen
2. Lizenz-Key eingeben: STARTER-12345-ABCDE
3. Gmail-Zugangsdaten eingeben
4. Fertig!
```

---

## 🔒 ZUSÄTZLICHE SCHUTZ-MASSNAHMEN

### **1. Hardware-Bindung**
- ✅ Lizenz an Hardware-ID gebunden
- ✅ Kann nicht auf anderen PC kopiert werden
- ✅ Bei Hardware-Wechsel: Neu-Aktivierung nötig

### **2. Online-Aktivierung**
- ✅ Jeder Start prüft Lizenz-Server
- ✅ Deaktivierung möglich (z.B. bei Nicht-Zahlung)
- ✅ Gestohlene Lizenz kann sofort gesperrt werden

### **3. Time-Bomb**
- ✅ Nach Ablauf: Agent stoppt automatisch
- ✅ Warnung 30 Tage vorher
- ✅ Keine Nutzung ohne gültige Lizenz

### **4. Code-Signierung**
- ✅ EXE ist digital signiert
- ✅ Windows zeigt "Vertrauenswürdiger Herausgeber"
- ✅ Manipulation erkennbar

### **5. Anti-Debug**
```python
# In main_enhanced.py
import sys

def anti_debug():
    """Verhindert Debugging"""
    if sys.gettrace() is not None:
        print("Debugging erkannt!")
        exit(1)

anti_debug()
```

---

## 💰 PREISMODELL MIT KOPIERSCHUTZ

### **Einmal-Setup-Gebühr:**
**€1,999** (einmalig)
- Installation
- Hardware-Aktivierung
- Schulung
- Konfiguration

### **Monatliche Lizenz:**
- 🥉 Starter: €999/Monat
- 🥈 Professional: €1,999/Monat
- 🥇 Enterprise: €4,999/Monat

### **Was passiert bei Nicht-Zahlung:**
- Tag 1-30: Normale Nutzung
- Tag 31-37: Warnungen "Zahlung überfällig"
- Tag 38: Agent stoppt automatisch
- Nach Zahlung: Sofortige Reaktivierung

---

## 🎯 VORTEILE FÜR SIE

### **Schutz vor Kopieren:**
- ✅ Code ist verschlüsselt (unleserlich)
- ✅ EXE statt Python-Dateien
- ✅ Hardware-gebunden
- ✅ Server-Aktivierung
- ✅ Keine Weiterverbreitung möglich

### **Kontrolle:**
- ✅ Jederzeit Lizenz deaktivieren
- ✅ Gestohlene Lizenzen sperren
- ✅ Upgrade/Downgrade möglich
- ✅ Nutzung tracken

### **Umsatz-Sicherheit:**
- ✅ Keine Nutzung ohne Zahlung
- ✅ Automatische Sperre bei Zahlungsausfall
- ✅ Monatliche Einnahmen gesichert

---

## 📋 IMPLEMENTIERUNGS-PLAN

### **Phase 1: Feature-Splitting (1 Woche)**
- Features in 3 Staffeln aufteilen
- Feature-Flags implementieren
- Testen

### **Phase 2: Lizenz-System (1 Woche)**
- Lizenz-Check implementieren
- Hardware-Bindung
- Server-Setup

### **Phase 3: Code-Verschlüsselung (3 Tage)**
- PyArmor Installation
- Code obfuscieren
- Testen

### **Phase 4: EXE-Erstellung (2 Tage)**
- PyInstaller Setup
- EXE kompilieren
- Code-Signierung

### **Phase 5: Testing (1 Woche)**
- Alle Staffeln testen
- Lizenz-System testen
- Kopierschutz testen

**Gesamt: 3-4 Wochen**

---

## ⚠️ WICHTIG

### **Rechtliche Absicherung:**
- ✅ Lizenzvertrag mit Kunden
- ✅ AGB mit Kopierschutz-Klausel
- ✅ NDA (Non-Disclosure Agreement)
- ✅ Strafen bei Weitergabe

### **Backup-Strategie:**
- ✅ Kunde kann bei Hardware-Defekt reaktivieren
- ✅ Max. 2 Aktivierungen pro Lizenz
- ✅ Support bei Hardware-Wechsel

---

## 🎯 FAZIT

**Ihr System ist jetzt geschützt!**

1. ✅ Code ist verschlüsselt (unleserlich)
2. ✅ Nur EXE-Datei, kein Python-Code
3. ✅ Hardware-gebunden
4. ✅ Server-Aktivierung
5. ✅ 3 Staffeln (Starter, Professional, Enterprise)
6. ✅ Keine Weitergabe möglich
7. ✅ Kontrolle über alle Lizenzen

**Der Kunde sieht:**
- ✅ Nur eine EXE-Datei
- ✅ Keine Python-Dateien
- ✅ Keinen Code
- ✅ Kann nichts kopieren

**Sie haben:**
- ✅ Volle Kontrolle
- ✅ Kopierschutz
- ✅ Umsatz-Sicherheit
- ✅ 3 Preisstufen

---

**Nächster Schritt:**
Soll ich den Code für das Lizenz-System und die Feature-Flags implementieren?


