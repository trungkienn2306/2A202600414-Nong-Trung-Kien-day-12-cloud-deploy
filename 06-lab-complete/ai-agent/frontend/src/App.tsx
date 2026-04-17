import { useCallback, useState } from 'react'
import { ChatComposer } from './components/chat/ChatComposer'
import { ChatRail } from './components/chat/ChatRail'
import { ChatTopBar } from './components/chat/ChatTopBar'
import { MessageList } from './components/chat/MessageList'
import { useTravelChat } from './hooks/useTravelChat'

const APP_TITLE = 'Du lịch AI'

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)

  const { messages, isTyping, sendMessage, clearChat } = useTravelChat()

  const onPickSuggestion = useCallback(
    (text: string) => {
      void sendMessage(text)
    },
    [sendMessage],
  )

  return (
    <div className="flex h-dvh max-h-dvh flex-col overflow-hidden bg-slate-100 font-sans text-slate-800">
      <div className="flex min-h-0 flex-1">
        <ChatRail
          open={sidebarOpen}
          collapsed={sidebarCollapsed}
          onToggle={() => setSidebarOpen((o) => !o)}
          onCollapse={() => setSidebarCollapsed((c) => !c)}
          onClearChat={clearChat}
          disableActions={isTyping}
          hasMessages={messages.length > 0}
        />

        <div className="flex min-w-0 flex-1 flex-col bg-white">
          <ChatTopBar title={APP_TITLE} onOpenSidebar={() => setSidebarOpen(true)} />

          <div className="hidden border-b border-slate-200/90 bg-white px-4 py-2 lg:block">
            <div className="mx-auto flex max-w-4xl items-center justify-between gap-3">
              <h1 className="truncate text-sm font-semibold text-slate-800">
                {APP_TITLE}
              </h1>
              <span className="shrink-0 rounded-md bg-amber-100 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-amber-900/90">
                Demo
              </span>
            </div>
          </div>

          <MessageList
            messages={messages}
            isTyping={isTyping}
            onPickSuggestion={onPickSuggestion}
          />
          <ChatComposer onSend={sendMessage} disabled={isTyping} />
        </div>
      </div>
    </div>
  )
}

export default App
