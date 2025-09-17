"use client";

import { HeaderBar } from "@/ui/HeaderBar";
import { ThemeSection } from "@/features/settings/ThemeSection";
import { ApiKeysSection } from "@/features/settings/ApiKeysSection";
import { NotificationsSection } from "@/features/settings/NotificationsSection";

export function SettingsPage() {
  return (
    <div className="space-y-6">
      <HeaderBar title="Réglages" breadcrumb="Personnalisation & sécurité" />
      <ThemeSection />
      <ApiKeysSection />
      <NotificationsSection />
    </div>
  );
}

export default SettingsPage;
