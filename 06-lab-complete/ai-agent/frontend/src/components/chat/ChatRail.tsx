import { PlaneIcon } from '../icons/PlaneIcon'

type Props = {
  open: boolean
  collapsed: boolean
  onToggle: () => void
  onCollapse: () => void
  onClearChat: () => void
  disableActions?: boolean
  hasMessages: boolean
}

export function ChatRail({
  open,
  collapsed,
  onToggle,
  onCollapse,
  onClearChat,
  disableActions,
  hasMessages,
}: Props) {
  return (
    <>
      {open ? (
        <button
          type="button"
          aria-label="Đóng menu"
          className="fixed inset-0 z-40 bg-black/40 lg:hidden"
          onClick={onToggle}
        />
      ) : null}

      <aside
        className={[
          'fixed inset-y-0 left-0 z-50 flex flex-col border-r border-slate-700/80 bg-slate-900 text-slate-100 transition-[width,transform] duration-200 ease-out lg:static lg:z-0',
          'w-[min(100vw,280px)]',
          collapsed ? 'lg:w-[52px]' : 'lg:w-[260px]',
          open ? 'translate-x-0' : '-translate-x-full lg:translate-x-0',
        ].join(' ')}
      >
        <div
          className={[
            'flex shrink-0 items-center gap-2 border-b border-slate-700/80 px-2 pt-[max(0px,env(safe-area-inset-top))]',
            collapsed
              ? 'h-12 lg:h-auto lg:flex-col lg:items-center lg:gap-2 lg:py-3'
              : 'h-12 lg:h-14',
          ].join(' ')}
        >
          <button
            type="button"
            aria-label={open ? 'Đóng sidebar' : 'Mở sidebar'}
            onClick={() => {
              if (typeof window !== 'undefined' && window.innerWidth < 1024) {
                onToggle()
              } else {
                onCollapse()
              }
            }}
            className="flex size-9 shrink-0 items-center justify-center rounded-lg text-slate-300 hover:bg-slate-800 hover:text-white"
          >
            <MenuIcon />
          </button>
          <span
            className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-linear-to-br from-brand-sky to-brand-teal text-white shadow-md ring-1 ring-white/15"
            aria-hidden
          >
            <PlaneIcon className="size-[18px]" />
          </span>
          {!collapsed ? (
            <span className="min-w-0 flex-1 truncate text-sm font-semibold tracking-tight text-white">
              Du lịch AI
            </span>
          ) : null}
        </div>

        <div
          className={`flex flex-1 flex-col gap-2 overflow-hidden p-2 ${collapsed ? 'lg:items-center lg:px-1' : ''}`}
        >
          <button
            type="button"
            disabled={disableActions}
            onClick={() => {
              onClearChat()
              if (typeof window !== 'undefined' && window.innerWidth < 1024) {
                onToggle()
              }
            }}
            className={[
              'flex w-full items-center gap-2 rounded-lg border border-slate-600/80 bg-slate-800/80 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50',
              collapsed
                ? 'justify-center px-0 py-2.5 lg:size-10 lg:py-0'
                : 'px-3 py-2.5 text-left lg:py-2',
            ].join(' ')}
            title="Đoạn chat mới"
          >
            <span className="text-lg leading-none" aria-hidden>
              +
            </span>
            {!collapsed ? <span>Đoạn chat mới</span> : null}
          </button>

          {!collapsed ? (
            <p className="text-[11px] leading-relaxed text-slate-500">
              Một cửa sổ chat duy nhất. Nút trên xóa tin trên màn hình và bắt đầu
              lại
              {hasMessages ? ' (có xác nhận).' : '.'}
            </p>
          ) : null}
        </div>

        {!collapsed ? (
          <p className="border-t border-slate-700/80 px-3 py-2 text-[10px] leading-snug text-slate-500">
            Demo — dữ liệu chỉ lưu trên trình duyệt.
          </p>
        ) : null}
      </aside>
    </>
  )
}

function MenuIcon() {
  return (
    <svg
      width="20"
      height="20"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      aria-hidden
    >
      <path d="M4 6h16M4 12h16M4 18h16" />
    </svg>
  )
}
