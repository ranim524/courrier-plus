import { useState, type FormEvent } from "react"
import { useNavigate } from "react-router-dom"
import { Button } from "../components/Button"
import { Input } from "../components/Input"

export function TrackSearch() {
  const [reference, setReference] = useState("")
  const navigate = useNavigate()

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (reference.trim()) {
      navigate(`/track/${encodeURIComponent(reference.trim())}`)
    }
  }

  return (
    <div className="mx-auto max-w-md px-4 py-20 text-center sm:px-6">
      <h1 className="text-2xl font-bold text-slate-800">Suivre un courrier</h1>
      <p className="mt-2 text-sm text-slate-500">Entrez la référence indiquée dans votre e-mail de confirmation.</p>
      <form onSubmit={handleSubmit} className="mt-8 flex flex-col gap-4">
        <Input
          label="Référence"
          placeholder="TN-2026-0001847"
          value={reference}
          onChange={(e) => setReference(e.target.value)}
        />
        <Button type="submit">Rechercher</Button>
      </form>
    </div>
  )
}
