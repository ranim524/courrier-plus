import { createContext, useContext, useMemo, useState, type ReactNode } from "react"
import type { RecipientInfo, SenderInfo } from "../types/letter"
import type { PricingBreakdown } from "../types/pricing"

interface WizardState {
  sender: SenderInfo
  recipient: RecipientInfo
  subject: string
  message: string
  document: File | null
  acknowledgmentOfReceipt: boolean
  pricing: PricingBreakdown | null
  letterId: string | null
  transactionId: string | null
  reference: string | null
}

interface WizardContextValue extends WizardState {
  setSender: (sender: SenderInfo) => void
  setRecipient: (recipient: RecipientInfo) => void
  setLetterContent: (subject: string, message: string, document: File | null) => void
  setAcknowledgmentOfReceipt: (value: boolean) => void
  setPricing: (pricing: PricingBreakdown | null) => void
  setLetterCreated: (letterId: string) => void
  setTransactionId: (transactionId: string) => void
  setReference: (reference: string) => void
  reset: () => void
}

const emptySender: SenderInfo = { firstName: "", lastName: "", email: "", phone: "" }
const emptyRecipient: RecipientInfo = { firstName: "", lastName: "", email: "", phone: "" }

const WizardContext = createContext<WizardContextValue | null>(null)

export function SendLetterWizardProvider({ children }: { children: ReactNode }) {
  const [sender, setSender] = useState<SenderInfo>(emptySender)
  const [recipient, setRecipient] = useState<RecipientInfo>(emptyRecipient)
  const [subject, setSubject] = useState("")
  const [message, setMessage] = useState("")
  const [document, setDocument] = useState<File | null>(null)
  const [acknowledgmentOfReceipt, setAcknowledgmentOfReceiptState] = useState(false)
  const [pricing, setPricingState] = useState<PricingBreakdown | null>(null)
  const [letterId, setLetterId] = useState<string | null>(null)
  const [transactionId, setTransactionIdState] = useState<string | null>(null)
  const [reference, setReferenceState] = useState<string | null>(null)

  const value = useMemo<WizardContextValue>(
    () => ({
      sender,
      recipient,
      subject,
      message,
      document,
      acknowledgmentOfReceipt,
      pricing,
      letterId,
      transactionId,
      reference,
      setSender,
      setRecipient,
      setLetterContent: (s, m, d) => {
        setSubject(s)
        setMessage(m)
        setDocument(d)
      },
      setAcknowledgmentOfReceipt: (value) => setAcknowledgmentOfReceiptState(value),
      setPricing: (pricing) => setPricingState(pricing),
      setLetterCreated: (id) => setLetterId(id),
      setTransactionId: (id) => setTransactionIdState(id),
      setReference: (ref) => setReferenceState(ref),
      reset: () => {
        setSender(emptySender)
        setRecipient(emptyRecipient)
        setSubject("")
        setMessage("")
        setDocument(null)
        setAcknowledgmentOfReceiptState(false)
        setPricingState(null)
        setLetterId(null)
        setTransactionIdState(null)
        setReferenceState(null)
      },
    }),
    [
      sender,
      recipient,
      subject,
      message,
      document,
      acknowledgmentOfReceipt,
      pricing,
      letterId,
      transactionId,
      reference,
    ],
  )

  return <WizardContext.Provider value={value}>{children}</WizardContext.Provider>
}

export function useSendLetterWizard(): WizardContextValue {
  const ctx = useContext(WizardContext)
  if (!ctx) throw new Error("useSendLetterWizard must be used within SendLetterWizardProvider")
  return ctx
}
