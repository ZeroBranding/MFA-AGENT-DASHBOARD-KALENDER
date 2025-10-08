#!/usr/bin/env python3
"""
SELF-LEARNING SYSTEM
Enterprise-Level Machine Learning für kontinuierliche Verbesserung
Lernt aus erfolgreichen Interaktionen und optimiert Intent-Erkennung
"""

import sqlite3
import logging
import json
import pickle
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import re
from collections import defaultdict, Counter
# Privacy helpers: redact PII before storing/training
from utils.privacy import redact_text, hash_owner, contains_pii
import hashlib
from pathlib import Path

logger = logging.getLogger(__name__)

class LearningType(Enum):
    """Typ des Lernens"""
    INTENT_CLASSIFICATION = "intent_classification"
    RESPONSE_GENERATION = "response_generation"
    ENTITY_EXTRACTION = "entity_extraction"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    URGENCY_ASSESSMENT = "urgency_assessment"

class LearningSource(Enum):
    """Quelle des Lernens"""
    USER_FEEDBACK = "user_feedback"
    SUCCESSFUL_INTERACTION = "successful_interaction"
    MANUAL_CORRECTION = "manual_correction"
    PATTERN_RECOGNITION = "pattern_recognition"
    STATISTICAL_ANALYSIS = "statistical_analysis"

@dataclass
class LearningExample:
    """Struktur für ein Lernbeispiel"""
    example_id: str
    learning_type: LearningType
    input_text: str
    expected_output: Any
    actual_output: Any
    confidence: float
    source: LearningSource
    timestamp: datetime
    is_verified: bool = False
    feedback_score: Optional[float] = None
    context: Optional[Dict[str, Any]] = None

@dataclass
class LearningPattern:
    """Struktur für erkannte Muster"""
    pattern_id: str
    pattern_type: str
    pattern_data: Dict[str, Any]
    confidence: float
    frequency: int
    success_rate: float
    created_at: datetime
    last_updated: datetime

