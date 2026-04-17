import { useCallback, useEffect, useState } from 'react'
import type { ChatMessage } from '../types/chat'
import {
  clearAllChatStorage,
  ensureSessionId,
  newSessionId,
  readAllMessages,
  writeAllMessages,
} from '../lib/chatStorage'
import { getHealth, postChat } from '../lib/chatApi'

function newMessage(role: ChatMessage['role'], content: string): ChatMessage {
  return {
    id: crypto.randomUUID(),
    role,
    content,
    createdAt: new Date().toISOString(),
  }
}

export function useTravelChat() {
  const [messages, setMessages] = useState<ChatMessage[]>(() => {
    ensureSessionId()
    return readAllMessages()
  })
  const [isTyping, setIsTyping] = useState(false)
  const [historyReady, setHistoryReady] = useState(false)
  const [threadId, setThreadId] = useState<string | null>(null)

  useEffect(() => {
    writeAllMessages(messages)
  }, [messages])

  useEffect(() => {
    let cancelled = false
    async function bootstrapHistory() {
      ensureSessionId()
      try {
        const health = await getHealth()
        if (health.core_agent === 'degraded') {
          if (!cancelled) {
            setMessages((prev) => {
              if (prev.length > 0) return prev
              return [
                newMessage(
                  'assistant',
                  `Core agent chưa sẵn sàng. Thiếu key: ${(health.missing_keys ?? []).join(', ')}`,
                ),
              ]
            })
          }
          return
        }
      } catch {
        if (!cancelled) {
          setMessages((prev) => {
            if (prev.length > 0) return prev
            return [
              newMessage(
                'assistant',
                'Không thể kết nối backend lúc này. Bạn kiểm tra API cổng 8000 trước khi tiếp tục.',
              ),
            ]
          })
        }
      } finally {
        if (!cancelled) setHistoryReady(true)
      }
    }

    void bootstrapHistory()
    return () => {
      cancelled = true
    }
  }, [])

  const clearChat = useCallback(() => {
    if (isTyping) return
    if (
      messages.length > 0 &&
      !window.confirm(
        'Xóa toàn bộ tin trên màn hình và bắt đầu đoạn chat mới? Dữ liệu demo trên máy bạn sẽ được xóa.',
      )
    ) {
      return
    }
    clearAllChatStorage()
    newSessionId()
    setMessages([])
    setThreadId(null)
  }, [isTyping, messages.length])

  const sendMessage = useCallback(
    async (text: string) => {
      const trimmed = text.trim()
      if (!trimmed || isTyping) return

      const userMsg = newMessage('user', trimmed)
      setMessages((prev) => [...prev, userMsg])
      setIsTyping(true)
      try {
        const result = await postChat({ message: trimmed, threadId })
        if (result.threadId) {
          setThreadId(result.threadId)
        }
        const replyText =
          result.status === 'need_input' ? (result.question ?? result.response) : result.response
        const botMsg = newMessage('assistant', replyText)
        setMessages((prev) => [...prev, botMsg])
      } catch (error) {
        console.error('[useTravelChat] sendMessage failed', {
          browserOrigin: window.location.origin,
          error,
        })
        const errorMsg = newMessage(
          'assistant',
          'Mình chưa thể xử lý vì backend chưa sẵn sàng. Vui lòng thử lại sau ít phút.',
        )
        setMessages((prev) => [...prev, errorMsg])
      } finally {
        setIsTyping(false)
      }
    },
    [isTyping, threadId],
  )

  return {
    messages,
    isTyping,
    historyReady,
    sendMessage,
    clearChat,
  }
}
