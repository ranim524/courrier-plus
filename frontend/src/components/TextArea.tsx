import type { TextareaHTMLAttributes } from "react"

interface TextAreaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label: string
  error?: string
}

export function TextArea({ label, error, id, className = "", ...rest }: TextAreaProps) {
  const areaId = id ?? label.toLowerCase().replace(/\s+/g, "-")
  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={areaId} className="text-sm font-medium text-slate-700">
        {label}
      </label>
      <textarea
        id={areaId}
        className={`rounded-lg border px-3.5 py-2.5 text-sm outline-none transition-colors focus:border-brand-500 focus:ring-2 focus:ring-brand-100 ${
          error ? "border-danger-500" : "border-slate-300"
        } ${className}`}
        {...rest}
      />
      {error && <p className="text-xs text-danger-500">{error}</p>}
    </div>
  )
}
