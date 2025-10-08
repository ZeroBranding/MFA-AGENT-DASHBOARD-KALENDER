/**
 * Hauptpipeline für E-Mail-Klassifikation und Intent-Erkennung
 * Orchestriert den gesamten Verarbeitungsprozess
 */

import { parseIntentJSON, createEmptyResponse } from "../intents/validate";
import { normalizeDateTimeSlots } from "../time/normalize";
import { gate, GateDecision } from "../intents/gates";
import { createProcessingPlan, ProcessingPlan, analyzeComplexity } from "../intents/multi";
import { IntentResponse, IntentItem } from "../intents/types";

export interface ClassificationResult {
  // Eingabe
  originalEmail: string;
  timestamp: string;
  
  // LLM-Verarbeitung
  llmResponse: string;
  llmModel?: string;
  llmDuration?: number;
  
  // Parsing und Validierung
  parsed: IntentResponse;
  normalized: IntentResponse;
  parsingError?: string;
  
  // Entscheidung und Planung
  decision: GateDecision;
  processingPlan: ProcessingPlan;
  complexity: ReturnType<typeof analyzeComplexity>;
  
  // Metadaten
  success: boolean;
  error?: string;
  warnings: string[];
}

export interface ClassificationOptions {
  slotDurationMinutes?: number;
  normalizeSlots?: boolean;
  llmModel?: string;
  enableFallback?: boolean;
  timeout?: number;
}

export interface LLMProvider {
  generateResponse(email: string, model?: string): Promise<{
    response: string;
    model: string;
    duration: number;
  }>;
}

const DEFAULT_OPTIONS: Required<ClassificationOptions> = {
  slotDurationMinutes: 15,
  normalizeSlots: true,
  llmModel: "claude-3.5-sonnet",
  enableFallback: true,
  timeout: 30000
};

/**
 * Erstellt den optimierten Prompt für Intent-Erkennung
 * @param email Die E-Mail
 * @returns Der Prompt
 */
function createIntentPrompt(email: string): string {
  return `Du bist eine präzise Intent-Extraktions-Engine für medizinische E-Mails an eine Arztpraxis.
Liefere AUSSCHLIESSLICH valides JSON gemäß Schema, ohne Kommentare oder Erklärungen.

JSON-Schema:
{
  "email_meta": {
    "language": "de",
    "received_at_iso": "string | null",
    "priority_indicator": "normal | urgent | emergency | null"
  },
  "items": [
    {
      "intent": "termin_anfragen | termin_verschieben | termin_absagen | rezept_anfordern | arbeitsunfaehigkeit | befundauskunft | allgemeine_info | notfall | laborbefund | ueberweisung",
      "confidence": "0..1",
      "slots": {
        "datum": "YYYY-MM-DD | null | string (bei relativen Angaben)",
        "zeit": "HH:MM-HH:MM | HH:MM | null | string (bei relativen Angaben)",
        "dringlichkeit": "hoch | normal | niedrig | null",
        "grund": "string | null",
        "person_name": "string | null",
        "geburtsdatum": "DD.MM.YYYY | null",
        "versicherung": "gesetzlich | privat | null",
        "medikament": "string | null",
        "symptome": "string | null",
        "kontakt": "string | null",
        "freie_form": "string | null"
      },
      "next_action": "slots_vervollstaendigen | termin_vorschlagen | rueckfrage_senden | eskalieren | notfall_protokoll | sofort_termin",
      "notes": "string (kurze Begründung)"
    }
  ],
  "overall": {
    "top_intent": "wie oben",
    "max_confidence": "0..1",
    "multi_intent": "true|false",
    "sentiment": "positiv | neutral | negativ | null",
    "requires_human": "true|false"
  }
}

Regeln:
- Erkenne medizinische Notfälle (Brustschmerzen, Atemnot, etc.) → intent="notfall", confidence=1.0, next_action="notfall_protokoll"
- Validiere auf Plausibilität: Datum/Zeit nur an Werktagen Mo-Fr 08:00-18:00, Mi 08:00-12:00
- Relative Zeitangaben ("morgen", "nächste Woche") als Slots unverändert belassen
- Mehrere Anliegen → mehrere items
- Bei Unsicherheit: confidence < 0.5 und next_action = "eskalieren"
- Wenn Slots fehlen: next_action = "slots_vervollstaendigen"
- Bei Dringlichkeit: Priorisiere entsprechend
- KEINE Erklärtexte ausgeben, nur JSON

E-Mail:
"""
${email.trim()}
"""`;
}

