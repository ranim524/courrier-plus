import { useEffect, useState } from "react"
import { useParams } from "react-router-dom"
import { Button } from "../components/Button"
import { DeliveryTimeline } from "../components/DeliveryTimeline"
import { ErrorMessage } from "../components/ErrorMessage"
import { LoadingSpinner } from "../components/LoadingSpinner"
import { StatusBadge } from "../components/StatusBadge"
import { confirmReceipt, getDocumentUrl, markOpened, viewLetterByToken } from "../services/access"
import { extractErrorMessage } from "../services/apiClient"
import type { AccessLetterView } from "../types/tracking"

export function Access() {
  const { token } = useParams<{ token: string }>()
  const [letter, setLetter] = useState<AccessLetterView | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [confirming, setConfirming] = useState(false)

  useEffect(() => {
    if (!token) return
    setLoading(true)
    viewLetterByToken(token)
      .then(() => markOpened(token))
      .then(setLetter)
      .catch((err) => setError(extractErrorMessage(err)))
      .finally(() => setLoading(false))
  }, [token])

  async function handleConfirm() {
    if (!token) return
    setConfirming(true)
    setError(null)
    try {
      const updated = await confirmReceipt(token)
      setLetter(updated)
    } catch (err) {
      setError(extractErrorMessage(err))
    } finally {
      setConfirming(false)
    }
  }

  if (loading) return <LoadingSpinner label="Ouverture du courrier..." />

  if (error || !letter) {
    return (
      <div className="mx-auto max-w-md px-4 py-20 sm:px-6">
        <ErrorMessage message={error ?? "Ce lien n'est plus valide"} />
      </div>
    )
  }

  const canConfirm = letter.status === "OPENED" && letter.acknowledgment_of_receipt
  const alreadyReceived = letter.status === "RECEIVED"

  return (
    <div className="mx-auto max-w-2xl px-4 py-12 sm:px-6">
      <div className="rounded-xl border border-slate-200 bg-white p-6">
        <div className="flex items-center justify-between">
          <p className="text-xs uppercase tracking-wide text-slate-400">
            De la part de {letter.sender_first_name} {letter.sender_last_name}
          </p>
          <StatusBadge status={letter.status} />
        </div>
        <h1 className="mt-2 text-xl font-bold text-slate-800">{letter.subject}</h1>

        <div className="mt-6 rounded-lg bg-slate-50 p-4">
          {letter.has_document ? (
            <a
              href={getDocumentUrl(token!)}
              target="_blank"
              rel="noreferrer"
              className="text-sm font-semibold text-brand-600 hover:underline"
            >
              Télécharger le document PDF
            </a>
          ) : (
            <p className="whitespace-pre-wrap text-sm text-slate-700">{letter.message}</p>
          )}
        </div>

        <ErrorMessage message={error} />

        <div className="mt-6">
          {alreadyReceived ? (
            <p className="text-sm font-medium text-accent-600">Réception déjà confirmée. Merci.</p>
          ) : letter.acknowledgment_of_receipt ? (
            <Button onClick={handleConfirm} isLoading={confirming} disabled={!canConfirm}>
              Confirmer la réception
            </Button>
          ) : (
            <p className="text-sm text-slate-500">
              Ce courrier ne comprend pas d'accusé de réception : aucune confirmation n'est nécessaire de votre part.
            </p>
          )}
        </div>

        {letter.acknowledgment_of_receipt && (
          <p className="mt-6 text-xs text-slate-400">
            Cette confirmation atteste techniquement la réception via Courrier+. Elle ne constitue pas, en l'état, une
            preuve légale équivalente à un accusé de réception postal officiel.
          </p>
        )}
      </div>

      {letter.delivery && (
        <div className="mt-6">
          <DeliveryTimeline delivery={letter.delivery} />
        </div>
      )}
    </div>
  )
}
