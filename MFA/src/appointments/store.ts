import { db } from "../db/db";

export function ensureResource(name: string): number {
  const up = db.prepare(`INSERT INTO resources(name) VALUES (?) ON CONFLICT(name) DO NOTHING`);
  up.run(name);
  const row = db.prepare(`SELECT id FROM resources WHERE name=?`).get(name);
  return row.id as number;
}

export function reserve(
  resource: string,
  slotISO: string,
  patientHash: string
): { ok: boolean; reason?: string } {
  const rid = ensureResource(resource);

  return db.transaction(() => {
    const cap = db.prepare(
      `SELECT max_bookings FROM slot_capacity WHERE resource_id=? AND slot_ts=?`
    ).get(rid, slotISO);
    const max = cap?.max_bookings ?? 1;

    const count = db.prepare(
      `SELECT COUNT(*) as c FROM reservations WHERE resource_id=? AND slot_ts=?`
    ).get(rid, slotISO).c as number;

    if (count >= max) {
      return { ok: false, reason: "capacity_reached" };
    }

    try {
      db.prepare(
        `INSERT INTO reservations(resource_id, slot_ts, patient_hash) VALUES (?,?,?)`
      ).run(rid, slotISO, patientHash);
      return { ok: true };
    } catch (e: any) {
      if (String(e.message).includes("UNIQUE")) {
        return { ok: false, reason: "duplicate_patient_slot" };
      }
      throw e;
    }
  })();
}
