import { useEffect } from "react"
import { Link, useNavigate } from "react-router-dom"
import { Button } from "../../components/Button"
import { useSendLetterWizard } from "../../hooks/useSendLetterWizard"

export function SuccessStep() {
  const wizard = useSendLetterWizard()
  const navigate = useNavigate()

  useEffect(() => {
    if (!wizard.letterId) {
      navigate("/send/sender")
    }
  }, [])

  return (
    <div className="mx-auto max-w-lg px-4 py-16 text-center sm:px-6">
      <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-accent-500/10 text-3xl text-accent-500">
        ✓
      </div>
      <h1 className="mt-6 text-2xl font-bold text-slate-800">Courrier envoyé avec succès</h1>
      <p className="mt-2 text-sm text-slate-500">
        Votre courrier va être imprimé et livré physiquement à votre destinataire. Vous recevrez un e-mail de
        confirmation une fois la livraison effectuée.
      </p>

      <div className="mt-8 flex flex-col items-center gap-3">
        <Link to="/track" onClick={() => wizard.reset()}>
          <Button>Suivre mon courrier</Button>
        </Link>
        <Link
          to="/"
          onClick={() => wizard.reset()}
          className="text-sm font-medium text-brand-600 hover:underline"
        >
          Retour à l'accueil
        </Link>
      </div>
    </div>
  )
}
