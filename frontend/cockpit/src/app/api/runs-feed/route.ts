import { NextRequest, NextResponse } from "next/server";
import { listRuns } from "@/lib/mockRuns";

export function GET(req: NextRequest) {
  const url = new URL(req.url);
  const statusParam = url.searchParams.get("status");
  const q = url.searchParams.get("q") || undefined;
  const status = statusParam ? statusParam.split(",").filter(Boolean) : undefined;
  const data = listRuns({ status, q });
  return NextResponse.json({ items: data, total: data.length });
}

