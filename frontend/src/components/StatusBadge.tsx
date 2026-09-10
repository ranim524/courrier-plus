import type { LetterStatus } from "../types/letter"

const STATUS_LABELS: Record<LetterStatus, string> = {
  DRAFT: "Brouillon",
  PENDING_PAYMENT: "Paiement en attente",
  PAID: "Payé",
  SENT: "Envoyé",
  DELIVERED: "Distribué",
  OPENED: "Consulté",
  RECEIVED: "Reçu",
  FAILED: "Échoué",
  REFUSED: "Refusé",
  EXPIRED: "Expiré",
  CANCELLED: "Annulé",
}

const STATUS_STYLES: Record<LetterStatus, string> = {
  DRAFT: "bg-slate-100 text-slate-700",
  PENDING_PAYMENT: "bg-warn-500/10 text-warn-500",
  PAID: "bg-brand-100 text-brand-700",
  SENT: "bg-brand-100 text-brand-700",
  DELIVERED: "bg-brand-100 text-brand-700",
  OPENED: "bg-accent-500/10 text-accent-600",
  RECEIVED: "bg-accent-500 text-white",
  FAILED: "bg-danger-500/10 text-danger-500",
  REFUSED: "bg-danger-500/10 text-danger-500",
  EXPIRED: "bg-slate-200 text-slate-600",
  CANCELLED: "bg-slate-200 text-slate-600",
}

export function StatusBadge({ status }: { status: LetterStatus }) {
  return (
    <span className={`inline-block rounded-full px-3 py-1 text-xs font-semibold ${STATUS_STYLES[status]}`}>
      {STATUS_LABELS[status]}
    </span>
  )
}
