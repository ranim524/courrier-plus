import { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"
import { Button } from "../../components/Button"
import { ErrorMessage } from "../../components/ErrorMessage"
import { PricingSummary } from "../../components/PricingSummary"
import { StepProgress } from "../../components/StepProgress"
import { useSendLetterWizard } from "../../hooks/useSendLetterWizard"
import { extractErrorMessage } from "../../services/apiClient"
import { createLetter } from "../../services/letters"
import { createPayment } from "../../services/payments"
import { previewPrice } from "../../services/pricing"
import { SEND_STEPS, STEP_NUMBERS } from "./steps"

export function ReviewStep() {
  const wizard = useSendLetterWizard()
  const navigate = useNavigate()
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    if (!wizard.subject) {
      navigate("/send/document")
      return
    }
    // The pricing preview from the document step is normally already stored
    // in the wizard, but refresh it here too in case the user navigated back
    // and forth -- this display is informational only, the backend always
    // recomputes the authoritative total when the letter is actually created.
    if (!wizard.pricing) {
      previewPrice(wizard.document, wizard.acknowledgmentOfReceipt).then(wizard.setPricing).catch(() => {})
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  async function handleConfirm() {
    setSubmitting(true)
    setError(null)
    try {
      let letterId = wizard.letterId
      if (!letterId) {
        const letter = await createLetter({
          sender: wizard.sender,
          recipient: wizard.recipient,
          subject: wizard.subject,
          message: wizard.message || undefined,
          document: wizard.document,
          acknowledgmentOfReceipt: wizard.acknowledgmentOfReceipt,
        })
        letterId = letter.id
        wizard.setLetterCreated(letter.id)
      }

      const payment = await createPayment(letterId)
      wizard.setTransactionId(payment.transaction_id)
      navigate("/send/payment")
    } catch (err) {
      setError(extractErrorMessage(err))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="mx-auto max-w-2xl px-4 py-12 sm:px-6">
      <StepProgress steps={SEND_STEPS} currentStep={STEP_NUMBERS.review} />
      <h1 className="mt-8 text-2xl font-bold text-slate-800">Vérification</h1>
      <p className="mt-1 text-sm text-slate-500">Vérifiez les informations avant de procéder au paiement.</p>

      <div className="mt-8 flex flex-col gap-4">
        <div className="rounded-xl border border-slate-200 bg-white p-5">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">Expéditeur</h2>
          <p className="mt-1 text-sm text-slate-800">
            {wizard.sender.firstName} {wizard.sender.lastName} — {wizard.sender.email}
          </p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-5">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">Destinataire</h2>
          <p className="mt-1 text-sm text-slate-800">
            {wizard.recipient.firstName} {wizard.recipient.lastName} — {wizard.recipient.email}
          </p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-5">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">Objet</h2>
          <p className="mt-1 text-sm text-slate-800">{wizard.subject}</p>
          {wizard.document ? (
            <p className="mt-2 text-sm text-slate-600">Document joint : {wizard.document.name}</p>
          ) : (
            <p className="mt-2 whitespace-pre-wrap text-sm text-slate-600">{wizard.message}</p>
          )}
        </div>

        {wizard.pricing ? (
          <PricingSummary pricing={wizard.pricing} documentName={wizard.document?.name} />
        ) : (
          <p className="text-sm text-slate-400">Calcul du tarif...</p>
        )}
      </div>

      <ErrorMessage message={error} />

      <div className="mt-6 flex justify-between">
        <Button type="button" variant="secondary" onClick={() => navigate("/send/document")} disabled={submitting}>
          Retour
        </Button>
        <Button type="button" onClick={handleConfirm} isLoading={submitting} disabled={!wizard.pricing}>
          Procéder au paiement
        </Button>
      </div>
    </div>
  )
}
