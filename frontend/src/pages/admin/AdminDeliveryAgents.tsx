import { useEffect, useState } from "react"
import { Button } from "../../components/Button"
import { ErrorMessage } from "../../components/ErrorMessage"
import { Input } from "../../components/Input"
import { LoadingSpinner } from "../../components/LoadingSpinner"
import { extractErrorMessage } from "../../services/apiClient"
import { createAgent, listAgents, listProviders, setAgentActive } from "../../services/delivery"
import type { DeliveryAgentRead, DeliveryProviderRead } from "../../types/delivery"

export function AdminDeliveryAgents() {
  const [agents, setAgents] = useState<DeliveryAgentRead[] | null>(null)
  const [providers, setProviders] = useState<DeliveryProviderRead[]>([])
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const [firstName, setFirstName] = useState("")
  const [lastName, setLastName] = useState("")
  const [phone, setPhone] = useState("")
  const [email, setEmail] = useState("")

  function load() {
    Promise.all([listAgents(), listProviders()])
      .then(([a, p]) => {
        setAgents(a)
        setProviders(p)
      })
      .catch((err) => setError(extractErrorMessage(err)))
  }

  useEffect(load, [])

  async function handleCreate() {
    if (!firstName || !lastName || !phone || providers.length === 0) return
    setSubmitting(true)
    setError(null)
    try {
      await createAgent({ providerId: providers[0].id, firstName, lastName, phone, email })
      setFirstName("")
      setLastName("")
      setPhone("")
      setEmail("")
      load()
    } catch (err) {
      setError(extractErrorMessage(err))
    } finally {
      setSubmitting(false)
    }
  }

  async function toggleActive(agent: DeliveryAgentRead) {
    try {
      await setAgentActive(agent.id, !agent.active)
      load()
    } catch (err) {
      setError(extractErrorMessage(err))
    }
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-slate-800">Livreurs</h1>
      <p className="mt-1 text-sm text-slate-500">Gestion des livreurs Courrier+ Delivery (suivi manuel).</p>

      <ErrorMessage message={error} />

      <div className="mt-6 rounded-xl border border-slate-200 bg-white p-5">
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-400">Ajouter un livreur</h2>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <Input label="Prénom" value={firstName} onChange={(e) => setFirstName(e.target.value)} />
          <Input label="Nom" value={lastName} onChange={(e) => setLastName(e.target.value)} />
          <Input label="Téléphone" value={phone} onChange={(e) => setPhone(e.target.value)} />
          <Input label="E-mail (optionnel)" type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
        </div>
        <Button className="mt-4" onClick={handleCreate} isLoading={submitting}>
          Ajouter
        </Button>
      </div>

      {!agents ? (
        <LoadingSpinner />
      ) : (
        <div className="mt-6 overflow-x-auto rounded-xl border border-slate-200 bg-white">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase text-slate-400">
              <tr>
                <th className="px-4 py-3">Nom</th>
                <th className="px-4 py-3">Téléphone</th>
                <th className="px-4 py-3">E-mail</th>
                <th className="px-4 py-3">Statut</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {agents.map((a) => (
                <tr key={a.id} className="border-t border-slate-100">
                  <td className="px-4 py-3">{a.first_name} {a.last_name}</td>
                  <td className="px-4 py-3">{a.phone}</td>
                  <td className="px-4 py-3">{a.email ?? "—"}</td>
                  <td className="px-4 py-3">
                    <span className={a.active ? "text-accent-600" : "text-slate-400"}>
                      {a.active ? "Actif" : "Inactif"}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button onClick={() => toggleActive(a)} className="text-brand-600 hover:underline">
                      {a.active ? "Désactiver" : "Réactiver"}
                    </button>
                  </td>
                </tr>
              ))}
              {agents.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center text-slate-400">
                    Aucun livreur enregistré.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
