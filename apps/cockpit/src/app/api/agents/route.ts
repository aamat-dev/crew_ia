import { NextResponse } from "next/server";

const data = [
  { date: "2024-01-01", value: 20 },
  { date: "2024-01-02", value: 24 },
  { date: "2024-01-03", value: 30 },
  { date: "2024-01-04", value: 28 },
  { date: "2024-01-05", value: 35 },
];

export function GET() {
  return NextResponse.json(data);
}

