import { NextRequest, NextResponse } from "next/server";
import { addVital, aggregate, vitalSchema } from "@/lib/vitals";

export async function POST(req: NextRequest) {
  try {
    const data = await req.json();
    const vital = vitalSchema.parse(data);
    addVital(vital);
    return NextResponse.json({ ok: true });
  } catch {
    return new NextResponse("Bad Request", { status: 400 });
  }
}

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const range = Number(searchParams.get("range")) || 24 * 60 * 60 * 1000;
  const result = aggregate(range);
  return NextResponse.json(result);
}
