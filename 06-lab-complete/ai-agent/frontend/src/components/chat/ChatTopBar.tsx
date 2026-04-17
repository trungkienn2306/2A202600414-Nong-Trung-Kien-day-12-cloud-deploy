type Props = {
  title: string
  onOpenSidebar: () => void
  showMenuButton?: boolean
}

export function ChatTopBar({
  title,
  onOpenSidebar,
  showMenuButton = true,
}: Props) {
  return (
    <header className="flex h-12 shrink-0 items-center gap-3 border-b border-slate-200/90 bg-white px-3 lg:hidden">
      {showMenuButton ? (
        <button
          type="button"
          aria-label="Mở menu"
          onClick={onOpenSidebar}
          className="flex size-9 items-center justify-center rounded-lg text-slate-600 hover:bg-slate-100"
        >
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
        </button>
      ) : null}
      <h1 className="min-w-0 flex-1 truncate text-sm font-semibold text-slate-800">
        {title}
      </h1>
    </header>
  )
}
