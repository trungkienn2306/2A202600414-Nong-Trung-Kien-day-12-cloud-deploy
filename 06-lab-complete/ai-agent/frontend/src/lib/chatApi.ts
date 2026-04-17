const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.trim()
  ? (import.meta.env.VITE_API_BASE_URL as string).replace(/\/+$/, '')
  : 'http://localhost:8000'

const AGENT_API_KEY = (import.meta.env.VITE_AGENT_API_KEY as string | undefined)?.trim() || 'dev-key-12345'

interface PostChatInput {
  message: string
  threadId: string | null
}

interface ChatResponseDTO {
  response: string
  status?: 'success' | 'need_input' | 'error'
  question?: string | null
  thread_id?: string | null
}

interface HealthResponseDTO {
  status: string
  core_agent?: 'ready' | 'degraded'
  missing_keys?: string[]
}

function debugRequestError(endpoint: string, error: unknown): void {
  console.error('[chatApi] Request failed', {
    endpoint,
    apiBaseUrl: API_BASE_URL,
    browserOrigin: window.location.origin,
    error,
  })
}

async function safeJson(res: Response): Promise<unknown> {
  try {
    return await res.json()
  } catch {
    return null
  }
}

export interface PostChatResult {
  response: string
  status: 'success' | 'need_input' | 'error'
  question: string | null
  threadId: string | null
}

export async function getHealth(): Promise<HealthResponseDTO> {
  const endpoint = `${API_BASE_URL}/health`
  try {
    const res = await fetch(endpoint, {
      headers: {
        'X-API-Key': AGENT_API_KEY
      }
    })
    const body = (await safeJson(res)) as HealthResponseDTO | null
    if (!res.ok || !body) {
      console.error('[chatApi] Invalid health response', {
        status: res.status,
        endpoint,
        browserOrigin: window.location.origin,
      })
      throw new Error('Không thể kiểm tra trạng thái backend.')
    }
    return body
  } catch (error) {
    debugRequestError(endpoint, error)
    throw error
  }
}

export async function postChat({
  message,
  threadId,
}: PostChatInput): Promise<PostChatResult> {
  const endpoint = `${API_BASE_URL}/chat`
  try {
    const res = await fetch(endpoint, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'X-API-Key': AGENT_API_KEY 
      },
      body: JSON.stringify({
        message,
        thread_id: threadId,
      }),
    })
    const body = (await safeJson(res)) as ChatResponseDTO | null
    if (!res.ok || !body) {
      console.error('[chatApi] Invalid chat response', {
        status: res.status,
        endpoint,
        browserOrigin: window.location.origin,
      })
      throw new Error('Không thể gửi tin tới backend.')
    }
    if (body.status === 'error') {
      console.error('[chatApi] Backend returned error status', {
        endpoint,
        browserOrigin: window.location.origin,
        response: body,
      })
    }
    return {
      response: body.response ?? '',
      status: body.status ?? 'success',
      question: body.question ?? null,
      threadId: body.thread_id ?? null,
    }
  } catch (error) {
    debugRequestError(endpoint, error)
    throw error
  }
}

