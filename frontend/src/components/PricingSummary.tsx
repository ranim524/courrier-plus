import type { PricingBreakdown } from "../types/pricing"

interface PricingSummaryProps {
  pricing: PricingBreakdown
  documentName?: string | null
}

export function PricingSummary({ pricing, documentName }: PricingSummaryProps) {
  return (
    <div className="rounded-xl border border-brand-200 bg-brand-50 p-5">
      {documentName && (
        <p className="mb-3 text-sm text-brand-700">
          <span className="text-brand-500">Document :</span> {documentName}
        </p>
      )}

      <div className="grid grid-cols-2 gap-y-1 text-sm text-brand-800 sm:grid-cols-4">
        <div>
          <p className="text-xs uppercase tracking-wide text-brand-500">Pages</p>
          <p className="font-semibold">{pricing.page_count}</p>
        </div>
        <div>
          <p className="text-xs uppercase tracking-wide text-brand-500">Poids estimé</p>
          <p className="font-semibold">{pricing.estimated_weight_g} g</p>
        </div>
        <div className="col-span-2 sm:col-span-2">
          <p className="text-xs uppercase tracking-wide text-brand-500">Tranche tarifaire</p>
          <p className="font-semibold">{pricing.weight_bracket}</p>
        </div>
      </div>

      <div className="mt-4 flex flex-col gap-1.5 border-t border-brand-200 pt-4 text-sm">
        <div className="flex justify-between">
          <span className="text-brand-600">Affranchissement</span>
          <span className="font-medium text-brand-800">{pricing.base_postage} {pricing.currency}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-brand-600">Recommandation</span>
          <span className="font-medium text-brand-800">{pricing.registered_fee} {pricing.currency}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-brand-600">Accusé de réception</span>
          <span className="font-medium text-brand-800">{pricing.acknowledgment_fee} {pricing.currency}</span>
        </div>
      </div>

      <div className="mt-4 flex items-center justify-between border-t border-brand-200 pt-4">
        <span className="text-sm font-semibold uppercase tracking-wide text-brand-500">Total</span>
        <span className="text-xl font-bold text-brand-800">
          {pricing.total} {pricing.currency}
        </span>
      </div>
    </div>
  )
}
