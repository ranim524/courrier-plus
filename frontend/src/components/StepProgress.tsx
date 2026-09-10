interface StepProgressProps {
  steps: string[]
  currentStep: number
}

export function StepProgress({ steps, currentStep }: StepProgressProps) {
  return (
    <ol className="flex w-full items-center">
      {steps.map((step, index) => {
        const stepNumber = index + 1
        const isActive = stepNumber === currentStep
        const isDone = stepNumber < currentStep
        return (
          <li key={step} className="flex flex-1 items-center last:flex-none">
            <div className="flex flex-col items-center gap-1.5">
              <div
                className={`flex h-8 w-8 items-center justify-center rounded-full text-sm font-semibold ${
                  isDone
                    ? "bg-accent-500 text-white"
                    : isActive
                      ? "bg-brand-600 text-white"
                      : "bg-slate-200 text-slate-500"
                }`}
              >
                {isDone ? "✓" : stepNumber}
              </div>
              <span
                className={`hidden text-xs font-medium sm:block ${isActive ? "text-brand-700" : "text-slate-500"}`}
              >
                {step}
              </span>
            </div>
            {stepNumber !== steps.length && (
              <div className={`mx-2 h-0.5 flex-1 ${isDone ? "bg-accent-500" : "bg-slate-200"}`} />
            )}
          </li>
        )
      })}
    </ol>
  )
}
