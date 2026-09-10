import { useEffect, useState } from "react"
import { useParams } from "react-router-dom"
import { ErrorMessage } from "../../components/ErrorMessage"
import { LoadingSpinner } from "../../components/LoadingSpinner"
import { StatusBadge } from "../../components/StatusBadge"
import { extractErrorMessage } from "../../services/apiClient"
import { getLetterDetail, getLetterDocumentUrl, getLetterEmails, getLetterEvents } from "../../services/admin"
import type { LetterEventRead, EmailEventRead } from "../../types/admin"
import type { LetterRead } from "../../types/letter"

export function AdminLetterDetail() {
  const { id } = useParams<{ id: string }>()
  const [letter, setLetter] = useState<LetterRead | null>(null)
  const [events, setEvents] = useState<LetterEventRead[]>([])
  const [emails, setEmails] = useState<EmailEventRead[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!id) return
    Promise.all([getLetterDetail(id), getLetterEvents(id), getLetterEmails(id)])
      .then(([l, e, em]) => {
        setLetter(l)
        setEvents(e)
        setEmails(em)
      })
      .catch((err) => setError(extractErrorMessage(err)))
  }, [id])

  if (error) return <ErrorMessage message={error} />
  if (!letter) return <LoadingSpinner />

  return (
    <div>
      <div className="flex items-center justify-between">
        <h1 className="font-mono text-2xl font-bold text-slate-800">{letter.reference ?? "Brouillon"}</h1>
        <StatusBadge status={letter.status} />
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-slate-200 bg-white p-5">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">Expéditeur</h2>
          <p className="mt-1 text-sm text-slate-800">
            {letter.sender_first_name} {letter.sender_last_name}
          </p>
          <p className="text-sm text-slate-500">{letter.sender_email}</p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-5">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">Destinataire</h2>
          <p className="mt-1 text-sm text-slate-800">
            {letter.recipient_first_name} {letter.recipient_last_name}
          </p>
          <p className="text-sm text-slate-500">{letter.recipient_email}</p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-5 lg:col-span-2">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">Contenu</h2>
          <p className="mt-1 font-medium text-slate-800">{letter.subject}</p>
          {letter.document ? (
            <div className="mt-2 text-sm text-slate-600">
              <p>Fichier : {letter.document.original_filename}</p>
              <p>Taille : {(letter.document.size_bytes / 1024).toFixed(1)} Ko</p>
              <p className="break-all font-mono text-xs text-slate-400">SHA-256 : {letter.document.sha256}</p>
              <a
                href={getLetterDocumentUrl(letter.id)}
                target="_blank"
                rel="noreferrer"
                className="mt-2 inline-block text-brand-600 hover:underline"
              >
                Télécharger le PDF
              </a>
            </div>
          ) : (
            <p className="mt-2 whitespace-pre-wrap text-sm text-slate-600">{letter.message}</p>
          )}
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-5 lg:col-span-2">
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-400">Tarification</h2>
          <div className="grid grid-cols-2 gap-4 text-sm sm:grid-cols-4">
            <div>
              <p className="text-xs text-slate-400">Pages</p>
              <p className="font-semibold text-slate-800">{letter.page_count}</p>
            </div>
            <div>
              <p className="text-xs text-slate-400">Poids estimé</p>
              <p className="font-semibold text-slate-800">{letter.estimated_weight_g} g</p>
            </div>
            <div>
              <p className="text-xs text-slate-400">Tranche tarifaire</p>
              <p className="font-semibold text-slate-800">{letter.weight_bracket}</p>
            </div>
            <div>
              <p className="text-xs text-slate-400">Accusé de réception</p>
              <p className="font-semibold text-slate-800">{letter.acknowledgment_of_receipt ? "Oui" : "Non"}</p>
            </div>
          </div>
          <div className="mt-4 flex flex-col gap-1.5 border-t border-slate-100 pt-4 text-sm">
            <div className="flex justify-between">
              <span className="text-slate-500">Affranchissement</span>
              <span className="text-slate-800">
                {letter.base_postage.toFixed(3)} {letter.currency}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Recommandation</span>
              <span className="text-slate-800">
                {letter.registered_fee.toFixed(3)} {letter.currency}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Accusé de réception</span>
              <span className="text-slate-800">
                {letter.acknowledgment_fee.toFixed(3)} {letter.currency}
              </span>
            </div>
            <div className="mt-2 flex justify-between border-t border-slate-100 pt-2 font-semibold">
              <span className="text-slate-700">Total</span>
              <span className="text-brand-700">
                {letter.total_amount.toFixed(3)} {letter.currency}
              </span>
            </div>
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-5">
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-400">Évènements</h2>
          <ul className="flex flex-col gap-2 text-sm">
            {events.map((e) => (
              <li key={e.id} className="flex justify-between border-b border-slate-50 pb-2 last:border-0">
                <span className="text-slate-700">{e.event_type}</span>
                <span className="text-xs text-slate-400">{new Date(e.created_at).toLocaleString("fr-FR")}</span>
              </li>
            ))}
            {events.length === 0 && <p className="text-slate-400">Aucun évènement.</p>}
          </ul>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-5">
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-400">E-mails</h2>
          <ul className="flex flex-col gap-2 text-sm">
            {emails.map((e) => (
              <li key={e.id} className="flex justify-between border-b border-slate-50 pb-2 last:border-0">
                <span className="text-slate-700">
                  {e.email_type} → {e.recipient}
                </span>
                <span
                  className={`text-xs font-semibold ${e.status === "SENT" ? "text-accent-600" : e.status === "FAILED" ? "text-danger-500" : "text-slate-400"}`}
                >
                  {e.status}
                </span>
              </li>
            ))}
            {emails.length === 0 && <p className="text-slate-400">Aucun e-mail.</p>}
          </ul>
        </div>
      </div>
    </div>
  )
}
