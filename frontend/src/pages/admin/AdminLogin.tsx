import { useState, type FormEvent } from "react"
import { useNavigate } from "react-router-dom"
import { Button } from "../../components/Button"
import { ErrorMessage } from "../../components/ErrorMessage"
import { Input } from "../../components/Input"
import { useAuth } from "../../hooks/useAuth"
import { extractErrorMessage } from "../../services/apiClient"
import { adminLogin } from "../../services/admin"

export function AdminLogin() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setSubmitting(true)
    setError(null)
    try {
      const result = await adminLogin(email, password)
      login(result.access_token)
      navigate("/admin")
    } catch (err) {
      setError(extractErrorMessage(err))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-brand-700 px-4">
      <div className="w-full max-w-sm rounded-2xl bg-white p-8 shadow-xl">
        <h1 className="text-center text-xl font-extrabold text-brand-700">
          Courrier<span className="text-accent-500">+</span>
        </h1>
        <p className="mt-1 text-center text-sm text-slate-500">Espace administrateur</p>

        <form onSubmit={handleSubmit} className="mt-8 flex flex-col gap-4">
          <Input label="E-mail" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          <Input
            label="Mot de passe"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          <ErrorMessage message={error} />
          <Button type="submit" className="mt-2 w-full" isLoading={submitting}>
            Se connecter
          </Button>
        </form>
      </div>
    </div>
  )
}
