import { Link, NavLink, Outlet, useNavigate } from "react-router-dom"
import { useAuth } from "../hooks/useAuth"

const NAV_ITEMS = [
  { to: "/admin", label: "Tableau de bord", end: true },
  { to: "/admin/letters", label: "Courriers" },
  { to: "/admin/deliveries", label: "Livraisons" },
  { to: "/admin/delivery-agents", label: "Livreurs" },
  { to: "/admin/payments", label: "Paiements" },
  { to: "/admin/events", label: "E-mails & évènements" },
]

export function AdminLayout() {
  const { logout } = useAuth()
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate("/admin/login")
  }

  return (
    <div className="flex min-h-screen bg-slate-50">
      <aside className="w-64 shrink-0 border-r border-slate-200 bg-white">
        <div className="border-b border-slate-200 px-6 py-5">
          <Link to="/admin" className="text-lg font-extrabold text-brand-700">
            Courrier<span className="text-accent-500">+</span> <span className="text-sm font-medium text-slate-400">Admin</span>
          </Link>
        </div>
        <nav className="flex flex-col gap-1 p-3">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                `rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                  isActive ? "bg-brand-600 text-white" : "text-slate-600 hover:bg-slate-100"
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="p-3">
          <button
            onClick={handleLogout}
            className="w-full rounded-lg px-3 py-2 text-left text-sm font-medium text-danger-500 hover:bg-danger-500/10"
          >
            Déconnexion
          </button>
        </div>
      </aside>

      <main className="flex-1 p-6 sm:p-8">
        <Outlet />
      </main>
    </div>
  )
}
