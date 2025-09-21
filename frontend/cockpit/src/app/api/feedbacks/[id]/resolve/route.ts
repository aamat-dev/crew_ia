import { NextResponse } from "next/server";
import { resolveFeedback } from "@/lib/mockFeedbacks";

export async function POST(
  _req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;

  if (!id) {
    return new NextResponse("Missing feedback id", { status: 400 });
  }

  const it = resolveFeedback(id);
  if (!it) {
    return new NextResponse("Not found", { status: 404 });
  }
  return NextResponse.json({ ok: true, id, resolved: true });
}
