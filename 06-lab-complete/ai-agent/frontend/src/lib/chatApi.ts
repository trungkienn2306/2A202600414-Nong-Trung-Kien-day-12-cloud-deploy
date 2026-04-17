const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.trim()
  ? (import.meta.env.VITE_API_BASE_URL as string).replace(/\/+$/, '')
  : '/api'

const AGENT_API_KEY = (import.meta.env.VITE_AGENT_API_KEY as string | undefined)?.trim() || 'trung-kien-agent'

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

async function debugRequestError(endpoint: string, error: unknown, response?: Response): Promise<void> {
  const errorDetails: any = {
    endpoint,
    apiBaseUrl: API_BASE_URL,
    browserOrigin: window.location.origin,
    error,
  }

  if (response) {
    errorDetails.status = response.status
    errorDetails.statusText = response.statusText
    // Try to get response body (could be Nginx HTML error page)
    try {
      const text = await response.clone().text()
      errorDetails.errorBodyPreview = text.slice(0, 500)
    } catch (e) {
      errorDetails.bodyError = 'Could not read response body'
    }
  }

  console.error('[PRO_DEBUG_REPORT]', errorDetails)
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
    await debugRequestError(endpoint, error, (error as any).response)
    throw error
  }
}

export async function postChat({
  message,
  threadId,
}: PostChatInput): Promise<PostChatResult> {
  const endpoint = `${API_BASE_URL}/chat`
  try {
    console.log('[chatApi] Sending POST request', {
      endpoint,
      key_prefix: AGENT_API_KEY ? AGENT_API_KEY.slice(0, 3) + '***' : 'MISSING',
      message_len: message.length
    })

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
        statusText: res.statusText,
        endpoint,
        key_used_prefix: AGENT_API_KEY ? AGENT_API_KEY.slice(0, 3) + '***' : 'MISSING',
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
    await debugRequestError(endpoint, error, (error as any).response)
    throw error
  }
}

