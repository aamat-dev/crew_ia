export default function PlansPage() {
  return (
    <main role="main" className="p-6 space-y-6">
      <h1 className="text-3xl font-extrabold tracking-tight text-slate-900">Plans</h1>
      <section className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div className="clay-card p-4">
          <h2 className="text-lg font-medium">Plans récents</h2>
          <p className="mt-2 text-sm text-slate-500">Aucun plan pour le moment.</p>
        </div>
        <div className="clay-card p-4">
          <h2 className="text-lg font-medium">Créer un plan</h2>
          <p className="mt-2 text-sm text-slate-500">Bientôt disponible.</p>
        </div>
      </section>
    </main>
  );
}
