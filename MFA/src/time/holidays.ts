import Holidays from "date-holidays";
const hd = new Holidays("DE");

export function isHoliday(dateISO: string, region?: string): boolean {
  const d = new Date(dateISO);
  if (region) hd.init("DE", region);
  return !!hd.isHoliday(d);
}
