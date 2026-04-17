import { useCallback, useRef, useState } from 'react'

type Props = {
  onSend: (text: string) => void
  disabled?: boolean
}

export function ChatComposer({ onSend, disabled }: Props) {
  const [value, setValue] = useState('')
  const taRef = useRef<HTMLTextAreaElement>(null)

  const submit = useCallback(() => {
    const t = value.trim()
    if (!t || disabled) return
    onSend(t)
    setValue('')
    taRef.current?.focus()
  }, [value, disabled, onSend])

  return (
    <footer className="shrink-0 border-t border-slate-200/90 bg-white px-3 py-3 sm:px-4 sm:py-4 lg:px-6">
      <form
        className="mx-auto flex w-full max-w-4xl items-end gap-2 rounded-2xl border border-slate-200 bg-slate-50/80 p-2 shadow-sm focus-within:border-brand-sky/40 focus-within:ring-2 focus-within:ring-brand-sky/15 sm:rounded-3xl sm:p-2.5"
        onSubmit={(e) => {
          e.preventDefault()
          submit()
        }}
      >
        <label htmlFor="chat-input" className="sr-only">
          Tin nhắn tới chatbot
        </label>
        <textarea
          ref={taRef}
          id="chat-input"
          name="message"
          rows={1}
          value={value}
          disabled={disabled}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault()
              submit()
            }
          }}
          placeholder="Nhập tin nhắn…"
          className="field-sizing-content max-h-40 min-h-11 flex-1 resize-none bg-transparent px-3 py-2 text-[15px] leading-6 text-slate-800 placeholder:text-slate-400 focus:outline-none disabled:opacity-60"
        />
        <button
          type="submit"
          disabled={disabled || !value.trim()}
          className="mb-0.5 flex size-10 shrink-0 items-center justify-center rounded-xl bg-brand-ocean text-white shadow-md transition hover:bg-brand-teal disabled:pointer-events-none disabled:opacity-40 sm:size-11 sm:rounded-2xl"
          aria-label="Gửi"
        >
          <SendIcon />
        </button>
      </form>
      <p className="mx-auto mt-2 max-w-4xl text-center text-[11px] text-slate-400">
        Du lịch AI có thể sai sót. Kiểm tra thông tin quan trọng trước khi đặt chỗ.
      </p>
    </footer>
  )
}

function SendIcon() {
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="currentColor"
      aria-hidden
    >
      <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
    </svg>
  )
}
