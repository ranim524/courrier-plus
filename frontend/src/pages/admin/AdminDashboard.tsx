import { useEffect, useState } from "react"
import { ErrorMessage } from "../../components/ErrorMessage"
import { LoadingSpinner } from "../../components/LoadingSpinner"
import { extractErrorMessage } from "../../services/apiClient"
import { getDashboardStats } from "../../services/admin"
import type { DashboardStats } from "../../types/admin"

const CARDS: { key: keyof DashboardStats; label: string }[] = [
  { key: "total_letters", label: "Total courriers" },
  { key: "draft_letters", label: "Brouillons" },
  { key: "pending_payment_letters", label: "Paiement en attente" },
  { key: "paid_letters", label: "Payés" },
  { key: "sent_letters", label: "Envoyés" },
  { key: "opened_letters", label: "Consultés" },
  { key: "received_letters", label: "Reçus" },
  { key: "failed_letters", label: "Échoués" },
]

const DELIVERY_CARDS: { key: keyof DashboardStats; label: string }[] = [
  { key: "total_deliveries", label: "Total livraisons" },
  { key: "deliveries_ready_for_dispatch", label: "Prêtes à expédier" },
  { key: "deliveries_assigned", label: "Affectées" },
  { key: "deliveries_in_transit", label: "En transit" },
  { key: "deliveries_out_for_delivery", label: "En cours de livraison" },
  { key: "deliveries_delivered", label: "Livrées" },
  { key: "deliveries_failed", label: "Échecs" },
  { key: "deliveries_returned", label: "Retournées" },
]

export function AdminDashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getDashboardStats()
      .then(setStats)
      .catch((err) => setError(extractErrorMessage(err)))
  }, [])

  if (error) return <ErrorMessage message={error} />
  if (!stats) return <LoadingSpinner />

  return (
    <div>
      <h1 className="text-2xl font-bold text-slate-800">Tableau de bord</h1>
      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {CARDS.map((card) => (
          <div key={card.key} className="rounded-xl border border-slate-200 bg-white p-5">
            <p className="text-xs font-medium uppercase tracking-wide text-slate-400">{card.label}</p>
            <p className="mt-2 text-2xl font-bold text-slate-800">{stats[card.key]}</p>
          </div>
        ))}
      </div>

      <div className="mt-6 grid gap-4 sm:grid-cols-2">
        <div className="rounded-xl border border-brand-200 bg-brand-50 p-5">
          <p className="text-xs font-medium uppercase tracking-wide text-brand-500">Total paiements</p>
          <p className="mt-2 text-2xl font-bold text-brand-800">{stats.total_payments}</p>
        </div>
        <div className="rounded-xl border border-accent-500/30 bg-accent-500/10 p-5">
          <p className="text-xs font-medium uppercase tracking-wide text-accent-600">Revenu total</p>
          <p className="mt-2 text-2xl font-bold text-accent-600">
            {stats.total_revenue.toFixed(2)} {stats.currency}
          </p>
        </div>
      </div>

      <h2 className="mt-8 text-lg font-bold text-slate-800">Livraisons</h2>
      <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {DELIVERY_CARDS.map((card) => (
          <div key={card.key} className="rounded-xl border border-slate-200 bg-white p-5">
            <p className="text-xs font-medium uppercase tracking-wide text-slate-400">{card.label}</p>
            <p className="mt-2 text-2xl font-bold text-slate-800">{stats[card.key]}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
