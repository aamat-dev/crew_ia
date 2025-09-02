import { NextResponse } from "next/server";

const data = [
  { date: "2024-01-01", p50: 120, p95: 300 },
  { date: "2024-01-02", p50: 110, p95: 280 },
  { date: "2024-01-03", p50: 130, p95: 320 },
  { date: "2024-01-04", p50: 125, p95: 310 },
  { date: "2024-01-05", p50: 115, p95: 290 },
];

export function GET() {
  return NextResponse.json(data);
}

