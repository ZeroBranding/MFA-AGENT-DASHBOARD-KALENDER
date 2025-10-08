"""
DASHBOARD API - FastAPI Server (Enterprise Edition)
Vollständige REST API nach Lovable Frontend-Spezifikation
Modulare Endpoints, Filter, Pagination, Actions, Templates
"""

from fastapi import FastAPI, HTTPException, Query, Path as PathParam, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import threading
import logging
import uvicorn
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import sqlite3
import requests
import json
import hmac
import hashlib
import os

logger = logging.getLogger(__name__)

# Globale Referenz zum Enterprise System
_enterprise_system = None
_system_start_time = datetime.now()
_active_websockets: List[WebSocket] = []  # WebSocket Clients

app = FastAPI(
    title="MFA Enterprise Dashboard API",
    description="Enterprise REST API für Lovable Dashboard",
    version="2.0.0"
)

# CORS für Lovable Dashboard (Port 8080)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://127.0.0.1:8080", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================
# PYDANTIC DATA MODELS (nach Lovable-Spezifikation)
# ============================================

# ============================================
# KALENDER-INTEGRATION MODELS
# ============================================

class Patient(BaseModel):
    id: Optional[str] = None
    firstName: str
    lastName: str
    birthDate: str  # ISO Date string
    phone: str
    email: str
    address: Optional[str] = None
    insuranceName: Optional[str] = None
    insuranceNumber: Optional[str] = None
    isExistingPatient: bool = False

class Appointment(BaseModel):
    id: Optional[str] = None
    patientId: Optional[str] = None
    patient: Optional[Patient] = None
    date: str  # ISO Date string
    startTime: str  # HH:MM format
    endTime: Optional[str] = None
    reason: str
    status: str = "confirmed"  # confirmed, cancelled, completed
    notes: Optional[str] = None

class CalendarAvailability(BaseModel):
    date: str
    time: str
    available: bool
    reason: Optional[str] = None

class Holiday(BaseModel):
    id: Optional[str] = None
    date: str  # ISO Date string
    description: str

class WebhookEvent(BaseModel):
    event: str  # booking_created, booking_cancelled, booking_updated
    timestamp: str
    data: Dict[str, Any]

# ============================================
# KALENDER-KONFIGURATION
# ============================================

# Kalender-API Basis-URL (wird über Environment-Variable gesetzt)
CALENDAR_API_BASE = os.getenv("CALENDAR_API_BASE", "http://localhost:3001/api")
CALENDAR_WEBHOOK_SECRET = os.getenv("CALENDAR_WEBHOOK_SECRET", "mfa-calendar-secret")

class EmailItem(BaseModel):
    id: str
    from_: str
    subject: str
    category: str
    confidence: float
    status: str
    receivedAt: str
    priority: Optional[str] = None
    hasAttachments: bool = False
    patientInfo: Optional[Dict[str, Any]] = None

class EmailDetail(BaseModel):
    id: str
    rawText: str
    extracted: Dict[str, Any]
    draft: Dict[str, Any]
    risk: Dict[str, Any]

class EmailStatsSummary(BaseModel):
    todayReceived: int
    autoAnswered: int
    avgResponseMinutes: float
    openDrafts: int
    llmClassificationsWeek: int
    calendarCreatedToday: int
    gdprCompliance: str

class IntentDistribution(BaseModel):
    buckets: List[Dict[str, Any]]

class TimeseriesPoint(BaseModel):
    ts: str
    avgResponseMinutes: float

class TimeseriesData(BaseModel):
    points: List[TimeseriesPoint]

class AgentItem(BaseModel):
    id: int
    name: str
    status: str
    description: str
    requests: int
    accuracy: int

class TemplateItem(BaseModel):
    id: int
    name: str
    category: str
    variables: List[str]
    version: str
    active: bool

class SystemStatus(BaseModel):
    emailConnector: Dict[str, Any]
    calendar: Dict[str, Any]
    llm: Dict[str, Any]
    license: Dict[str, Any]

class ProfileSettings(BaseModel):
    name: str
    address: str
    phone: str

class GuardrailsSettings(BaseModel):
    confidenceThreshold: float
    autoSend: bool
    piiDetection: bool

class EmailIntegration(BaseModel):
    gmail: Dict[str, bool]
    microsoft: Dict[str, bool]
    imap: Dict[str, bool]

class LicenseInfo(BaseModel):
    status: str
    tier: str
    validUntil: str

class VoiceTranscript(BaseModel):
    transcript: str


# ============================================
# SYSTEM FUNCTIONS
# ============================================

def set_enterprise_system(system):
    """Setzt Referenz zum Enterprise System"""
    global _enterprise_system
    _enterprise_system = system
    logger.info("Enterprise System für API registriert")


def _get_system_status() -> SystemStatus:
    """System-Status nach Lovable-Spezifikation"""
    return SystemStatus(
        emailConnector={
            "status": "online",
            "connectedAccounts": 1
        },
        calendar={
            "status": "online",
            "providers": ["google"],
            "connected": 1
        },
        llm={
            "status": "online",
            "cpuLoad": 0.65
        },
        license={
            "status": "valid",
            "tier": "pro",
            "expiresAt": "2024-12-31"
        }
    )


def _get_email_stats() -> Dict[str, Any]:
    """E-Mail Statistiken"""
    try:
        conn = sqlite3.connect("conversations.db")
        cursor = conn.cursor()

        # Heute verarbeitet
        today = datetime.now().date().isoformat()
        cursor.execute(
            "SELECT COUNT(*) FROM conversations WHERE DATE(timestamp) = ?",
            (today,)
        )
        today_received = cursor.fetchone()[0]

        # Letzte 7 Tage
        week_ago = (datetime.now() - timedelta(days=7)).isoformat()
        cursor.execute(
            "SELECT COUNT(*) FROM conversations WHERE timestamp > ?",
            (week_ago,)
        )
        week_total = cursor.fetchone()[0]

        conn.close()

        return EmailStatsSummary(
            todayReceived=today_received,
            autoAnswered=int(today_received * 0.8),
            avgResponseMinutes=2.3,
            openDrafts=0,
            llmClassificationsWeek=week_total,
            calendarCreatedToday=int(today_received * 0.7),
            gdprCompliance="100%"
        ).dict()
    except Exception as e:
        logger.error(f"Email Stats Fehler: {e}")
        return {"error": str(e)}


