import type { ChatMessage } from '../types/chat'

/** Một key duy nhất cho toàn bộ tin (một cửa sổ chat). */
export const MESSAGES_STORAGE_KEY = 'travel_chat_messages'

/** UUID phiên — tạo mới mỗi lần “Đoạn chat mới” để sau này đồng bộ API. */
export const SESSION_STORAGE_KEY = 'travel_chat_session_id'

const LEGACY_CONVERSATIONS_KEY = 'travel_chat_conversations'
const LEGACY_ACTIVE_KEY = 'travel_chat_active_id'

function safeParseMessages(raw: string | null): ChatMessage[] {
  if (!raw) return []
  try {
    const data = JSON.parse(raw) as unknown
    if (!Array.isArray(data)) return []
    return data.filter(
      (m): m is ChatMessage =>
        typeof m === 'object' &&
        m !== null &&
        'id' in m &&
        'role' in m &&
        'content' in m &&
        'createdAt' in m &&
        (m.role === 'user' || m.role === 'assistant'),
    )
  } catch {
    return []
  }
}

function legacyMessagesKey(sessionId: string): string {
  return `travel_chat_messages:${sessionId}`
}

/** Đọc tin; nếu chưa có key mới thì migrate từ bản đa hội thoại / session cũ. */
export function readAllMessages(): ChatMessage[] {
  try {
    const direct = localStorage.getItem(MESSAGES_STORAGE_KEY)
    if (direct) {
      return safeParseMessages(direct)
    }

    const active = localStorage.getItem(LEGACY_ACTIVE_KEY)
    if (active) {
      const msgs = safeParseMessages(localStorage.getItem(legacyMessagesKey(active)))
      if (msgs.length > 0) {
        writeAllMessages(msgs)
        cleanupLegacyStorage()
        return msgs
      }
    }

    const sid = localStorage.getItem(SESSION_STORAGE_KEY)
    if (sid) {
      const msgs = safeParseMessages(localStorage.getItem(legacyMessagesKey(sid)))
      if (msgs.length > 0) {
        writeAllMessages(msgs)
        cleanupLegacyStorage()
        return msgs
      }
    }

    cleanupLegacyStorage()
    return []
  } catch {
    return []
  }
}

export function writeAllMessages(messages: ChatMessage[]): void {
  try {
    localStorage.setItem(MESSAGES_STORAGE_KEY, JSON.stringify(messages))
  } catch {
    /* ignore */
  }
}

export function clearAllChatStorage(): void {
  try {
    localStorage.removeItem(MESSAGES_STORAGE_KEY)
    cleanupLegacyStorage()
  } catch {
    /* ignore */
  }
}

function cleanupLegacyStorage(): void {
  try {
    localStorage.removeItem(LEGACY_CONVERSATIONS_KEY)
    localStorage.removeItem(LEGACY_ACTIVE_KEY)
    const sid = localStorage.getItem(SESSION_STORAGE_KEY)
    if (sid) {
      localStorage.removeItem(legacyMessagesKey(sid))
    }
    for (let i = localStorage.length - 1; i >= 0; i--) {
      const k = localStorage.key(i)
      if (k?.startsWith('travel_chat_messages:')) {
        localStorage.removeItem(k)
      }
    }
  } catch {
    /* ignore */
  }
}

export function readSessionId(): string | null {
  try {
    return localStorage.getItem(SESSION_STORAGE_KEY)
  } catch {
    return null
  }
}

export function writeSessionId(id: string): void {
  try {
    localStorage.setItem(SESSION_STORAGE_KEY, id)
  } catch {
    /* ignore */
  }
}

export function ensureSessionId(): string {
  const existing = readSessionId()
  if (existing) return existing
  const id = crypto.randomUUID()
  writeSessionId(id)
  return id
}

export function newSessionId(): string {
  const id = crypto.randomUUID()
  writeSessionId(id)
  return id
}
