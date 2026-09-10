import { Link } from "react-router-dom"

const STEPS = [
  {
    title: "1. Rédigez votre courrier",
    text: "Renseignez l'expéditeur et le destinataire, puis rédigez votre message ou joignez un PDF.",
  },
  {
    title: "2. Payez en ligne",
    text: "Réglez le tarif fixe de votre envoi de façon simple et sécurisée.",
  },
  {
    title: "3. Suivi en temps réel",
    text: "Votre destinataire reçoit un lien sécurisé par e-mail ; vous suivez chaque étape jusqu'à la confirmation de réception.",
  },
]

const BENEFITS = [
  { title: "Rapide", text: "Votre courrier part en quelques minutes, sans détour par la poste." },
  { title: "Traçable", text: "Chaque évènement clé est horodaté : envoi, ouverture, réception." },
  { title: "Sécurisé", text: "Liens d'accès uniques, documents intègres (empreinte SHA-256), aucune donnée superflue." },
  { title: "Sans compte", text: "Ni l'expéditeur ni le destinataire n'ont besoin de créer de compte." },
]

export function Home() {
  return (
    <div>
      <section className="bg-gradient-to-b from-brand-700 to-brand-600 text-white">
        <div className="mx-auto max-w-6xl px-4 py-20 sm:px-6 text-center">
          <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl">
            Le courrier recommandé numérique, réinventé pour la Tunisie
          </h1>
          <p className="mx-auto mt-5 max-w-2xl text-lg text-brand-100">
            Envoyez un document important à quelqu'un en quelques minutes, avec preuve d'envoi, de consultation et de
            réception — sans papier, sans file d'attente.
          </p>
          <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <Link
              to="/send/sender"
              className="rounded-lg bg-white px-6 py-3 text-sm font-semibold text-brand-700 hover:bg-brand-50"
            >
              Envoyer un courrier
            </Link>
            <Link
              to="/track"
              className="rounded-lg border border-white/40 px-6 py-3 text-sm font-semibold text-white hover:bg-white/10"
            >
              Suivre un courrier
            </Link>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 py-16 sm:px-6">
        <h2 className="text-center text-2xl font-bold text-slate-800">Comment ça marche</h2>
        <div className="mt-10 grid gap-8 sm:grid-cols-3">
          {STEPS.map((step) => (
            <div key={step.title} className="rounded-xl border border-slate-200 bg-white p-6">
              <h3 className="font-semibold text-brand-700">{step.title}</h3>
              <p className="mt-2 text-sm text-slate-600">{step.text}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="bg-white py-16">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <h2 className="text-center text-2xl font-bold text-slate-800">Pourquoi Courrier+</h2>
          <div className="mt-10 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {BENEFITS.map((b) => (
              <div key={b.title} className="rounded-xl bg-slate-50 p-5">
                <h3 className="font-semibold text-slate-800">{b.title}</h3>
                <p className="mt-1.5 text-sm text-slate-600">{b.text}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 py-16 sm:px-6">
        <div className="rounded-2xl bg-brand-50 px-8 py-10 text-center">
          <h2 className="text-2xl font-bold text-brand-800">Besoin d'aide ?</h2>
          <p className="mx-auto mt-2 max-w-xl text-sm text-brand-700">
            Pour toute question sur un envoi ou sur le fonctionnement de Courrier+, contactez-nous à{" "}
            <a href="mailto:support@courrierplus.tn" className="font-semibold underline">
              support@courrierplus.tn
            </a>
            .
          </p>
        </div>
      </section>
    </div>
  )
}
