/**
 * Input-Sanitizing und PII-Redaktion für E-Mail-Inhalte
 * Entfernt HTML-Tags und redigiert persönliche Informationen
 */

export function stripHtml(input: string): string {
  return input.replace(/<[^>]*>/g, " ").replace(/\s+/g, " ").trim();
}

export function redactPII(input: string): string {
  return input
    .replace(/\b[\w.%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b/g, "[email:redacted]")
    .replace(/\b(\+?49|0)[1-9]\d{7,}\b/g, "[phone:redacted]")
    .replace(/\b(0[1-9]|[12]\d|3[01])\.(0[1-9]|1[0-2])\.(19|20)\d{2}\b/g, "[dob:redacted]");
}

export function sanitizeInboundEmail(htmlOrText: string): string {
  return redactPII(stripHtml(htmlOrText));
}
