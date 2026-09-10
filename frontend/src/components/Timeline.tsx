import type { TrackingEvent } from "../types/tracking"

const EVENT_LABELS: Record<string, string> = {
  LETTER_CREATED: "Courrier créé",
  PAYMENT_STARTED: "Paiement initié",
  PAYMENT_SUCCEEDED: "Paiement réussi",
  PAYMENT_FAILED: "Paiement échoué",
  LETTER_SENT: "Courrier envoyé",
  EMAIL_SENT: "E-mail envoyé",
  EMAIL_FAILED: "Échec de l'e-mail",
  RECIPIENT_LINK_ACCESSED: "Lien consulté par le destinataire",
  LETTER_OPENED: "Courrier ouvert",
  RECEIPT_CONFIRMED: "Réception confirmée",
  TOKEN_EXPIRED: "Lien expiré",
  ADMIN_LOGIN: "Connexion admin",
  ADMIN_VIEWED_LETTER: "Consulté par un administrateur",
  LETTER_CANCELLED: "Courrier annulé",
  LETTER_REFUSED: "Courrier refusé",
}

export function Timeline({ events }: { events: TrackingEvent[] }) {
  if (events.length === 0) {
    return <p className="text-sm text-slate-500">Aucun évènement pour le moment.</p>
  }

  return (
    <ol className="relative border-l-2 border-slate-200 pl-6">
      {events.map((event, index) => (
        <li key={`${event.event_type}-${index}`} className="mb-6 last:mb-0">
          <span className="absolute -left-[9px] mt-1 h-4 w-4 rounded-full border-2 border-white bg-brand-600" />
          <p className="text-sm font-semibold text-slate-800">
            {EVENT_LABELS[event.event_type] ?? event.event_type}
          </p>
          <p className="text-xs text-slate-500">{new Date(event.created_at).toLocaleString("fr-FR")}</p>
        </li>
      ))}
    </ol>
  )
}
