/**
 * Geschäftszeiten-Management für die Arztpraxis
 * Verwaltet Öffnungszeiten, Feiertage und Sonderregelungen
 */

import { parseISO, format, isValid, addDays } from "date-fns";
import { de } from "date-fns/locale";

interface BusinessHours {
  [day: string]: Array<[string, string]>; // [start, end]
}

interface Holiday {
  date: string; // YYYY-MM-DD
  name: string;
  type: "federal" | "state" | "practice";
}

// Standardwerte für Geschäftszeiten (Mo-Fr)
const DEFAULT_BUSINESS_HOURS: BusinessHours = {
  mon: [["08:00", "12:00"], ["14:00", "18:00"]],
  tue: [["08:00", "12:00"], ["14:00", "18:00"]],
  wed: [["08:00", "12:00"]], // Mittwoch nur vormittags
  thu: [["08:00", "12:00"], ["14:00", "18:00"]],
  fri: [["08:00", "13:00"]], // Freitag bis 13 Uhr
  sat: [], // Samstag geschlossen
  sun: []  // Sonntag geschlossen
};

// Deutsche Feiertage 2024/2025 (Basis)
const DEFAULT_HOLIDAYS: Holiday[] = [
  { date: "2024-01-01", name: "Neujahr", type: "federal" },
  { date: "2024-03-29", name: "Karfreitag", type: "federal" },
  { date: "2024-04-01", name: "Ostermontag", type: "federal" },
  { date: "2024-05-01", name: "Tag der Arbeit", type: "federal" },
  { date: "2024-05-09", name: "Christi Himmelfahrt", type: "federal" },
  { date: "2024-05-20", name: "Pfingstmontag", type: "federal" },
  { date: "2024-10-03", name: "Tag der Deutschen Einheit", type: "federal" },
  { date: "2024-12-25", name: "1. Weihnachtsfeiertag", type: "federal" },
  { date: "2024-12-26", name: "2. Weihnachtsfeiertag", type: "federal" },
  { date: "2025-01-01", name: "Neujahr", type: "federal" },
  { date: "2025-04-18", name: "Karfreitag", type: "federal" },
  { date: "2025-04-21", name: "Ostermontag", type: "federal" },
  { date: "2025-05-01", name: "Tag der Arbeit", type: "federal" },
  { date: "2025-05-29", name: "Christi Himmelfahrt", type: "federal" },
  { date: "2025-06-09", name: "Pfingstmontag", type: "federal" },
  { date: "2025-10-03", name: "Tag der Deutschen Einheit", type: "federal" },
  { date: "2025-12-25", name: "1. Weihnachtsfeiertag", type: "federal" },
  { date: "2025-12-26", name: "2. Weihnachtsfeiertag", type: "federal" }
];

// Aktuelle Konfiguration
let businessHours: BusinessHours = { ...DEFAULT_BUSINESS_HOURS };
let holidays: Holiday[] = [...DEFAULT_HOLIDAYS];
let initialized = false;

/**
 * Initialisiert die Geschäftszeiten aus der Datenbank oder Konfiguration
 * @param hours Geschäftszeiten-Objekt oder null für Standardwerte
 * @param holidayList Liste der Feiertage
 */
export function initBusinessHours(
  hours?: BusinessHours | null, 
  holidayList?: Holiday[] | null
): void {
  if (hours) {
    businessHours = hours;
  }
  
  if (holidayList) {
    holidays = holidayList;
  }
  
  initialized = true;
  console.log("Business hours initialized:", businessHours);
}

/**
 * Lädt Geschäftszeiten aus der Config-Klasse
 */
export function loadFromConfig(): void {
  try {
    // Importiere Config dynamisch, um Circular Imports zu vermeiden
    // Dynamisches Laden der Python Config über Settings-DB
    const Database = require('better-sqlite3');
    const db = new Database('calendar.db');
    
    try {
      // Lade Business Hours aus DB Settings
      const businessHoursFromDB = {};
      const days = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'];
      
      for (const day of days) {
        const row = db.prepare("SELECT value FROM settings WHERE key = ?").get(`business_hours_${day}`);
        if (row) {
          businessHoursFromDB[day] = JSON.parse(row.value);
        }
      }
      
      if (Object.keys(businessHoursFromDB).length > 0) {
        businessHours = businessHoursFromDB;
      }
    } catch (error) {
      console.warn("Could not load business hours from DB, using defaults:", error);
    }
    
    if (Config.BUSINESS_HOURS) {
      businessHours = Config.BUSINESS_HOURS;
    }
    
    if (Config.HOLIDAYS) {
      holidays = Config.HOLIDAYS.map((date: string) => ({
        date,
        name: "Praxis-Feiertag",
        type: "practice" as const
      }));
    }
    
    initialized = true;
  } catch (error) {
    console.warn("Could not load from Config, using defaults:", error);
    initialized = true;
  }
}

