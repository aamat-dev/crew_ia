import { NextRequest, NextResponse } from "next/server";
import { resolveFeedback } from "@/lib/mockFeedbacks";

export function POST(_req: NextRequest, { params }: { params: { id: string } }) {
  const it = resolveFeedback(params.id);
  if (!it) return new NextResponse("Not found", { status: 404 });
  return NextResponse.json({ ok: true, id: params.id, resolved: true });
}
