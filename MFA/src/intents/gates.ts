/**
 * Entscheidungslogik für Intent-Verarbeitung
 * Bestimmt, wie mit erkannten Intents umgegangen werden soll
 */

import type { IntentResponse, IntentItem, IntentType } from "./types";
import { EMERGENCY_KEYWORDS } from "./types";

export type GateDecision =
  | { action: "AUTO_PROCESS"; items: IntentItem[]; confidence: number; reason: string }
  | { action: "ASK_CONFIRM"; items: IntentItem[]; reason: string; confidence: number; missingSlots?: string[] }
  | { action: "ESCALATE"; items: IntentItem[]; reason: string; confidence: number }
  | { action: "EMERGENCY"; items: IntentItem[]; reason: string; urgency: "high" | "critical" };

export interface GateConfig {
  autoProcessThreshold: number;    // >= diesem Wert: automatisch verarbeiten
  confirmThreshold: number;        // >= diesem Wert: Bestätigung einholen
  escalateThreshold: number;       // < diesem Wert: eskalieren
  emergencyKeywords: string[];     // Keywords für Notfälle
  requiredSlots: { [intent: string]: string[] }; // Pflichtfelder pro Intent
}

const DEFAULT_CONFIG: GateConfig = {
  autoProcessThreshold: 0.85,
  confirmThreshold: 0.5,
  escalateThreshold: 0.5,
  emergencyKeywords: [...EMERGENCY_KEYWORDS],
  requiredSlots: {
    termin_anfragen: ["datum", "zeit"],
    termin_verschieben: ["datum"],
    termin_absagen: [],
    rezept_anfordern: ["medikament"],
    arbeitsunfaehigkeit: ["grund"],
    befundauskunft: [],
    laborbefund: [],
    ueberweisung: ["grund"],
    notfall: [],
    allgemeine_info: []
  }
};

let gateConfig: GateConfig = { ...DEFAULT_CONFIG };

/**
 * Konfiguriert die Gate-Parameter
 * @param config Die neue Konfiguration
 */
export function configureGates(config: Partial<GateConfig>): void {
  gateConfig = { ...gateConfig, ...config };
}

/**
 * Entscheidet, wie mit einer Intent-Erkennung umgegangen werden soll
 * @param resp Die Intent-Response
 * @param originalText Der Original-E-Mail-Text (für Notfall-Prüfung)
 * @returns Die Entscheidung
 */
export function gate(resp: IntentResponse, originalText?: string): GateDecision {
  // 1. Notfälle haben oberste Priorität
  const emergencyDecision = checkForEmergency(resp, originalText);
  if (emergencyDecision) {
    return emergencyDecision;
  }
  
  // 2. Wenn LLM explizit menschliche Bearbeitung empfiehlt
  if (resp.overall.requires_human) {
    return { 
      action: "ESCALATE", 
      items: resp.items, 
      reason: "LLM empfiehlt menschliche Bearbeitung",
      confidence: resp.overall.max_confidence
    };
  }
  
  const c = resp.overall.max_confidence;
  
  // 3. Hohe Konfidenz: Prüfe Vollständigkeit und verarbeite automatisch
  if (c >= gateConfig.autoProcessThreshold) {
    const missingSlots = findMissingSlots(resp.items);
    
    if (missingSlots.length === 0) {
      return { 
        action: "AUTO_PROCESS", 
        items: resp.items,
        confidence: c,
        reason: "Hohe Konfidenz und alle Slots verfügbar"
      };
    } else {
      return { 
        action: "ASK_CONFIRM", 
        items: resp.items, 
        reason: "Hohe Konfidenz, aber fehlende Informationen",
        confidence: c,
        missingSlots
      };
    }
  }
  
  // 4. Mittlere Konfidenz: Bestätigung einholen
  if (c >= gateConfig.confirmThreshold) {
    const missingSlots = findMissingSlots(resp.items);
    
    return { 
      action: "ASK_CONFIRM", 
      items: resp.items, 
      reason: "Mittlere Sicherheit bei der Erkennung",
      confidence: c,
      missingSlots: missingSlots.length > 0 ? missingSlots : undefined
    };
  }
  
  // 5. Niedrige Konfidenz: an Menschen eskalieren
  return { 
    action: "ESCALATE", 
    items: resp.items, 
    reason: "Niedrige Sicherheit bei der Erkennung",
    confidence: c
  };
}

