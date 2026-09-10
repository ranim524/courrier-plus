import { useState, type FormEvent } from "react"
import { useNavigate } from "react-router-dom"
import { Button } from "../../components/Button"
import { Input } from "../../components/Input"
import { StepProgress } from "../../components/StepProgress"
import { useSendLetterWizard } from "../../hooks/useSendLetterWizard"
import { SEND_STEPS, STEP_NUMBERS } from "./steps"

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

export function SenderStep() {
  const { sender, setSender } = useSendLetterWizard()
  const navigate = useNavigate()
  const [form, setForm] = useState(sender)
  const [errors, setErrors] = useState<Record<string, string>>({})

  function validate(): boolean {
    const next: Record<string, string> = {}
    if (!form.firstName.trim()) next.firstName = "Le prénom est requis"
    if (!form.lastName.trim()) next.lastName = "Le nom est requis"
    if (!EMAIL_REGEX.test(form.email)) next.email = "Adresse e-mail invalide"
    setErrors(next)
    return Object.keys(next).length === 0
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (!validate()) return
    setSender(form)
    navigate("/send/recipient")
  }

  return (
    <div className="mx-auto max-w-2xl px-4 py-12 sm:px-6">
      <StepProgress steps={SEND_STEPS} currentStep={STEP_NUMBERS.sender} />
      <h1 className="mt-8 text-2xl font-bold text-slate-800">Vos informations</h1>
      <p className="mt-1 text-sm text-slate-500">Ces informations identifient l'expéditeur du courrier.</p>

      <form onSubmit={handleSubmit} className="mt-8 flex flex-col gap-5">
        <div className="grid gap-5 sm:grid-cols-2">
          <Input
            label="Prénom"
            value={form.firstName}
            onChange={(e) => setForm({ ...form, firstName: e.target.value })}
            error={errors.firstName}
            required
          />
          <Input
            label="Nom"
            value={form.lastName}
            onChange={(e) => setForm({ ...form, lastName: e.target.value })}
            error={errors.lastName}
            required
          />
        </div>
        <Input
          label="E-mail"
          type="email"
          value={form.email}
          onChange={(e) => setForm({ ...form, email: e.target.value })}
          error={errors.email}
          required
        />
        <Input
          label="Téléphone (optionnel)"
          type="tel"
          value={form.phone}
          onChange={(e) => setForm({ ...form, phone: e.target.value })}
        />

        <div className="mt-4 flex justify-end">
          <Button type="submit">Continuer</Button>
        </div>
      </form>
    </div>
  )
}