def _get_recent_emails(limit: int = 10) -> Dict[str, List[EmailItem]]:
    """Letzte E-Mails"""
    try:
        conn = sqlite3.connect("conversations.db")
        cursor = conn.cursor()

        cursor.execute("""
            SELECT conversation_id, email_address, subject, intent_type, confidence, timestamp
            FROM conversations
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))

        emails = []
        for row in cursor.fetchall():
            emails.append(EmailItem(
                id=row[0],
                from_=row[1],
                subject=row[2],
                category=row[3],
                confidence=row[4],
                status="auto-sent",
                receivedAt=row[5],
                hasAttachments=False,
                patientInfo={"name": "Patient", "birthDate": "1990-01-01"}
            ))

        conn.close()
        return {"items": [email.dict() for email in emails]}
    except Exception as e:
        logger.error(f"Recent Emails Fehler: {e}")
        return {"items": [], "error": str(e)}


def _get_intent_distribution() -> IntentDistribution:
    """Intent-Verteilung"""
    try:
        conn = sqlite3.connect("conversations.db")
        cursor = conn.cursor()

        cursor.execute("""
            SELECT intent_type, COUNT(*) as count
            FROM conversations
            WHERE timestamp > ?
            GROUP BY intent_type
        """, ((datetime.now() - timedelta(days=7)).isoformat(),))

        results = cursor.fetchall()
        conn.close()

        total = sum(count for _, count in results)
        buckets = []

        for intent, count in results:
            percentage = (count / total * 100) if total > 0 else 0
            buckets.append({
                "intent": intent,
                "percentage": round(percentage, 1)
            })

        return IntentDistribution(buckets=buckets)
    except Exception as e:
        logger.error(f"Intent Distribution Fehler: {e}")
        return IntentDistribution(buckets=[])


def _get_timeseries_data(bucket: str = "hour", range_days: int = 7) -> TimeseriesData:
    """Zeitreihen-Daten"""
    try:
        points = []
        start_date = datetime.now() - timedelta(days=range_days)

        for i in range(range_days * (24 if bucket == "hour" else 1)):
            if bucket == "hour":
                point_date = start_date + timedelta(hours=i)
            else:
                point_date = start_date + timedelta(days=i)
            points.append(TimeseriesPoint(
                ts=point_date.isoformat(),
                avgResponseMinutes=round(2.0 + (i * 0.1), 1)
            ))

        return TimeseriesData(points=points)
    except Exception as e:
        logger.error(f"Timeseries Fehler: {e}")
        return TimeseriesData(points=[])


def _format_uptime(uptime: timedelta) -> str:
    """Formatiert Uptime"""
    seconds = int(uptime.total_seconds())
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    if days > 0:
        return f"{days}d {hours}h {minutes}m"
    elif hours > 0:
        return f"{hours}h {minutes}m"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"


# ============================================
# API ENDPOINTS (nach Lovable-Spezifikation)
# ============================================

@app.get("/")
async def root():
    """Root Endpoint - API Info"""
    uptime = datetime.now() - _system_start_time
    return {
        "name": "MFA Enterprise Dashboard API",
        "version": "2.0.0",
        "status": "running",
        "uptime": _format_uptime(uptime),
        "endpoints": {
            "health": "/api/health",
            "system": "/api/system/status",
            "emails": "/api/emails",
            "stats": "/api/emails/stats/summary",
            "timeseries": "/api/emails/stats/timeseries",
            "intents": "/api/intents/distribution"
        }
    }


@app.get("/api/health")
async def health_check():
    """Health Check"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/api/system/status")
async def system_status():
    """System Status"""
    return _get_system_status().dict()


@app.get("/api/emails/recent")
async def recent_emails(limit: int = Query(10, ge=1, le=100)):
    """Letzte E-Mails"""
    return _get_recent_emails(limit)