/**
 * Prüft auf medizinische Notfälle
 * @param resp Die Intent-Response
 * @param originalText Der Original-E-Mail-Text
 * @returns Emergency-Decision oder null
 */
function checkForEmergency(resp: IntentResponse, originalText?: string): GateDecision | null {
  // 1. Intent-basierte Notfall-Erkennung
  const emergencyItems = resp.items.filter(item => 
    item.intent === "notfall" || 
    item.next_action === "notfall_protokoll"
  );
  
  if (emergencyItems.length > 0) {
    const highestConfidence = Math.max(...emergencyItems.map(item => item.confidence));
    
    return { 
      action: "EMERGENCY", 
      items: emergencyItems, 
      reason: "Notfall-Intent erkannt",
      urgency: highestConfidence > 0.8 ? "critical" : "high"
    };
  }
  
  // 2. Keyword-basierte Notfall-Erkennung im Original-Text
  if (originalText) {
    const lowerText = originalText.toLowerCase();
    const foundEmergencyKeywords = gateConfig.emergencyKeywords.filter(keyword => 
      lowerText.includes(keyword.toLowerCase())
    );
    
    if (foundEmergencyKeywords.length > 0) {
      // Erstelle ein Emergency-Item
      const emergencyItem: IntentItem = {
        intent: "notfall",
        confidence: 0.9,
        slots: {
          datum: null,
          zeit: null,
          dringlichkeit: "hoch",
          grund: `Notfall-Keywords erkannt: ${foundEmergencyKeywords.join(', ')}`,
          person_name: null,
          geburtsdatum: null,
          versicherung: null,
          medikament: null,
          symptome: foundEmergencyKeywords.join(', '),
          kontakt: null,
          freie_form: originalText.substring(0, 200)
        },
        next_action: "notfall_protokoll",
        notes: `Automatische Notfall-Erkennung durch Keywords: ${foundEmergencyKeywords.join(', ')}`
      };
      
      return {
        action: "EMERGENCY",
        items: [emergencyItem],
        reason: `Notfall-Keywords erkannt: ${foundEmergencyKeywords.join(', ')}`,
        urgency: foundEmergencyKeywords.some(kw => 
          ["herzinfarkt", "schlaganfall", "bewusstlos", "atemnot"].includes(kw)
        ) ? "critical" : "high"
      };
    }
  }
  
  return null;
}

/**
 * Findet fehlende Pflichtslots für alle Items
 * @param items Die Intent-Items
 * @returns Array von fehlenden Slot-Namen
 */
function findMissingSlots(items: IntentItem[]): string[] {
  const allMissingSlots = new Set<string>();
  
  for (const item of items) {
    const requiredSlots = gateConfig.requiredSlots[item.intent] || [];
    
    for (const requiredSlot of requiredSlots) {
      const slotValue = item.slots[requiredSlot as keyof typeof item.slots];
      
      if (!slotValue || (typeof slotValue === 'string' && slotValue.trim() === '')) {
        allMissingSlots.add(requiredSlot);
      }
    }
  }
  
  return Array.from(allMissingSlots);
}

/**
 * Prüft, ob ein Intent-Item vollständig ist
 * @param item Das Intent-Item
 * @returns true, wenn alle benötigten Slots gefüllt sind
 */
export function isItemComplete(item: IntentItem): boolean {
  const requiredSlots = gateConfig.requiredSlots[item.intent] || [];
  
  for (const requiredSlot of requiredSlots) {
    const slotValue = item.slots[requiredSlot as keyof typeof item.slots];
    
    if (!slotValue || (typeof slotValue === 'string' && slotValue.trim() === '')) {
      return false;
    }
  }
  
  return true;
}

/**
 * Bewertet die Dringlichkeit eines Intent-Items
 * @param item Das Intent-Item
 * @param originalText Der Original-E-Mail-Text
 * @returns Dringlichkeitsscore (0-1)
 */
