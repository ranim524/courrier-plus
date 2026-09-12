import { Link } from "react-router-dom"

const STEPS = [
  {
    number: "1",
    title: "Rédigez votre courrier",
    text: "Sans créer de compte, renseignez l'expéditeur et le destinataire, puis rédigez votre message ou joignez un document PDF.",
  },
  {
    number: "2",
    title: "Le tarif est calculé automatiquement",
    text: "Selon le nombre de pages, le mode d'impression et l'option d'accusé de réception, Courrier+ calcule le prix exact avant tout engagement.",
  },
  {
    number: "3",
    title: "Vous payez en ligne",
    text: "Le paiement est réglé en toute sécurité. Une fois confirmé, une référence de suivi unique est générée pour votre courrier.",
  },
  {
    number: "4",
    title: "Courrier+ imprime et livre physiquement",
    text: "Votre document est imprimé puis remis à un agent de livraison qui l'achemine physiquement jusqu'au destinataire, sans qu'il ait besoin de créer de compte.",
  },
  {
    number: "5",
    title: "Vous suivez chaque étape",
    text: "Grâce à votre référence unique, vous suivez publiquement l'avancement — payé, envoyé, livré — et recevez une confirmation dès la réception si vous avez choisi l'accusé de réception.",
  },
]

const CONCEPT_POINTS = [
  {
    title: "Le problème",
    text: "Envoyer un courrier recommandé en Tunisie signifie encore, aujourd'hui, se déplacer à la poste, faire la queue et gérer un reçu papier facile à perdre. Pour un document important — mise en demeure, résiliation, notification officielle — cette friction ralentit des démarches qui devraient être simples.",
  },
  {
    title: "La solution Courrier+",
    text: "Courrier+ combine le meilleur des deux mondes : la simplicité d'un envoi en ligne et la valeur d'une remise physique traçable. Vous rédigez et payez depuis votre navigateur ; nous imprimons et livrons le courrier chez le destinataire, avec une preuve de dépôt et un suivi à chaque étape.",
  },
]

const SENDER_JOURNEY = [
  "Renseigner ses informations et celles du destinataire",
  "Rédiger un message ou joindre un document PDF",
  "Choisir l'option d'accusé de réception si besoin",
  "Payer en ligne et recevoir une référence unique",
  "Suivre l'avancement jusqu'à la livraison",
]

const RECIPIENT_JOURNEY = [
  "Reçoit le courrier physiquement à son adresse, sans démarche préalable",
  "N'a besoin d'aucun compte ni d'aucune application pour le recevoir",
  "Peut, si un accusé de réception a été demandé, confirmer la bonne réception via un lien dédié",
]

const RELIABILITY_POINTS = [
  {
    title: "Référence unique et vérifiable",
    text: "Chaque courrier reçoit une référence unique, générée après paiement, qui permet de le suivre publiquement du dépôt à la livraison.",
  },
  {
    title: "Suivi public et transparent",
    text: "L'état du courrier (payé, envoyé, livré, reçu) est consultable à tout moment avec la référence, sans compte à créer.",
  },
  {
    title: "Livraison physique et traçable",
    text: "Le courrier est réellement imprimé et remis à un agent de livraison, avec un historique horodaté de chaque étape jusqu'à la remise.",
  },
  {
    title: "Confirmation de réception",
    text: "Pour les courriers avec accusé de réception, une confirmation est enregistrée et communiquée à l'expéditeur une fois le courrier reçu.",
  },
  {
    title: "Intégrité des documents",
    text: "Les documents envoyés sont protégés par une empreinte SHA-256, garantissant qu'ils ne sont pas altérés entre l'envoi et l'impression.",
  },
]

