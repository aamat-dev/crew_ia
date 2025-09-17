import { NextRequest, NextResponse } from "next/server";
import { listFeedbacks, Criticity } from "@/lib/mockFeedbacks";

export function GET(req: NextRequest) {
  const url = new URL(req.url);
  const q = url.searchParams.get("q") || undefined;
  const criticityParam = url.searchParams.get("criticity");
  const criticity = criticityParam
    ? criticityParam
        .split(",")
        .filter((value): value is Criticity => ["critical", "major", "minor"].includes(value as Criticity))
    : undefined;
  const data = listFeedbacks({ q, criticity });
  return NextResponse.json({ items: data, total: data.length });
}
