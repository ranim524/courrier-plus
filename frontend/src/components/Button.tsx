import type { ButtonHTMLAttributes } from "react"

type Variant = "primary" | "secondary" | "ghost" | "danger"

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant
  isLoading?: boolean
}

const base =
  "inline-flex items-center justify-center gap-2 rounded-lg px-5 py-2.5 text-sm font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed"

const variants: Record<Variant, string> = {
  primary: "bg-brand-600 text-white hover:bg-brand-700",
  secondary: "bg-white text-brand-600 border border-brand-200 hover:bg-brand-50",
  ghost: "bg-transparent text-brand-600 hover:bg-brand-50",
  danger: "bg-danger-500 text-white hover:opacity-90",
}

export function Button({ variant = "primary", isLoading, className = "", children, disabled, ...rest }: ButtonProps) {
  return (
    <button className={`${base} ${variants[variant]} ${className}`} disabled={disabled || isLoading} {...rest}>
      {isLoading && (
        <span className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
      )}
      {children}
    </button>
  )
}
