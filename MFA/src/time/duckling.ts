/**
 * Duckling-API-Client für deutsche Datum/Zeit-Erkennung
 * Unterstützt relative Zeitangaben wie "morgen", "nächste Woche", etc.
 */

export type DucklingTime = {
  body: string; 
  value: { 
    values: { value: string; grain?: string }[]; 
    value: string; 
    grain?: string; 
    type?: string;
  };
  start: number; 
  end: number; 
  dim: "time";
};

export type DucklingOptions = {
  locale?: string;
  timezone?: string;
  referenceTime?: string;
  useCache?: boolean;
  ducklingUrl?: string;
  timeout?: number;
};

const DEFAULT_OPTIONS: DucklingOptions = {
  locale: "de_DE",
  timezone: "Europe/Berlin",
  useCache: true,
  ducklingUrl: "http://localhost:8000/parse",
  timeout: 5000
};

// Cache für Duckling-Anfragen (LRU-ähnlich)
const timeCache = new Map<string, { data: DucklingTime[]; timestamp: number }>();
const CACHE_TTL = 60000; // 1 Minute Cache-Zeit

/**
 * Parst deutsche Zeitangaben mit Duckling
 * @param text Der zu parsende Text
 * @param options Optionen für Duckling
 * @returns Array von erkannten Zeitangaben
 */
export async function parseTimesDe(
  text: string, 
  options: Partial<DucklingOptions> = {}
): Promise<DucklingTime[]> {
  const opts = { ...DEFAULT_OPTIONS, ...options };
  const now = opts.referenceTime ?? new Date().toISOString();
  
  // Cache-Key generieren
  const cacheKey = `${text}|${opts.locale}|${opts.timezone}|${now}`;
  
  // Cache prüfen
  if (opts.useCache && timeCache.has(cacheKey)) {
    const cached = timeCache.get(cacheKey)!;
    if (Date.now() - cached.timestamp < CACHE_TTL) {
      return cached.data;
    } else {
      timeCache.delete(cacheKey);
    }
  }
  
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), opts.timeout);
    
    const res = await fetch(opts.ducklingUrl!, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8" },
      body: new URLSearchParams({ 
        text, 
        locale: opts.locale!, 
        tz: opts.timezone!, 
        referenceTime: now 
      }),
      signal: controller.signal
    });
    
    clearTimeout(timeoutId);
    
    if (!res.ok) {
      throw new Error(`Duckling API error: ${res.status} ${res.statusText}`);
    }
    
    const data = (await res.json()) as DucklingTime[];
    
    // Filtern nach Zeit-Dimension
    const timeData = data.filter(d => d.dim === "time");
    
    // Sortieren nach Präzision (Uhrzeit > Tag > Woche > Monat)
    const withTime = timeData.filter(d => /\d{2}:\d{2}/.test(d.value.value));
    const result = withTime.length ? withTime : timeData;
    
    // Im Cache speichern
    if (opts.useCache) {
      timeCache.set(cacheKey, { data: result, timestamp: Date.now() });
      
      // Cache-Größe begrenzen
      if (timeCache.size > 1000) {
        const oldestKey = timeCache.keys().next().value;
        timeCache.delete(oldestKey);
      }
    }
    
    return result;
  } catch (error) {
    if (error instanceof Error && error.name === 'AbortError') {
      console.error("Duckling request timeout");
      return [];
    }
    console.error("Duckling parsing error:", error);
    return [];
  }
}

/**
 * Prüft, ob Duckling verfügbar ist
 * @param url Die URL des Duckling-Servers
 * @returns true, wenn Duckling verfügbar ist
 */
export async function isDucklingAvailable(url: string = DEFAULT_OPTIONS.ducklingUrl!): Promise<boolean> {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 3000);
    
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8" },
      body: new URLSearchParams({ 
        text: "heute", 
        locale: "de_DE", 
        tz: "Europe/Berlin" 
      }),
      signal: controller.signal
    });
    
    clearTimeout(timeoutId);
    return res.ok;
  } catch (error) {
    console.error("Duckling availability check failed:", error);
    return false;
  }
}

/**
 * Erweiterte Zeitparsing-Funktion mit Fallback auf deutsche Regex-Patterns
 * @param text Der zu parsende Text
 * @param options Optionen
 * @returns Erkannte Zeitangaben (Duckling + Regex-Fallback)
 */
