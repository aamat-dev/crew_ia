import { ClayCard } from "@/components/ds/ClayCard";

export default function PlansPage() {
  return (
    <main role="main" className="p-6 space-y-6">
      <h1 className="text-3xl font-extrabold tracking-tight text-slate-900">Plans</h1>
      <section className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <ClayCard className="p-4">
          <h2 className="text-lg font-medium">Plans récents</h2>
          <p className="mt-2 text-sm text-slate-500">
            Les plans s'affichent après génération depuis la page « Tasks ».
            Après avoir généré un plan, vous serez redirigé vers sa page détaillée
            pour le valider.
          </p>
        </ClayCard>
        <ClayCard className="p-4">
          <h2 className="text-lg font-medium">Créer un plan</h2>
          <p className="mt-2 text-sm text-slate-500">
            Créez d'abord une tâche puis utilisez « Générer un plan » depuis « Tasks ».
          </p>
        </ClayCard>
      </section>
    </main>
  );
}
