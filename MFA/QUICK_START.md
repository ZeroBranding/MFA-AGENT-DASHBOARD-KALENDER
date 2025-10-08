# 🚀 MFA Enterprise KI-Agent - Quick Start

## ⚡ Schnellstart (2 Minuten)

### 1️⃣ Voraussetzungen prüfen
```bash
# Python Version (min. 3.8)
python --version

# Ollama läuft
curl http://localhost:11434/api/version

# Node.js (optional für TypeScript Services)
node --version
```

### 2️⃣ System starten
```bash
# Windows:
START_AGENT.bat

# Oder direkt:
python -m core.main_enhanced
```

---

## 📁 Neue Projektstruktur

```
MFA/
├── 🤖 agents/              → E-Mail & Patienten-Management
│   ├── email_agent.py
│   ├── enhanced_email_agent.py
│   └── patient_management_agent.py
│
├── ⚙️ services/            → Business-Logik Services
│   ├── ollama_service.py
│   ├── intent_service.py
│   ├── email_queue.py
│   └── mail_processor.py
│
├── 🏢 enterprise/          → Enterprise-Features
│   ├── enterprise_system_final.py
│   ├── enterprise_nlu.py
│   ├── enterprise_response_generator.py
│   ├── enterprise_integration_coordinator.py
│   ├── enterprise_error_handling.py
│   └── enterprise_performance_cache.py
│
├── 🔧 core/               → Kern-System
│   ├── config.py           → Konfiguration
│   ├── conversation_db.py  → Datenbank
│   ├── advanced_chat_history.py
│   └── main_enhanced.py    → HAUPTEINSTIEG
│
├── 🛠️ utils/              → Hilfsfunktionen
│   ├── intelligent_name_extractor.py
│   ├── privacy.py
│   ├── self_learning_system.py
│   └── personalization.py
│
└── 📦 CLEANUP_BACKUP_2025-10-01/  → Alte Dateien (sicher)
```

---

## 🔧 Konfiguration

### .env Datei erstellen
```bash
# Kopiere Beispiel
cp env.example.txt .env

# Bearbeite .env
GMAIL_ADDRESS=ihre-email@gmail.com
GMAIL_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx
OLLAMA_BASE_URL=http://localhost:11434
```

### Wichtige Einstellungen in `core/config.py`
- `OLLAMA_MODEL` - LLM-Modell ([[memory:9493720]])
- `CHECK_INTERVAL_SECONDS` - Abruf-Intervall
- `PRACTICE_NAME` - Praxisname

---

## 📊 Module verwenden

### Import-Beispiele (neue Struktur)
```python
# Agents
from agents import EnhancedEmailAgent, PatientManagementAgent

# Services
from services import OllamaService, IntentService, EmailQueue

# Enterprise
from enterprise import EnterpriseNLU, EnterpriseSystemFinal

# Core
from core import Config, ConversationDB

# Utils
from utils import IntelligentNameExtractor, redact_text
```

---

## 🧪 System testen

### Komponenten-Test
```python
python -m utils.problem_analysis
```

### Einzelne Services testen
```python
# Ollama testen
from services.ollama_service import OllamaService
ollama = OllamaService()
response = ollama.generate("Hallo")

# NLU testen
from enterprise.enterprise_nlu import EnterpriseNLU
nlu = EnterpriseNLU()
result = nlu.analyze_email("Termin", "Ich brauche einen Termin", "test@email.com")
```

---

## 🔍 Troubleshooting

### Problem: Import-Fehler
```bash
# Stelle sicher, dass du im MFA/-Verzeichnis bist
cd MFA

# Starte mit Modul-Syntax
python -m core.main_enhanced
```

### Problem: Ollama nicht erreichbar
```bash
# Ollama starten
ollama serve

# Modell laden
ollama pull qwen2.5:3b
```

### Problem: E-Mail-Verbindung
- Prüfe `.env` Datei
- Gmail App-Password verwenden (nicht normales Passwort!)
- IMAP/SMTP in Gmail aktivieren

---

## 📝 Logs & Monitoring

### Log-Dateien
```
MFA/
├── email_agent.log         → Haupt-Log
├── logs/
│   ├── error_handler.log   → Fehler
│   ├── error_metrics.log   → Metriken
│   └── recovery.log        → Recovery-Aktionen
```

### Live-Monitoring
```bash
# Log-Dateien überwachen
tail -f email_agent.log
tail -f logs/error_handler.log
```

---

## 🚀 Produktiv-Betrieb

### 1. Datenbank-Migrationen
```bash
python -m utils.run_migration
```

### 2. Performance-Tuning
In `core/config.py`:
- `CHECK_INTERVAL_SECONDS = 60` (Produktion: längere Intervalle)
- `MAX_RETRIES = 5`
- `ENABLE_PERSISTENT_DEDUPE = True`

### 3. Enterprise-Features aktiviert
✅ Intelligente Namenserkennung  
✅ Chat-History & Kontext  
✅ Self-Learning System  
✅ Enterprise Error-Handling  
✅ Performance-Cache  
✅ Circuit-Breaker Pattern  
✅ Automatische Recovery  

---

## 📚 Weitere Dokumentation

- `CLEANUP_DOCUMENTATION.md` - Aufräum-Details
- `ENTERPRISE_SYSTEM_DOCUMENTATION.md` - Enterprise-Features
- `IMPLEMENTATION_SUMMARY.md` - Implementierungs-Details
- `README.md` - Vollständige Dokumentation

---

## ⚠️ Wichtige Hinweise

### Backup
Alle alten Dateien sind in `CLEANUP_BACKUP_2025-10-01/` gesichert.

### Keine Test-Dateien mehr
Wir erstellen **keine separaten Test-Dateien** mehr. Tests werden direkt in den Hauptdateien durchgeführt.

### Import-Pfade
**ALT (funktioniert nicht mehr):**
```python
from config import Config
from ollama_service import OllamaService
```

**NEU (korrekt):**
```python
from core.config import Config
from services.ollama_service import OllamaService
```

---

*Letztes Update: 01.10.2025*  
*Version: 2.0 (Aufgeräumt & Optimiert)*