export async function parseTimesWithFallback(
  text: string, 
  options: Partial<DucklingOptions> = {}
): Promise<DucklingTime[]> {
  // Erst Duckling versuchen
  const ducklingResults = await parseTimesDe(text, options);
  
  if (ducklingResults.length > 0) {
    return ducklingResults;
  }
  
  // Fallback auf deutsche Regex-Patterns
  return parseGermanTimePatterns(text);
}

/**
 * Fallback-Parser für deutsche Zeitangaben mit Regex
 * @param text Der Text
 * @returns Erkannte Zeitangaben als Duckling-kompatible Objekte
 */
function parseGermanTimePatterns(text: string): DucklingTime[] {
  const results: DucklingTime[] = [];
  const lowerText = text.toLowerCase();
  
  // Relative Tage
  const relativeDays = [
    { pattern: /\bheute\b/, offset: 0 },
    { pattern: /\bmorgen\b/, offset: 1 },
    { pattern: /\bübermorgen\b/, offset: 2 },
    { pattern: /\bnächste woche\b/, offset: 7 },
    { pattern: /\bnächsten? (montag|dienstag|mittwoch|donnerstag|freitag|samstag|sonntag)\b/, offset: null }
  ];
  
  for (const { pattern, offset } of relativeDays) {
    const match = lowerText.match(pattern);
    if (match && offset !== null) {
      const date = new Date();
      date.setDate(date.getDate() + offset);
      
      results.push({
        body: match[0],
        value: {
          values: [{ value: date.toISOString().split('T')[0] }],
          value: date.toISOString().split('T')[0]
        },
        start: match.index!,
        end: match.index! + match[0].length,
        dim: "time"
      });
    }
  }
  
  // Uhrzeiten
  const timePattern = /\b(\d{1,2}):?(\d{2})?\s*(uhr)?\b/gi;
  let timeMatch;
  
  while ((timeMatch = timePattern.exec(text)) !== null) {
    const hours = parseInt(timeMatch[1]);
    const minutes = parseInt(timeMatch[2] || "0");
    
    if (hours >= 0 && hours <= 23 && minutes >= 0 && minutes <= 59) {
      const today = new Date();
      today.setHours(hours, minutes, 0, 0);
      
      results.push({
        body: timeMatch[0],
        value: {
          values: [{ value: today.toISOString() }],
          value: today.toISOString()
        },
        start: timeMatch.index,
        end: timeMatch.index + timeMatch[0].length,
        dim: "time"
      });
    }
  }
  
  return results;
}

/**
 * Startet Duckling als Docker-Container
 * @returns Promise, das sich auflöst, wenn Duckling bereit ist
 */
export async function startDucklingDocker(): Promise<boolean> {
  try {
    // Prüfe erst, ob Duckling bereits läuft
    if (await isDucklingAvailable()) {
      console.log("Duckling is already running");
      return true;
    }
    
    console.log("Starting Duckling Docker container...");
    
    // Docker-Befehl ausführen (würde normalerweise ein Child Process sein)
    // Hier nur als Beispiel - in der Praxis würde man child_process verwenden
    console.log("Execute: docker run -d -p 8000:8000 rasa/duckling");
    
    // Warten bis Duckling verfügbar ist (max 30 Sekunden)
    for (let i = 0; i < 30; i++) {
      await new Promise(resolve => setTimeout(resolve, 1000));
      if (await isDucklingAvailable()) {
        console.log("Duckling is ready!");
        return true;
      }
    }
    
    console.error("Duckling startup timeout");
    return false;
  } catch (error) {
    console.error("Failed to start Duckling:", error);
    return false;
  }
}

/**
 * Cache-Statistiken abrufen
 * @returns Cache-Informationen
 */
export function getCacheStats() {
  const now = Date.now();
  const validEntries = Array.from(timeCache.values()).filter(
    entry => now - entry.timestamp < CACHE_TTL
  ).length;
  
  return {
    totalEntries: timeCache.size,
    validEntries,
    expiredEntries: timeCache.size - validEntries
  };
}

/**
 * Cache leeren
 */
export function clearCache(): void {
  timeCache.clear();
}