/**
 * Gibt den Wochentag-Schlüssel für ein Datum zurück
 * @param date Das Datum
 * @returns Der Wochentag-Schlüssel (mon, tue, etc.)
 */
export function getDayKey(date: Date): string {
  const dayNum = date.getDay(); // 0 = Sonntag, 1 = Montag, ...
  const days = ["sun", "mon", "tue", "wed", "thu", "fri", "sat"];
  return days[dayNum];
}

/**
 * Prüft, ob ein Datum ein Feiertag ist
 * @param dateStr Das Datum als YYYY-MM-DD String
 * @returns Holiday-Objekt wenn Feiertag, sonst null
 */
export function isHoliday(dateStr: string): Holiday | null {
  if (!initialized) {
    loadFromConfig();
  }
  
  return holidays.find(h => h.date === dateStr) || null;
}

/**
 * Prüft, ob ein Zeitpunkt innerhalb der Geschäftszeiten liegt
 * @param dateISO Das Datum als ISO-String
 * @returns true, wenn der Zeitpunkt innerhalb der Geschäftszeiten liegt
 */
export function isWithinBusinessHours(dateISO: string): boolean {
  if (!initialized) {
    loadFromConfig();
  }
  
  try {
    const date = parseISO(dateISO);
    
    if (!isValid(date)) {
      return false;
    }
    
    const dateStr = format(date, "yyyy-MM-dd");
    
    // Prüfe auf Feiertag
    if (isHoliday(dateStr)) {
      return false;
    }
    
    const dayKey = getDayKey(date);
    
    // Prüfen, ob der Tag überhaupt Geschäftszeiten hat
    if (!businessHours[dayKey] || businessHours[dayKey].length === 0) {
      return false;
    }
    
    const timeSlots = businessHours[dayKey];
    const hours = date.getHours();
    const minutes = date.getMinutes();
    const totalMinutes = hours * 60 + minutes;
    
    // Prüfen, ob die Zeit in einem der Slots liegt
    for (const [start, end] of timeSlots) {
      const [startHours, startMinutes] = start.split(":").map(Number);
      const [endHours, endMinutes] = end.split(":").map(Number);
      
      if (isNaN(startHours) || isNaN(startMinutes) || isNaN(endHours) || isNaN(endMinutes)) {
        continue;
      }
      
      const slotStartMinutes = startHours * 60 + startMinutes;
      const slotEndMinutes = endHours * 60 + endMinutes;
      
      if (totalMinutes >= slotStartMinutes && totalMinutes <= slotEndMinutes) {
        return true;
      }
    }
    
    return false;
  } catch (error) {
    console.error("Error checking business hours:", error);
    return false;
  }
}

/**
 * Gibt die Geschäftszeiten für einen Tag zurück
 * @param dayKey Der Wochentag-Schlüssel (mon, tue, etc.)
 * @returns Die Geschäftszeiten für den Tag
 */
export function getBusinessHoursForDay(dayKey: string): Array<[string, string]> {
  if (!initialized) {
    loadFromConfig();
  }
  
  return businessHours[dayKey] || [];
}

/**
 * Gibt alle Geschäftszeiten zurück
 * @returns Die Geschäftszeiten
 */
export function getAllBusinessHours(): BusinessHours {
  if (!initialized) {
    loadFromConfig();
  }
  
  return { ...businessHours };
}

/**
 * Formatiert die Geschäftszeiten für einen Tag als lesbaren String
 * @param dayKey Der Wochentag-Schlüssel (mon, tue, etc.)
 * @returns Die formatierten Geschäftszeiten
 */
