/**
 * Datum/Zeit-Normalisierung für Intent-Slots
 * Konvertiert relative Zeitangaben in absolute ISO-Formate
 */

import { parseTimesDe, DucklingTime } from "./duckling";
import { isWithinBusinessHours } from "./businessHours";
import { parseISO, format, isValid, addMinutes, startOfDay } from "date-fns";
import { de } from "date-fns/locale";

export type NormalizedDate = {
  raw: string | null;
  iso: string | null;
  dateOnly: string | null; // YYYY-MM-DD
  formatted: string | null;
  withinBH: boolean | null;
  isRelative: boolean;
};

export type NormalizedTime = {
  raw: string | null;
  iso: string | null;
  timeOnly: string | null; // HH:MM
  range: [string, string] | null; // [start, end]
  formatted: string | null;
  isRelative: boolean;
};

export type NormalizedDateTime = {
  date: NormalizedDate;
  time: NormalizedTime;
  combined: string | null; // Vollständiger ISO-Zeitstempel
  withinBH: boolean | null;
};

/**
 * Normalisiert einen Datum-Slot
 * @param raw Der rohe Datum-String
 * @param referenceDate Referenzdatum für relative Angaben
 * @returns Das normalisierte Datum
 */
export async function normalizeDateSlot(
  raw: string | null,
  referenceDate?: Date
): Promise<NormalizedDate> {
  if (!raw) {
    return { 
      raw: null, 
      iso: null, 
      dateOnly: null,
      formatted: null, 
      withinBH: null,
      isRelative: false
    };
  }
  
  try {
    // Prüfe, ob es eine relative Zeitangabe ist
    const isRelative = isRelativeTimeExpression(raw);
    
    const hits = await parseTimesDe(raw, {
      referenceTime: referenceDate?.toISOString()
    });
    
    if (hits.length === 0) {
      return { 
        raw, 
        iso: null, 
        dateOnly: null,
        formatted: null, 
        withinBH: null,
        isRelative
      };
    }
    
    const iso = hits[0]?.value?.value ?? null;
    
    if (!iso || !isValid(parseISO(iso))) {
      return { 
        raw, 
        iso: null, 
        dateOnly: null,
        formatted: null, 
        withinBH: null,
        isRelative
      };
    }
    
    const date = parseISO(iso);
    const dateOnly = format(date, "yyyy-MM-dd");
    const formatted = format(date, "EEEE, d. MMMM yyyy", { locale: de });
    
    // Für Datum-Only-Checks nehmen wir den Beginn des Tages
    const dayStart = startOfDay(date);
    const withinBH = isWithinBusinessHours(dayStart.toISOString());
    
    return { 
      raw, 
      iso, 
      dateOnly,
      formatted, 
      withinBH,
      isRelative
    };
  } catch (error) {
    console.error("Date normalization error:", error);
    return { 
      raw, 
      iso: null, 
      dateOnly: null,
      formatted: null, 
      withinBH: null,
      isRelative: false
    };
  }
}

/**
 * Normalisiert einen Zeit-Slot
 * @param raw Der rohe Zeit-String
 * @param slotDurationMinutes Die Dauer eines Slots in Minuten
 * @param referenceDate Referenzdatum für relative Angaben
 * @returns Die normalisierte Zeit
 */
export async function normalizeTimeSlot(
  raw: string | null, 
  slotDurationMinutes: number = 15,
  referenceDate?: Date
): Promise<NormalizedTime> {
  if (!raw) {
    return { 
      raw: null, 
      iso: null, 
      timeOnly: null,
      range: null, 
      formatted: null,
      isRelative: false
    };
  }
  
  try {
    // Prüfe, ob es eine relative Zeitangabe ist
    const isRelative = isRelativeTimeExpression(raw);
    
    const hits = await parseTimesDe(raw, {
      referenceTime: referenceDate?.toISOString()
    });
    
    if (hits.length === 0) {
      return { 
        raw, 
        iso: null, 
        timeOnly: null,
        range: null, 
        formatted: null,
        isRelative
      };
    }
    
    const iso = hits[0]?.value?.value ?? null;
    
    if (!iso || !isValid(parseISO(iso))) {
      return { 
        raw, 
        iso: null, 
        timeOnly: null,
        range: null, 
        formatted: null,
        isRelative
      };
    }
    
    const date = parseISO(iso);
    const timeOnly = format(date, "HH:mm");
    
    // Slot-Ende berechnen
    const endDate = addMinutes(date, slotDurationMinutes);
    const endTimeOnly = format(endDate, "HH:mm");
    
    const range: [string, string] = [timeOnly, endTimeOnly];
    const formatted = `${timeOnly}-${endTimeOnly} Uhr`;
    
    return { 
      raw, 
      iso, 
      timeOnly,
      range, 
      formatted,
      isRelative
    };
  } catch (error) {
    console.error("Time normalization error:", error);
    return { 
      raw, 
      iso: null, 
      timeOnly: null,
      range: null, 
      formatted: null,
      isRelative: false
    };
  }
}

