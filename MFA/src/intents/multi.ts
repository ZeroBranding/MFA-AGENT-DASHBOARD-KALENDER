/**
 * Multi-Intent-Handling für komplexe E-Mails
 * Verwaltet mehrere Anliegen in einer E-Mail
 */

import type { IntentItem, IntentType } from "./types";

export interface IntentBucket {
  intent: IntentType;
  items: IntentItem[];
  confidence: number; // Durchschnittliche Konfidenz
  priority: number;   // Prioritätswert (1 = höchste Priorität)
}

export interface ProcessingPlan {
  buckets: IntentBucket[];
  totalItems: number;
  multiIntent: boolean;
  processingOrder: IntentType[];
  estimatedDuration: number; // Geschätzte Bearbeitungszeit in Minuten
}

// Prioritätsreihenfolge für Intents (1 = höchste Priorität)
const INTENT_PRIORITIES: { [intent: string]: number } = {
  notfall: 1,
  termin_anfragen: 2,
  rezept_anfordern: 3,
  arbeitsunfaehigkeit: 4,
  befundauskunft: 5,
  termin_verschieben: 6,
  termin_absagen: 7,
  laborbefund: 8,
  ueberweisung: 9,
  allgemeine_info: 10
};

// Geschätzte Bearbeitungszeit pro Intent (in Minuten)
const PROCESSING_DURATION: { [intent: string]: number } = {
  notfall: 0, // Sofortige Weiterleitung
  termin_anfragen: 2,
  termin_verschieben: 1,
  termin_absagen: 1,
  rezept_anfordern: 1,
  arbeitsunfaehigkeit: 3,
  befundauskunft: 2,
  laborbefund: 2,
  ueberweisung: 2,
  allgemeine_info: 1
};

/**
 * Gruppiert Intent-Items nach Intent-Typ
 * @param items Die Intent-Items
 * @returns Eine Map von Intent-Typ zu Bucket
 */
export function splitByIntent(items: IntentItem[]): Map<IntentType, IntentBucket> {
  const buckets = new Map<IntentType, IntentBucket>();
  
  for (const item of items) {
    const intent = item.intent;
    
    if (!buckets.has(intent)) {
      buckets.set(intent, {
        intent,
        items: [],
        confidence: 0,
        priority: INTENT_PRIORITIES[intent] || 99
      });
    }
    
    const bucket = buckets.get(intent)!;
    bucket.items.push(item);
    
    // Konfidenz neu berechnen (gewichteter Durchschnitt)
    bucket.confidence = bucket.items.reduce(
      (sum, item) => sum + item.confidence, 
      0
    ) / bucket.items.length;
  }
  
  return buckets;
}

/**
 * Priorisiert Intent-Buckets nach Wichtigkeit und Konfidenz
 * @param buckets Die Intent-Buckets
 * @returns Die priorisierten Buckets
 */
export function prioritizeIntents(buckets: Map<IntentType, IntentBucket>): IntentBucket[] {
  const bucketsArray = Array.from(buckets.values());
  
  // Sortiere nach Priorität (niedrigere Zahl = höhere Priorität), dann nach Konfidenz
  return bucketsArray.sort((a, b) => {
    if (a.priority !== b.priority) {
      return a.priority - b.priority;
    }
    return b.confidence - a.confidence; // Höhere Konfidenz zuerst
  });
}

/**
 * Erstellt einen Verarbeitungsplan für Multi-Intent-E-Mails
 * @param items Die Intent-Items
 * @returns Ein strukturierter Verarbeitungsplan
 */
export function createProcessingPlan(items: IntentItem[]): ProcessingPlan {
  const bucketMap = splitByIntent(items);
  const prioritizedBuckets = prioritizeIntents(bucketMap);
  
  const processingOrder = prioritizedBuckets.map(bucket => bucket.intent);
  const estimatedDuration = prioritizedBuckets.reduce(
    (total, bucket) => total + (PROCESSING_DURATION[bucket.intent] || 1) * bucket.items.length,
    0
  );
  
  return {
    buckets: prioritizedBuckets,
    totalItems: items.length,
    multiIntent: bucketMap.size > 1,
    processingOrder,
    estimatedDuration
  };
}

