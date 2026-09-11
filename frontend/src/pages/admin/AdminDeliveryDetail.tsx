import { useEffect, useState } from "react"
import { useParams } from "react-router-dom"
import { Button } from "../../components/Button"
import { ConfirmDialog } from "../../components/ConfirmDialog"
import { DeliveryStatusBadge } from "../../components/DeliveryStatusBadge"
import { ErrorMessage } from "../../components/ErrorMessage"
import { LoadingSpinner } from "../../components/LoadingSpinner"
import { extractErrorMessage } from "../../services/apiClient"
import {
  assignCourier,
  cancelDelivery,
  confirmDelivery,
  getDelivery,
  listAgents,
  markFailed,
  markInTransit,
  markOutForDelivery,
  markPickedUp,
  retryDelivery,
  returnToSender,
} from "../../services/delivery"
import type { DeliveryAgentRead, DeliveryFailureReason, DeliveryOrderRead } from "../../types/delivery"

const FAILURE_REASON_LABELS: Record<DeliveryFailureReason, string> = {
  RECIPIENT_UNAVAILABLE: "Destinataire absent",
  INCORRECT_ADDRESS: "Adresse incorrecte",
  RECIPIENT_REFUSED: "Destinataire a refusé",
  ADDRESS_INACCESSIBLE: "Adresse inaccessible",
  OTHER: "Autre",
}

const TIMELINE_STEPS: { key: keyof DeliveryOrderRead; label: string }[] = [
  { key: "created_at", label: "Livraison créée" },
  { key: "assigned_at", label: "Affectée au livreur" },
  { key: "picked_up_at", label: "Prise en charge" },
  { key: "in_transit_at", label: "En transit" },
  { key: "out_for_delivery_at", label: "En cours de livraison" },
  { key: "delivered_at", label: "Livrée" },
]

