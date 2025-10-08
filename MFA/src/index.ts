/**
 * Intent-Erkennungs-System für MFA
 * Haupteinstiegspunkt für die Integration
 */

export * from "./intents/types";
export * from "./intents/validate";
export * from "./intents/gates";
export * from "./intents/multi";

export * from "./time/duckling";
export * from "./time/businessHours";
export * from "./time/normalize";

export * from "./pipeline/classifyExtract";

// Convenience Exports für einfache Nutzung
export { classifyEmail, type ClassificationResult } from "./pipeline/classifyExtract";
export { parseIntentJSON } from "./intents/validate";
export { gate } from "./intents/gates";
export { createProcessingPlan } from "./intents/multi";
export { normalizeDateTimeSlots } from "./time/normalize";
export { initBusinessHours, isWithinBusinessHours } from "./time/businessHours";
export { parseTimesDe, isDucklingAvailable } from "./time/duckling";

/**
 * Kommandozeilen-Interface für Python-Integration
 */
async function main() {
    const [,, emailText, sender = "", subject = ""] = process.argv;

    if (!emailText) {
        console.error("Fehler: E-Mail-Text erforderlich");
        process.exit(1);
    }

    try {
        const result = await classifyEmail(emailText, sender, subject);
        console.log(JSON.stringify(result, null, 2));
    } catch (error) {
        console.error("Klassifikationsfehler:", error);
        process.exit(1);
    }
}

// Führe main aus, wenn direkt aufgerufen
if (typeof require !== 'undefined' && require.main === module) {
    main().catch(console.error);
} else if (typeof import.meta !== 'undefined' && import.meta.url === `file://${process.argv[1]}`) {
    main().catch(console.error);
}