class SelfLearningSystem:
    """
    Enterprise-Level Self-Learning-System
    Lernt kontinuierlich aus Interaktionen und verbessert die Performance
    """
    
    def __init__(self, db_path: str = "self_learning.db", model_path: str = "models/"):
        """Initialisiert das Self-Learning-System"""
        self.db_path = db_path
        self.model_path = Path(model_path)
        self.model_path.mkdir(exist_ok=True)
        
        self._init_database()
        self._load_learning_models()
        self._load_patterns()
        
    def _init_database(self):
        """Initialisiert die Datenbank für das Lernsystem"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Tabelle für Lernbeispiele
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS learning_examples (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        example_id TEXT UNIQUE NOT NULL,
                        learning_type TEXT NOT NULL,
                        input_text TEXT NOT NULL,
                        expected_output TEXT NOT NULL,  -- JSON
                        actual_output TEXT NOT NULL,    -- JSON
                        confidence REAL NOT NULL,
                        source TEXT NOT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        is_verified BOOLEAN DEFAULT 0,
                        feedback_score REAL,
                        context TEXT,  -- JSON
                        UNIQUE(example_id)
                    )
                ''')
                
                # Tabelle für erkannte Muster
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS learning_patterns (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        pattern_id TEXT UNIQUE NOT NULL,
                        pattern_type TEXT NOT NULL,
                        pattern_data TEXT NOT NULL,  -- JSON
                        confidence REAL NOT NULL,
                        frequency INTEGER DEFAULT 1,
                        success_rate REAL DEFAULT 0.0,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Tabelle für Performance-Metriken
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS performance_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        learning_type TEXT NOT NULL,
                        metric_name TEXT NOT NULL,
                        metric_value REAL NOT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        context TEXT  -- JSON
                    )
                ''')
                
                # Tabelle für Feedback
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_feedback (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        example_id TEXT NOT NULL,
                        feedback_type TEXT NOT NULL,
                        feedback_value REAL NOT NULL,
                        feedback_text TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (example_id) REFERENCES learning_examples(example_id)
                    )
                ''')
                
                # Indizes für Performance
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_learning_type ON learning_examples(learning_type)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON learning_examples(timestamp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_pattern_type ON learning_patterns(pattern_type)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_metrics_type ON performance_metrics(learning_type)')
                
                conn.commit()
                logger.info("Self-Learning-Datenbank initialisiert")
                
        except Exception as e:
            logger.error(f"Fehler bei Datenbank-Initialisierung: {e}")
            raise
    
    def _load_learning_models(self):
        """Lädt oder erstellt Machine Learning Modelle"""
        self.models = {}
        
        # Intent Classification Model
        self.models['intent_classification'] = self._load_or_create_model('intent_classification')
        
        # Entity Extraction Model
        self.models['entity_extraction'] = self._load_or_create_model('entity_extraction')
        
        # Sentiment Analysis Model
        self.models['sentiment_analysis'] = self._load_or_create_model('sentiment_analysis')
        
        # Response Quality Model
        self.models['response_quality'] = self._load_or_create_model('response_quality')
    
    def _load_or_create_model(self, model_type: str):
        """Lädt ein existierendes Modell oder erstellt ein neues"""
        model_file = self.model_path / f"{model_type}.pkl"
        
        if model_file.exists():
            try:
                with open(model_file, 'rb') as f:
                    model = pickle.load(f)
                logger.info(f"Modell geladen: {model_type}")
                return model
            except Exception as e:
                logger.warning(f"Fehler beim Laden des Modells {model_type}: {e}")
        
        # Erstelle neues Modell
        return self._create_new_model(model_type)
    
    def _create_new_model(self, model_type: str):
        """Erstellt ein neues Machine Learning Modell"""
        if model_type == 'intent_classification':
            return self._create_intent_classification_model()
        elif model_type == 'entity_extraction':
            return self._create_entity_extraction_model()
        elif model_type == 'sentiment_analysis':
            return self._create_sentiment_analysis_model()
        elif model_type == 'response_quality':
            return self._create_response_quality_model()
        else:
            return None
    
    def _create_intent_classification_model(self):
        """Erstellt ein Intent-Classification-Modell"""
        return {
            'type': 'intent_classification',
            'patterns': {},
            'weights': {},
            'confidence_threshold': 0.7,
            'created_at': datetime.now().isoformat()
        }
    
    def _create_entity_extraction_model(self):
        """Erstellt ein Entity-Extraction-Modell"""
        return {
            'type': 'entity_extraction',
            'patterns': {},
            'regex_patterns': {},
            'confidence_threshold': 0.6,
            'created_at': datetime.now().isoformat()
        }
    
    def _create_sentiment_analysis_model(self):
        """Erstellt ein Sentiment-Analysis-Modell"""
        return {
            'type': 'sentiment_analysis',
            'positive_words': set(),
            'negative_words': set(),
            'neutral_words': set(),
            'confidence_threshold': 0.5,
            'created_at': datetime.now().isoformat()
        }
    
    def _create_response_quality_model(self):
        """Erstellt ein Response-Quality-Modell"""
        return {
            'type': 'response_quality',
            'quality_indicators': {},
            'success_patterns': {},
            'confidence_threshold': 0.8,
            'created_at': datetime.now().isoformat()
        }
    
    def _load_patterns(self):
        """Lädt erkannte Muster aus der Datenbank"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM learning_patterns')
                
                self.patterns = {}
                for row in cursor.fetchall():
                    pattern = LearningPattern(
                        pattern_id=row[1],
                        pattern_type=row[2],
                        pattern_data=json.loads(row[3]),
                        confidence=row[4],
                        frequency=row[5],
                        success_rate=row[6],
                        created_at=datetime.fromisoformat(row[7]),
                        last_updated=datetime.fromisoformat(row[8])
                    )
                    self.patterns[pattern.pattern_id] = pattern
                
                logger.info(f"{len(self.patterns)} Muster geladen")
                
        except Exception as e:
            logger.error(f"Fehler beim Laden der Muster: {e}")
            self.patterns = {}
    
    def add_learning_example(self, example: LearningExample) -> bool:
        """Fügt ein Lernbeispiel hinzu"""
        try:
            # Handle privacy: if owner email present in context, replace with hash and remove raw email
            ctx = example.context or {}
            if isinstance(ctx, dict) and ctx.get('owner_email'):
                try:
                    owner = ctx.get('owner_email')
                    ctx['owner_hash'] = hash_owner(owner)
                except Exception:
                    ctx['owner_hash'] = None
                # remove raw owner email
                ctx.pop('owner_email', None)

            # Redact PII from texts before storage/training
            redacted_input = redact_text(example.input_text)
            redacted_expected = redact_text(json.dumps(example.expected_output)) if example.expected_output is not None else None
            redacted_actual = redact_text(json.dumps(example.actual_output)) if example.actual_output is not None else None

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO learning_examples
                    (example_id, learning_type, input_text, expected_output, actual_output,
                     confidence, source, timestamp, is_verified, feedback_score, context)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    example.example_id, example.learning_type.value, redacted_input,
                    redacted_expected, redacted_actual,
                    example.confidence, example.source.value, example.timestamp.isoformat(),
                    example.is_verified, example.feedback_score,
                    json.dumps(ctx) if ctx else None
                ))
                
                conn.commit()
                
                # Trigger Learning Process using redacted example to avoid learning raw PII
                redacted_example = LearningExample(
                    example_id=example.example_id,
                    learning_type=example.learning_type,
                    input_text=redacted_input,
                    expected_output=example.expected_output,
                    actual_output=example.actual_output,
                    confidence=example.confidence,
                    source=example.source,
                    timestamp=example.timestamp,
                    is_verified=example.is_verified,
                    feedback_score=example.feedback_score,
                    context=ctx
                )
                self._trigger_learning_process(redacted_example)
                
                logger.info(f"Lernbeispiel hinzugefügt: {example.example_id}")
                return True
                
        except Exception as e:
            logger.error(f"Fehler beim Hinzufügen des Lernbeispiels: {e}")
            return False
    
    def _trigger_learning_process(self, example: LearningExample):
        """Triggert den Lernprozess basierend auf dem Beispiel"""
        try:
            if example.learning_type == LearningType.INTENT_CLASSIFICATION:
                self._learn_intent_classification(example)
            elif example.learning_type == LearningType.ENTITY_EXTRACTION:
                self._learn_entity_extraction(example)
            elif example.learning_type == LearningType.SENTIMENT_ANALYSIS:
                self._learn_sentiment_analysis(example)
            elif example.learning_type == LearningType.RESPONSE_GENERATION:
                self._learn_response_generation(example)
            
        except Exception as e:
            logger.error(f"Fehler im Lernprozess: {e}")
    
    def _learn_intent_classification(self, example: LearningExample):
        """Lernt aus Intent-Classification-Beispielen"""
        if example.expected_output != example.actual_output:
            # Fehlerkorrektur
            self._update_intent_patterns(example.input_text, example.expected_output, example.actual_output)
        else:
            # Erfolgreiche Klassifikation
            self._reinforce_intent_patterns(example.input_text, example.expected_output)
    
    def _learn_entity_extraction(self, example: LearningExample):
        """Lernt aus Entity-Extraction-Beispielen"""
        if example.expected_output != example.actual_output:
            # Fehlerkorrektur
            self._update_entity_patterns(example.input_text, example.expected_output, example.actual_output)
        else:
            # Erfolgreiche Extraktion
            self._reinforce_entity_patterns(example.input_text, example.expected_output)
    
    def _learn_sentiment_analysis(self, example: LearningExample):
        """Lernt aus Sentiment-Analysis-Beispielen"""
        if example.expected_output != example.actual_output:
            # Fehlerkorrektur
            self._update_sentiment_patterns(example.input_text, example.expected_output, example.actual_output)
        else:
            # Erfolgreiche Analyse
            self._reinforce_sentiment_patterns(example.input_text, example.expected_output)
    
    def _learn_response_generation(self, example: LearningExample):
        """Lernt aus Response-Generation-Beispielen"""
        if example.feedback_score and example.feedback_score > 0.7:
            # Positive Bewertung
            self._reinforce_response_patterns(example.input_text, example.expected_output)
        elif example.feedback_score and example.feedback_score < 0.3:
            # Negative Bewertung
            self._update_response_patterns(example.input_text, example.expected_output, example.actual_output)
    
    def _update_intent_patterns(self, text: str, expected_intent: str, actual_intent: str):
        """Aktualisiert Intent-Pattern basierend auf Fehlern"""
        # Extrahiere Schlüsselwörter aus dem Text
        keywords = self._extract_keywords(text)
        
        # Erstelle Pattern-ID
        pattern_id = f"intent_{hashlib.md5(text.encode()).hexdigest()[:8]}"
        
        # Speichere oder aktualisiere Pattern
        if pattern_id in self.patterns:
            pattern = self.patterns[pattern_id]
            pattern.frequency += 1
            pattern.success_rate = (pattern.success_rate * (pattern.frequency - 1) + 0.0) / pattern.frequency
        else:
            pattern = LearningPattern(
                pattern_id=pattern_id,
                pattern_type="intent_classification",
                pattern_data={
                    "keywords": keywords,
                    "expected_intent": expected_intent,
                    "actual_intent": actual_intent,
                    "text_sample": text[:100]
                },
                confidence=0.5,
                frequency=1,
                success_rate=0.0,
                created_at=datetime.now(),
                last_updated=datetime.now()
            )
            self.patterns[pattern_id] = pattern
        
        # Aktualisiere Modell
        self._update_intent_model(pattern)
    
    def _reinforce_intent_patterns(self, text: str, intent: str):
        """Verstärkt erfolgreiche Intent-Pattern"""
        keywords = self._extract_keywords(text)
        
        # Finde ähnliche Pattern
        for pattern in self.patterns.values():
            if (pattern.pattern_type == "intent_classification" and 
                pattern.pattern_data.get("expected_intent") == intent):
                
                # Berechne Ähnlichkeit
                similarity = self._calculate_keyword_similarity(keywords, pattern.pattern_data.get("keywords", []))
                
                if similarity > 0.7:
                    pattern.frequency += 1
                    pattern.success_rate = (pattern.success_rate * (pattern.frequency - 1) + 1.0) / pattern.frequency
                    pattern.last_updated = datetime.now()
    
    def _update_entity_patterns(self, text: str, expected_entities: Dict, actual_entities: Dict):
        """Aktualisiert Entity-Pattern basierend auf Fehlern"""
        text_lower = text.lower()

        # Analysiere fehlende Entities
        for entity_type, expected_values in expected_entities.items():
            if entity_type not in actual_entities:
                # Entity-Typ wurde nicht erkannt - lerne neue Pattern
                self._learn_entity_type_pattern(entity_type, text_lower, expected_values)
            else:
                actual_values = actual_entities[entity_type]
                # Prüfe auf falsche Werte
                for expected_value in expected_values:
                    if expected_value not in actual_values:
                        self._learn_entity_value_pattern(entity_type, expected_value, text_lower)

        # Analysiere falsch erkannte Entities
        for entity_type, actual_values in actual_entities.items():
            if entity_type not in expected_entities:
                # Entity-Typ wurde falsch erkannt - lerne negative Pattern
                self._learn_negative_entity_pattern(entity_type, text_lower)
    
    def _reinforce_entity_patterns(self, text: str, entities: Dict):
        """Verstärkt erfolgreiche Entity-Pattern"""
        text_lower = text.lower()

        for entity_type, values in entities.items():
            for value in values:
                # Verstärke erfolgreiche Erkennungen
                self._reinforce_entity_type_pattern(entity_type, text_lower)
                self._reinforce_entity_value_pattern(entity_type, value, text_lower)
    
    def _update_sentiment_patterns(self, text: str, expected_sentiment: str, actual_sentiment: str):
        """Aktualisiert Sentiment-Pattern basierend auf Fehlern"""
        words = text.lower().split()
        
        if expected_sentiment == "positive" and actual_sentiment != "positive":
            # Füge Wörter zu positiven Wörtern hinzu
            for word in words:
                if word not in self.models['sentiment_analysis']['negative_words']:
                    self.models['sentiment_analysis']['positive_words'].add(word)
        
        elif expected_sentiment == "negative" and actual_sentiment != "negative":
            # Füge Wörter zu negativen Wörtern hinzu
            for word in words:
                if word not in self.models['sentiment_analysis']['positive_words']:
                    self.models['sentiment_analysis']['negative_words'].add(word)
    
    def _reinforce_sentiment_patterns(self, text: str, sentiment: str):
        """Verstärkt erfolgreiche Sentiment-Pattern"""
        words = text.lower().split()
        
        if sentiment == "positive":
            for word in words:
                self.models['sentiment_analysis']['positive_words'].add(word)
        elif sentiment == "negative":
            for word in words:
                self.models['sentiment_analysis']['negative_words'].add(word)
        else:
            for word in words:
                self.models['sentiment_analysis']['neutral_words'].add(word)
    
    def _update_response_patterns(self, input_text: str, expected_response: str, actual_response: str):
        """Aktualisiert Response-Pattern basierend auf Fehlern"""
        # Analysiere Unterschiede zwischen erwarteter und tatsächlicher Antwort
        expected_words = set(self._extract_keywords(expected_response))
        actual_words = set(self._extract_keywords(actual_response))

        # Finde fehlende wichtige Wörter
        missing_words = expected_words - actual_words
        extra_words = actual_words - expected_words

        # Erstelle Korrektur-Pattern
        pattern_id = f"response_correction_{hashlib.md5(input_text.encode()).hexdigest()[:8]}"

        if pattern_id not in self.patterns:
            pattern = LearningPattern(
                pattern_id=pattern_id,
                pattern_type="response_correction",
                pattern_data={
                    "input_keywords": self._extract_keywords(input_text),
                    "missing_words": list(missing_words),
                    "extra_words": list(extra_words),
                    "expected_response_sample": expected_response[:100],
                    "actual_response_sample": actual_response[:100]
                },
                confidence=0.7,
                frequency=1,
                success_rate=0.0,
                created_at=datetime.now(),
                last_updated=datetime.now()
            )
            self.patterns[pattern_id] = pattern
    
    def _reinforce_response_patterns(self, input_text: str, response: str):
        """Verstärkt erfolgreiche Response-Pattern"""
        # Analysiere erfolgreiche Response-Pattern
        input_keywords = self._extract_keywords(input_text)
        response_keywords = self._extract_keywords(response)

        # Finde ähnliche Pattern und verstärke sie
        for pattern in self.patterns.values():
            if pattern.pattern_type == "response_correction":
                pattern_keywords = pattern.pattern_data.get("input_keywords", [])

                # Berechne Ähnlichkeit
                similarity = self._calculate_keyword_similarity(input_keywords, pattern_keywords)

                if similarity > 0.8:  # Hohe Ähnlichkeit
                    pattern.frequency += 1
                    pattern.success_rate = (pattern.success_rate * (pattern.frequency - 1) + 1.0) / pattern.frequency
                    pattern.last_updated = datetime.now()

    def _generate_entity_patterns(self, entity_type: str, text: str) -> List[str]:
        """Generiert Regex-Pattern für Entity-Typen"""
        patterns = []

        if entity_type == "date":
            patterns = [
                r'\b\d{1,2}\.\d{1,2}\.\d{4}\b',  # DD.MM.YYYY
                r'\b\d{4}-\d{1,2}-\d{1,2}\b',    # YYYY-MM-DD
                r'\b(heute|morgen|übermorgen)\b',
                r'\b(nächste|letzte)\s+(woche|monat|jahr)\b'
            ]
        elif entity_type == "time":
            patterns = [
                r'\b\d{1,2}:\d{2}\b',  # HH:MM
                r'\b\d{1,2}\s*(uhr|Uhr)\b',
                r'\b(morgen|mittag|abend|nacht)\b'
            ]
        elif entity_type == "medication":
            patterns = [
                r'\b[A-ZÄÖÜ][a-zäöüß]+\s*(tabletten|kapseln|tropfen|spray|creme)\b',
                r'\b(medikament|arznei|präparat)\s+[a-zäöüß\s]+\b'
            ]

        return patterns

    def _learn_negative_entity_pattern(self, entity_type: str, text: str):
        """Lernt negative Pattern für falsch erkannte Entities"""
        # Erstelle negatives Pattern um zu vermeiden, dass dieser Entity-Typ falsch erkannt wird
        pattern_id = f"negative_entity_{entity_type}_{hashlib.md5(text.encode()).hexdigest()[:8]}"

        if pattern_id not in self.patterns:
            pattern = LearningPattern(
                pattern_id=pattern_id,
                pattern_type="negative_entity",
                pattern_data={
                    "entity_type": entity_type,
                    "text_sample": text[:100],
                    "negative_keywords": self._extract_keywords(text)
                },
                confidence=0.8,
                frequency=1,
                success_rate=0.0,
                created_at=datetime.now(),
                last_updated=datetime.now()
            )
            self.patterns[pattern_id] = pattern
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extrahiert Schlüsselwörter aus Text"""
        # Entferne Stoppwörter und extrahiere relevante Wörter
        stop_words = {'der', 'die', 'das', 'und', 'oder', 'aber', 'mit', 'für', 'von', 'zu', 'in', 'auf', 'an', 'ist', 'sind', 'haben', 'werden', 'können', 'müssen', 'sollen', 'ich', 'du', 'er', 'sie', 'es', 'wir', 'ihr', 'sie'}
        
        words = re.findall(r'\b[a-zA-ZäöüÄÖÜß]+\b', text.lower())
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        return keywords
    
    def _calculate_keyword_similarity(self, keywords1: List[str], keywords2: List[str]) -> float:
        """Berechnet Ähnlichkeit zwischen zwei Keyword-Listen"""
        if not keywords1 or not keywords2:
            return 0.0
        
        set1 = set(keywords1)
        set2 = set(keywords2)
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0
    
    def _update_intent_model(self, pattern: LearningPattern):
        """Aktualisiert das Intent-Classification-Modell"""
        if pattern.pattern_type == "intent_classification":
            intent = pattern.pattern_data.get("expected_intent")
            keywords = pattern.pattern_data.get("keywords", [])
            
            if intent not in self.models['intent_classification']['patterns']:
                self.models['intent_classification']['patterns'][intent] = []
            
            # Füge Keywords zum Intent hinzu
            for keyword in keywords:
                if keyword not in self.models['intent_classification']['patterns'][intent]:
                    self.models['intent_classification']['patterns'][intent].append(keyword)
            
            # Aktualisiere Gewichtungen
            if intent not in self.models['intent_classification']['weights']:
                self.models['intent_classification']['weights'][intent] = 1.0
            else:
                self.models['intent_classification']['weights'][intent] += 0.1
    
    def predict_intent(self, text: str) -> Tuple[str, float]:
        """Vorhersage des Intents basierend auf gelernten Mustern"""
        keywords = self._extract_keywords(text)
        intent_scores = {}
        
        for intent, intent_keywords in self.models['intent_classification']['patterns'].items():
            similarity = self._calculate_keyword_similarity(keywords, intent_keywords)
            weight = self.models['intent_classification']['weights'].get(intent, 1.0)
            intent_scores[intent] = similarity * weight
        
        if intent_scores:
            best_intent = max(intent_scores.items(), key=lambda x: x[1])
            confidence = min(best_intent[1], 1.0)
            return best_intent[0], confidence
        
        return "unknown", 0.0
    
    def predict_sentiment(self, text: str) -> Tuple[str, float]:
        """Vorhersage des Sentiments basierend auf gelernten Mustern"""
        words = text.lower().split()
        
        positive_score = 0
        negative_score = 0
        neutral_score = 0
        
        for word in words:
            if word in self.models['sentiment_analysis']['positive_words']:
                positive_score += 1
            elif word in self.models['sentiment_analysis']['negative_words']:
                negative_score += 1
            elif word in self.models['sentiment_analysis']['neutral_words']:
                neutral_score += 1
        
        total_score = positive_score + negative_score + neutral_score
        
        if total_score == 0:
            return "neutral", 0.5
        
        if positive_score > negative_score and positive_score > neutral_score:
            confidence = positive_score / total_score
            return "positive", confidence
        elif negative_score > positive_score and negative_score > neutral_score:
            confidence = negative_score / total_score
            return "negative", confidence
        else:
            confidence = neutral_score / total_score
            return "neutral", confidence
    
    def save_models(self):
        """Speichert alle Modelle"""
        try:
            for model_type, model in self.models.items():
                model_file = self.model_path / f"{model_type}.pkl"
                with open(model_file, 'wb') as f:
                    pickle.dump(model, f)
            
            logger.info("Modelle gespeichert")
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Modelle: {e}")
            return False
    
    def get_learning_statistics(self) -> Dict[str, Any]:
        """Holt Statistiken über das Lernsystem"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Gesamtstatistiken
                cursor.execute('SELECT COUNT(*) FROM learning_examples')
                total_examples = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM learning_patterns')
                total_patterns = cursor.fetchone()[0]
                
                # Lernbeispiele nach Typ
                cursor.execute('''
                    SELECT learning_type, COUNT(*) 
                    FROM learning_examples 
                    GROUP BY learning_type
                ''')
                examples_by_type = dict(cursor.fetchall())
                
                # Pattern nach Typ
                cursor.execute('''
                    SELECT pattern_type, COUNT(*) 
                    FROM learning_patterns 
                    GROUP BY pattern_type
                ''')
                patterns_by_type = dict(cursor.fetchall())
                
                # Erfolgsrate
                cursor.execute('''
                    SELECT AVG(success_rate) 
                    FROM learning_patterns 
                    WHERE success_rate > 0
                ''')
                avg_success_rate = cursor.fetchone()[0] or 0.0
                
                return {
                    "total_examples": total_examples,
                    "total_patterns": total_patterns,
                    "examples_by_type": examples_by_type,
                    "patterns_by_type": patterns_by_type,
                    "average_success_rate": avg_success_rate,
                    "model_types": list(self.models.keys()),
                    "generated_at": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Fehler beim Laden der Lernstatistiken: {e}")
            return {}


# Test-Funktion für das Self-Learning-System
def test_self_learning():
    """Testet das Self-Learning-System"""
    learning_system = SelfLearningSystem()
    
    # Test-Lernbeispiele
    examples = [
        LearningExample(
            example_id="ex_001",
            learning_type=LearningType.INTENT_CLASSIFICATION,
            input_text="Ich brauche einen Termin für nächste Woche",
            expected_output="appointment",
            actual_output="appointment",
            confidence=0.9,
            source=LearningSource.SUCCESSFUL_INTERACTION,
            timestamp=datetime.now()
        ),
        LearningExample(
            example_id="ex_002",
            learning_type=LearningType.INTENT_CLASSIFICATION,
            input_text="Ich habe starke Schmerzen",
            expected_output="emergency",
            actual_output="medical_question",
            confidence=0.7,
            source=LearningSource.MANUAL_CORRECTION,
            timestamp=datetime.now()
        )
    ]
    
    # Füge Beispiele hinzu
    for example in examples:
        learning_system.add_learning_example(example)
    
    # Teste Vorhersagen
    test_text = "Ich brauche einen Termin"
    intent, confidence = learning_system.predict_intent(test_text)
    print(f"Intent-Vorhersage: {intent} (Vertrauen: {confidence:.2f})")
    
    # Speichere Modelle
    learning_system.save_models()
    
    # Zeige Statistiken
    stats = learning_system.get_learning_statistics()
    print(f"Lernstatistiken: {stats}")


if __name__ == "__main__":
    test_self_learning()
