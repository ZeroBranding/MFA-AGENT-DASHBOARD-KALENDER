import fc from "fast-check";
import { parseIntentJSON } from "../src/intents/validate";

test("parseIntentJSON is resilient to arbitrary input", () => {
  fc.assert(
    fc.property(fc.string(), (s) => {
      try {
        parseIntentJSON(s);
      } catch {
        // darf fehlschlagen, aber niemals crashen
      }
    })
  );
});
