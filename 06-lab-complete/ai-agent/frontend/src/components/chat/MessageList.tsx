import { useEffect, useRef } from 'react'
import type { ChatMessage } from '../../types/chat'
import { MessageBubble } from './MessageBubble'
import { TypingIndicator } from './TypingIndicator'
import { ChatEmptyState } from './ChatEmptyState'

type Props = {
  messages: ChatMessage[]
  isTyping: boolean
  onPickSuggestion: (text: string) => void
}

export function MessageList({
  messages,
  isTyping,
  onPickSuggestion,
}: Props) {
  const endRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [messages, isTyping])

  const empty = messages.length === 0 && !isTyping

  return (
    <div
      className="flex min-h-0 flex-1 flex-col overflow-hidden bg-white"
      aria-label="Cuộc hội thoại"
    >
      {empty ? (
        <ChatEmptyState
          onPickSuggestion={onPickSuggestion}
          disabled={isTyping}
        />
      ) : (
        <div
          className="flex min-h-0 flex-1 flex-col overflow-y-auto overscroll-contain"
          role="log"
          aria-live="polite"
          aria-relevant="additions"
        >
          {messages.map((m) => (
            <MessageBubble key={m.id} message={m} />
          ))}
          {isTyping ? <TypingIndicator /> : null}
          <div ref={endRef} className="h-4 shrink-0" aria-hidden />
        </div>
      )}
    </div>
  )
}
