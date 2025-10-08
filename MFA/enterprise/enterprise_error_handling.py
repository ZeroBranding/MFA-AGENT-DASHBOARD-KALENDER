#!/usr/bin/env python3
"""
ENTERPRISE ERROR HANDLING SYSTEM
Robuste Fehlerbehandlung mit Recovery, Retry-Logik und Monitoring
Sichert Systemstabilität auch bei kritischen Fehlern
"""

import logging
import traceback
import time
import json
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import functools
import asyncio
from pathlib import Path
import sqlite3
import threading
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """Schweregrad eines Fehlers"""
    LOW = "low"           # Informational, System läuft weiter
    MEDIUM = "medium"     # Funktionalität eingeschränkt, aber behebbar
    HIGH = "high"         # Kritische Funktionalität betroffen
    CRITICAL = "critical" # System nicht funktionsfähig

class ErrorCategory(Enum):
    """Kategorie eines Fehlers"""
    NETWORK = "network"
    DATABASE = "database"
    EMAIL = "email"
    INTENT_CLASSIFICATION = "intent_classification"
    RESPONSE_GENERATION = "response_generation"
    CALENDAR = "calendar"
    EXTERNAL_API = "external_api"
    SYSTEM = "system"
    CONFIGURATION = "configuration"
    AUTHENTICATION = "authentication"

class RecoveryStrategy(Enum):
    """Strategie zur Fehlerbehebung"""
    RETRY = "retry"
    FALLBACK = "fallback"
    ESCALATE = "escalate"
    IGNORE = "ignore"
    RESTART = "restart"
    MANUAL_INTERVENTION = "manual_intervention"

@dataclass
class ErrorContext:
    """Kontext eines Fehlers"""
    error_id: str
    timestamp: datetime
    severity: ErrorSeverity
    category: ErrorCategory
    component: str
    function_name: str
    error_message: str
    stack_trace: str
    context_data: Dict[str, Any]
    user_impact: str
    recovery_strategy: RecoveryStrategy
    retry_count: int = 0
    max_retries: int = 3
    is_resolved: bool = False
    resolution_notes: str = ""

@dataclass
class RecoveryAction:
    """Aktion zur Fehlerbehebung"""
    action_id: str
    error_id: str
    action_type: str
    parameters: Dict[str, Any]
    timestamp: datetime
    success: bool = False
    result: Optional[Any] = None
    error_message: str = ""

