# 🚀 MFA Enterprise KI-Agent - E-Mail-Automatisierung

**Intelligenter E-Mail-Agent für Arztpraxen mit Enterprise-Features, sofortiger E-Mail-Erkennung und vollständiger Dashboard-API.**

## ✨ Features

### 🤖 **KI-gestützte E-Mail-Verarbeitung**
- ⚡ **IMAP IDLE**: Sofortige E-Mail-Erkennung (< 1 Sekunde)
- 🧠 **Enterprise NLU**: 25+ Intent-Typen, Facharzt-Erkennung
- 🤖 **Qwen 2.5 3B**: Lokale KI für professionelle Antworten
- 📧 **Intelligente Antworten**: Kontextbasierte, personalisierte E-Mails

### 📊 **Enterprise Dashboard-API**
- 🌐 **REST API** auf Port 5000 für externes Dashboard
- 📈 **Echtzeit-Metriken**: E-Mails, Performance, System-Status
- 🔄 **Live-Updates**: WebSocket für sofortige Daten-Aktualisierung
- 📋 **Vollständige CRUD**: E-Mail-Management, Templates, Einstellungen

### 🏗️ **Enterprise-Architektur**
- 📦 **Modulare Struktur**: agents/, services/, enterprise/, core/
- 🔒 **Datenschutz**: Lokale Verarbeitung, keine Cloud-Speicherung
- ⚙️ **Konfigurierbar**: Flexible Einstellungen für alle Features
- 🔄 **Self-Learning**: Automatische Verbesserung durch Nutzung

## 🚀 Schnellstart

### 1️⃣ **Dependencies installieren**
```bash
pip install -r requirements.txt
```

### 2️⃣ **Umgebungsvariablen konfigurieren**
Erstellen Sie eine `.env` Datei:
```bash
GMAIL_ADDRESS=ihr-gmail-account@gmail.com
GMAIL_APP_PASSWORD=ihr-16-stelliges-app-password
OLLAMA_BASE_URL=http://localhost:11434
```

### 3️⃣ **Ollama Modell laden**
```bash
ollama pull qwen2.5:3b  # Optimiert für Raspberry Pi & Mini-PCs
```

### 4️⃣ **System starten**
```bash
# Windows (empfohlen)
START_AGENT.bat

# Oder direkt
python -m core.main_enhanced
```

## 📊 Dashboard Integration

### **API Endpoints verfügbar:**
```
🌐 http://localhost:5000/api/stats        # Alle System-Daten
📧 http://localhost:5000/api/emails       # E-Mail-Management
⚙️ http://localhost:5000/api/settings     # System-Einstellungen
📚 http://localhost:5000/docs             # API-Dokumentation
```

### **Für Ihr externes Dashboard:**
```typescript
// Beispiel: React Query Setup
import { QueryClient, QueryClientProvider } from 'react-query';

const queryClient = new QueryClient();

// Stats abrufen
const { data: stats } = useQuery({
  queryKey: ['dashboard-stats'],
  queryFn: () => fetch('http://localhost:5000/api/stats').then(r => r.json()),
  refetchInterval: 5000
});
```

## 🏗️ Architektur

```
MFA/
├── 🤖 agents/              → E-Mail & Patienten-Management
│   ├── email_agent.py      → Basis E-Mail-Agent mit IMAP IDLE
│   ├── enhanced_email_agent.py → Enterprise E-Mail-Verarbeitung
│   └── patient_management_agent.py → Patienten-Datenbank
│
├── ⚙️ services/            → Business-Logik
│   ├── ollama_service.py   → KI-Integration
│   ├── intent_service.py   → Intent-Erkennung
│   └── email_queue.py      → E-Mail-Warteschlange
│
├── 🏢 enterprise/          → Enterprise-Features
│   ├── enterprise_system_final.py → Haupt-System
│   ├── enterprise_nlu.py   → Erweiterte Sprachverarbeitung
│   ├── enterprise_response_generator.py → Antwort-Generierung
│   ├── enterprise_error_handling.py → Robuste Fehlerbehandlung
│   └── enterprise_performance_cache.py → Performance-Optimierung
│
├── 🔧 core/               → Kern-System
│   ├── config.py          → Konfiguration
│   ├── conversation_db.py → Datenbank-Management
│   ├── advanced_chat_history.py → Chat-Historie
│   └── main_enhanced.py   → Haupteinstiegspunkt
│
├── 🛠️ utils/              → Hilfsfunktionen
│   ├── intelligent_name_extractor.py → Namen-Erkennung
│   ├── privacy.py         → Datenschutz-Funktionen
│   ├── self_learning_system.py → Lernsystem
│   └── personalization.py → Personalisierung
│
├── 📡 api/                → Dashboard-API
│   ├── dashboard_api.py   → FastAPI Server
│   └── __init__.py        → API-Module
│
├── 📦 CLEANUP_BACKUP_2025-10-01/ → Alte Dateien (sicher)
└── 📚 Dokumentation/       → QUICK_START.md, API_DOCS.md
```

