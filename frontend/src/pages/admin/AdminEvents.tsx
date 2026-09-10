import { useEffect, useState } from "react"
import { ErrorMessage } from "../../components/ErrorMessage"
import { LoadingSpinner } from "../../components/LoadingSpinner"
import { extractErrorMessage } from "../../services/apiClient"
import { listEmails } from "../../services/admin"
import type { EmailEventRead, Page } from "../../types/admin"

export function AdminEvents() {
  const [data, setData] = useState<Page<EmailEventRead> | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [page, setPage] = useState(1)

  useEffect(() => {
    listEmails(page)
      .then(setData)
      .catch((err) => setError(extractErrorMessage(err)))
  }, [page])

  if (error) return <ErrorMessage message={error} />
  if (!data) return <LoadingSpinner />

  return (
    <div>
      <h1 className="text-2xl font-bold text-slate-800">E-mails envoyés</h1>
      <div className="mt-4 overflow-x-auto rounded-xl border border-slate-200 bg-white">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-50 text-xs uppercase text-slate-400">
            <tr>
              <th className="px-4 py-3">Type</th>
              <th className="px-4 py-3">Destinataire</th>
              <th className="px-4 py-3">Statut</th>
              <th className="px-4 py-3">Erreur</th>
              <th className="px-4 py-3">Date</th>
            </tr>
          </thead>
          <tbody>
            {data.items.map((e) => (
              <tr key={e.id} className="border-t border-slate-100">
                <td className="px-4 py-3">{e.email_type}</td>
                <td className="px-4 py-3">{e.recipient}</td>
                <td
                  className={`px-4 py-3 font-semibold ${e.status === "SENT" ? "text-accent-600" : e.status === "FAILED" ? "text-danger-500" : "text-slate-400"}`}
                >
                  {e.status}
                </td>
                <td className="px-4 py-3 text-xs text-slate-400">{e.error_message ?? "—"}</td>
                <td className="px-4 py-3 text-slate-500">{new Date(e.created_at).toLocaleString("fr-FR")}</td>
              </tr>
            ))}
            {data.items.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-slate-400">
                  Aucun e-mail.
                </td>
              </tr>
            )}
          </tbody>
        </table>

        <div className="flex items-center justify-between border-t border-slate-100 px-4 py-3 text-sm text-slate-500">
          <span>
            Page {data.page} / {data.total_pages}
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
    </div>
  )
}
