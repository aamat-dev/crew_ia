import { ClayCard } from "@/components/ds/ClayCard";
import { ThemeToggle } from "@/components/shell/ThemeToggle";
import { Input } from "@/components/ds/Input";
import { useState } from "react";

export default function SettingsPage() {
  const [apiKey, setApiKey] = useState("");
  return (
    <main role="main" className="p-6 space-y-6">
      <h1 className="text-3xl font-extrabold tracking-tight text-slate-100">Réglages</h1>
      <section className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <ClayCard className="p-4">
          <h2 className="text-lg font-medium text-slate-100">Apparence</h2>
          <p className="mt-2 text-sm text-slate-400">Basculer entre clair/sombre (persisté).</p>
          <div className="mt-3"><ThemeToggle /></div>
        </ClayCard>
        <ClayCard className="p-4">
          <h2 className="text-lg font-medium text-slate-100">Clés API</h2>
          <label className="sr-only" htmlFor="api-key">Clé API</label>
          <div className="mt-2 rounded-2xl border border-slate-700 bg-[#2A2D36] px-3 py-2 shadow-[inset_0_2px_6px_rgba(255,255,255,0.04)]">
            <Input id="api-key" type="password" value={apiKey} onChange={(e) => setApiKey(e.target.value)} placeholder="••••••••" className="w-full border-0 bg-transparent p-0 text-slate-100 placeholder:text-slate-500 focus-visible:ring-0" />
          </div>
          <div className="mt-3 flex gap-2">
            <button className="rounded-xl border border-slate-700 bg-[#2A2D36] px-3 py-2 text-sm text-slate-200 hover:bg-indigo-600/15 focus:outline-none focus-visible:ring-2 focus-visible:ring-[hsl(var(--ring))]">Afficher</button>
            <button className="rounded-xl border border-slate-700 bg-[#2A2D36] px-3 py-2 text-sm text-slate-200 hover:bg-indigo-600/15 focus:outline-none focus-visible:ring-2 focus-visible:ring-[hsl(var(--ring))]">Régénérer</button>
          </div>
        </ClayCard>
        <ClayCard className="p-4">
          <h2 className="text-lg font-medium text-slate-100">Notifications & alertes</h2>
          <p className="mt-2 text-sm text-slate-400">Toasts, e-mails, seuils de quota.</p>
          <div className="mt-3 flex gap-2">
            <button className="rounded-xl border border-slate-700 bg-[#2A2D36] px-3 py-2 text-sm text-slate-200 hover:bg-indigo-600/15 focus:outline-none focus-visible:ring-2 focus-visible:ring-[hsl(var(--ring))]">Activer toasts</button>
            <button className="rounded-xl border border-slate-700 bg-[#2A2D36] px-3 py-2 text-sm text-slate-200 hover:bg-indigo-600/15 focus:outline-none focus-visible:ring-2 focus-visible:ring-[hsl(var(--ring))]">Alertes e-mail</button>
          </div>
        </ClayCard>
      </section>
    </main>
  );
}
