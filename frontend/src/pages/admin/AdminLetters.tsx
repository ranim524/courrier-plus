import { useEffect, useState } from "react"
import { Link } from "react-router-dom"
import { ErrorMessage } from "../../components/ErrorMessage"
import { LoadingSpinner } from "../../components/LoadingSpinner"
import { StatusBadge } from "../../components/StatusBadge"
import { extractErrorMessage } from "../../services/apiClient"
import { listLetters } from "../../services/admin"
import type { LetterStatus, LetterSummary } from "../../types/letter"
import type { Page } from "../../types/admin"

const STATUS_OPTIONS: LetterStatus[] = [
  "DRAFT",
  "PENDING_PAYMENT",
  "PAID",
  "SENT",
  "DELIVERED",
  "OPENED",
  "RECEIVED",
  "FAILED",
  "REFUSED",
  "EXPIRED",
  "CANCELLED",
]

export function AdminLetters() {
  const [data, setData] = useState<Page<LetterSummary> | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState("")
  const [status, setStatus] = useState<LetterStatus | "">("")
  const [page, setPage] = useState(1)

  useEffect(() => {
    listLetters({ page, search: search || undefined, status: status || undefined })
      .then(setData)
      .catch((err) => setError(extractErrorMessage(err)))
  }, [page, search, status])

  return (
    <div>
      <h1 className="text-2xl font-bold text-slate-800">Courriers</h1>

      <div className="mt-4 flex flex-col gap-3 sm:flex-row">
        <input
          placeholder="Rechercher par référence, expéditeur, destinataire..."
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
            setStatus(e.target.value as LetterStatus | "")
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
                <th className="px-4 py-3">Référence</th>
                <th className="px-4 py-3">Expéditeur</th>
                <th className="px-4 py-3">Destinataire</th>
                <th className="px-4 py-3">Objet</th>
                <th className="px-4 py-3">Statut</th>
                <th className="px-4 py-3">Date</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((letter) => (
                <tr key={letter.id} className="border-t border-slate-100 hover:bg-slate-50">
                  <td className="px-4 py-3">
                    <Link to={`/admin/letters/${letter.id}`} className="font-mono text-brand-600 hover:underline">
                      {letter.reference ?? "—"}
                    </Link>
                  </td>
                  <td className="px-4 py-3">
                    {letter.sender_first_name} {letter.sender_last_name}
                  </td>
                  <td className="px-4 py-3">
                    {letter.recipient_first_name} {letter.recipient_last_name}
                  </td>
                  <td className="px-4 py-3">{letter.subject}</td>
                  <td className="px-4 py-3">
                    <StatusBadge status={letter.status} />
                  </td>
                  <td className="px-4 py-3 text-slate-500">
                    {new Date(letter.created_at).toLocaleDateString("fr-FR")}
                  </td>
                </tr>
              ))}
              {data.items.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-slate-400">
                    Aucun courrier trouvé.
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
