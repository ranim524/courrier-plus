import { useEffect, useState } from "react"
import { Link } from "react-router-dom"
import { DeliveryStatusBadge } from "../../components/DeliveryStatusBadge"
import { ErrorMessage } from "../../components/ErrorMessage"
import { LoadingSpinner } from "../../components/LoadingSpinner"
import { extractErrorMessage } from "../../services/apiClient"
import { listDeliveries } from "../../services/delivery"
import type { Page } from "../../types/admin"
import type { DeliveryOrderSummary, DeliveryStatus } from "../../types/delivery"

const STATUS_OPTIONS: DeliveryStatus[] = [
  "CREATED",
  "READY_FOR_DISPATCH",
  "ASSIGNED",
  "PICKED_UP",
  "IN_TRANSIT",
  "OUT_FOR_DELIVERY",
  "DELIVERED",
  "DELIVERY_FAILED",
  "RETURNED_TO_SENDER",
  "CANCELLED",
]

export function AdminDeliveries() {
  const [data, setData] = useState<Page<DeliveryOrderSummary> | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState("")
  const [status, setStatus] = useState<DeliveryStatus | "">("")
  const [page, setPage] = useState(1)

  useEffect(() => {
    listDeliveries({ page, search: search || undefined, status: status || undefined })
      .then(setData)
      .catch((err) => setError(extractErrorMessage(err)))
  }, [page, search, status])

  return (
    <div>
      <h1 className="text-2xl font-bold text-slate-800">Livraisons</h1>
      <p className="mt-1 text-sm text-slate-500">
        Suivi manuel — gestion interne des livraisons physiques Courrier+.
      </p>

      <div className="mt-4 flex flex-col gap-3 sm:flex-row">
        <input
          placeholder="Rechercher par numéro de suivi ou référence..."
          value={search}
          onChange={(e) => {
            setPage(1)
            setSearch(e.target.value)
          }}
          className="flex-1 rounded-lg border border-slate-300 px-3.5 py-2.5 text-sm outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-100"
        />
        <select
          value={status}
          onChange={(e) => {
            setPage(1)
            setStatus(e.target.value as DeliveryStatus | "")
          }}
          className="rounded-lg border border-slate-300 px-3.5 py-2.5 text-sm outline-none focus:border-brand-500"
        >
          <option value="">Tous les statuts</option>
          {STATUS_OPTIONS.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </div>

      <ErrorMessage message={error} />

      {!data ? (
        <LoadingSpinner />
      ) : (
        <div className="mt-4 overflow-x-auto rounded-xl border border-slate-200 bg-white">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase text-slate-400">
              <tr>
                <th className="px-4 py-3">Suivi</th>
                <th className="px-4 py-3">Lettre</th>
                <th className="px-4 py-3">Destinataire</th>
                <th className="px-4 py-3">Livreur</th>
                <th className="px-4 py-3">Statut</th>
                <th className="px-4 py-3">Date</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((d) => (
                <tr key={d.id} className="border-t border-slate-100 hover:bg-slate-50">
                  <td className="px-4 py-3">
                    <Link to={`/admin/deliveries/${d.id}`} className="font-mono text-brand-600 hover:underline">
                      {d.tracking_number}
                    </Link>
                  </td>
                  <td className="px-4 py-3 font-mono text-xs">{d.letter_reference ?? "—"}</td>
                  <td className="px-4 py-3">{d.recipient_name}</td>
                  <td className="px-4 py-3">{d.courier_name ?? "—"}</td>
                  <td className="px-4 py-3">
                    <DeliveryStatusBadge status={d.status} />
                  </td>
                  <td className="px-4 py-3 text-slate-500">{new Date(d.created_at).toLocaleDateString("fr-FR")}</td>
                </tr>
              ))}
              {data.items.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-slate-400">
                    Aucune livraison trouvée.
                  </td>
                </tr>
              )}
            </tbody>
          </table>

          <div className="flex items-center justify-between border-t border-slate-100 px-4 py-3 text-sm text-slate-500">
            <span>
              Page {data.page} / {data.total_pages} ({data.total} résultats)
            </span>
            <div className="flex gap-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage((p) => p - 1)}
                className="rounded-md border border-slate-200 px-3 py-1 disabled:opacity-40"
              >
                Précédent
              </button>
              <button
                disabled={page >= data.total_pages}
                onClick={() => setPage((p) => p + 1)}
                className="rounded-md border border-slate-200 px-3 py-1 disabled:opacity-40"
              >
                Suivant
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
