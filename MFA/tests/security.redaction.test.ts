import { sanitizeInboundEmail } from "../src/security/sanitize";

test("PII redaction works", () => {
  const input = "Mail: max@test.de Tel: 01761234567 Geb. 01.01.1990";
  const out = sanitizeInboundEmail(input);
  expect(out).not.toMatch(/@/);
  expect(out).not.toMatch(/0176/);
  expect(out).not.toMatch(/1990/);
});
