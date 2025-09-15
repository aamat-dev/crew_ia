import { NextRequest, NextResponse } from "next/server";
import { resumeRun } from "@/lib/mockRuns";

export function POST(_req: NextRequest, { params }: { params: { id: string } }) {
  const { id } = params;
  const r = resumeRun(id);
  if (!r) return new NextResponse("Not found", { status: 404 });
  return NextResponse.json({ ok: true, id, status: r.status });
}

