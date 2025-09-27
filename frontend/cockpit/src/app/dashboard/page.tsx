"use client";

import * as React from "react";
import { DashboardPage as DashboardFeature } from "@/features/dashboard/DashboardPage";

export default function DashboardPage() {
  return (
    <React.Suspense fallback={null}>
      <DashboardFeature />
    </React.Suspense>
  );
}
