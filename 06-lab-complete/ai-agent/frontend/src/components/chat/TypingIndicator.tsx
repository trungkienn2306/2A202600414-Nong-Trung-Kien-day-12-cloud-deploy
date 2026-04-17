export function TypingIndicator() {
  return (
    <div
      className="border-b border-slate-100/90 bg-white"
      role="status"
      aria-live="polite"
      aria-label="Trợ lý đang soạn tin"
    >
      <div className="mx-auto flex max-w-4xl gap-4 px-4 py-5 sm:px-6 lg:px-8">
        <div
          className="flex size-8 shrink-0 items-center justify-center rounded-md bg-linear-to-br from-brand-sky to-brand-teal text-sm text-white shadow-sm sm:size-9"
          aria-hidden
        >
          ✈
        </div>
        <div className="flex min-w-0 flex-1 flex-col gap-2 pt-1">
          <span className="sr-only">Đang soạn gợi ý</span>
          <span className="text-sm font-semibold text-slate-800">Du lịch AI</span>
          <div className="flex items-center gap-2">
            <span className="text-sm text-slate-500">Đang soạn gợi ý</span>
            <span className="flex gap-1">
              <span className="size-1.5 animate-bounce rounded-full bg-brand-teal [animation-delay:0ms]" />
              <span className="size-1.5 animate-bounce rounded-full bg-brand-teal [animation-delay:150ms]" />
              <span className="size-1.5 animate-bounce rounded-full bg-brand-teal [animation-delay:300ms]" />
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}