/**
 * Klassifiziert eine E-Mail mit einem LLM-Provider
 * @param email Die E-Mail
 * @param llmProvider Der LLM-Provider
 * @param options Optionen für die Klassifikation
 * @returns Das Klassifikationsergebnis
 */
export async function classifyEmail(
  email: string,
  llmProvider: LLMProvider,
  options: Partial<ClassificationOptions> = {}
): Promise<ClassificationResult> {
  const opts = { ...DEFAULT_OPTIONS, ...options };
  const timestamp = new Date().toISOString();
  const warnings: string[] = [];
  
  try {
    // 1. LLM-Klassifikation
    console.log("Starting LLM classification...");
    const prompt = createIntentPrompt(email);
    
    const llmResult = await Promise.race([
      llmProvider.generateResponse(prompt, opts.llmModel),
      new Promise<never>((_, reject) => 
        setTimeout(() => reject(new Error("LLM timeout")), opts.timeout)
      )
    ]);
    
    console.log(`LLM response received in ${llmResult.duration}ms`);
    
    // 2. JSON parsen und validieren
    let parsed: IntentResponse;
    let parsingError: string | undefined;
    
    try {
      parsed = parseIntentJSON(llmResult.response);
      console.log(`Parsed ${parsed.items.length} intent items`);
    } catch (error) {
      parsingError = error instanceof Error ? error.message : String(error);
      console.error("Parsing failed:", parsingError);
      
      if (opts.enableFallback) {
        warnings.push("JSON-Parsing fehlgeschlagen, verwende Fallback");
        parsed = createEmptyResponse("Parsing-Fehler: " + parsingError);
      } else {
        throw error;
      }
    }
    
    // 3. Normalisierung (Datum/Zeit)
    console.log("Starting slot normalization...");
    const normalized = structuredClone(parsed);
    
    if (opts.normalizeSlots) {
      // Parallel normalisieren für bessere Performance
      const normalizations = await Promise.allSettled(
        normalized.items.map(async (item, index) => {
          try {
            const dateTime = await normalizeDateTimeSlots(
              item.slots.datum,
              item.slots.zeit,
              opts.slotDurationMinutes
            );
            
            return { index, dateTime };
          } catch (error) {
            warnings.push(`Normalisierung für Item ${index} fehlgeschlagen: ${error}`);
            return null;
          }
        })
      );
      
      // Ergebnisse in die Items einfügen
      normalizations.forEach((result, index) => {
        if (result.status === 'fulfilled' && result.value) {
          const { dateTime } = result.value;
          const item = normalized.items[index];
          
          // Datum normalisieren
          if (dateTime.date.dateOnly) {
            item.slots.datum = dateTime.date.dateOnly;
          }
          
          // Zeit normalisieren
          if (dateTime.time.timeOnly) {
            item.slots.zeit = dateTime.time.range ? 
              `${dateTime.time.range[0]}-${dateTime.time.range[1]}` : 
              dateTime.time.timeOnly;
          }
          
          // Metadaten hinzufügen
          (item as any).meta = {
            date_normalized: dateTime.date.formatted,
            time_normalized: dateTime.time.formatted,
            within_business_hours: dateTime.withinBH,
            is_relative_date: dateTime.date.isRelative,
            is_relative_time: dateTime.time.isRelative
          };
        }
      });
    }
    
    // 4. Gate-Entscheidung
    console.log("Making gate decision...");
    const decision = gate(normalized, email);
    
    // 5. Verarbeitungsplan erstellen
    console.log("Creating processing plan...");
    const processingPlan = createProcessingPlan(normalized.items);
    
    // 6. Komplexitätsanalyse
    const complexity = analyzeComplexity(processingPlan);
    
    console.log(`Classification completed successfully - Decision: ${decision.action}, Complexity: ${complexity.level}`);
    
    return {
      originalEmail: email,
      timestamp,
      llmResponse: llmResult.response,
      llmModel: llmResult.model,
      llmDuration: llmResult.duration,
      parsed,
      normalized,
      parsingError,
      decision,
      processingPlan,
      complexity,
      success: true,
      warnings
    };
    
  } catch (error) {
    console.error("Classification pipeline error:", error);
    
    const errorMessage = error instanceof Error ? error.message : String(error);
    
    // Fehlerfall: Rückgabe mit Fehlerinformation
    return {
      originalEmail: email,
      timestamp,
      llmResponse: "",
      parsed: createEmptyResponse("Kritischer Fehler"),
      normalized: createEmptyResponse("Kritischer Fehler"),
      decision: { 
        action: "ESCALATE", 
        items: [], 
        reason: "Kritischer Fehler bei der Klassifikation", 
        confidence: 0 
      },
      processingPlan: {
        buckets: [],
        totalItems: 0,
        multiIntent: false,
        processingOrder: [],
        estimatedDuration: 0
      },
      complexity: {
        level: "critical",
        score: 1.0,
        factors: ["Klassifikationsfehler"]
      },
      success: false,
      error: errorMessage,
      warnings
    };
  }
}