/**
 * Findet das Intent-Item mit der höchsten Konfidenz
 * @param items Die Intent-Items
 * @returns Das Item mit der höchsten Konfidenz
 */
export function findHighestConfidenceItem(items: IntentItem[]): IntentItem | null {
  if (items.length === 0) {
    return null;
  }
  
  return items.reduce((highest, current) => 
    current.confidence > highest.confidence ? current : highest
  );
}

/**
 * Findet das wichtigste Intent basierend auf Priorität und Konfidenz
 * @param buckets Die Intent-Buckets
 * @returns Das wichtigste Intent oder null
 */
export function findPrimaryIntent(buckets: IntentBucket[]): IntentBucket | null {
  if (buckets.length === 0) {
    return null;
  }
  
  // Notfälle haben immer Vorrang
  const emergency = buckets.find(bucket => bucket.intent === "notfall");
  if (emergency) {
    return emergency;
  }
  
  // Sonst das erste nach Priorität sortierte
  return buckets[0];
}

/**
 * Gruppiert Intent-Items nach Verarbeitungsreihenfolge
 * @param plan Der Verarbeitungsplan
 * @returns Array von Item-Gruppen in Verarbeitungsreihenfolge
 */
export function groupByProcessingOrder(plan: ProcessingPlan): IntentItem[][] {
  return plan.buckets.map(bucket => bucket.items);
}

/**
 * Prüft, ob Intent-Kombinationen sinnvoll zusammen verarbeitet werden können
 * @param intents Array von Intent-Typen
 * @returns true, wenn die Kombination sinnvoll ist
 */
export function areIntentsCompatible(intents: IntentType[]): boolean {
  // Notfälle können nicht mit anderen Intents kombiniert werden
  if (intents.includes("notfall") && intents.length > 1) {
    return false;
  }
  
  // Termin-Operationen können kombiniert werden
  const terminIntents = ["termin_anfragen", "termin_verschieben", "termin_absagen"];
  const hasTerminIntent = intents.some(intent => terminIntents.includes(intent));
  
  if (hasTerminIntent) {
    // Termin-Intents nur mit Rezept oder allgemeinen Infos kombinierbar
    const compatibleWithTermin = [...terminIntents, "rezept_anfordern", "allgemeine_info"];
    return intents.every(intent => compatibleWithTermin.includes(intent));
  }
  
  // Andere Kombinationen sind normalerweise ok
  return true;
}

/**
 * Schlägt eine optimale Verarbeitungsstrategie vor
 * @param plan Der Verarbeitungsplan
 * @returns Eine Verarbeitungsstrategie
 */
export function suggestProcessingStrategy(plan: ProcessingPlan): {
  strategy: "sequential" | "parallel" | "split";
  reason: string;
  groups: IntentItem[][];
} {
  // Notfälle immer sofort und einzeln
  if (plan.buckets.some(bucket => bucket.intent === "notfall")) {
    const emergencyItems = plan.buckets
      .filter(bucket => bucket.intent === "notfall")
      .flatMap(bucket => bucket.items);
    
    return {
      strategy: "split",
      reason: "Notfall erkannt - sofortige Bearbeitung erforderlich",
      groups: [emergencyItems]
    };
  }
  
  // Bei vielen verschiedenen Intents: aufteilen
  if (plan.buckets.length > 3) {
    return {
      strategy: "split",
      reason: "Zu viele verschiedene Anliegen - Aufteilung empfohlen",
      groups: plan.buckets.map(bucket => bucket.items)
    };
  }
  
  // Bei kompatiblen Intents: parallel verarbeiten
  const intents = plan.buckets.map(bucket => bucket.intent);
  if (areIntentsCompatible(intents)) {
    return {
      strategy: "parallel",
      reason: "Kompatible Anliegen - parallele Bearbeitung möglich",
      groups: [plan.buckets.flatMap(bucket => bucket.items)]
    };
  }
  
  // Standard: sequenziell nach Priorität
  return {
    strategy: "sequential",
    reason: "Standard-Verarbeitung nach Priorität",
    groups: plan.buckets.map(bucket => bucket.items)
  };
}

