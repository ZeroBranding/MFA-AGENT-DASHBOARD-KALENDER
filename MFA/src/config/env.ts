import 'dotenv/config';
import { z } from 'zod';

const EnvSchema = z.object({
  IMAP_SERVER: z.string().min(1),
  IMAP_PORT: z.coerce.number().int().positive(),
  IMAP_USER: z.string().email(),
  IMAP_PASS: z.string().min(16),
  SMTP_SERVER: z.string().min(1),
  SMTP_PORT: z.coerce.number().int().positive(),
  SMTP_USER: z.string().email(),
  SMTP_PASS: z.string().min(16),
  OLLAMA_URL: z.string().url().default('http://localhost:11434'),
  OLLAMA_MODEL: z.string().default('qwen2.5:14b-instruct'),
});

export const Env = EnvSchema.parse(process.env);
