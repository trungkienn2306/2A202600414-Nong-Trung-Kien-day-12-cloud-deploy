import type { ChatMessage } from '../../types/chat'

function formatTime(iso: string): string {
  try {
    return new Intl.DateTimeFormat('vi-VN', {
      hour: '2-digit',
      minute: '2-digit',
    }).format(new Date(iso))
  } catch {
    return ''
  }
}

export function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === 'user'

  if (isUser) {
    return (
      <article className="border-b border-slate-100/90 bg-slate-50/90">
        <div className="mx-auto flex max-w-4xl justify-end px-4 py-4 sm:px-6 lg:px-8 lg:py-5">
          <div className="max-w-[min(100%,42rem)]">
            <div className="rounded-[22px] bg-[#2f2f2f] px-5 py-3.5 text-[15px] leading-7 text-white shadow-sm sm:px-6 sm:py-4">
              <p className="whitespace-pre-wrap wrap-break-word">{message.content}</p>
            </div>
          </div>
        </div>
      </article>
    )
  }

  return (
    <article className="border-b border-slate-100/90 bg-white">
      <div className="mx-auto flex max-w-4xl gap-4 px-4 py-6 sm:px-6 lg:px-8 lg:py-7">
        <div
          className="flex size-8 shrink-0 items-center justify-center rounded-md text-sm sm:size-9"
          aria-hidden
        >
          <span className="flex size-8 items-center justify-center rounded-md bg-linear-to-br from-brand-sky to-brand-teal text-sm text-white shadow-sm sm:size-9">
            ✈
          </span>
        </div>
        <div className="min-w-0 flex-1 pt-0.5">
          <div className="mb-1 flex items-center gap-2">
            <span className="text-sm font-semibold text-slate-800">
              Du lịch AI
            </span>
            <time
              className="text-xs text-slate-400"
              dateTime={message.createdAt}
            >
              {formatTime(message.createdAt)}
            </time>
          </div>
          <div className="text-[15px] leading-7 text-slate-700">
            <p className="whitespace-pre-wrap wrap-break-word">{message.content}</p>
          </div>
        </div>
      </div>
    </article>
  )
}