/**
 * Analysiert die Komplexität einer Multi-Intent-Anfrage
 * @param plan Der Verarbeitungsplan
 * @returns Komplexitätsanalyse
 */
export function analyzeComplexity(plan: ProcessingPlan): {
  level: "simple" | "medium" | "complex" | "critical";
  score: number; // 0-1
  factors: string[];
} {
  let score = 0;
  const factors: string[] = [];
  
  // Anzahl verschiedener Intents
  if (plan.buckets.length > 1) {
    score += 0.2 * Math.min(plan.buckets.length - 1, 3);
    factors.push(`${plan.buckets.length} verschiedene Anliegen`);
  }
  
  // Notfälle erhöhen Komplexität drastisch
  if (plan.buckets.some(bucket => bucket.intent === "notfall")) {
    score += 0.5;
    factors.push("Notfall erkannt");
  }
  
  // Niedrige Konfidenz erhöht Komplexität
  const avgConfidence = plan.buckets.reduce(
    (sum, bucket) => sum + bucket.confidence, 
    0
  ) / plan.buckets.length;
  
  if (avgConfidence < 0.6) {
    score += 0.3;
    factors.push("Niedrige Erkennungssicherheit");
  }
  
  // Geschätzte Bearbeitungszeit
  if (plan.estimatedDuration > 5) {
    score += 0.2;
    factors.push("Längere Bearbeitungszeit erwartet");
  }
  
  // Inkompatible Intent-Kombinationen
  const intents = plan.buckets.map(bucket => bucket.intent);
  if (!areIntentsCompatible(intents)) {
    score += 0.3;
    factors.push("Inkompatible Anliegen-Kombination");
  }
  
  // Level bestimmen
  let level: "simple" | "medium" | "complex" | "critical";
  if (score >= 0.8) {
    level = "critical";
  } else if (score >= 0.5) {
    level = "complex";
  } else if (score >= 0.3) {
    level = "medium";
  } else {
    level = "simple";
  }
  
  return { level, score, factors };
}

/**
 * Erstellt eine Zusammenfassung der erkannten Intents
 * @param plan Der Verarbeitungsplan
 * @returns Eine menschenlesbare Zusammenfassung
 */
export function summarizeIntents(plan: ProcessingPlan): string {
  if (plan.buckets.length === 0) {
    return "Keine Anliegen erkannt";
  }
  
  if (plan.buckets.length === 1) {
    const bucket = plan.buckets[0];
    const intentName = getIntentDisplayName(bucket.intent);
    return `Ein Anliegen erkannt: ${intentName} (${Math.round(bucket.confidence * 100)}% Sicherheit)`;
  }
  
  const intentNames = plan.buckets.map(bucket => 
    `${getIntentDisplayName(bucket.intent)} (${Math.round(bucket.confidence * 100)}%)`
  );
  
  return `${plan.buckets.length} Anliegen erkannt: ${intentNames.join(', ')}`;
}

/**
 * Wandelt Intent-Typen in benutzerfreundliche Namen um
 * @param intent Der Intent-Typ
 * @returns Der benutzerfreundliche Name
 */
function getIntentDisplayName(intent: IntentType): string {
  const displayNames: { [key: string]: string } = {
    termin_anfragen: "Terminanfrage",
    termin_verschieben: "Termin verschieben",
    termin_absagen: "Termin absagen",
    rezept_anfordern: "Rezeptanfrage",
    arbeitsunfaehigkeit: "Arbeitsunfähigkeitsbescheinigung",
    befundauskunft: "Befundauskunft",
    allgemeine_info: "Allgemeine Information",
    notfall: "Notfall",
    laborbefund: "Laborbefund",
    ueberweisung: "Überweisung"
  };
  
  return displayNames[intent] || intent;
}
