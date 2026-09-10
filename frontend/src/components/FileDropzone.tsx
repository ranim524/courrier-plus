import { useRef, type DragEvent } from "react"

interface FileDropzoneProps {
  file: File | null
  onFileSelected: (file: File | null) => void
  error?: string
}

const MAX_SIZE_MB = 10

export function FileDropzone({ file, onFileSelected, error }: FileDropzoneProps) {
  const inputRef = useRef<HTMLInputElement>(null)

  function handleFiles(fileList: FileList | null) {
    const selected = fileList?.[0]
    if (!selected) return
    onFileSelected(selected)
  }

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault()
    handleFiles(event.dataTransfer.files)
  }

  return (
    <div>
      <div
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className="flex cursor-pointer flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed border-slate-300 bg-slate-50 px-6 py-10 text-center transition-colors hover:border-brand-400 hover:bg-brand-50"
      >
        <span className="text-sm font-medium text-slate-700">
          {file ? file.name : "Glissez-déposez un PDF ici, ou cliquez pour sélectionner"}
        </span>
        <span className="text-xs text-slate-400">PDF uniquement, {MAX_SIZE_MB} Mo maximum</span>
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf"
          className="hidden"
          onChange={(e) => handleFiles(e.target.files)}
        />
      </div>
      {error && <p className="mt-1.5 text-xs text-danger-500">{error}</p>}
    </div>
  )
}