class EnterpriseErrorHandler:
    """
    Enterprise-Level Fehlerbehandlungssystem
    Bietet robuste Fehlerbehandlung mit automatischer Recovery
    """
    
    def __init__(self, db_path: str = "error_handling.db", log_level: str = "INFO"):
        """Initialisiert das Enterprise-Fehlerbehandlungssystem"""
        self.db_path = db_path
        self.log_level = getattr(logging, log_level.upper())
        self._init_database()
        self._init_logging()
        self._load_recovery_strategies()
        self._error_counters = {}
        self._circuit_breakers = {}
        self._retry_queues = {}
        
    def _init_database(self):
        """Initialisiert die Datenbank für Fehlerbehandlung"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Tabelle für Fehlerkontexte
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS error_contexts (
                        error_id TEXT PRIMARY KEY,
                        timestamp DATETIME NOT NULL,
                        severity TEXT NOT NULL,
                        category TEXT NOT NULL,
                        component TEXT NOT NULL,
                        function_name TEXT NOT NULL,
                        error_message TEXT NOT NULL,
                        stack_trace TEXT,
                        context_data TEXT,  -- JSON
                        user_impact TEXT,
                        recovery_strategy TEXT NOT NULL,
                        retry_count INTEGER DEFAULT 0,
                        max_retries INTEGER DEFAULT 3,
                        is_resolved BOOLEAN DEFAULT 0,
                        resolution_notes TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Tabelle für Recovery-Aktionen
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS recovery_actions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        action_id TEXT UNIQUE NOT NULL,
                        error_id TEXT NOT NULL,
                        action_type TEXT NOT NULL,
                        parameters TEXT,  -- JSON
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        success BOOLEAN DEFAULT 0,
                        result TEXT,  -- JSON
                        error_message TEXT,
                        FOREIGN KEY (error_id) REFERENCES error_contexts(error_id)
                    )
                ''')
                
                # Tabelle für System-Metriken
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS system_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        metric_name TEXT NOT NULL,
                        metric_value REAL NOT NULL,
                        component TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        context TEXT  -- JSON
                    )
                ''')

                # Performance-Indizes für schnelle Abfragen
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_error_contexts_timestamp ON error_contexts(timestamp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_error_contexts_severity ON error_contexts(severity)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_error_contexts_category ON error_contexts(category)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_error_contexts_component ON error_contexts(component)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_error_contexts_resolved ON error_contexts(is_resolved)')

                # Zusammengesetzte Indizes für komplexe Abfragen
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_error_contexts_compound ON error_contexts(component, severity, timestamp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_system_metrics_compound ON system_metrics(component, metric_name, timestamp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_recovery_error ON recovery_actions(error_id)')
                
                conn.commit()
                logger.info("Fehlerbehandlungs-Datenbank initialisiert")
                
        except Exception as e:
            print(f"Kritischer Fehler bei Datenbank-Initialisierung: {e}")
            raise
    
    def _init_logging(self):
        """Initialisiert erweiterte Logging-Konfiguration"""
        # Erstelle Logger für verschiedene Komponenten
        self.loggers = {
            'error_handler': logging.getLogger('enterprise_error_handler'),
            'recovery': logging.getLogger('error_recovery'),
            'metrics': logging.getLogger('error_metrics'),
            'circuit_breaker': logging.getLogger('circuit_breaker')
        }
        
        # Konfiguriere Logging-Level
        for logger in self.loggers.values():
            logger.setLevel(self.log_level)
            
        # Erstelle Handler für verschiedene Log-Level
        error_handler = logging.FileHandler('logs/error_handler.log')
        recovery_handler = logging.FileHandler('logs/recovery.log')
        metrics_handler = logging.FileHandler('logs/error_metrics.log')
        
        # Formatiere Logs
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        for handler in [error_handler, recovery_handler, metrics_handler]:
            handler.setFormatter(formatter)
        
        # Weise Handler zu
        self.loggers['error_handler'].addHandler(error_handler)
        self.loggers['recovery'].addHandler(recovery_handler)
        self.loggers['metrics'].addHandler(metrics_handler)
    
    def _load_recovery_strategies(self):
        """Lädt Recovery-Strategien für verschiedene Fehlertypen"""
        self.recovery_strategies = {
            ErrorCategory.NETWORK: {
                'retry_delays': [1, 2, 5, 10, 30],  # Sekunden
                'max_retries': 5,
                'fallback_action': 'use_cached_data',
                'escalation_threshold': 3
            },
            ErrorCategory.DATABASE: {
                'retry_delays': [0.5, 1, 2, 5],
                'max_retries': 4,
                'fallback_action': 'use_backup_db',
                'escalation_threshold': 2
            },
            ErrorCategory.EMAIL: {
                'retry_delays': [2, 5, 15, 60],
                'max_retries': 4,
                'fallback_action': 'queue_for_later',
                'escalation_threshold': 2
            },
            ErrorCategory.INTENT_CLASSIFICATION: {
                'retry_delays': [0.1, 0.5, 1],
                'max_retries': 3,
                'fallback_action': 'use_rule_based_classification',
                'escalation_threshold': 2
            },
            ErrorCategory.RESPONSE_GENERATION: {
                'retry_delays': [1, 3, 10],
                'max_retries': 3,
                'fallback_action': 'use_template_response',
                'escalation_threshold': 2
            },
            ErrorCategory.CALENDAR: {
                'retry_delays': [1, 2, 5],
                'max_retries': 3,
                'fallback_action': 'manual_booking_required',
                'escalation_threshold': 2
            }
        }
    
    def handle_error(self, error: Exception, component: str, function_name: str, 
                    context_data: Dict[str, Any] = None, severity: ErrorSeverity = None,
                    category: ErrorCategory = None) -> str:
        """
        Behandelt einen Fehler mit Enterprise-Level-Logik
        
        Args:
            error: Der aufgetretene Fehler
            component: Komponente, in der der Fehler aufgetreten ist
            function_name: Funktion, in der der Fehler aufgetreten ist
            context_data: Zusätzliche Kontextdaten
            severity: Schweregrad des Fehlers
            category: Kategorie des Fehlers
            
        Returns:
            error_id: Eindeutige ID des Fehlers
        """
        try:
            # Bestimme Schweregrad und Kategorie automatisch
            if severity is None:
                severity = self._determine_severity(error, component)
            
            if category is None:
                category = self._determine_category(error, component)
            
            # Erstelle Fehlerkontext
            error_id = f"err_{int(time.time() * 1000)}_{component}"
            error_context = ErrorContext(
                error_id=error_id,
                timestamp=datetime.now(),
                severity=severity,
                category=category,
                component=component,
                function_name=function_name,
                error_message=str(error),
                stack_trace=traceback.format_exc(),
                context_data=context_data or {},
                user_impact=self._assess_user_impact(severity, category),
                recovery_strategy=self._determine_recovery_strategy(category, severity)
            )
            
            # Speichere Fehlerkontext
            self._save_error_context(error_context)
            
            # Logge Fehler
            self._log_error(error_context)
            
            # Führe Recovery-Strategie aus
            self._execute_recovery_strategy(error_context)
            
            # Aktualisiere Metriken
            self._update_error_metrics(error_context)
            
            return error_id
            
        except Exception as e:
            # Kritischer Fehler im Fehlerbehandlungssystem
            print(f"KRITISCHER FEHLER im Fehlerbehandlungssystem: {e}")
            return f"critical_error_{int(time.time())}"
    
    def _determine_severity(self, error: Exception, component: str) -> ErrorSeverity:
        """Bestimmt automatisch den Schweregrad eines Fehlers"""
        error_type = type(error).__name__
        error_message = str(error).lower()
        
        # Kritische Fehler
        if any(keyword in error_message for keyword in ['database', 'connection', 'authentication', 'permission']):
            return ErrorSeverity.CRITICAL
        
        # Hohe Schwere
        if any(keyword in error_message for keyword in ['timeout', 'network', 'service unavailable']):
            return ErrorSeverity.HIGH
        
        # Mittlere Schwere
        if any(keyword in error_message for keyword in ['validation', 'format', 'parse']):
            return ErrorSeverity.MEDIUM
        
        # Niedrige Schwere
        return ErrorSeverity.LOW
    
    def _determine_category(self, error: Exception, component: str) -> ErrorCategory:
        """Bestimmt automatisch die Kategorie eines Fehlers"""
        error_type = type(error).__name__
        error_message = str(error).lower()
        
        if 'network' in error_message or 'connection' in error_message:
            return ErrorCategory.NETWORK
        elif 'database' in error_message or 'sql' in error_message:
            return ErrorCategory.DATABASE
        elif 'email' in error_message or 'smtp' in error_message or 'imap' in error_message:
            return ErrorCategory.EMAIL
        elif 'intent' in error_message or 'classification' in error_message:
            return ErrorCategory.INTENT_CLASSIFICATION
        elif 'response' in error_message or 'generation' in error_message:
            return ErrorCategory.RESPONSE_GENERATION
        elif 'calendar' in error_message or 'appointment' in error_message:
            return ErrorCategory.CALENDAR
        elif 'api' in error_message or 'external' in error_message:
            return ErrorCategory.EXTERNAL_API
        elif 'config' in error_message or 'configuration' in error_message:
            return ErrorCategory.CONFIGURATION
        elif 'auth' in error_message or 'permission' in error_message:
            return ErrorCategory.AUTHENTICATION
        else:
            return ErrorCategory.SYSTEM
    
    def _assess_user_impact(self, severity: ErrorSeverity, category: ErrorCategory) -> str:
        """Bewertet die Auswirkung auf den Benutzer"""
        impact_map = {
            (ErrorSeverity.CRITICAL, ErrorCategory.EMAIL): "E-Mail-Verarbeitung komplett unterbrochen",
            (ErrorSeverity.CRITICAL, ErrorCategory.DATABASE): "Datenbankzugriff nicht möglich",
            (ErrorSeverity.HIGH, ErrorCategory.EMAIL): "E-Mail-Verarbeitung verzögert",
            (ErrorSeverity.HIGH, ErrorCategory.INTENT_CLASSIFICATION): "Intent-Erkennung unzuverlässig",
            (ErrorSeverity.MEDIUM, ErrorCategory.RESPONSE_GENERATION): "Antworten möglicherweise generisch",
            (ErrorSeverity.LOW, ErrorCategory.SYSTEM): "Minimale Auswirkung auf Benutzer"
        }
        
        return impact_map.get((severity, category), "Unbekannte Auswirkung")
    
    def _determine_recovery_strategy(self, category: ErrorCategory, severity: ErrorSeverity) -> RecoveryStrategy:
        """Bestimmt die Recovery-Strategie basierend auf Kategorie und Schweregrad"""
        if severity == ErrorSeverity.CRITICAL:
            return RecoveryStrategy.ESCALATE
        elif severity == ErrorSeverity.HIGH:
            return RecoveryStrategy.RETRY
        elif category in [ErrorCategory.NETWORK, ErrorCategory.EMAIL]:
            return RecoveryStrategy.RETRY
        elif category in [ErrorCategory.INTENT_CLASSIFICATION, ErrorCategory.RESPONSE_GENERATION]:
            return RecoveryStrategy.FALLBACK
        else:
            return RecoveryStrategy.IGNORE
    
    def _save_error_context(self, error_context: ErrorContext):
        """Speichert den Fehlerkontext in der Datenbank"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO error_contexts
                    (error_id, timestamp, severity, category, component, function_name,
                     error_message, stack_trace, context_data, user_impact, recovery_strategy,
                     retry_count, max_retries, is_resolved, resolution_notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    error_context.error_id, error_context.timestamp.isoformat(),
                    error_context.severity.value, error_context.category.value,
                    error_context.component, error_context.function_name,
                    error_context.error_message, error_context.stack_trace,
                    json.dumps(error_context.context_data), error_context.user_impact,
                    error_context.recovery_strategy.value, error_context.retry_count,
                    error_context.max_retries, error_context.is_resolved,
                    error_context.resolution_notes
                ))
                conn.commit()
                
        except Exception as e:
            print(f"Fehler beim Speichern des Fehlerkontexts: {e}")
    
    def _log_error(self, error_context: ErrorContext):
        """Loggt den Fehler mit angemessenem Level"""
        log_message = f"Fehler in {error_context.component}.{error_context.function_name}: {error_context.error_message}"
        
        if error_context.severity == ErrorSeverity.CRITICAL:
            self.loggers['error_handler'].critical(log_message)
        elif error_context.severity == ErrorSeverity.HIGH:
            self.loggers['error_handler'].error(log_message)
        elif error_context.severity == ErrorSeverity.MEDIUM:
            self.loggers['error_handler'].warning(log_message)
        else:
            self.loggers['error_handler'].info(log_message)
    
    def _execute_recovery_strategy(self, error_context: ErrorContext):
        """Führt die Recovery-Strategie aus"""
        try:
            if error_context.recovery_strategy == RecoveryStrategy.RETRY:
                self._execute_retry_strategy(error_context)
            elif error_context.recovery_strategy == RecoveryStrategy.FALLBACK:
                self._execute_fallback_strategy(error_context)
            elif error_context.recovery_strategy == RecoveryStrategy.ESCALATE:
                self._execute_escalation_strategy(error_context)
            elif error_context.recovery_strategy == RecoveryStrategy.RESTART:
                self._execute_restart_strategy(error_context)
                
        except Exception as e:
            self.loggers['recovery'].error(f"Fehler bei Recovery-Strategie: {e}")
    
    def _execute_retry_strategy(self, error_context: ErrorContext):
        """Führt Retry-Strategie aus"""
        if error_context.retry_count >= error_context.max_retries:
            self.loggers['recovery'].warning(f"Maximale Retry-Versuche erreicht für {error_context.error_id}")
            return
        
        # Hole Retry-Konfiguration
        strategy_config = self.recovery_strategies.get(error_context.category, {})
        retry_delays = strategy_config.get('retry_delays', [1, 2, 5])
        
        if error_context.retry_count < len(retry_delays):
            delay = retry_delays[error_context.retry_count]
            self.loggers['recovery'].info(f"Retry {error_context.retry_count + 1} in {delay} Sekunden für {error_context.error_id}")
            
            # Hier würde der eigentliche Retry-Code stehen
            # Für jetzt nur Logging
            time.sleep(delay)
    
    def _execute_fallback_strategy(self, error_context: ErrorContext):
        """Führt Fallback-Strategie aus"""
        fallback_action = self.recovery_strategies.get(error_context.category, {}).get('fallback_action', 'unknown')
        self.loggers['recovery'].info(f"Fallback-Aktion '{fallback_action}' für {error_context.error_id}")
        
        # Hier würde die Fallback-Logik stehen
        # z.B. Wechsel zu Template-basierten Antworten
    
    def _execute_escalation_strategy(self, error_context: ErrorContext):
        """Führt Eskalations-Strategie aus"""
        self.loggers['recovery'].critical(f"ESKALATION erforderlich für {error_context.error_id}")
        
        # Hier würde die Eskalations-Logik stehen
        # z.B. Benachrichtigung an Administratoren
    
    def _execute_restart_strategy(self, error_context: ErrorContext):
        """Führt Restart-Strategie aus"""
        self.loggers['recovery'].warning(f"Restart erforderlich für {error_context.error_id}")
        
        # Hier würde die Restart-Logik stehen
        # z.B. Neustart des betroffenen Services
    
    def _update_error_metrics(self, error_context: ErrorContext):
        """Aktualisiert Fehler-Metriken"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Zähle Fehler nach Kategorie
                cursor.execute('''
                    INSERT INTO system_metrics (metric_name, metric_value, component, context)
                    VALUES (?, ?, ?, ?)
                ''', (
                    f"error_count_{error_context.category.value}",
                    1,
                    error_context.component,
                    json.dumps({"severity": error_context.severity.value})
                ))
                
                conn.commit()
                
        except Exception as e:
            print(f"Fehler beim Aktualisieren der Metriken: {e}")
    
    def retry_with_backoff(self, func: Callable, max_retries: int = 3, 
                          backoff_factor: float = 2.0, exceptions: Tuple = (Exception,)):
        """
        Decorator für Retry-Logik mit Exponential Backoff
        
        Args:
            func: Funktion, die wiederholt werden soll
            max_retries: Maximale Anzahl Wiederholungen
            backoff_factor: Faktor für Exponential Backoff
            exceptions: Tupel von Exceptions, die wiederholt werden sollen
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        # Letzter Versuch fehlgeschlagen
                        error_id = self.handle_error(
                            e, 
                            component=func.__module__,
                            function_name=func.__name__,
                            context_data={"attempt": attempt + 1, "max_retries": max_retries}
                        )
                        raise e
                    
                    # Berechne Wartezeit mit Exponential Backoff
                    wait_time = backoff_factor ** attempt
                    self.loggers['recovery'].info(f"Retry {attempt + 1}/{max_retries} in {wait_time}s für {func.__name__}")
                    time.sleep(wait_time)
            
            raise last_exception
        
        return wrapper
    
    def circuit_breaker(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        """
        Decorator für Circuit Breaker Pattern
        
        Args:
            failure_threshold: Anzahl Fehler vor Öffnung des Circuit Breakers
            recovery_timeout: Zeit in Sekunden, nach der der Circuit Breaker geschlossen wird
        """
        def decorator(func: Callable):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                circuit_key = f"{func.__module__}.{func.__name__}"
                
                # Hole Circuit Breaker Status
                if circuit_key not in self._circuit_breakers:
                    self._circuit_breakers[circuit_key] = {
                        'state': 'closed',  # closed, open, half_open
                        'failure_count': 0,
                        'last_failure_time': None
                    }
                
                circuit = self._circuit_breakers[circuit_key]
                current_time = time.time()
                
                # Prüfe Circuit Breaker Status
                if circuit['state'] == 'open':
                    if current_time - circuit['last_failure_time'] > recovery_timeout:
                        circuit['state'] = 'half_open'
                        self.loggers['circuit_breaker'].info(f"Circuit Breaker für {circuit_key} auf half_open gesetzt")
                    else:
                        raise Exception(f"Circuit Breaker für {circuit_key} ist geöffnet")
                
                try:
                    result = func(*args, **kwargs)
                    
                    # Erfolg - schließe Circuit Breaker
                    if circuit['state'] == 'half_open':
                        circuit['state'] = 'closed'
                        circuit['failure_count'] = 0
                        self.loggers['circuit_breaker'].info(f"Circuit Breaker für {circuit_key} geschlossen")
                    
                    return result
                    
                except Exception as e:
                    circuit['failure_count'] += 1
                    circuit['last_failure_time'] = current_time
                    
                    if circuit['failure_count'] >= failure_threshold:
                        circuit['state'] = 'open'
                        self.loggers['circuit_breaker'].warning(f"Circuit Breaker für {circuit_key} geöffnet")
                    
                    raise e
            
            return wrapper
        return decorator
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Holt Fehlerstatistiken"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Gesamtfehler
                cursor.execute('SELECT COUNT(*) FROM error_contexts')
                total_errors = cursor.fetchone()[0]
                
                # Fehler nach Schweregrad
                cursor.execute('''
                    SELECT severity, COUNT(*) 
                    FROM error_contexts 
                    GROUP BY severity
                ''')
                errors_by_severity = dict(cursor.fetchall())
                
                # Fehler nach Kategorie
                cursor.execute('''
                    SELECT category, COUNT(*) 
                    FROM error_contexts 
                    GROUP BY category
                ''')
                errors_by_category = dict(cursor.fetchall())
                
                # Fehler nach Komponente
                cursor.execute('''
                    SELECT component, COUNT(*) 
                    FROM error_contexts 
                    GROUP BY component
                    ORDER BY COUNT(*) DESC
                    LIMIT 10
                ''')
                errors_by_component = dict(cursor.fetchall())
                
                # Gelöste vs. ungelöste Fehler
                cursor.execute('''
                    SELECT is_resolved, COUNT(*) 
                    FROM error_contexts 
                    GROUP BY is_resolved
                ''')
                resolution_status = dict(cursor.fetchall())
                
                return {
                    "total_errors": total_errors,
                    "errors_by_severity": errors_by_severity,
                    "errors_by_category": errors_by_category,
                    "errors_by_component": errors_by_component,
                    "resolution_status": resolution_status,
                    "circuit_breakers": len(self._circuit_breakers),
                    "generated_at": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Fehler beim Laden der Fehlerstatistiken: {e}")
            return {}


# Globaler Error Handler für das gesamte System
enterprise_error_handler = EnterpriseErrorHandler()

# Convenience-Funktionen
def handle_error(error: Exception, component: str, function_name: str, **kwargs) -> str:
    """Behandelt einen Fehler mit dem Enterprise Error Handler"""
    return enterprise_error_handler.handle_error(error, component, function_name, **kwargs)

def retry_with_backoff(max_retries: int = 3, backoff_factor: float = 2.0, exceptions: Tuple = (Exception,)):
    """Decorator für Retry-Logik"""
    def decorator(func: Callable) -> Callable:
        return enterprise_error_handler.retry_with_backoff(func, max_retries=max_retries, backoff_factor=backoff_factor, exceptions=exceptions)
    return decorator

def circuit_breaker(failure_threshold: int = 5, recovery_timeout: int = 60):
    """Decorator für Circuit Breaker Pattern"""
    def decorator(func: Callable) -> Callable:
        return enterprise_error_handler.circuit_breaker(failure_threshold=failure_threshold, recovery_timeout=recovery_timeout)(func)
    return decorator


# Test-Funktion
def test_error_handling():
    """Testet das Fehlerbehandlungssystem"""
    handler = EnterpriseErrorHandler()
    
    # Test verschiedene Fehlertypen
    try:
        raise ConnectionError("Verbindung zur Datenbank fehlgeschlagen")
    except Exception as e:
        error_id = handler.handle_error(e, "database", "connect")
        print(f"Fehler behandelt: {error_id}")
    
    # Test Retry-Decorator
    @retry_with_backoff(max_retries=3)
    def failing_function():
        raise ValueError("Test-Fehler")
    
    try:
        failing_function()
    except Exception as e:
        print(f"Retry-Funktion fehlgeschlagen: {e}")
    
    # Zeige Statistiken
    stats = handler.get_error_statistics()
    print(f"Fehlerstatistiken: {stats}")


if __name__ == "__main__":
    test_error_handling()