@app.get("/api/emails/{email_id}")
async def email_detail(email_id: str = PathParam(...)):
    """Einzelne E-Mail Details"""
    try:
        conn = sqlite3.connect("conversations.db")
        cursor = conn.cursor()

        cursor.execute("""
            SELECT conversation_id, email_address, subject, incoming_message, intent_type, confidence, timestamp
            FROM conversations
            WHERE conversation_id = ?
        """, (email_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            raise HTTPException(status_code=404, detail="E-Mail nicht gefunden")

        return EmailDetail(
            id=row[0],
            rawText=row[3],
            extracted={
                "patient_name": "Patient Name",
                "appointment_type": row[4]
            },
            draft={
                "content": "Sehr geehrte/r {patient_name}, ...",
                "placeholders": ["patient_name", "appointment_date"]
            },
            risk={
                "isHighRisk": False,
                "reasons": []
            }
        ).dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/emails")
async def list_emails(
    status: str = Query(None),
    category: str = Query(None),
    q: str = Query(None),
    page: int = Query(1, ge=1),
    pageSize: int = Query(25, ge=1, le=100)
):
    """E-Mail Liste mit Filter & Pagination"""
    try:
        conn = sqlite3.connect("conversations.db")
        cursor = conn.cursor()

        # Basis-Query
        query = """
            SELECT conversation_id, email_address, subject, intent_type, confidence, timestamp
            FROM conversations
            WHERE 1=1
        """
        params = []

        # Filter hinzufügen
        if status:
            query += " AND status = ?"
            params.append(status)

        if category:
            query += " AND intent_type = ?"
            params.append(category)

        if q:
            query += " AND (subject LIKE ? OR incoming_message LIKE ?)"
            params.extend([f"%{q}%", f"%{q}%"])

        # Pagination
        offset = (page - 1) * pageSize
        query += f" ORDER BY timestamp DESC LIMIT {pageSize} OFFSET {offset}"

        cursor.execute(query, params)
        results = cursor.fetchall()

        # Gesamt-Anzahl für Pagination
        count_query = query.replace(f" ORDER BY timestamp DESC LIMIT {pageSize} OFFSET {offset}", "")
        cursor.execute(count_query, params)
        total = cursor.fetchone()[0]

        conn.close()

        emails = []
        for row in results:
            emails.append(EmailItem(
                id=row[0],
                from_=row[1],
                subject=row[2],
                category=row[3],
                confidence=row[4],
                status="auto-sent",
                receivedAt=row[5]
            ).dict())

        return {
            "items": emails,
            "page": page,
            "pageSize": pageSize,
            "total": total
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/emails/{email_id}/actions/send")
async def send_email_action(email_id: str = PathParam(...)):
    """E-Mail senden"""
    return {"status": "sent", "email_id": email_id}


@app.post("/api/emails/{email_id}/actions/escalate")
async def escalate_email(email_id: str = PathParam(...)):
    """E-Mail eskalieren"""
    return {"status": "escalated", "email_id": email_id}


@app.post("/api/emails/{email_id}/actions/archive")
async def archive_email(email_id: str = PathParam(...)):
    """E-Mail archivieren"""
    return {"status": "archived", "email_id": email_id}


@app.get("/api/emails/stats/summary")
async def email_stats_summary(range_days: str = Query("7d", regex="^(24h|7d|30d)$")):
    """E-Mail Statistiken Summary"""
    return _get_email_stats()


@app.get("/api/emails/stats/timeseries")
async def email_stats_timeseries(
    bucket: str = Query("hour", regex="^(hour|day)$"),
    range_days: str = Query("7d", regex="^(24h|7d|30d)$")
):
    """Zeitreihen-Daten für Charts"""
    return _get_timeseries_data(bucket, int(range_days[:-1])).dict()


@app.get("/api/intents/distribution")
async def intents_distribution(range_days: str = Query("7d", regex="^(7d|30d)$")):
    """Intent-Verteilung"""
    return _get_intent_distribution().dict()


@app.get("/api/agents")
async def list_agents():
    """Agenten-Liste"""
    agents = [
        AgentItem(
            id=1,
            name="E-Mail Klassifikator",
            status="online",
            description="Ollama (Qwen 2.5 3B)",
            requests=1247,
            accuracy=92
        )
    ]
    return {"items": [agent.dict() for agent in agents]}


@app.get("/api/templates")
async def list_templates():
    """Templates-Liste"""
    templates = [
        TemplateItem(
            id=1,
            name="Terminbestätigung",
            category="Termin",
            variables=["patient_name", "appointment_date", "appointment_time"],
            version="2.1",
            active=True
        )
    ]
    return {"items": [template.dict() for template in templates]}


@app.get("/api/settings/profile")
async def get_profile():
    """Profile-Settings"""
    return ProfileSettings(
        name="Praxis Dr. Müller",
        address="Hauptstraße 123, 10115 Berlin",
        phone="+49 30 12345678"
    ).dict()


@app.put("/api/settings/profile")
async def update_profile(settings: ProfileSettings):
    """Profile-Settings aktualisieren"""
    return {"status": "updated"}


@app.get("/api/settings/guardrails")
async def get_guardrails():
    """Guardrails-Settings"""
    return GuardrailsSettings(
        confidenceThreshold=0.75,
        autoSend=True,
        piiDetection=True
    ).dict()


@app.put("/api/settings/guardrails")
async def update_guardrails(settings: GuardrailsSettings):
    """Guardrails-Settings aktualisieren"""
    return {"status": "updated"}


@app.get("/api/integrations/email")
async def get_email_integrations():
    """E-Mail-Integrationen"""
    return EmailIntegration(
        gmail={"connected": True},
        microsoft={"connected": False},
        imap={"configured": False}
    ).dict()


@app.post("/api/integrations/email")
async def update_email_integrations(integration: EmailIntegration):
    """E-Mail-Integrationen aktualisieren"""
    return {"status": "updated"}


@app.get("/api/license")
async def get_license():
    """Lizenz-Info"""
    return LicenseInfo(
        status="active",
        tier="pro",
        validUntil="2024-12-31"
    ).dict()


@app.post("/api/voice/transcribe")
async def transcribe_voice():
    """Voice Transcription (Mock)"""
    return VoiceTranscript(
        transcript="Bitte um Rückruf bezüglich Terminverschiebung."
    ).dict()


# ============================================
# SERVER STARTEN
# ============================================

def start_api_server(host: str = "0.0.0.0", port: int = 5000, enterprise_system=None):
    """Startet FastAPI Server in eigenem Thread"""
    if enterprise_system:
        set_enterprise_system(enterprise_system)

    def run_server():
        logger.info(f"🚀 Dashboard API startet auf http://{host}:{port}")
        logger.info("📊 Dashboard kann verbinden zu: http://localhost:5000/api/stats")
        logger.info("📚 API Docs: http://localhost:5000/docs")
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="info",
            access_log=False  # Reduziert Log-Spam
        )

    api_thread = threading.Thread(target=run_server, daemon=True)
    api_thread.start()
    logger.info("✅ Dashboard API-Thread gestartet")

    return api_thread


# ============================================
# SYSTEM FUNCTIONS (Duplicate cleanup)
# ============================================

def set_enterprise_system(system):
    """Setzt Referenz zum Enterprise System"""
    global _enterprise_system
    _enterprise_system = system
    logger.info("Enterprise System für API registriert")


def _get_system_status() -> Dict[str, Any]:
    """System-Status"""
    if not _enterprise_system:
        return {
            "status": "initializing",
            "uptime": "0s",
            "idle_mode_active": False
        }
    
    try:
        agent = _enterprise_system.email_agent
        uptime = datetime.now() - getattr(_enterprise_system, 'start_time', datetime.now())
        
        return {
            "status": "running",
            "uptime_seconds": int(uptime.total_seconds()),
            "uptime_formatted": _format_uptime(uptime),
            "idle_mode_active": agent.idle_running if hasattr(agent, 'idle_running') else False,
            "ollama_connected": True,  # TODO: Echten Status prüfen
            "imap_connected": agent.imap_connection is not None,
            "smtp_connected": agent.smtp_connection is not None
        }
    except Exception as e:
        logger.error(f"System Status Fehler: {e}")
        return {"status": "error", "error": str(e)}


def _get_email_stats() -> Dict[str, Any]:
    """E-Mail Statistiken aus DB"""
    try:
        conn = sqlite3.connect("conversations.db")
        cursor = conn.cursor()
        
        # Gesamt verarbeitet
        cursor.execute("SELECT COUNT(*) FROM conversations")
        total = cursor.fetchone()[0]
        
        # Heute verarbeitet
        today = datetime.now().date().isoformat()
        cursor.execute(
            "SELECT COUNT(*) FROM conversations WHERE DATE(timestamp) = ?",
            (today,)
        )
        today_count = cursor.fetchone()[0]
        
        # Letzte 24h
        yesterday = (datetime.now() - timedelta(days=1)).isoformat()
        cursor.execute(
            "SELECT COUNT(*) FROM conversations WHERE timestamp > ?",
            (yesterday,)
        )
        last_24h = cursor.fetchone()[0]
        
        # Durchschnittliche Response-Zeit (Mock - müsste getracked werden)
        avg_response_time = 6.2  # Sekunden
        
        conn.close()
        
        return {
            "total_processed": total,
            "processed_today": today_count,
            "processed_last_24h": last_24h,
            "pending_queue": 0,  # TODO: Aus Email Queue holen
            "failed_count": 0,   # TODO: Aus Error DB holen
            "avg_response_time_seconds": avg_response_time,
            "success_rate_percent": 98.5  # TODO: Berechnen
        }
    except Exception as e:
        logger.error(f"Email Stats Fehler: {e}")
        return {
            "total_processed": 0,
            "processed_today": 0,
            "error": str(e)
        }


def _get_intent_distribution() -> Dict[str, int]:
    """Intent-Verteilung"""
    try:
        conn = sqlite3.connect("conversations.db")
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT intent_type, COUNT(*) as count
            FROM conversations
            GROUP BY intent_type
            ORDER BY count DESC
        """)
        
        results = cursor.fetchall()
        conn.close()
        
        distribution = {intent: count for intent, count in results}
        return distribution
    except Exception as e:
        logger.error(f"Intent Distribution Fehler: {e}")
        return {"error": str(e)}


def _get_performance_metrics() -> Dict[str, Any]:
    """Performance-Metriken"""
    try:
        # TODO: Echte Metrics von Performance Cache holen
        return {
            "ollama_avg_latency_ms": 4200,
            "ollama_requests_total": 142,
            "imap_connections_today": 456,
            "cache_hit_rate_percent": 67.3,
            "memory_usage_mb": 245,  # TODO: Echte Memory Usage
            "cpu_usage_percent": 12.5  # TODO: Echte CPU Usage
        }
    except Exception as e:
        logger.error(f"Performance Metrics Fehler: {e}")
        return {"error": str(e)}


def _get_realtime_activity() -> Dict[str, Any]:
    """Echtzeit-Aktivität"""
    try:
        conn = sqlite3.connect("conversations.db")
        cursor = conn.cursor()
        
        # Letzte verarbeitete E-Mail
        cursor.execute("""
            SELECT timestamp, subject, intent_type
            FROM conversations
            ORDER BY timestamp DESC
            LIMIT 1
        """)
        
        last_email = cursor.fetchone()
        conn.close()
        
        if last_email:
            return {
                "last_email_processed": last_email[0],
                "last_email_subject": last_email[1],
                "last_email_intent": last_email[2],
                "current_activity": "idle" if not last_email else "processing"
            }
        else:
            return {
                "last_email_processed": None,
                "current_activity": "waiting"
            }
    except Exception as e:
        logger.error(f"Realtime Activity Fehler: {e}")
        return {"error": str(e)}


def _format_uptime(uptime: timedelta) -> str:
    """Formatiert Uptime"""
    seconds = int(uptime.total_seconds())
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    if days > 0:
        return f"{days}d {hours}h {minutes}m"
    elif hours > 0:
        return f"{hours}h {minutes}m"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"


# ============================================
# API ENDPOINTS
# ============================================

@app.get("/")
async def root():
    """Root Endpoint - API Info"""
    return {
        "name": "MFA Enterprise KI-Agent API",
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs",
        "endpoints": {
            "stats": "/api/stats",
            "health": "/api/health",
            "emails": "/api/emails",
            "intents": "/api/intents",
            "performance": "/api/performance",
            "websocket": "/ws"
        }
    }


@app.get("/api/health")
async def health_check():
    """Health Check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "system_running": _enterprise_system is not None
    }


@app.get("/api/stats")
async def get_stats():
    """Alle System-Statistiken (Haupt-Endpoint)"""
    return JSONResponse(content={
        "timestamp": datetime.now().isoformat(),
        "system": _get_system_status(),
        "emails": _get_email_stats(),
        "intents": _get_intent_distribution(),
        "performance": _get_performance_metrics(),
        "activity": _get_realtime_activity()
    })


@app.get("/api/emails")
async def get_emails():
    """Nur E-Mail Statistiken"""
    return JSONResponse(content={
        "timestamp": datetime.now().isoformat(),
        "emails": _get_email_stats()
    })


@app.get("/api/intents")
async def get_intents():
    """Intent-Verteilung"""
    return JSONResponse(content={
        "timestamp": datetime.now().isoformat(),
        "intents": _get_intent_distribution()
    })


@app.get("/api/performance")
async def get_performance():
    """Performance-Metriken"""
    return JSONResponse(content={
        "timestamp": datetime.now().isoformat(),
        "performance": _get_performance_metrics()
    })


@app.get("/api/emails/recent")
async def get_recent_emails(limit: int = 10):
    """Letzte verarbeitete E-Mails"""
    try:
        conn = sqlite3.connect("conversations.db")
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT timestamp, email_address, subject, intent_type, confidence
            FROM conversations
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        
        emails = []
        for row in cursor.fetchall():
            emails.append({
                "timestamp": row[0],
                "sender": row[1],
                "subject": row[2],
                "intent": row[3],
                "confidence": row[4]
            })
        
        conn.close()
        return JSONResponse(content={"emails": emails})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/api/system/config")
async def get_config():
    """System-Konfiguration (ohne Secrets!)"""
    from core.config import Config
    
    return {
        "idle_enabled": Config.ENABLE_IMAP_IDLE,
        "check_interval": Config.CHECK_INTERVAL_SECONDS,
        "ollama_model": Config.OLLAMA_MODEL,
        "practice_name": Config.PRACTICE_NAME
    }


# ============================================
# WEBSOCKET für Live-Updates
# ============================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket für Echtzeit-Updates"""
    await websocket.accept()
    _active_websockets.append(websocket)
    logger.info("WebSocket Client verbunden")
    
    try:
        while True:
            # Sende Updates alle 2 Sekunden
            stats = {
                "timestamp": datetime.now().isoformat(),
                "system": _get_system_status(),
                "emails": _get_email_stats(),
                "intents": _get_intent_distribution(),
                "performance": _get_performance_metrics(),
                "activity": _get_realtime_activity()
            }
            await websocket.send_json(stats)
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        _active_websockets.remove(websocket)
        logger.info("WebSocket Client getrennt")
    except Exception as e:
        logger.error(f"WebSocket Fehler: {e}")
        if websocket in _active_websockets:
            _active_websockets.remove(websocket)


async def broadcast_update(data: Dict[str, Any]):
    """Sendet Update an alle verbundenen Clients"""
    for websocket in _active_websockets:
        try:
            await websocket.send_json(data)
        except Exception as e:
            logger.error(f"Broadcast Fehler: {e}")


# ============================================
# AGENT-STEUERUNG ENDPOINTS
# ============================================

@app.post("/api/agent/start")
async def start_agent_endpoint():
    """Startet den E-Mail-Agenten"""
    try:
        global _enterprise_system
        
        if _enterprise_system and hasattr(_enterprise_system, 'email_agent'):
            # Starte IMAP IDLE wenn nicht schon läuft
            if not _enterprise_system.email_agent.idle_running:
                _enterprise_system.email_agent.start_idle_mode(
                    lambda: _enterprise_system.email_agent.process_emails()
                )
                
                logger.info("✅ Agent gestartet via API")
                
                return JSONResponse(content={
                    "success": True,
                    "message": "E-Mail Agent gestartet",
                    "idle_mode": True,
                    "timestamp": datetime.now().isoformat()
                })
            else:
                return JSONResponse(content={
                    "success": False,
                    "message": "Agent läuft bereits",
                    "idle_mode": True
                }, status_code=400)
        else:
            return JSONResponse(content={
                "success": False,
                "message": "Enterprise System nicht verfügbar"
            }, status_code=503)
            
    except Exception as e:
        logger.error(f"Fehler beim Agent-Start: {e}")
        return JSONResponse(content={
            "success": False,
            "message": f"Fehler: {str(e)}"
        }, status_code=500)


@app.post("/api/agent/stop")
async def stop_agent_endpoint():
    """Stoppt den E-Mail-Agenten"""
    try:
        global _enterprise_system
        
        if _enterprise_system and hasattr(_enterprise_system, 'email_agent'):
            if _enterprise_system.email_agent.idle_running:
                _enterprise_system.email_agent.stop_idle_mode()
                
                logger.info("⏸️ Agent gestoppt via API")
                
                return JSONResponse(content={
                    "success": True,
                    "message": "E-Mail Agent gestoppt",
                    "idle_mode": False,
                    "timestamp": datetime.now().isoformat()
                })
            else:
                return JSONResponse(content={
                    "success": False,
                    "message": "Agent läuft nicht"
                }, status_code=400)
        else:
            return JSONResponse(content={
                "success": False,
                "message": "Enterprise System nicht verfügbar"
            }, status_code=503)
            
    except Exception as e:
        logger.error(f"Fehler beim Agent-Stop: {e}")
        return JSONResponse(content={
            "success": False,
            "message": f"Fehler: {str(e)}"
        }, status_code=500)


@app.post("/api/agent/restart")
async def restart_agent_endpoint():
    """Startet den E-Mail-Agenten neu"""
    try:
        # Stoppe zuerst
        await stop_agent_endpoint()
        
        # Warte kurz
        import asyncio
        await asyncio.sleep(2)
        
        # Starte wieder
        result = await start_agent_endpoint()
        
        logger.info("🔄 Agent neu gestartet via API")
        return result
        
    except Exception as e:
        logger.error(f"Fehler beim Agent-Restart: {e}")
        return JSONResponse(content={
            "success": False,
            "message": f"Fehler: {str(e)}"
        }, status_code=500)


# ============================================
# E-MAIL MANAGEMENT ENDPOINTS
# ============================================

@app.get("/api/emails/{email_id}")
async def get_email_detail(email_id: str = PathParam(..., description="E-Mail ID")):
    """Holt Details einer einzelnen E-Mail"""
    try:
        # Hole E-Mail aus conversations.db
        with sqlite3.connect("conversations.db") as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT thread_id, subject, sender, recipient, body, ai_response, 
                       created_at, message_id
                FROM conversations
                WHERE message_id = ? OR thread_id = ?
                LIMIT 1
            ''', (email_id, email_id))
            
            row = cursor.fetchone()
            
            if not row:
                raise HTTPException(status_code=404, detail="E-Mail nicht gefunden")
            
            return JSONResponse(content={
                "id": row[0],
                "subject": row[1],
                "from": row[2],
                "to": row[3],
                "body": row[4],
                "response": row[5],
                "timestamp": row[6],
                "message_id": row[7]
            })
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Fehler beim E-Mail-Abruf: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/emails/{email_id}")
async def update_email(
    email_id: str = PathParam(..., description="E-Mail ID"),
    updates: Dict[str, Any] = None
):
    """Aktualisiert eine E-Mail"""
    try:
        if not updates:
            raise HTTPException(status_code=400, detail="Keine Updates angegeben")
        
        # Aktualisiere in DB
        with sqlite3.connect("conversations.db") as conn:
            cursor = conn.cursor()
            
            # Baue UPDATE-Statement dynamisch
            set_clauses = []
            values = []
            
            if 'status' in updates:
                set_clauses.append("status = ?")
                values.append(updates['status'])
            
            if 'ai_response' in updates:
                set_clauses.append("ai_response = ?")
                values.append(updates['ai_response'])
            
            if not set_clauses:
                raise HTTPException(status_code=400, detail="Keine aktualisierbaren Felder")
            
            values.append(email_id)
            
            cursor.execute(f'''
                UPDATE conversations
                SET {', '.join(set_clauses)}
                WHERE message_id = ? OR thread_id = ?
            ''', values + [email_id])
            
            conn.commit()
            
            return JSONResponse(content={
                "success": True,
                "message": "E-Mail aktualisiert",
                "updated_fields": list(updates.keys())
            })
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Fehler beim E-Mail-Update: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/emails/{email_id}")
async def delete_email(email_id: str = PathParam(..., description="E-Mail ID")):
    """Löscht eine E-Mail"""
    try:
        with sqlite3.connect("conversations.db") as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM conversations
                WHERE message_id = ? OR thread_id = ?
            ''', (email_id, email_id))
            
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="E-Mail nicht gefunden")
            
            conn.commit()
            
            return JSONResponse(content={
                "success": True,
                "message": "E-Mail gelöscht"
            })
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Fehler beim E-Mail-Löschen: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# TEMPLATE MANAGEMENT ENDPOINTS
# ============================================

