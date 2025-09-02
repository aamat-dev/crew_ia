import { NextResponse } from "next/server";

const data = [
  { date: "2024-01-01", positive: 80, neutral: 15, negative: 5 },
  { date: "2024-01-02", positive: 82, neutral: 10, negative: 8 },
  { date: "2024-01-03", positive: 78, neutral: 12, negative: 10 },
  { date: "2024-01-04", positive: 85, neutral: 9, negative: 6 },
  { date: "2024-01-05", positive: 88, neutral: 7, negative: 5 },
];

export function GET() {
  return NextResponse.json(data);
}

