import { useEffect, useState } from "react"
import { useParams } from "react-router-dom"
import { DeliveryTimeline } from "../components/DeliveryTimeline"
import { ErrorMessage } from "../components/ErrorMessage"
import { LoadingSpinner } from "../components/LoadingSpinner"
import { StatusBadge } from "../components/StatusBadge"
import { Timeline } from "../components/Timeline"
import { extractErrorMessage } from "../services/apiClient"
import { getTracking } from "../services/tracking"
import type { TrackingRead } from "../types/tracking"

export function TrackResult() {
  const { reference } = useParams<{ reference: string }>()
  const [tracking, setTracking] = useState<TrackingRead | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!reference) return
    setLoading(true)
    getTracking(reference)
      .then(setTracking)
      .catch((err) => setError(extractErrorMessage(err)))
      .finally(() => setLoading(false))
  }, [reference])

  if (loading) return <LoadingSpinner label="Recherche du courrier..." />

  if (error || !tracking) {
    return (
      <div className="mx-auto max-w-md px-4 py-20 sm:px-6">
        <ErrorMessage message={error ?? "Courrier introuvable"} />
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-2xl px-4 py-12 sm:px-6">
      <div className="rounded-xl border border-slate-200 bg-white p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs uppercase tracking-wide text-slate-400">Référence</p>
            <p className="font-mono text-lg font-semibold text-slate-800">{tracking.reference}</p>
          </div>
          <StatusBadge status={tracking.status} />
        </div>
        <div className="mt-4 grid gap-3 text-sm text-slate-600 sm:grid-cols-2">
          <p>
            <span className="text-slate-400">Objet :</span> {tracking.subject}
          </p>
          <p>
            <span className="text-slate-400">Destinataire :</span> {tracking.recipient_first_name}{" "}
            {tracking.recipient_last_name}
          </p>
        </div>
      </div>

      <div className="mt-8 rounded-xl border border-slate-200 bg-white p-6">
        <h2 className="mb-6 text-sm font-semibold uppercase tracking-wide text-slate-400">Historique</h2>
        <Timeline events={tracking.events} />
      </div>

      {tracking.delivery && (
        <div className="mt-8">
          <DeliveryTimeline delivery={tracking.delivery} />
        </div>
      )}
    </div>
  )
}
