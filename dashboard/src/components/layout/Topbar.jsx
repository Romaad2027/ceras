export const Topbar = ({ organizationName = 'Current Organization', onLogout }) => {
  return (
    <header className="sticky top-0 z-30 h-16 bg-surface-variant backdrop-blur-md border-b border-outline-variant flex items-center justify-between px-5 md:px-6">
      <div className="flex items-center gap-3">
        <span className="inline-flex items-center rounded-md bg-primary-container px-2 py-1 text-sm text-primary-container-foreground">
          {organizationName}
        </span>
      </div>
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={onLogout}
          className="inline-flex items-center rounded-md px-3 py-1.5 text-sm text-surface-foreground hover:bg-secondary-container"
        >
          Logout
        </button>
      </div>
    </header>
  )
}


