/**
 * Intent-Erkennungs-System für medizinische E-Mails
 * Typdefinitionen für Intent-Klassifikation und Slot-Filling
 */

export type IntentType =
  | "termin_anfragen"
  | "termin_verschieben"
  | "termin_absagen"
  | "rezept_anfordern"
  | "arbeitsunfaehigkeit"
  | "befundauskunft"
  | "allgemeine_info"
  | "notfall"
  | "laborbefund"
  | "ueberweisung";

export type NextAction =
  | "slots_vervollstaendigen"
  | "termin_vorschlagen"
  | "rueckfrage_senden"
  | "eskalieren"
  | "notfall_protokoll"
  | "sofort_termin";

export type PriorityLevel = "normal" | "urgent" | "emergency" | null;
export type Sentiment = "positiv" | "neutral" | "negativ" | null;
export type Dringlichkeit = "hoch" | "normal" | "niedrig" | null;
export type Versicherung = "gesetzlich" | "privat" | null;

export interface IntentSlots {
  datum: string | null;        // "YYYY-MM-DD" oder raw wie "morgen"
  zeit: string | null;         // "HH:MM" | "HH:MM-HH:MM"
  dringlichkeit: Dringlichkeit;
  grund: string | null;
  person_name: string | null;
  geburtsdatum: string | null; // "DD.MM.YYYY"
  versicherung: Versicherung;
  medikament: string | null;
  symptome: string | null;
  kontakt: string | null;
  freie_form: string | null;
}

export interface IntentItem {
  intent: IntentType;
  confidence: number; // 0..1
  slots: IntentSlots;
  next_action: NextAction;
  notes: string;
}

export interface IntentResponse {
  email_meta: { 
    language: "de"; 
    received_at_iso: string | null;
    priority_indicator: PriorityLevel;
  };
  items: IntentItem[];
  overall: { 
    top_intent: IntentType; 
    max_confidence: number; 
    multi_intent: boolean;
    sentiment: Sentiment;
    requires_human: boolean;
  };
}

// Konstanten für die Intent-Typen und Aktionen
export const INTENT_TYPES: ReadonlyArray<IntentType> = [
  "termin_anfragen",
  "termin_verschieben", 
  "termin_absagen",
  "rezept_anfordern",
  "arbeitsunfaehigkeit",
  "befundauskunft",
  "allgemeine_info",
  "notfall",
  "laborbefund",
  "ueberweisung"
] as const;

export const NEXT_ACTIONS: ReadonlyArray<NextAction> = [
  "slots_vervollstaendigen",
  "termin_vorschlagen",
  "rueckfrage_senden", 
  "eskalieren",
  "notfall_protokoll",
  "sofort_termin"
] as const;

// Notfall-Keywords für schnelle Erkennung
export const EMERGENCY_KEYWORDS = [
  "notfall", "dringend", "sofort", "akut", "schmerzen", "atemnot", 
  "brustschmerzen", "herzinfarkt", "schlaganfall", "bewusstlos",
  "blutung", "vergiftung", "unfall", "sturz", "kollaps"
] as const;

// Medizinische Keywords für Topic-Filter
export const MEDICAL_KEYWORDS = [
  "arzt", "doktor", "praxis", "termin", "behandlung", "medizin", 
  "medikament", "rezept", "überweisung", "attest", "krankheit", 
  "symptom", "schmerz", "untersuchung", "therapie", "gesundheit",
  "patient", "sprechstunde", "hausarzt", "facharzt"
] as const;