/**
 * Kombiniert Datum und Zeit zu einem vollständigen Normalisierungsobjekt
 * @param dateRaw Der rohe Datum-String
 * @param timeRaw Der rohe Zeit-String
 * @param slotDurationMinutes Slot-Dauer in Minuten
 * @param referenceDate Referenzdatum
 * @returns Vollständige Datum/Zeit-Normalisierung
 */
export async function normalizeDateTimeSlots(
  dateRaw: string | null,
  timeRaw: string | null,
  slotDurationMinutes: number = 15,
  referenceDate?: Date
): Promise<NormalizedDateTime> {
  // Parallel normalisieren für bessere Performance
  const [dateNorm, timeNorm] = await Promise.all([
    normalizeDateSlot(dateRaw, referenceDate),
    normalizeTimeSlot(timeRaw, slotDurationMinutes, referenceDate)
  ]);
  
  // Versuche, kombinierte ISO-Zeit zu erstellen
  let combined: string | null = null;
  let withinBH: boolean | null = null;
  
  if (dateNorm.dateOnly && timeNorm.timeOnly) {
    combined = combineDateTimeToISO(dateNorm.dateOnly, timeNorm.timeOnly);
    if (combined) {
      withinBH = isWithinBusinessHours(combined);
    }
  } else if (dateNorm.iso) {
    // Nur Datum vorhanden
    withinBH = dateNorm.withinBH;
  } else if (timeNorm.iso) {
    // Nur Zeit vorhanden - prüfe für heute
    const today = format(new Date(), "yyyy-MM-dd");
    combined = combineDateTimeToISO(today, timeNorm.timeOnly!);
    if (combined) {
      withinBH = isWithinBusinessHours(combined);
    }
  }
  
  return {
    date: dateNorm,
    time: timeNorm,
    combined,
    withinBH
  };
}

/**
 * Kombiniert Datum und Zeit zu einem vollständigen ISO-Zeitstempel
 * @param dateIso Das Datum als ISO-String (YYYY-MM-DD)
 * @param timeStr Die Zeit als String (HH:MM)
 * @returns Der kombinierte ISO-Zeitstempel
 */
export function combineDateTimeToISO(dateIso: string, timeStr: string): string | null {
  try {
    if (!dateIso || !timeStr) {
      return null;
    }
    
    const [hours, minutes] = timeStr.split(':').map(Number);
    const date = parseISO(dateIso);
    
    if (!isValid(date) || isNaN(hours) || isNaN(minutes)) {
      return null;
    }
    
    const combined = new Date(date);
    combined.setHours(hours, minutes, 0, 0);
    
    return combined.toISOString();
  } catch (error) {
    console.error("Error combining date and time:", error);
    return null;
  }
}

/**
 * Prüft, ob ein Text eine relative Zeitangabe enthält
 * @param text Der Text
 * @returns true, wenn relative Zeitangabe erkannt wurde
 */
function isRelativeTimeExpression(text: string): boolean {
  const relativePatterns = [
    /\b(heute|morgen|übermorgen)\b/i,
    /\b(nächste|kommende)\s+(woche|monat)\b/i,
    /\b(nächsten?|kommenden?)\s+(montag|dienstag|mittwoch|donnerstag|freitag|samstag|sonntag)\b/i,
    /\bin\s+\d+\s+(tagen?|wochen?|monaten?)\b/i,
    /\bvor\s+\d+\s+(tagen?|wochen?|monaten?)\b/i
  ];
  
  return relativePatterns.some(pattern => pattern.test(text));
}