/**
 * Batch-Klassifikation für mehrere E-Mails
 * @param emails Array von E-Mails
 * @param llmProvider Der LLM-Provider
 * @param options Optionen
 * @returns Array von Klassifikationsergebnissen
 */
export async function classifyEmailBatch(
  emails: string[],
  llmProvider: LLMProvider,
  options: Partial<ClassificationOptions> = {}
): Promise<ClassificationResult[]> {
  console.log(`Starting batch classification for ${emails.length} emails`);
  
  // Parallel verarbeiten (mit Begrenzung)
  const BATCH_SIZE = 3; // Maximal 3 gleichzeitige LLM-Anfragen
  const results: ClassificationResult[] = [];
  
  for (let i = 0; i < emails.length; i += BATCH_SIZE) {
    const batch = emails.slice(i, i + BATCH_SIZE);
    
    const batchPromises = batch.map(email => 
      classifyEmail(email, llmProvider, options)
    );
    
    const batchResults = await Promise.all(batchPromises);
    results.push(...batchResults);
    
    console.log(`Completed batch ${Math.floor(i / BATCH_SIZE) + 1}/${Math.ceil(emails.length / BATCH_SIZE)}`);
  }
  
  return results;
}

/**
 * Validiert ein Klassifikationsergebnis
 * @param result Das Ergebnis
 * @returns Validierungsfehler oder null
 */
export function validateClassificationResult(result: ClassificationResult): string[] {
  const errors: string[] = [];
  
  // Grundlegende Validierung
  if (!result.success && !result.error) {
    errors.push("Ergebnis als fehlgeschlagen markiert, aber kein Fehler angegeben");
  }
  
  if (result.parsed.items.length === 0 && result.success) {
    errors.push("Keine Intent-Items erkannt, aber als erfolgreich markiert");
  }
  
  // Intent-spezifische Validierung
  for (const item of result.normalized.items) {
    if (item.confidence < 0 || item.confidence > 1) {
      errors.push(`Ungültige Konfidenz für ${item.intent}: ${item.confidence}`);
    }
    
    if (item.intent === "notfall" && result.decision.action !== "EMERGENCY") {
      errors.push("Notfall erkannt, aber nicht als Emergency eingestuft");
    }
  }
  
  // Konsistenz zwischen parsed und normalized prüfen
  if (result.parsed.items.length !== result.normalized.items.length) {
    errors.push("Anzahl Items zwischen parsed und normalized inkonsistent");
  }
  
  return errors;
}

/**
 * Erstellt eine Zusammenfassung des Klassifikationsergebnisses
 * @param result Das Ergebnis
 * @returns Eine menschenlesbare Zusammenfassung
 */
export function summarizeClassificationResult(result: ClassificationResult): string {
  if (!result.success) {
    return `Klassifikation fehlgeschlagen: ${result.error}`;
  }
  
  const itemCount = result.normalized.items.length;
  const confidence = Math.round(result.parsed.overall.max_confidence * 100);
  const complexity = result.complexity.level;
  const decision = result.decision.action;
  
  let summary = `${itemCount} Anliegen erkannt (${confidence}% Sicherheit), `;
  summary += `Komplexität: ${complexity}, Entscheidung: ${decision}`;
  
  if (result.warnings.length > 0) {
    summary += `, ${result.warnings.length} Warnung(en)`;
  }
  
  return summary;
}

/**
 * Exportiert Klassifikationsdaten für Debugging
 * @param result Das Ergebnis
 * @returns Debug-Informationen
 */
export function exportDebugInfo(result: ClassificationResult): object {
  return {
    timestamp: result.timestamp,
    llm: {
      model: result.llmModel,
      duration: result.llmDuration,
      response_length: result.llmResponse.length
    },
    parsing: {
      success: !result.parsingError,
      error: result.parsingError
    },
    items: result.normalized.items.map(item => ({
      intent: item.intent,
      confidence: item.confidence,
      slots_filled: Object.values(item.slots).filter(v => v !== null).length,
      next_action: item.next_action
    })),
    decision: {
      action: result.decision.action,
      confidence: result.decision.confidence,
      reason: result.decision.reason
    },
    complexity: result.complexity,
    warnings: result.warnings
  };
}
