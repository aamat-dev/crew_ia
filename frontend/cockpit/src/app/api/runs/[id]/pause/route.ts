import { NextResponse } from "next/server";
import { pauseRun } from "@/lib/mockRuns";

export async function POST(
  _req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const r = pauseRun(id);
  if (!r) {
    return new NextResponse("Not found", { status: 404 });
  }
  return NextResponse.json({ ok: true, id, status: r.status });
}
