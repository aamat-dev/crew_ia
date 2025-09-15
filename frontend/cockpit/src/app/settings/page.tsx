export default function SettingsPage() {
  return (
    <main role="main" className="p-6 space-y-6">
      <h1 className="text-3xl font-extrabold tracking-tight text-slate-900">Settings</h1>
      <section className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div className="clay-card p-4">
          <h2 className="text-lg font-medium">Apparence</h2>
          <p className="mt-2 text-sm text-slate-500">Mode clair par défaut. Toggle dans l’en-tête.</p>
        </div>
        <div className="clay-card p-4">
          <h2 className="text-lg font-medium">Notifications</h2>
          <p className="mt-2 text-sm text-slate-500">Paramètres de notifications à venir.</p>
        </div>
      </section>
    </main>
  );
}
