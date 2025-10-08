# 📊 MFA Dashboard API - Dokumentation

## 🚀 **Schnellstart**

### Installation
```bash
pip install fastapi uvicorn websockets
```

### Server starten
Der API-Server startet **automatisch** mit dem MFA-System:
```bash
START_AGENT.bat
```

API läuft auf: **http://localhost:5000**

---

## 📡 **API Endpoints**

### **GET /** - API Info
Allgemeine API-Informationen
```json
{
  "name": "MFA Enterprise KI-Agent API",
  "version": "2.0.0",
  "status": "running",
  "endpoints": {...}
}
```

---

### **GET /api/stats** - Alle Statistiken ⭐
**Haupt-Endpoint** für Dashboard - Gibt alle Daten zurück

**Response:**
```json
{
  "timestamp": "2025-10-02T02:15:00Z",
  "system": {
    "status": "running",
    "uptime_seconds": 7845,
    "uptime_formatted": "2h 10m",
    "idle_mode_active": true,
    "ollama_connected": true,
    "imap_connected": true,
    "smtp_connected": true
  },
  "emails": {
    "total_processed": 142,
    "processed_today": 23,
    "processed_last_24h": 31,
    "pending_queue": 0,
    "failed_count": 2,
    "avg_response_time_seconds": 6.2,
    "success_rate_percent": 98.5
  },
  "intents": {
    "question": 66,
    "appointment": 45,
    "medication": 28,
    "emergency": 3
  },
  "performance": {
    "ollama_avg_latency_ms": 4200,
    "ollama_requests_total": 142,
    "imap_connections_today": 456,
    "cache_hit_rate_percent": 67.3,
    "memory_usage_mb": 245,
    "cpu_usage_percent": 12.5
  },
  "realtime": {
    "last_email_processed": "2025-10-02T02:10:00Z",
    "last_email_subject": "Terminanfrage",
    "last_email_intent": "appointment",
    "current_activity": "idle"
  }
}
```

---

### **GET /api/health** - Health Check
Prüft ob System läuft
```json
{
  "status": "healthy",
  "timestamp": "2025-10-02T02:15:00Z",
  "system_running": true
}
```

---

### **GET /api/emails** - E-Mail Stats
Nur E-Mail-Statistiken
```json
{
  "timestamp": "2025-10-02T02:15:00Z",
  "emails": {
    "total_processed": 142,
    "processed_today": 23,
    "...": "..."
  }
}
```

---

### **GET /api/intents** - Intent-Verteilung
Intent-Analyse
```json
{
  "timestamp": "2025-10-02T02:15:00Z",
  "intents": {
    "question": 66,
    "appointment": 45,
    "medication": 28,
    "emergency": 3
  }
}
```

---

### **GET /api/performance** - Performance-Metriken
System-Performance
```json
{
  "timestamp": "2025-10-02T02:15:00Z",
  "performance": {
    "ollama_avg_latency_ms": 4200,
    "imap_connections_today": 456,
    "cache_hit_rate_percent": 67.3
  }
}
```

---

### **GET /api/emails/recent?limit=10** - Letzte E-Mails
Liste der zuletzt verarbeiteten E-Mails
```json
{
  "emails": [
    {
      "timestamp": "2025-10-02T02:10:00Z",
      "sender": "patient@example.com",
      "subject": "Terminanfrage",
      "intent": "appointment",
      "confidence": 0.95
    }
  ]
}
```

---

### **GET /api/system/config** - System-Konfiguration
Aktuelle System-Einstellungen (ohne Secrets!)
```json
{
  "idle_enabled": true,
  "check_interval": 10,
  "ollama_model": "qwen2.5:14b-instruct",
  "practice_name": "Eli5 Praxis"
}
```

---

## 🔌 **WebSocket - Live Updates**

### **WS /ws** - Echtzeit-Verbindung
Empfängt **alle 2 Sekunden** automatisch Updates

**JavaScript Beispiel:**
```javascript
const ws = new WebSocket('ws://localhost:5000/ws');

ws.onmessage = (event) => {
  const stats = JSON.parse(event.data);
  console.log('Live Update:', stats);
  // Update Dashboard UI
};

ws.onerror = (error) => {
  console.error('WebSocket Error:', error);
};
```

**React Beispiel:**
```typescript
useEffect(() => {
  const ws = new WebSocket('ws://localhost:5000/ws');
  
  ws.onmessage = (event) => {
    const stats = JSON.parse(event.data);
    setDashboardData(stats);
  };
  
  return () => ws.close();
}, []);
```

---

