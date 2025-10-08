/**
 * JSON-Validierung für Intent-Responses mit Zod
 * Parst und validiert LLM-Ausgaben zu strukturierten Intent-Objekten
 */

import { z } from "zod";
import { IntentResponse, IntentType, NextAction, INTENT_TYPES, NEXT_ACTIONS } from "./types";
import { jsonrepair } from "jsonrepair";

// Zod-Schema für Slot-Validierung
const Slots = z.object({
  datum: z.string().nullable(),
  zeit: z.string().nullable(),
  dringlichkeit: z.enum(["hoch", "normal", "niedrig"]).nullable(),
  grund: z.string().nullable(),
  person_name: z.string().nullable(),
  geburtsdatum: z.string().nullable(),
  versicherung: z.enum(["gesetzlich", "privat"]).nullable(),
  medikament: z.string().nullable(),
  symptome: z.string().nullable(),
  kontakt: z.string().nullable(),
  freie_form: z.string().nullable(),
});

// Zod-Schema für Intent-Items
const IntentItem = z.object({
  intent: z.enum(INTENT_TYPES as unknown as [IntentType, ...IntentType[]]),
  confidence: z.number().min(0).max(1),
  slots: Slots,
  next_action: z.enum(NEXT_ACTIONS as unknown as [NextAction, ...NextAction[]]),
  notes: z.string(),
});

// Hauptschema für Intent-Response
const IntentResponseSchema = z.object({
  email_meta: z.object({
    language: z.literal("de"),
    received_at_iso: z.string().nullable(),
    priority_indicator: z.enum(["normal", "urgent", "emergency"]).nullable(),
  }),
  items: z.array(IntentItem).min(1),
  overall: z.object({
    top_intent: z.enum(INTENT_TYPES as unknown as [IntentType, ...IntentType[]]),
    max_confidence: z.number().min(0).max(1),
    multi_intent: z.boolean(),
    sentiment: z.enum(["positiv", "neutral", "negativ"]).nullable(),
    requires_human: z.boolean(),
  }),
});

/**
 * Parst und validiert eine JSON-Antwort des LLM-Modells
 * @param raw Die Rohausgabe des LLM-Modells
 * @returns Ein validiertes IntentResponse-Objekt
 * @throws Error bei ungültigem JSON oder Validierungsfehlern
 */
export function parseIntentJSON(raw: string): IntentResponse {
  try {
    let txt = raw.trim();
    
    // Entferne Codefences, falls vorhanden
    if (txt.startsWith("```")) {
      txt = txt.replace(/^```[a-zA-Z]*\n?/, "").replace(/```$/, "");
    }
    
    // Entferne eventuelle Erklärungen vor oder nach dem JSON
    const jsonStart = txt.indexOf('{');
    const jsonEnd = txt.lastIndexOf('}');
    
    if (jsonStart >= 0 && jsonEnd >= 0) {
      txt = txt.substring(jsonStart, jsonEnd + 1);
    }
    
    // Repariere häufige JSON-Fehler
    let repaired: string;
    try {
      repaired = jsonrepair(txt);
    } catch (repairError) {
      console.warn("JSON repair failed, using original:", repairError);
      repaired = txt;
    }
    
    // Parse und validiere
    const obj = JSON.parse(repaired);
    const validated = IntentResponseSchema.parse(obj);
    
    // Zusätzliche Plausibilitätsprüfungen
    validatePlausibility(validated);
    
    return validated;
  } catch (error) {
    console.error("JSON Parsing error:", error);
    console.error("Raw input:", raw.substring(0, 500) + "...");
    throw new Error(`Ungültiges Intent-JSON: ${error instanceof Error ? error.message : String(error)}`);
  }
}

/**
 * Zusätzliche Plausibilitätsprüfungen für Intent-Response
 * @param response Die validierte Response
 */
function validatePlausibility(response: IntentResponse): void {
  // Prüfe, ob top_intent auch in items vorhanden ist
  const topIntentExists = response.items.some(item => item.intent === response.overall.top_intent);
  if (!topIntentExists) {
    throw new Error(`Top intent "${response.overall.top_intent}" nicht in items gefunden`);
  }
  
  // Prüfe, ob max_confidence korrekt berechnet wurde
  const actualMaxConfidence = Math.max(...response.items.map(item => item.confidence));
  if (Math.abs(response.overall.max_confidence - actualMaxConfidence) > 0.01) {
    console.warn(`Max confidence mismatch: declared=${response.overall.max_confidence}, actual=${actualMaxConfidence}`);
  }
  
  // Prüfe multi_intent Flag
  const uniqueIntents = new Set(response.items.map(item => item.intent));
  const actualMultiIntent = uniqueIntents.size > 1;
  if (response.overall.multi_intent !== actualMultiIntent) {
    console.warn(`Multi intent mismatch: declared=${response.overall.multi_intent}, actual=${actualMultiIntent}`);
  }
}

/**
 * Erstellt ein leeres Intent-Response-Objekt für Fehlerfälle
 * @param reason Der Grund für die leere Response
 * @returns Eine leere Intent-Response
 */
export function createEmptyResponse(reason: string = "Unbekannter Fehler"): IntentResponse {
  return {
    email_meta: {
      language: "de",
      received_at_iso: null,
      priority_indicator: null
    },
    items: [{
      intent: "allgemeine_info",
      confidence: 0.1,
      slots: {
        datum: null,
        zeit: null,
        dringlichkeit: null,
        grund: null,
        person_name: null,
        geburtsdatum: null,
        versicherung: null,
        medikament: null,
        symptome: null,
        kontakt: null,
        freie_form: reason
      },
      next_action: "eskalieren",
      notes: `Fehlerhafte Klassifikation: ${reason}`
    }],
    overall: {
      top_intent: "allgemeine_info",
      max_confidence: 0.1,
      multi_intent: false,
      sentiment: null,
      requires_human: true
    }
  };
}

/**
 * Repariert häufige JSON-Probleme in LLM-Ausgaben
 * @param text Der JSON-Text
 * @returns Der reparierte JSON-Text
 */
export function preprocessJSON(text: string): string {
  let cleaned = text.trim();
  
  // Entferne häufige Prefixe
  const prefixes = ["json", "```json", "```", "JSON:"];
  for (const prefix of prefixes) {
    if (cleaned.toLowerCase().startsWith(prefix.toLowerCase())) {
      cleaned = cleaned.substring(prefix.length).trim();
    }
  }
  
  // Entferne Suffixe
  if (cleaned.endsWith("```")) {
    cleaned = cleaned.substring(0, cleaned.length - 3).trim();
  }
  
  // Repariere häufige Escape-Probleme
  cleaned = cleaned.replace(/\\"/g, '"');
  cleaned = cleaned.replace(/"\s*:\s*"([^"]*)"([^,}])/g, '": "$1"$2');
  
  return cleaned;
}

/**
 * Validiert ein einzelnes Intent-Item
 * @param item Das Intent-Item
 * @returns true, wenn das Item valide ist
 */
export function validateIntentItem(item: IntentItem): boolean {
  try {
    IntentItem.parse(item);
    return true;
  } catch (error) {
    console.error("Intent item validation failed:", error);
    return false;
  }
}
