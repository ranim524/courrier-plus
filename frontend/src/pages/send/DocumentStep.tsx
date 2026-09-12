import { useEffect, useState, type FormEvent } from "react"
import { Navigate, useNavigate } from "react-router-dom"
import { Button } from "../../components/Button"
import { ErrorMessage } from "../../components/ErrorMessage"
import { FileDropzone } from "../../components/FileDropzone"
import { Input } from "../../components/Input"
import { PricingSummary } from "../../components/PricingSummary"
import { StepProgress } from "../../components/StepProgress"
import { TextArea } from "../../components/TextArea"
import { useSendLetterWizard } from "../../hooks/useSendLetterWizard"
import { extractErrorMessage } from "../../services/apiClient"
import { previewPrice } from "../../services/pricing"
import type { PricingBreakdown } from "../../types/pricing"
import { SEND_STEPS, STEP_NUMBERS } from "./steps"

const MAX_SIZE_BYTES = 10 * 1024 * 1024
const PREVIEW_DEBOUNCE_MS = 400

type Mode = "message" | "pdf"

export function DocumentStep() {
  const wizard = useSendLetterWizard()
  const { subject, message, document, acknowledgmentOfReceipt, recipient } = wizard
  const navigate = useNavigate()
  const [mode, setMode] = useState<Mode>(document ? "pdf" : "message")
  const [subjectValue, setSubjectValue] = useState(subject)
  const [messageValue, setMessageValue] = useState(message)
  const [file, setFile] = useState<File | null>(document)
  const [ackOfReceipt, setAckOfReceipt] = useState(acknowledgmentOfReceipt)
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [pricing, setPricingLocal] = useState<PricingBreakdown | null>(null)
  const [pricingError, setPricingError] = useState<string | null>(null)
  const [pricingLoading, setPricingLoading] = useState(false)

  // The backend is the only source of truth for page count and price: every
  // time the PDF or the acknowledgment-of-receipt option changes, ask it for
  // a fresh preview rather than computing anything client-side.
  useEffect(() => {
    if (mode === "pdf" && !file) {
      setPricingLocal(null)
      return
    }

    const timer = setTimeout(() => {
      setPricingLoading(true)
      setPricingError(null)
      previewPrice(mode === "pdf" ? file : null, ackOfReceipt)
        .then((breakdown) => {
          setPricingLocal(breakdown)
          wizard.setPricing(breakdown)
        })
        .catch((err) => {
          setPricingLocal(null)
          setPricingError(extractErrorMessage(err))
        })
        .finally(() => setPricingLoading(false))
    }, PREVIEW_DEBOUNCE_MS)

    return () => clearTimeout(timer)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mode, file, ackOfReceipt])

  if (!recipient.email) {
    return <Navigate to="/send/recipient" replace />
  }

  function validate(): boolean {
    const next: Record<string, string> = {}
    if (!subjectValue.trim()) next.subject = "L'objet est requis"

    if (mode === "message" && !messageValue.trim()) {
      next.message = "Le message est requis"
    }
    if (mode === "pdf") {
      if (!file) {
        next.document = "Veuillez sélectionner un fichier PDF"
      } else if (file.type !== "application/pdf") {
        next.document = "Seuls les fichiers PDF sont acceptés"
      } else if (file.size > MAX_SIZE_BYTES) {
        next.document = "Le fichier dépasse la taille maximale de 10 Mo"
      } else if (pricingError) {
        next.document = pricingError
      }
    }
    setErrors(next)
    return Object.keys(next).length === 0
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (!validate()) return
    wizard.setLetterContent(subjectValue, mode === "message" ? messageValue : "", mode === "pdf" ? file : null)
    wizard.setAcknowledgmentOfReceipt(ackOfReceipt)
    navigate("/send/review")
  }

  return (
    <div className="mx-auto max-w-2xl px-4 py-12 sm:px-6">
      <StepProgress steps={SEND_STEPS} currentStep={STEP_NUMBERS.document} />
      <h1 className="mt-8 text-2xl font-bold text-slate-800">Votre courrier</h1>
      <p className="mt-1 text-sm text-slate-500">Rédigez un message ou joignez un document PDF.</p>

      <form onSubmit={handleSubmit} className="mt-8 flex flex-col gap-5">
        <Input
          label="Objet"
          value={subjectValue}
          onChange={(e) => setSubjectValue(e.target.value)}
          error={errors.subject}
          required
        />

        <div className="flex gap-2 rounded-lg bg-slate-100 p-1 text-sm font-medium">
          <button
            type="button"
            onClick={() => setMode("message")}
            className={`flex-1 rounded-md py-2 transition-colors ${mode === "message" ? "bg-white shadow-sm text-brand-700" : "text-slate-500"}`}
          >
            Écrire un message
          </button>
          <button
            type="button"
            onClick={() => setMode("pdf")}
            className={`flex-1 rounded-md py-2 transition-colors ${mode === "pdf" ? "bg-white shadow-sm text-brand-700" : "text-slate-500"}`}
          >
            Joindre un PDF
          </button>
        </div>

        {mode === "message" ? (
          <TextArea
            label="Message"
            rows={8}
            value={messageValue}
            onChange={(e) => setMessageValue(e.target.value)}
            error={errors.message}
          />
        ) : (
          <FileDropzone file={file} onFileSelected={setFile} error={errors.document ?? (file ? pricingError ?? undefined : undefined)} />
        )}

        <label className="flex items-center gap-2 text-sm font-medium text-slate-700">
          <input
            type="checkbox"
            checked={ackOfReceipt}
            onChange={(e) => setAckOfReceipt(e.target.checked)}
            className="h-4 w-4 rounded border-slate-300 text-brand-600 focus:ring-brand-500"
          />
          Avec accusé de réception (+2.500 TND)
        </label>

        {pricingLoading && <p className="text-sm text-slate-400">Calcul du tarif...</p>}
        {pricing && !pricingLoading && (
          <PricingSummary pricing={pricing} documentName={mode === "pdf" ? file?.name : null} />
        )}
        {mode === "pdf" && file && pricingError && <ErrorMessage message={pricingError} />}

        <div className="mt-4 flex justify-between">
          <Button type="button" variant="secondary" onClick={() => navigate("/send/recipient")}>
            Retour
          </Button>
          <Button type="submit" disabled={mode === "pdf" && (!pricing || !!pricingError)}>
            Continuer
          </Button>
        </div>
      </form>
    </div>
  )
}
