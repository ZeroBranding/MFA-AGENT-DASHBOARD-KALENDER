import { jsonrepair } from "jsonrepair";
import { parseIntentJSON } from "../intents/validate";
import { ollamaChat } from "./ollamaClient";
import { Env } from "../config/env";

const SYSTEM_PROMPT = `
Du bist eine präzise Intent-Extraktions-Engine für medizinische E-Mails.
Antworte ausschließlich mit JSON gemäß Schema, keine Erklärungen.
`;

export async function classifyEmail(text: string) {
  const raw = await ollamaChat(Env.OLLAMA_URL, {
    model: Env.OLLAMA_MODEL,
    messages: [
      { role: "system", content: SYSTEM_PROMPT },
      { role: "user", content: `E-Mail:\n"""\n${text}\n"""` }
    ]
  });

  let fixed = raw.trim();
  if (fixed.startsWith("```")) fixed = fixed.replace(/^```[a-zA-Z]*\n?/, "").replace(/```$/, "");
  fixed = jsonrepair(fixed);
  return parseIntentJSON(fixed);
}
