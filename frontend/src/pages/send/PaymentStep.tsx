import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { Button } from "../../components/Button"
import { ErrorMessage } from "../../components/ErrorMessage"
import { StepProgress } from "../../components/StepProgress"
import { extractErrorMessage } from "../../services/apiClient"
import { confirmMockPayment } from "../../services/payments"
import { useSendLetterWizard } from "../../hooks/useSendLetterWizard"
import { SEND_STEPS, STEP_NUMBERS } from "./steps"

export function PaymentStep() {
  const wizard = useSendLetterWizard()
  const navigate = useNavigate()
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  if (!wizard.transactionId) {
    navigate("/send/review")
    return null
  }

  async function pay(outcome: "success" | "failure") {
    setSubmitting(true)
    setError(null)
    try {
      const payment = await confirmMockPayment(wizard.transactionId!, outcome)
      if (payment.status === "PAID") {
        navigate("/send/success")
      } else {
        setError("Le paiement a échoué. Vous pouvez réessayer.")
      }
    } catch (err) {
      setError(extractErrorMessage(err))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="mx-auto max-w-lg px-4 py-12 sm:px-6">
      <StepProgress steps={SEND_STEPS} currentStep={STEP_NUMBERS.payment} />
      <h1 className="mt-8 text-2xl font-bold text-slate-800">Paiement</h1>
      <p className="mt-1 text-sm text-slate-500">
        Environnement de développement — ceci est un paiement fictif (mode <code>mock</code>), aucun débit réel
        n'est effectué.
      </p>

      <div className="mt-8 rounded-xl border border-slate-200 bg-white p-6 text-center">
        <p className="text-sm text-slate-500">Référence de transaction</p>
        <p className="mt-1 font-mono text-sm text-slate-700">{wizard.transactionId}</p>

        <Button className="mt-6 w-full" onClick={() => pay("success")} isLoading={submitting}>
          Payer maintenant
        </Button>
        <button
          onClick={() => pay("failure")}
          disabled={submitting}
          className="mt-3 text-xs text-slate-400 underline hover:text-slate-600"
        >
          Simuler un échec de paiement (test)
        </button>
      </div>

      <ErrorMessage message={error} />
    </div>
  )
}
