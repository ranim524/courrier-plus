import { DeliveryStatusBadge } from "./DeliveryStatusBadge"
import type { DeliveryPublicView } from "../types/delivery"

export function DeliveryTimeline({ delivery }: { delivery: DeliveryPublicView }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-wide text-slate-400">Suivi de livraison (manuel)</p>
          <p className="font-mono text-sm font-semibold text-slate-800">{delivery.tracking_number}</p>
        </div>
        <DeliveryStatusBadge status={delivery.status} />
      </div>

      <ol className="mt-4 flex flex-col gap-2 text-sm">
        {delivery.events.map((event, index) => (
          <li key={index} className="flex items-center gap-2">
            <span className="text-accent-600">✓</span>
            <span className="text-slate-700">{event.label}</span>
            <span className="ml-auto text-xs text-slate-400">{new Date(event.at).toLocaleString("fr-FR")}</span>
          </li>
        ))}
      </ol>
    </div>
  )
}