export function assessUrgency(item: IntentItem, originalText?: string): number {
  let urgencyScore = 0;
  
  // 1. Intent-basierte Dringlichkeit
  switch (item.intent) {
    case "notfall":
      urgencyScore += 1.0;
      break;
    case "termin_anfragen":
      urgencyScore += item.slots.dringlichkeit === "hoch" ? 0.8 : 
                     item.slots.dringlichkeit === "normal" ? 0.4 : 0.2;
      break;
    case "rezept_anfordern":
      urgencyScore += 0.6;
      break;
    case "arbeitsunfaehigkeit":
      urgencyScore += 0.7;
      break;
    default:
      urgencyScore += 0.3;
  }
  
  // 2. Keyword-basierte Dringlichkeit im Text
  if (originalText) {
    const urgentKeywords = [
      "dringend", "eilig", "sofort", "asap", "urgent", "schnell",
      "heute noch", "so schnell wie möglich", "notfall"
    ];
    
    const lowerText = originalText.toLowerCase();
    const urgentKeywordCount = urgentKeywords.filter(keyword => 
      lowerText.includes(keyword)
    ).length;
    
    urgencyScore += urgentKeywordCount * 0.2;
  }
  
  // 3. Zeitbezogene Dringlichkeit
  if (item.slots.datum || item.slots.zeit) {
    const dateText = (item.slots.datum || '') + ' ' + (item.slots.zeit || '');
    if (dateText.includes('heute') || dateText.includes('sofort')) {
      urgencyScore += 0.3;
    }
  }
  
  return Math.min(urgencyScore, 1.0);
}

/**
 * Erstellt eine Begründung für eine Gate-Entscheidung
 * @param decision Die Entscheidung
 * @returns Eine menschenlesbare Begründung
 */
export function explainDecision(decision: GateDecision): string {
  switch (decision.action) {
    case "AUTO_PROCESS":
      return `Automatische Verarbeitung (Konfidenz: ${Math.round(decision.confidence * 100)}%)`;
      
    case "ASK_CONFIRM":
      let explanation = `Bestätigung erforderlich (Konfidenz: ${Math.round(decision.confidence * 100)}%)`;
      if (decision.missingSlots && decision.missingSlots.length > 0) {
        explanation += `. Fehlende Informationen: ${decision.missingSlots.join(', ')}`;
      }
      return explanation;
      
    case "ESCALATE":
      return `Weiterleitung an menschlichen Operator (Konfidenz: ${Math.round(decision.confidence * 100)}%)`;
      
    case "EMERGENCY":
      return `NOTFALL erkannt! Sofortige Aufmerksamkeit erforderlich (${decision.urgency})`;
      
    default:
      return "Unbekannte Entscheidung";
  }
}

/**
 * Prüft, ob eine Entscheidung eine Rückfrage erfordert
 * @param decision Die Entscheidung
 * @returns true, wenn eine Rückfrage nötig ist
 */
export function requiresFollowUp(decision: GateDecision): boolean {
  return decision.action === "ASK_CONFIRM" || 
         (decision.action === "AUTO_PROCESS" && decision.reason.includes("fehlende"));
}

/**
 * Generiert Rückfragen basierend auf fehlenden Slots
 * @param missingSlots Die fehlenden Slots
 * @param intent Der Intent-Typ
 * @returns Array von Rückfragen
 */
export function generateFollowUpQuestions(missingSlots: string[], intent: IntentType): string[] {
  const questions: string[] = [];
  
  const slotQuestions: { [key: string]: string } = {
    datum: "An welchem Tag möchten Sie den Termin?",
    zeit: "Zu welcher Uhrzeit soll der Termin stattfinden?",
    grund: "Was ist der Grund für Ihren Besuch?",
    medikament: "Welches Medikament benötigen Sie?",
    person_name: "Wie ist Ihr vollständiger Name?",
    geburtsdatum: "Wie ist Ihr Geburtsdatum?",
    kontakt: "Unter welcher Telefonnummer können wir Sie erreichen?"
  };
  
  for (const slot of missingSlots) {
    if (slotQuestions[slot]) {
      questions.push(slotQuestions[slot]);
    }
  }
  
  return questions;
}