/**
 * Extrahiert Zeitbereich aus einem Text (z.B. "14-16 Uhr")
 * @param text Der Text
 * @returns Zeitbereich oder null
 */
export function extractTimeRange(text: string): [string, string] | null {
  const rangePatterns = [
    /(\d{1,2}):?(\d{2})?\s*-\s*(\d{1,2}):?(\d{2})?\s*(uhr)?/i,
    /(\d{1,2})\s*bis\s*(\d{1,2})\s*(uhr)?/i,
    /von\s*(\d{1,2}):?(\d{2})?\s*bis\s*(\d{1,2}):?(\d{2})?\s*(uhr)?/i
  ];
  
  for (const pattern of rangePatterns) {
    const match = text.match(pattern);
    if (match) {
      const startHour = parseInt(match[1]);
      const startMin = parseInt(match[2] || "0");
      const endHour = parseInt(match[3] || match[2] || startHour + 1);
      const endMin = parseInt(match[4] || match[3] || "0");
      
      if (startHour >= 0 && startHour <= 23 && endHour >= 0 && endHour <= 23 &&
          startMin >= 0 && startMin <= 59 && endMin >= 0 && endMin <= 59) {
        
        const startTime = `${startHour.toString().padStart(2, '0')}:${startMin.toString().padStart(2, '0')}`;
        const endTime = `${endHour.toString().padStart(2, '0')}:${endMin.toString().padStart(2, '0')}`;
        
        return [startTime, endTime];
      }
    }
  }
  
  return null;
}

/**
 * Formatiert eine Zeitdauer in lesbaren Text
 * @param minutes Die Dauer in Minuten
 * @returns Formatierte Zeitdauer
 */
export function formatDuration(minutes: number): string {
  if (minutes < 60) {
    return `${minutes} Minuten`;
  } else if (minutes === 60) {
    return "1 Stunde";
  } else if (minutes % 60 === 0) {
    return `${minutes / 60} Stunden`;
  } else {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return `${hours} Stunde${hours > 1 ? 'n' : ''} und ${mins} Minuten`;
  }
}

/**
 * Generiert mögliche Zeitslots für einen Tag
 * @param date Das Datum
 * @param slotDuration Slot-Dauer in Minuten
 * @param bufferMinutes Puffer zwischen Slots
 * @returns Array von Zeitslots
 */
export async function generateTimeSlotsForDate(
  date: string, // YYYY-MM-DD
  slotDuration: number = 15,
  bufferMinutes: number = 5
): Promise<Array<{ start: string; end: string; available: boolean }>> {
  const slots: Array<{ start: string; end: string; available: boolean }> = [];
  
  try {
    const dateObj = parseISO(date);
    if (!isValid(dateObj)) {
      return slots;
    }
    
    // Geschäftszeiten für diesen Tag abrufen
    const { getBusinessHoursForDay, getDayKey } = await import("./businessHours");
    const dayKey = getDayKey(dateObj);
    const businessHours = getBusinessHoursForDay(dayKey);
    
    for (const [start, end] of businessHours) {
      const [startHour, startMin] = start.split(':').map(Number);
      const [endHour, endMin] = end.split(':').map(Number);
      
      let currentMinutes = startHour * 60 + startMin;
      const endMinutes = endHour * 60 + endMin;
      
      while (currentMinutes + slotDuration <= endMinutes) {
        const slotStart = new Date(dateObj);
        slotStart.setHours(Math.floor(currentMinutes / 60), currentMinutes % 60, 0, 0);
        
        const slotEnd = new Date(slotStart);
        slotEnd.setMinutes(slotEnd.getMinutes() + slotDuration);
        
        const startTime = format(slotStart, "HH:mm");
        const endTime = format(slotEnd, "HH:mm");
        
        // Hier könnte eine Verfügbarkeitsprüfung gegen den Kalender erfolgen
        const available = true; // Placeholder
        
        slots.push({
          start: startTime,
          end: endTime,
          available
        });
        
        currentMinutes += slotDuration + bufferMinutes;
      }
    }
    
    return slots;
  } catch (error) {
    console.error("Error generating time slots:", error);
    return [];
  }
}
