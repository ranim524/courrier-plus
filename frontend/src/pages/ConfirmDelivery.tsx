import { useEffect, useState } from "react"
import { useParams } from "react-router-dom"
import { Button } from "../components/Button"
import { ErrorMessage } from "../components/ErrorMessage"
import { LoadingSpinner } from "../components/LoadingSpinner"
import { extractErrorMessage } from "../services/apiClient"
import { confirmDeliveryReceipt, getDeliveryConfirmation } from "../services/deliveryConfirmation"
import type { DeliveryConfirmationView } from "../types/delivery"

export function ConfirmDelivery() {
  const { token } = useParams<{ token: string }>()
  const [view, setView] = useState<DeliveryConfirmationView | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [confirming, setConfirming] = useState(false)

  useEffect(() => {
    if (!token) return
    getDeliveryConfirmation(token)
      .then(setView)
      .catch((err) => setError(extractErrorMessage(err)))
      .finally(() => setLoading(false))
  }, [token])

  async function handleConfirm() {
    if (!token) return
    setConfirming(true)
    setError(null)
    try {
      const updated = await confirmDeliveryReceipt(token)
      setView(updated)
    } catch (err) {
      setError(extractErrorMessage(err))
    } finally {
      setConfirming(false)
    }
  }

  if (loading) return <LoadingSpinner label="Chargement..." />

  if (error || !view) {
    return (
      <div className="mx-auto max-w-md px-4 py-20 sm:px-6">
        <ErrorMessage message={error ?? "Ce lien de confirmation n'est plus valide"} />
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-md px-4 py-20 sm:px-6">
      <div className="rounded-xl border border-slate-200 bg-white p-6 text-center">
        {view.confirmed ? (
          <>
            <p className="text-lg font-semibold text-accent-600">Merci, votre confirmation est enregistrée.</p>
            <p className="mt-2 text-sm text-slate-500">L'expéditeur a été informé que vous avez bien reçu son courrier.</p>
          </>
        ) : (
          <>
            <p className="text-xs uppercase tracking-wide text-slate-400">
              De la part de {view.sender_first_name} {view.sender_last_name}
            </p>
            <p className="mt-1 font-mono text-sm text-slate-600">{view.reference}</p>
            <p className="mt-4 text-sm text-slate-700">
              Un courrier physique Courrier+ vient d'être déposé dans votre boîte aux lettres. Confirmez-vous l'avoir
              bien reçu ?
            </p>
            <div className="mt-6">
              <Button onClick={handleConfirm} isLoading={confirming}>
                J'ai bien reçu ce courrier
              </Button>
            </div>
            <ErrorMessage message={error} />
          </>
        )}
      </div>
    </div>
  )
}
