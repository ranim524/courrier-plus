import { Link, Outlet } from "react-router-dom"

export function PublicLayout() {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4 sm:px-6">
          <Link to="/" className="flex items-center gap-2 text-xl font-extrabold text-brand-700">
            Courrier<span className="text-accent-500">+</span>
          </Link>
          <nav className="flex items-center gap-4 text-sm font-medium text-slate-600">
            <Link to="/send/sender" className="hover:text-brand-700">
              Envoyer un courrier
            </Link>
            <Link to="/track" className="hover:text-brand-700">
              Suivre un courrier
            </Link>
          </nav>
        </div>
      </header>

      <main className="flex-1 bg-slate-50">
        <Outlet />
      </main>

      <footer className="border-t border-slate-200 bg-white py-8 text-sm text-slate-500">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <p className="font-semibold text-slate-700">Courrier+</p>
          <p className="mt-1 max-w-2xl">
            Courrier+ est un prototype technique de courrier recommandé numérique pour la Tunisie. Il ne constitue
            pas, en l'état, un service de courrier recommandé certifié au sens de la réglementation postale ou des
            services de confiance électronique.
          </p>
          <p className="mt-3 text-xs text-slate-400">© {new Date().getFullYear()} Courrier+</p>
        </div>
      </footer>
    </div>
  )
}