export function AdminDeliveryDetail() {
  const { id } = useParams<{ id: string }>()
  const [delivery, setDelivery] = useState<DeliveryOrderRead | null>(null)
  const [agents, setAgents] = useState<DeliveryAgentRead[]>([])
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const [showAssign, setShowAssign] = useState(false)
  const [selectedAgent, setSelectedAgent] = useState("")
  const [showConfirm, setShowConfirm] = useState(false)
  const [showFail, setShowFail] = useState(false)
  const [failReason, setFailReason] = useState<DeliveryFailureReason>("RECIPIENT_UNAVAILABLE")
  const [failNotes, setFailNotes] = useState("")

  function load() {
    if (!id) return
    Promise.all([getDelivery(id), listAgents()])
      .then(([d, a]) => {
        setDelivery(d)
        setAgents(a.filter((agent) => agent.active))
      })
      .catch((err) => setError(extractErrorMessage(err)))
  }

  useEffect(load, [id])

  async function runAction(fn: () => Promise<DeliveryOrderRead>) {
    setBusy(true)
    setError(null)
    try {
      const updated = await fn()
      setDelivery(updated)
    } catch (err) {
      setError(extractErrorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  if (error && !delivery) return <ErrorMessage message={error} />
  if (!delivery) return <LoadingSpinner />

  const d = delivery

  return (
    <div>
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-mono text-2xl font-bold text-slate-800">{d.tracking_number}</h1>
          <p className="mt-1 text-sm text-slate-500">
            Courrier : <span className="font-mono">{d.letter_reference ?? "—"}</span>
          </p>
        </div>
        <DeliveryStatusBadge status={d.status} />
      </div>

      <ErrorMessage message={error} />

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-slate-200 bg-white p-5">
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-400">Détails</h2>
          <dl className="flex flex-col gap-2 text-sm">
            <div className="flex justify-between">
              <dt className="text-slate-500">Prestataire</dt>
              <dd className="text-slate-800">{d.provider.name} (suivi manuel)</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-slate-500">Livreur</dt>
              <dd className="text-slate-800">{d.courier ? `${d.courier.first_name} ${d.courier.last_name}` : "—"}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-slate-500">Tentatives échouées</dt>
              <dd className="text-slate-800">{d.attempt_count}</dd>
            </div>
          </dl>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-5">
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-400">Timeline</h2>
          <ol className="flex flex-col gap-2 text-sm">
            {TIMELINE_STEPS.map((step) => {
              const value = d[step.key] as string | null
              return (
                <li key={step.key} className="flex items-center gap-2">
                  <span className={value ? "text-accent-600" : "text-slate-300"}>{value ? "✓" : "○"}</span>
                  <span className={value ? "text-slate-800" : "text-slate-400"}>{step.label}</span>
                  {value && (
                    <span className="ml-auto text-xs text-slate-400">{new Date(value).toLocaleString("fr-FR")}</span>
                  )}
                </li>
              )
            })}
          </ol>
        </div>

        {d.attempts.length > 0 && (
          <div className="rounded-xl border border-slate-200 bg-white p-5 lg:col-span-2">
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-400">Tentatives échouées</h2>
            <ul className="flex flex-col gap-2 text-sm">
              {d.attempts.map((a) => (
                <li key={a.id} className="border-b border-slate-50 pb-2 last:border-0">
                  <div className="flex justify-between">
                    <span className="font-medium text-slate-700">Tentative #{a.attempt_number}</span>
                    <span className="text-xs text-slate-400">{new Date(a.attempted_at).toLocaleString("fr-FR")}</span>
                  </div>
                  <p className="text-slate-600">{FAILURE_REASON_LABELS[a.reason]}</p>
                  {a.notes && <p className="text-xs text-slate-400">{a.notes}</p>}
                </li>
              ))}
            </ul>
          </div>
        )}

        {d.proof && (
          <div className="rounded-xl border border-accent-500/30 bg-accent-500/10 p-5 lg:col-span-2">
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-accent-600">Preuve de livraison</h2>
            <dl className="grid gap-2 text-sm sm:grid-cols-2">
              <div><dt className="text-accent-600/70">Livrée le</dt><dd className="text-slate-800">{new Date(d.proof.delivered_at).toLocaleString("fr-FR")}</dd></div>
              <div><dt className="text-accent-600/70">Confirmé par</dt><dd className="text-slate-800">{d.proof.delivered_by}</dd></div>
              <div><dt className="text-accent-600/70">Méthode</dt><dd className="text-slate-800">{d.proof.delivery_method ?? "—"}</dd></div>
              <div><dt className="text-accent-600/70">Type de preuve</dt><dd className="text-slate-800">Confirmation manuelle</dd></div>
            </dl>
          </div>
        )}

        <div className="rounded-xl border border-slate-200 bg-white p-5 lg:col-span-2">
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-400">Actions</h2>
          <div className="flex flex-wrap gap-3">
            {d.status === "READY_FOR_DISPATCH" && (
              <Button onClick={() => setShowAssign(true)} disabled={busy}>
                Assigner au livreur
              </Button>
            )}
            {d.status === "ASSIGNED" && (
              <Button onClick={() => runAction(() => markPickedUp(d.id))} isLoading={busy}>
                Marquer comme prise en charge
              </Button>
            )}
            {d.status === "PICKED_UP" && (
              <Button onClick={() => runAction(() => markInTransit(d.id))} isLoading={busy}>
                Marquer en transit
              </Button>
            )}
            {d.status === "IN_TRANSIT" && (
              <Button onClick={() => runAction(() => markOutForDelivery(d.id))} isLoading={busy}>
                Marquer en cours de livraison
              </Button>
            )}
            {d.status === "OUT_FOR_DELIVERY" && (
              <>
                <Button onClick={() => setShowConfirm(true)} disabled={busy}>
                  Confirmer la livraison
                </Button>
                <Button variant="danger" onClick={() => setShowFail(true)} disabled={busy}>
                  Marquer comme échouée
                </Button>
              </>
            )}
            {d.status === "DELIVERY_FAILED" && (
              <>
                <Button onClick={() => runAction(() => retryDelivery(d.id))} isLoading={busy}>
                  Réessayer la livraison
                </Button>
                <Button variant="danger" onClick={() => runAction(() => returnToSender(d.id))} isLoading={busy}>
                  Retourner à l'expéditeur
                </Button>
              </>
            )}
            {["CREATED", "READY_FOR_DISPATCH", "ASSIGNED"].includes(d.status) && (
              <Button variant="secondary" onClick={() => runAction(() => cancelDelivery(d.id))} disabled={busy}>
                Annuler la livraison
              </Button>
            )}
            {["DELIVERED", "RETURNED_TO_SENDER", "CANCELLED"].includes(d.status) && (
              <p className="text-sm text-slate-400">Aucune action disponible — statut final.</p>
            )}
          </div>
        </div>
      </div>

      {showAssign && (
        <ConfirmDialog
          title="Assigner au livreur"
          description="Sélectionnez le livreur qui va prendre en charge ce courrier."
          confirmLabel="Assigner"
          isLoading={busy}
          onCancel={() => setShowAssign(false)}
          onConfirm={() => {
            if (!selectedAgent) return
            runAction(() => assignCourier(d.id, selectedAgent)).then(() => setShowAssign(false))
          }}
        >
          <select
            value={selectedAgent}
            onChange={(e) => setSelectedAgent(e.target.value)}
            className="w-full rounded-lg border border-slate-300 px-3.5 py-2.5 text-sm outline-none focus:border-brand-500"
          >
            <option value="">Sélectionner un livreur</option>
            {agents.map((a) => (
              <option key={a.id} value={a.id}>
                {a.first_name} {a.last_name}
              </option>
            ))}
          </select>
        </ConfirmDialog>
      )}

      {showConfirm && (
        <ConfirmDialog
          title="Confirmer la livraison physique ?"
          description={
            <>
              Cette action signifie que le courrier papier a réellement été remis au destinataire.
              <br />
              <br />
              Cette confirmation déclenchera les notifications de livraison.
            </>
          }
          confirmLabel="Confirmer la livraison"
          isLoading={busy}
          onCancel={() => setShowConfirm(false)}
          onConfirm={() => {
            runAction(() => confirmDelivery(d.id)).then(() => setShowConfirm(false))
          }}
        />
      )}

      {showFail && (
        <ConfirmDialog
          title="Marquer la livraison comme échouée"
          description="Précisez la raison de l'échec de cette tentative de livraison."
          confirmLabel="Enregistrer l'échec"
          danger
          isLoading={busy}
          onCancel={() => setShowFail(false)}
          onConfirm={() => {
            runAction(() => markFailed(d.id, failReason, failNotes || undefined)).then(() => {
              setShowFail(false)
              setFailNotes("")
            })
          }}
        >
          <div className="flex flex-col gap-3">
            <select
              value={failReason}
              onChange={(e) => setFailReason(e.target.value as DeliveryFailureReason)}
              className="w-full rounded-lg border border-slate-300 px-3.5 py-2.5 text-sm outline-none focus:border-brand-500"
            >
              {Object.entries(FAILURE_REASON_LABELS).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
            <textarea
              placeholder="Notes (optionnel)"
              value={failNotes}
              onChange={(e) => setFailNotes(e.target.value)}
              rows={3}
              className="w-full rounded-lg border border-slate-300 px-3.5 py-2.5 text-sm outline-none focus:border-brand-500"
            />
          </div>
        </ConfirmDialog>
      )}
    </div>
  )
}