class Template(BaseModel):
    id: Optional[int] = None
    name: str
    category: str
    subject: str
    body: str
    variables: List[str] = []
    active: bool = True


@app.get("/api/templates")
async def get_templates():
    """Holt alle E-Mail-Templates"""
    try:
        with sqlite3.connect("conversations.db") as conn:
            cursor = conn.cursor()
            
            # Erstelle Templates-Tabelle falls nicht vorhanden
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS email_templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    body TEXT NOT NULL,
                    variables TEXT,
                    active BOOLEAN DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                SELECT id, name, category, subject, body, variables, active
                FROM email_templates
                WHERE active = 1
                ORDER BY category, name
            ''')
            
            templates = []
            for row in cursor.fetchall():
                import json
                variables = json.loads(row[5]) if row[5] else []
                templates.append({
                    "id": row[0],
                    "name": row[1],
                    "category": row[2],
                    "subject": row[3],
                    "body": row[4],
                    "variables": variables,
                    "active": bool(row[6])
                })
            
            return JSONResponse(content={"templates": templates})
            
    except Exception as e:
        logger.error(f"Fehler beim Template-Abruf: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/templates")
async def create_template(template: Template):
    """Erstellt ein neues Template"""
    try:
        import json
        
        with sqlite3.connect("conversations.db") as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO email_templates (name, category, subject, body, variables, active)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                template.name,
                template.category,
                template.subject,
                template.body,
                json.dumps(template.variables),
                template.active
            ))
            
            template_id = cursor.lastrowid
            conn.commit()
            
            return JSONResponse(content={
                "success": True,
                "message": "Template erstellt",
                "id": template_id
            })
            
    except Exception as e:
        logger.error(f"Fehler beim Template-Erstellen: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/templates/{template_id}")
async def update_template(
    template_id: int = PathParam(..., description="Template ID"),
    template: Template = None
):
    """Aktualisiert ein Template"""
    try:
        import json
        
        with sqlite3.connect("conversations.db") as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE email_templates
                SET name = ?, category = ?, subject = ?, body = ?, 
                    variables = ?, active = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (
                template.name,
                template.category,
                template.subject,
                template.body,
                json.dumps(template.variables),
                template.active,
                template_id
            ))
            
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Template nicht gefunden")
            
            conn.commit()
            
            return JSONResponse(content={
                "success": True,
                "message": "Template aktualisiert"
            })
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Fehler beim Template-Update: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/templates/{template_id}")
async def delete_template(template_id: int = PathParam(..., description="Template ID")):
    """Löscht ein Template (Soft-Delete)"""
    try:
        with sqlite3.connect("conversations.db") as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE email_templates
                SET active = 0, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (template_id,))
            
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Template nicht gefunden")
            
            conn.commit()
            
            return JSONResponse(content={
                "success": True,
                "message": "Template gelöscht"
            })
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Fehler beim Template-Löschen: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# SETTINGS ENDPOINTS
# ============================================

class SystemSettings(BaseModel):
    check_interval: int = 60
    max_emails_per_cycle: int = 50
    auto_add_booking_link: bool = True
    imap_idle_enabled: bool = True
    practice_name: str = "Ihre Praxis"
    practice_email: str = ""
    practice_phone: str = ""
    online_booking_url: str = ""


@app.get("/api/settings")
async def get_settings():
    """Holt System-Einstellungen"""
    try:
        from core.config import Config
        
        return JSONResponse(content={
            "check_interval": Config.CHECK_INTERVAL_SECONDS,
            "max_emails_per_cycle": Config.MAX_EMAILS_PER_CYCLE,
            "auto_add_booking_link": Config.AUTO_ADD_BOOKING_LINK,
            "imap_idle_enabled": Config.ENABLE_IMAP_IDLE,
            "practice_name": Config.PRACTICE_NAME,
            "practice_email": Config.EMAIL_ADDRESS,
            "practice_phone": getattr(Config, 'PRACTICE_PHONE', ''),
            "online_booking_url": Config.ONLINE_BOOKING_URL,
        })
        
    except Exception as e:
        logger.error(f"Fehler beim Settings-Abruf: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/settings")
async def update_settings(settings: SystemSettings):
    """Aktualisiert System-Einstellungen"""
    try:
        # WICHTIG: In Produktion sollten Settings in Datenbank gespeichert werden
        # und beim Start geladen werden. Hier nur als Beispiel.
        
        from core.config import Config
        
        # Aktualisiere Config (nur für aktuelle Session)
        if settings.check_interval:
            Config.CHECK_INTERVAL_SECONDS = settings.check_interval
        if settings.max_emails_per_cycle:
            Config.MAX_EMAILS_PER_CYCLE = settings.max_emails_per_cycle
        if settings.practice_name:
            Config.PRACTICE_NAME = settings.practice_name
        
        logger.info("⚙️ Einstellungen aktualisiert via API")
        
        return JSONResponse(content={
            "success": True,
            "message": "Einstellungen aktualisiert",
            "note": "Einstellungen sind nur für aktuelle Session aktiv. Für dauerhafte Änderungen .env bearbeiten."
        })
        
    except Exception as e:
        logger.error(f"Fehler beim Settings-Update: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# WHISPER STT ENDPOINTS (Voice-to-Text)
# ============================================

from fastapi import UploadFile, File

@app.post("/api/whisper/transcribe")
async def transcribe_audio(
    audio: UploadFile = File(...),
    language: str = Query("de", description="Sprache (de, en, etc.)")
):
    """
    Transkribiert Audio zu Text mit Whisper
    Nutzt DirectML GPU-Beschleunigung (AMD RX 7800 XT)
    """
    try:
        from services.whisper_service import get_whisper_service
        import tempfile
        
        # Whisper-Service holen
        whisper = get_whisper_service()
        
        if not whisper.is_available():
            raise HTTPException(
                status_code=503, 
                detail="Whisper-Service nicht verfügbar"
            )
        
        # Audio temporär speichern
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            content = await audio.read()
            temp_file.write(content)
            temp_path = temp_file.name
        
        try:
            # Transkribiere
            result = whisper.transcribe(temp_path, language)
            
            return JSONResponse(content={
                "success": True,
                "text": result.text,
                "language": result.language,
                "confidence": result.confidence,
                "duration": result.duration,
                "segments": result.segments[:10],  # Nur erste 10 Segmente
                "device": whisper.get_info()["device"],
                "gpu_accelerated": whisper.get_info()["gpu_accelerated"]
            })
            
        finally:
            # Lösche temporäre Datei
            try:
                os.unlink(temp_path)
            except:
                pass
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Whisper-Transkription fehlgeschlagen: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/whisper/status")
async def whisper_status():
    """Gibt Whisper-Service-Status zurück"""
    try:
        from services.whisper_service import get_whisper_service
        
        whisper = get_whisper_service()
        info = whisper.get_info()
        
        return JSONResponse(content={
            "available": info["available"],
            "model": info["model"],
            "device": info["device"],
            "gpu_accelerated": info["gpu_accelerated"],
            "ready": True
        })
        
    except Exception as e:
        return JSONResponse(content={
            "available": False,
            "error": str(e),
            "ready": False
        }, status_code=503)


# ============================================
# KALENDER-API ENDPOINTS
# ============================================

async def _get_calendar_data(endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
    """Hilfsfunktion für Kalender-API Aufrufe"""
    try:
        url = f"{CALENDAR_API_BASE}/{endpoint}"
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Kalender-API Fehler ({endpoint}): {e}")
        raise HTTPException(status_code=503, detail=f"Kalender-Service nicht verfügbar: {str(e)}")

async def _post_calendar_data(endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Hilfsfunktion für Kalender-API POST Aufrufe"""
    try:
        url = f"{CALENDAR_API_BASE}/{endpoint}"
        response = requests.post(url, json=data, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Kalender-API POST Fehler ({endpoint}): {e}")
        raise HTTPException(status_code=503, detail=f"Kalender-Service nicht verfügbar: {str(e)}")

async def _put_calendar_data(endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Hilfsfunktion für Kalender-API PUT Aufrufe"""
    try:
        url = f"{CALENDAR_API_BASE}/{endpoint}"
        response = requests.put(url, json=data, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Kalender-API PUT Fehler ({endpoint}): {e}")
        raise HTTPException(status_code=503, detail=f"Kalender-Service nicht verfügbar: {str(e)}")

async def _delete_calendar_data(endpoint: str) -> Dict[str, Any]:
    """Hilfsfunktion für Kalender-API DELETE Aufrufe"""
    try:
        url = f"{CALENDAR_API_BASE}/{endpoint}"
        response = requests.delete(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Kalender-API DELETE Fehler ({endpoint}): {e}")
        raise HTTPException(status_code=503, detail=f"Kalender-Service nicht verfügbar: {str(e)}")

# ==================== KALENDER ENDPOINTS ====================

@app.get("/api/calendar/appointments")
async def get_appointments(
    date: Optional[str] = Query(None, description="Datum filtern (YYYY-MM-DD)"),
    patientId: Optional[str] = Query(None, description="Nach Patient-ID filtern"),
    status: Optional[str] = Query(None, description="Status filtern (confirmed, cancelled, completed)")
):
    """Alle Termine abrufen mit optionalen Filtern"""
    params = {}
    if date:
        params["date"] = date
    if patientId:
        params["patientId"] = patientId
    if status:
        params["status"] = status

    return await _get_calendar_data("appointments", params)

@app.get("/api/calendar/appointments/{appointment_id}")
async def get_appointment(appointment_id: str = PathParam(..., description="Termin-ID")):
    """Einzelnen Termin abrufen"""
    return await _get_calendar_data(f"appointments/{appointment_id}")

@app.post("/api/calendar/appointments")
async def create_appointment(appointment: Appointment):
    """Neuen Termin erstellen"""
    data = appointment.dict(exclude_unset=True)
    result = await _post_calendar_data("appointments", data)

    # Trigger KI-Agent für Bestätigungs-E-Mail (async)
    asyncio.create_task(_send_appointment_confirmation(result))

    return result

@app.put("/api/calendar/appointments/{appointment_id}")
async def update_appointment(
    appointment_id: str = PathParam(..., description="Termin-ID"),
    updates: Dict[str, Any] = None
):
    """Termin aktualisieren"""
    if not updates:
        raise HTTPException(status_code=400, detail="Keine Updates angegeben")

    return await _put_calendar_data(f"appointments/{appointment_id}", updates)

@app.delete("/api/calendar/appointments/{appointment_id}/cancel")
async def cancel_appointment(appointment_id: str = PathParam(..., description="Termin-ID")):
    """Termin stornieren"""
    return await _delete_calendar_data(f"appointments/{appointment_id}/cancel")

@app.get("/api/calendar/availability/{date}")
async def get_availability(date: str = PathParam(..., description="Datum (YYYY-MM-DD)")):
    """Verfügbare Slots für ein Datum abrufen"""
    return await _get_calendar_data(f"availability/{date}")

@app.post("/api/calendar/availability/check")
async def check_availability(availability: CalendarAvailability):
    """Slot-Verfügbarkeit prüfen"""
    return await _post_calendar_data("availability/check", availability.dict())

@app.get("/api/calendar/patients")
async def get_patients():
    """Alle Patienten abrufen"""
    return await _get_calendar_data("patients")

@app.get("/api/calendar/patients/{patient_id}")
async def get_patient(patient_id: str = PathParam(..., description="Patienten-ID")):
    """Patienten abrufen"""
    return await _get_calendar_data(f"patients/{patient_id}")

@app.get("/api/calendar/patients/email/{email}")
async def get_patient_by_email(email: str = PathParam(..., description="Patienten-E-Mail")):
    """Patient per E-Mail finden"""
    return await _get_calendar_data(f"patients/email/{email}")

@app.post("/api/calendar/patients")
async def create_patient(patient: Patient):
    """Neuen Patienten erstellen"""
    return await _post_calendar_data("patients", patient.dict(exclude_unset=True))

@app.put("/api/calendar/patients/{patient_id}")
async def update_patient(
    patient_id: str = PathParam(..., description="Patienten-ID"),
    updates: Dict[str, Any] = None
):
    """Patient aktualisieren"""
    if not updates:
        raise HTTPException(status_code=400, detail="Keine Updates angegeben")

    return await _put_calendar_data(f"patients/{patient_id}", updates)

@app.get("/api/calendar/holidays")
async def get_holidays():
    """Alle Feiertage abrufen"""
    return await _get_calendar_data("holidays")

@app.post("/api/calendar/holidays")
async def create_holiday(holiday: Holiday):
    """Feiertag erstellen (Admin)"""
    return await _post_calendar_data("holidays", holiday.dict(exclude_unset=True))

@app.put("/api/calendar/holidays/{holiday_id}")
async def update_holiday(
    holiday_id: str = PathParam(..., description="Feiertags-ID"),
    updates: Dict[str, Any] = None
):
    """Feiertag aktualisieren (Admin)"""
    if not updates:
        raise HTTPException(status_code=400, detail="Keine Updates angegeben")

    return await _put_calendar_data(f"holidays/{holiday_id}", updates)

@app.delete("/api/calendar/holidays/{holiday_id}")
async def delete_holiday(holiday_id: str = PathParam(..., description="Feiertags-ID")):
    """Feiertag löschen (Admin)"""
    return await _delete_calendar_data(f"holidays/{holiday_id}")

@app.get("/api/calendar/settings")
async def get_calendar_settings():
    """Kalender-Einstellungen abrufen"""
    return await _get_calendar_data("settings")

@app.put("/api/calendar/settings")
async def update_calendar_settings(settings: Dict[str, Any]):
    """Kalender-Einstellungen aktualisieren"""
    return await _put_calendar_data("settings", settings)

# ==================== WEBHOOK ENDPOINT ====================

@app.post("/api/calendar/webhook")
async def calendar_webhook(event: WebhookEvent):
    """Webhook-Endpoint für Kalender-Events"""
    logger.info(f"📅 Kalender-Webhook erhalten: {event.event}")

    try:
        # Event verarbeiten
        if event.event == "booking_created":
            await _handle_booking_created(event.data)
        elif event.event == "booking_cancelled":
            await _handle_booking_cancelled(event.data)
        elif event.event == "booking_updated":
            await _handle_booking_updated(event.data)
        else:
            logger.warning(f"Unbekanntes Kalender-Event: {event.event}")

        return {"status": "ok", "event": event.event}

    except Exception as e:
        logger.error(f"Fehler bei Webhook-Verarbeitung: {e}")
        raise HTTPException(status_code=500, detail="Webhook-Verarbeitung fehlgeschlagen")

# ==================== KALENDER EVENT HANDLER ====================

async def _handle_booking_created(data: Dict[str, Any]):
    """Neue Buchung verarbeiten"""
    logger.info("🎯 Neue Terminbuchung erhalten - sende Bestätigungs-E-Mail")

    appointment = data.get("appointment", {})
    patient = data.get("patient", {})

    if not appointment or not patient:
        logger.error("Unvollständige Buchungsdaten")
        return

    # Bestätigungs-E-Mail über KI-Agent senden
    await _send_appointment_confirmation(appointment, patient)

async def _handle_booking_cancelled(data: Dict[str, Any]):
    """Stornierung verarbeiten"""
    logger.info("❌ Termin storniert - sende Stornierungs-E-Mail")

    appointment = data.get("appointment", {})
    patient = data.get("patient", {})

    if not appointment or not patient:
        logger.error("Unvollständige Stornierungsdaten")
        return

    # Stornierungs-E-Mail senden
    await _send_appointment_cancellation(appointment, patient)

async def _handle_booking_updated(data: Dict[str, Any]):
    """Termin-Änderung verarbeiten"""
    logger.info("📝 Termin geändert - sende Änderungs-E-Mail")

    appointment = data.get("appointment", {})
    changes = data.get("changes", {})
    patient = data.get("patient", {})

    if not appointment or not patient:
        logger.error("Unvollständige Änderungsdaten")
        return

    # Änderungs-E-Mail senden
    await _send_appointment_update(appointment, patient, changes)

# ==================== KI-AGENT EMAIL FUNKTIONEN ====================

async def _send_appointment_confirmation(appointment: Dict[str, Any], patient: Optional[Dict[str, Any]] = None):
    """Bestätigungs-E-Mail für neue Buchung senden"""
    try:
        if not patient and "patient" in appointment:
            patient = appointment["patient"]

        if not patient:
            logger.error("Keine Patientendaten für Bestätigungs-E-Mail")
            return

        # E-Mail-Inhalt erstellen
        subject = f"Terminbestätigung - {appointment.get('reason', 'Termin')}"
        body = f"""
Liebe/r {patient['firstName']} {patient['lastName']},

Ihr Termin wurde erfolgreich gebucht!

📅 Datum: {appointment['date']}
🕐 Uhrzeit: {appointment['startTime']} - {appointment['endTime']}
📋 Grund: {appointment['reason']}
🏥 Status: {appointment['status']}

Bitte erscheinen Sie 15 Minuten vor Ihrem Termin.

Bei Fragen oder Änderungswünschen kontaktieren Sie uns gerne.

Mit freundlichen Grüßen,
Ihre Praxis
        """.strip()

        # KI-Agent für E-Mail-Versand nutzen
        await _send_email_via_agent(patient['email'], subject, body, "calendar_confirmation")

    except Exception as e:
        logger.error(f"Fehler beim Senden der Bestätigungs-E-Mail: {e}")

async def _send_appointment_cancellation(appointment: Dict[str, Any], patient: Dict[str, Any]):
    """Stornierungs-E-Mail senden"""
    try:
        subject = f"Termin storniert - {appointment.get('reason', 'Termin')}"
        body = f"""
Liebe/r {patient['firstName']} {patient['lastName']},

Ihr Termin wurde storniert.

📅 Datum: {appointment['date']}
🕐 Uhrzeit: {appointment['startTime']} - {appointment['endTime']}
📋 Grund: {appointment['reason']}

Falls Sie einen neuen Termin wünschen, können Sie diesen gerne online buchen
oder uns kontaktieren.

Mit freundlichen Grüßen,
Ihre Praxis
        """.strip()

        await _send_email_via_agent(patient['email'], subject, body, "calendar_cancellation")

    except Exception as e:
        logger.error(f"Fehler beim Senden der Stornierungs-E-Mail: {e}")

async def _send_appointment_update(appointment: Dict[str, Any], patient: Dict[str, Any], changes: Dict[str, Any]):
    """Änderungs-E-Mail senden"""
    try:
        subject = f"Terminänderung - {appointment.get('reason', 'Termin')}"
        body = f"""
Liebe/r {patient['firstName']} {patient['lastName']},

Ihr Termin wurde geändert.

📅 Neues Datum: {appointment['date']}
🕐 Neue Uhrzeit: {appointment['startTime']} - {appointment['endTime']}
📋 Grund: {appointment['reason']}
🏥 Status: {appointment['status']}

Änderungen: {', '.join([f"{k}: {v}" for k, v in changes.items()])}

Bitte bestätigen Sie Ihre Teilnahme.

Mit freundlichen Grüßen,
Ihre Praxis
        """.strip()

        await _send_email_via_agent(patient['email'], subject, body, "calendar_update")

    except Exception as e:
        logger.error(f"Fehler beim Senden der Änderungs-E-Mail: {e}")

async def _send_email_via_agent(recipient: str, subject: str, body: str, template_category: str = "calendar"):
    """E-Mail über KI-Agent senden"""
    try:
        if not _enterprise_system:
            logger.warning("Enterprise System nicht verfügbar für E-Mail-Versand")
            return

        # E-Mail über Agent senden
        logger.info(f"📧 Sende {template_category}-E-Mail an {recipient}: {subject}")

        # Verwende die entsprechende Agent-Methode basierend auf template_category
        if template_category == "calendar_confirmation":
            success = _enterprise_system.agent.send_calendar_confirmation_email(recipient, {"patient": {"email": recipient}, "subject": subject, "body": body})
        elif template_category == "calendar_cancellation":
            success = _enterprise_system.agent.send_calendar_cancellation_email(recipient, {"patient": {"email": recipient}, "subject": subject, "body": body})
        elif template_category == "calendar_update":
            success = _enterprise_system.agent.send_calendar_update_email(recipient, {"patient": {"email": recipient}, "subject": subject, "body": body}, {})
        else:
            logger.warning(f"Unbekannte E-Mail-Kategorie: {template_category}")
            return

        if success:
            logger.info(f"✅ {template_category}-E-Mail erfolgreich gesendet")
        else:
            logger.error(f"❌ {template_category}-E-Mail-Versand fehlgeschlagen")

    except Exception as e:
        logger.error(f"Fehler beim E-Mail-Versand über Agent: {e}")

# ============================================
# SERVER STARTEN
# ============================================

def start_api_server(host: str = "0.0.0.0", port: int = 8004, enterprise_system=None):
    """Startet FastAPI Server in eigenem Thread"""
    if enterprise_system:
        set_enterprise_system(enterprise_system)
        # Setze Start-Zeit
        enterprise_system.start_time = datetime.now()

    def run_server():
        logger.info(f"🚀 Dashboard API startet auf http://{host}:{port}")
        logger.info(f"📊 Dashboard kann verbinden zu: http://{host}:{port}/api/stats")
        logger.info(f"📚 API Docs: http://{host}:{port}/docs")
        
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="info",
            access_log=False  # Reduziert Log-Spam
        )
    
    api_thread = threading.Thread(target=run_server, daemon=True)
    api_thread.start()
    logger.info(f"✅ Dashboard API-Thread gestartet")
    
    return api_thread