## 🎨 **Dashboard - Was du noch einbauen solltest:**

### **1. Status-Karten (Cards)**
```
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ Heute           │  │ Gesamt          │  │ Erfolgsrate     │
│ 23 E-Mails      │  │ 142 E-Mails     │  │ 98.5%           │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

### **2. Intent-Diagramm**
- Pie Chart oder Bar Chart
- Zeigt Intent-Verteilung
- Daten aus: `stats.intents`

### **3. Live-Activity Feed**
```
🟢 IDLE - Warte auf neue E-Mails
📧 2:10 Uhr - Terminanfrage von patient@example.com
📧 2:05 Uhr - Rezeptanfrage von user@example.com
```

### **4. Performance-Metriken**
- Ollama Latenz: Gauge/Speedometer
- IMAP Verbindungen: Counter
- Cache Hit-Rate: Percentage Bar

### **5. System-Status**
```
✅ IDLE-Modus: AKTIV
✅ Ollama: VERBUNDEN
✅ IMAP: VERBUNDEN
✅ SMTP: VERBUNDEN
⏱️  Uptime: 2h 10m
```

### **6. Zeitreihen-Diagramm (Optional)**
- E-Mails pro Stunde
- Response-Zeiten über Zeit
- Braucht: Historische Daten sammeln

### **7. Fehler-Log (Optional)**
- Letzte Fehler anzeigen
- Daten aus: Error Handling DB

### **8. Konfigurations-Panel**
- System-Config anzeigen (Read-Only)
- Daten aus: `/api/system/config`

---

## 🔧 **CORS - Wichtig!**

API hat **CORS aktiviert** für alle Origins (`*`).

**Für Produktion:**
```python
# In dashboard_api.py ändern:
allow_origins=["http://localhost:3000"]  # Dein Dashboard-URL
```

---

## 📦 **Dependencies**

In `requirements.txt` hinzufügen:
```txt
fastapi>=0.104.0
uvicorn>=0.24.0
websockets>=12.0
```

Installation:
```bash
pip install -r requirements.txt
```

---

## 🧪 **Testen**

### API Docs (Swagger UI)
```
http://localhost:5000/docs
```

### Manueller Test
```bash
# Health Check
curl http://localhost:5000/api/health

# Alle Stats
curl http://localhost:5000/api/stats
```

### WebSocket Test (Browser Console)
```javascript
const ws = new WebSocket('ws://localhost:5000/ws');
ws.onmessage = (e) => console.log(JSON.parse(e.data));
```

---

## 🎯 **Dashboard-Struktur Vorschlag**

```
Dashboard
├── Header
│   ├── Logo
│   ├── System Status (🟢 Online)
│   └── Uptime
├── Stats Grid (4 Spalten)
│   ├── E-Mails Heute
│   ├── E-Mails Gesamt
│   ├── Erfolgsrate
│   └── Durchschn. Zeit
├── Charts (2 Spalten)
│   ├── Intent-Verteilung (Pie)
│   └── Performance (Gauge)
└── Activity Feed
    └── Live E-Mail-Liste
```

---

## 📝 **Beispiel Dashboard-Code (React/TypeScript)**

```typescript
import { useEffect, useState } from 'react';

interface DashboardStats {
  system: { status: string; uptime_formatted: string };
  emails: { total_processed: number; processed_today: number };
  // ... rest
}

function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  
  // WebSocket für Live-Updates
  useEffect(() => {
    const ws = new WebSocket('ws://localhost:5000/ws');
    ws.onmessage = (event) => {
      setStats(JSON.parse(event.data));
    };
    return () => ws.close();
  }, []);
  
  // Fallback: Polling (falls WebSocket fehlschlägt)
  useEffect(() => {
    const interval = setInterval(async () => {
      const response = await fetch('http://localhost:5000/api/stats');
      const data = await response.json();
      setStats(data);
    }, 5000); // Alle 5 Sekunden
    
    return () => clearInterval(interval);
  }, []);
  
  if (!stats) return <div>Loading...</div>;
  
  return (
    <div>
      <h1>MFA Dashboard</h1>
      <div className="stats-grid">
        <StatsCard
          title="E-Mails Heute"
          value={stats.emails.processed_today}
        />
        <StatsCard
          title="Gesamt"
          value={stats.emails.total_processed}
        />
        <StatsCard
          title="System Status"
          value={stats.system.status}
          color="green"
        />
      </div>
      <IntentChart data={stats.intents} />
      <ActivityFeed recent={stats.realtime} />
    </div>
  );
}
```

---

**API ist PRODUKTIONSREIF! 🚀**