## ⚡ Performance & Hardware

### **Empfohlene Hardware für 24/7 Betrieb:**

| Setup | Hardware | RAM | Strom/Jahr | Kosten | Empfehlung |
|-------|----------|-----|------------|--------|------------|
| **Budget** | Raspberry Pi 5 (8GB) | 8GB | 15€ | 120€ | ⭐⭐⭐ |
| **Balance** | Intel N100 Mini-PC (16GB) | 16GB | 35€ | 200€ | ⭐⭐⭐⭐ |
| **Performance** | Ryzen Mini-PC (32GB) | 32GB | 40€ | 280€ | ⭐⭐⭐⭐⭐ |

### **Ollama Modelle:**
```
qwen2.5:3b    → Raspberry Pi (2-4GB RAM)
qwen2.5:14b   → Intel N100+ (10-12GB RAM)
```

## 🔒 Sicherheit & Datenschutz

- ✅ **Lokale KI**: Alle Daten bleiben auf Ihrem System
- ✅ **Keine Cloud-Speicherung**: Patientendaten verlassen nie Ihren PC
- ✅ **Verschlüsselte Verbindungen**: IMAP/SMTP über SSL/TLS
- ✅ **App-Passwords**: Sichere Gmail-Authentifizierung
- ✅ **DSGVO-konform**: Lokale Verarbeitung ohne Drittanbieter

## 📈 System-Metriken

### **Dashboard-API liefert:**
- 📊 **E-Mail-Statistiken**: Verarbeitete, ausstehende, fehlgeschlagene
- 📈 **Performance-Metriken**: Antwortzeiten, Systemlast, Cache-Hits
- 🤖 **Agenten-Status**: Aktive Agenten, Genauigkeit, Requests
- 📋 **E-Mail-Management**: CRUD-Operationen, Filter, Pagination
- ⚙️ **System-Einstellungen**: Profile, Guardrails, Integrationen

## 🛠️ Entwicklung & Erweiterung

### **Für Ihr externes Dashboard:**
1. **API-Server läuft automatisch** auf Port 5000
2. **CORS konfiguriert** für Port 8080 (Lovable-Standard)
3. **Alle Datenmodelle** nach Ihren Spezifikationen implementiert
4. **WebSocket-Support** für Live-Updates verfügbar

### **Konfiguration anpassen:**
```python
# In core/config.py
ENABLE_IMAP_IDLE = True        # Sofortige E-Mail-Erkennung
CHECK_INTERVAL_SECONDS = 10    # Fallback-Intervall
OLLAMA_MODEL = "qwen2.5:3b"    # Für Raspberry Pi optimiert
ONLINE_BOOKING_URL = "https://ihre-termine.de"  # Automatische Links
```

## 🚨 Wichtige Hinweise

### **Keine Termine mehr:**
- ❌ **Terminbuchung entfernt** (wie gewünscht)
- ✅ **Termin-Links** werden automatisch in E-Mail-Antworten eingefügt
- 📅 **Externer Terminkalender** kann über Links verbunden werden

### **Datenschutz:**
- ✅ **Alle Patientendaten** bleiben lokal
- ✅ **Keine Gesundheitsdaten** werden online gespeichert
- ✅ **Termin-Links** enthalten nur minimale Informationen

## 📚 Dokumentation

- 📖 **[QUICK_START.md](./QUICK_START.md)** - Schnelleinstieg
- 📖 **[API_DOCUMENTATION.md](./API_DOCUMENTATION.md)** - Komplette API-Referenz
- 📖 **[CLEANUP_DOCUMENTATION.md](./CLEANUP_DOCUMENTATION.md)** - Aufräum-Bericht

---

**System ist produktionsreif und wartet auf Ihr Dashboard! 🚀**
