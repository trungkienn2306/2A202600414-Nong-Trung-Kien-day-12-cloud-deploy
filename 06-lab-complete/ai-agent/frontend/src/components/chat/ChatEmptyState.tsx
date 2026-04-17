const SUGGESTIONS = [
  'Gợi ý 3 ngày ở Đà Lạt tầm 4 triệu/người?',
  'Đi biển Phú Quốc hay Nha Trang hợp tháng 7?',
  'Cách chia ngân sách khi du lịch nhóm 4 người?',
]

type Props = {
  onPickSuggestion: (text: string) => void
  disabled?: boolean
}

export function ChatEmptyState({ onPickSuggestion, disabled }: Props) {
  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-8 px-4 py-10 sm:px-8">
      <div className="mx-auto max-w-3xl text-center">
        <div
          className="mx-auto mb-6 flex size-16 items-center justify-center rounded-2xl bg-linear-to-br from-brand-cyan/40 to-brand-sky/30 text-4xl shadow-inner"
          aria-hidden
        >
          🧭
        </div>
        <h2 className="text-2xl font-semibold tracking-tight text-slate-800 sm:text-3xl">
          Bạn muốn đi đâu?
        </h2>
        <p className="mt-3 text-base leading-relaxed text-slate-600 sm:text-lg">
          Hỏi về điểm đến, lịch trình, ngân sách hoặc mẹo an toàn. Đây là bản demo —
          phản hồi được mô phỏng.
        </p>
      </div>

      <div className="grid w-full max-w-3xl gap-2 sm:grid-cols-3">
        {SUGGESTIONS.map((text) => (
          <button
            key={text}
            type="button"
            disabled={disabled}
            onClick={() => onPickSuggestion(text)}
            className="rounded-xl border border-slate-200 bg-slate-50/90 px-4 py-3 text-left text-sm leading-snug text-slate-700 shadow-sm transition hover:border-brand-sky/40 hover:bg-white disabled:pointer-events-none disabled:opacity-50"
          >
            {text}
          </button>
        ))}
      </div>
    </div>
  )
}
