import type { DeliveryStatus } from "../types/delivery"

const STATUS_LABELS: Record<DeliveryStatus, string> = {
  CREATED: "Créée",
  READY_FOR_DISPATCH: "Prête à expédier",
  ASSIGNED: "Affectée",
  PICKED_UP: "Prise en charge",
  IN_TRANSIT: "En transit",
  OUT_FOR_DELIVERY: "En cours de livraison",
  DELIVERED: "Livrée",
  DELIVERY_FAILED: "Échec de livraison",
  RETURNED_TO_SENDER: "Retournée à l'expéditeur",
  CANCELLED: "Annulée",
}

const STATUS_STYLES: Record<DeliveryStatus, string> = {
  CREATED: "bg-slate-100 text-slate-700",
  READY_FOR_DISPATCH: "bg-slate-100 text-slate-700",
  ASSIGNED: "bg-brand-100 text-brand-700",
  PICKED_UP: "bg-brand-100 text-brand-700",
  IN_TRANSIT: "bg-brand-100 text-brand-700",
  OUT_FOR_DELIVERY: "bg-warn-500/10 text-warn-500",
  DELIVERED: "bg-accent-500 text-white",
  DELIVERY_FAILED: "bg-danger-500/10 text-danger-500",
  RETURNED_TO_SENDER: "bg-danger-500/10 text-danger-500",
  CANCELLED: "bg-slate-200 text-slate-600",
}

export function DeliveryStatusBadge({ status }: { status: DeliveryStatus }) {
  return (
    <span className={`inline-block rounded-full px-3 py-1 text-xs font-semibold ${STATUS_STYLES[status]}`}>
      {STATUS_LABELS[status]}
    </span>
  )
}
