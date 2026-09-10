import { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"
import { Button } from "../../components/Button"
import { ErrorMessage } from "../../components/ErrorMessage"
import { StepProgress } from "../../components/StepProgress"
import { extractErrorMessage } from "../../services/apiClient"
import { getPublicConfig } from "../../services/config"
import { createLetter } from "../../services/letters"
import { createPayment } from "../../services/payments"
import { useSendLetterWizard } from "../../hooks/useSendLetterWizard"
import { SEND_STEPS, STEP_NUMBERS } from "./steps"

export function ReviewStep() {
  const wizard = useSendLetterWizard()
  const navigate = useNavigate()
  const [price, setPrice] = useState<number | null>(null)
  const [currency, setCurrency] = useState("TND")
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    if (!wizard.subject) {
      navigate("/send/document")
      return
    }
    getPublicConfig()
      .then((config) => {
        setPrice(config.letter_price)
        setCurrency(config.currency)
      })
      .catch(() => {
        setPrice(15)
      })
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

        <div className="rounded-xl border border-brand-200 bg-brand-50 p-5">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-brand-500">Montant à payer</h2>
          <p className="mt-1 text-xl font-bold text-brand-800">
            {price !== null ? `${price.toFixed(2)} ${currency}` : "..."}
          </p>
        </div>
      </div>

      <ErrorMessage message={error} />

      <div className="mt-6 flex justify-between">
        <Button type="button" variant="secondary" onClick={() => navigate("/send/document")} disabled={submitting}>
          Retour
        </Button>
        <Button type="button" onClick={handleConfirm} isLoading={submitting}>
          Procéder au paiement
        </Button>
      </div>
    </div>
  )
}
