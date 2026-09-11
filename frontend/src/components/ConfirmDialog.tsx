import type { ReactNode } from "react"
import { Button } from "./Button"

interface ConfirmDialogProps {
  title: string
  description: ReactNode
  confirmLabel?: string
  isLoading?: boolean
  danger?: boolean
  onConfirm: () => void
  onCancel: () => void
  children?: ReactNode
}

export function ConfirmDialog({
  title,
  description,
  confirmLabel = "Confirmer",
  isLoading,
  danger,
  onConfirm,
  onCancel,
  children,
}: ConfirmDialogProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4">
      <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-xl">
        <h2 className="text-lg font-bold text-slate-800">{title}</h2>
        <div className="mt-2 text-sm text-slate-600">{description}</div>
        {children && <div className="mt-4">{children}</div>}
        <div className="mt-6 flex justify-end gap-3">
          <Button type="button" variant="secondary" onClick={onCancel} disabled={isLoading}>
            Annuler
          </Button>
          <Button type="button" variant={danger ? "danger" : "primary"} onClick={onConfirm} isLoading={isLoading}>
            {confirmLabel}
          </Button>
        </div>
      </div>
    </div>
  )
}
