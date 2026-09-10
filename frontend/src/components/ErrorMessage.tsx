export function ErrorMessage({ message }: { message: string | null }) {
  if (!message) return null
  return (
    <div className="rounded-lg border border-danger-500/30 bg-danger-500/10 px-4 py-3 text-sm text-danger-500">
      {message}
    </div>
  )
}
