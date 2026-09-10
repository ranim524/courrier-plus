export const SEND_STEPS = ["Expéditeur", "Destinataire", "Courrier", "Vérification", "Paiement"]

export const STEP_NUMBERS = {
  sender: 1,
  recipient: 2,
  document: 3,
  review: 4,
  payment: 5,
} as const