export function HowItWorks() {
  return (
    <div>
      <section className="bg-gradient-to-b from-brand-700 to-brand-600 text-white">
        <div className="mx-auto max-w-6xl px-4 py-20 sm:px-6 text-center">
          <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl">Comment fonctionne Courrier+</h1>
          <p className="mx-auto mt-5 max-w-2xl text-lg text-brand-100">
            Du clic d'envoi à la remise physique entre les mains du destinataire, découvrez chaque étape du
            fonctionnement de Courrier+, en toute transparence.
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
        <h2 className="text-center text-2xl font-bold text-slate-800">Le concept</h2>
        <div className="mt-10 grid gap-6 sm:grid-cols-2">
          {CONCEPT_POINTS.map((point) => (
            <div key={point.title} className="rounded-xl border border-slate-200 bg-white p-6">
              <h3 className="font-semibold text-brand-700">{point.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-slate-600">{point.text}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="bg-white py-16">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <h2 className="text-center text-2xl font-bold text-slate-800">Comment ça marche en 5 étapes</h2>
          <div className="mt-10 grid gap-6 sm:grid-cols-2 lg:grid-cols-5">
            {STEPS.map((step) => (
              <div key={step.number} className="rounded-xl bg-slate-50 p-5">
                <div className="flex h-9 w-9 items-center justify-center rounded-full bg-brand-600 text-sm font-bold text-white">
                  {step.number}
                </div>
                <h3 className="mt-3 font-semibold text-slate-800">{step.title}</h3>
                <p className="mt-1.5 text-sm leading-relaxed text-slate-600">{step.text}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 py-16 sm:px-6">
        <h2 className="text-center text-2xl font-bold text-slate-800">Fonctionnement de la plateforme</h2>
        <div className="mt-10 grid gap-8 lg:grid-cols-2">
          <div className="rounded-xl border border-slate-200 bg-white p-6">
            <h3 className="font-semibold text-brand-700">Le parcours de l'expéditeur</h3>
            <ol className="mt-4 space-y-3">
              {SENDER_JOURNEY.map((item, index) => (
                <li key={item} className="flex gap-3 text-sm text-slate-600">
                  <span className="flex h-6 w-6 flex-none items-center justify-center rounded-full bg-brand-50 text-xs font-bold text-brand-600">
                    {index + 1}
                  </span>
                  <span className="leading-relaxed">{item}</span>
                </li>
              ))}
            </ol>
          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-6">
            <h3 className="font-semibold text-brand-700">Le parcours du destinataire</h3>
            <ol className="mt-4 space-y-3">
              {RECIPIENT_JOURNEY.map((item, index) => (
                <li key={item} className="flex gap-3 text-sm text-slate-600">
                  <span className="flex h-6 w-6 flex-none items-center justify-center rounded-full bg-brand-50 text-xs font-bold text-brand-600">
                    {index + 1}
                  </span>
                  <span className="leading-relaxed">{item}</span>
                </li>
              ))}
            </ol>
          </div>
        </div>

        <div className="mt-8 rounded-xl border border-slate-200 bg-white p-6">
          <h3 className="font-semibold text-brand-700">Paiement, référence unique et livraison physique</h3>
          <p className="mt-2 text-sm leading-relaxed text-slate-600">
            Le paiement en ligne déclenche la génération d'une référence unique pour votre courrier : c'est elle qui
            permet, ensuite, de le suivre publiquement à tout moment. Une fois le paiement confirmé, Courrier+
            imprime le document et le fait livrer physiquement à l'adresse du destinataire par un agent de livraison,
            sans que celui-ci n'ait besoin de créer de compte ni d'installer quoi que ce soit.
          </p>
        </div>
      </section>

      <section className="bg-white py-16">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <h2 className="text-center text-2xl font-bold text-slate-800">Pourquoi c'est fiable</h2>
          <div className="mt-10 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {RELIABILITY_POINTS.map((point) => (
              <div key={point.title} className="rounded-xl bg-slate-50 p-5">
                <h3 className="font-semibold text-slate-800">{point.title}</h3>
                <p className="mt-1.5 text-sm leading-relaxed text-slate-600">{point.text}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 py-16 sm:px-6">
        <div className="rounded-2xl bg-brand-50 px-8 py-10 text-center">
          <h2 className="text-2xl font-bold text-brand-800">Prêt à envoyer votre premier courrier ?</h2>
          <p className="mx-auto mt-2 max-w-xl text-sm text-brand-700">
            Aucun compte requis, aucun déplacement à prévoir. Rédigez votre courrier maintenant, Courrier+ s'occupe
            du reste.
          </p>
          <div className="mt-6 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <Link
              to="/send/sender"
              className="rounded-lg bg-brand-600 px-6 py-3 text-sm font-semibold text-white hover:bg-brand-700"
            >
              Envoyer un courrier
            </Link>
            <Link to="/track" className="text-sm font-semibold text-brand-700 hover:underline">
              Suivre un courrier existant
            </Link>
          </div>
        </div>
      </section>
    </div>
  )
}