export function formatBusinessHours(dayKey: string): string {
  const hours = getBusinessHoursForDay(dayKey);
  
  if (hours.length === 0) {
    return "Geschlossen";
  }
  
  return hours.map(([start, end]) => `${start}-${end}`).join(", ");
}

/**
 * Gibt die nächsten verfügbaren Termine zurück
 * @param startDate Das Startdatum (default: heute)
 * @param count Anzahl der Tage
 * @returns Array von verfügbaren Tagen mit Slots
 */
export function getNextAvailableSlots(
  startDate: Date = new Date(),
  count: number = 5
): Array<{ date: string; dayName: string; slots: string[]; isHoliday: boolean }> {
  if (!initialized) {
    loadFromConfig();
  }
  
  const results: Array<{ date: string; dayName: string; slots: string[]; isHoliday: boolean }> = [];
  let currentDate = new Date(startDate);
  let daysChecked = 0;
  
  // Maximal 14 Tage in die Zukunft schauen
  while (results.length < count && daysChecked < 14) {
    const dayKey = getDayKey(currentDate);
    const dateStr = format(currentDate, "yyyy-MM-dd");
    const dayName = format(currentDate, "EEEE, d. MMMM", { locale: de });
    
    const holiday = isHoliday(dateStr);
    const isHolidayDay = !!holiday;
    
    // Wenn der Tag Geschäftszeiten hat und kein Feiertag ist
    if (businessHours[dayKey] && businessHours[dayKey].length > 0 && !isHolidayDay) {
      const slots: string[] = [];
      
      for (const [start, end] of businessHours[dayKey]) {
        slots.push(`${start}-${end} Uhr`);
      }
      
      if (slots.length > 0) {
        results.push({ 
          date: dateStr, 
          dayName, 
          slots, 
          isHoliday: false 
        });
      }
    } else if (isHolidayDay) {
      // Feiertag mit aufnehmen, aber als geschlossen markieren
      results.push({
        date: dateStr,
        dayName,
        slots: [`Geschlossen (${holiday!.name})`],
        isHoliday: true
      });
    }
    
    // Nächster Tag
    currentDate = addDays(currentDate, 1);
    daysChecked++;
  }
  
  return results;
}

/**
 * Prüft, ob ein bestimmter Wochentag grundsätzlich geöffnet ist
 * @param dayKey Der Wochentag-Schlüssel
 * @returns true, wenn an diesem Wochentag geöffnet ist
 */
export function isDayOpen(dayKey: string): boolean {
  if (!initialized) {
    loadFromConfig();
  }
  
  const hours = businessHours[dayKey];
  return hours && hours.length > 0;
}

/**
 * Erstellt eine textuelle Übersicht der Öffnungszeiten
 * @returns Formatierte Öffnungszeiten für alle Tage
 */
export function getOpeningHoursOverview(): string {
  if (!initialized) {
    loadFromConfig();
  }
  
  const dayNames = {
    mon: "Montag",
    tue: "Dienstag", 
    wed: "Mittwoch",
    thu: "Donnerstag",
    fri: "Freitag",
    sat: "Samstag",
    sun: "Sonntag"
  };
  
  const lines: string[] = [];
  
  for (const [key, name] of Object.entries(dayNames)) {
    const hours = formatBusinessHours(key);
    lines.push(`${name}: ${hours}`);
  }
  
  return lines.join('\n');
}

/**
 * Setzt neue Geschäftszeiten für einen Tag
 * @param dayKey Der Wochentag-Schlüssel
 * @param hours Die neuen Geschäftszeiten
 */
export function setBusinessHoursForDay(dayKey: string, hours: Array<[string, string]>): void {
  if (!initialized) {
    loadFromConfig();
  }
  
  businessHours[dayKey] = hours;
}

/**
 * Fügt einen Feiertag hinzu
 * @param holiday Das Feiertag-Objekt
 */
export function addHoliday(holiday: Holiday): void {
  if (!initialized) {
    loadFromConfig();
  }
  
  // Prüfe, ob Feiertag bereits existiert
  const existingIndex = holidays.findIndex(h => h.date === holiday.date);
  
  if (existingIndex >= 0) {
    holidays[existingIndex] = holiday; // Überschreiben
  } else {
    holidays.push(holiday); // Hinzufügen
  }
  
  // Sortieren nach Datum
  holidays.sort((a, b) => a.date.localeCompare(b.date));
}
