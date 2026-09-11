import { Navigate, Route, Routes } from "react-router-dom"
import { ProtectedRoute } from "./components/ProtectedRoute"
import { AuthProvider } from "./hooks/useAuth"
import { SendLetterWizardProvider } from "./hooks/useSendLetterWizard"
import { AdminLayout } from "./layouts/AdminLayout"
import { PublicLayout } from "./layouts/PublicLayout"
import { Access } from "./pages/Access"
import { Home } from "./pages/Home"
import { TrackResult } from "./pages/TrackResult"
import { TrackSearch } from "./pages/TrackSearch"
import { AdminDashboard } from "./pages/admin/AdminDashboard"
import { AdminDeliveries } from "./pages/admin/AdminDeliveries"
import { AdminDeliveryAgents } from "./pages/admin/AdminDeliveryAgents"
import { AdminDeliveryDetail } from "./pages/admin/AdminDeliveryDetail"
import { AdminEvents } from "./pages/admin/AdminEvents"
import { AdminLetterDetail } from "./pages/admin/AdminLetterDetail"
import { AdminLetters } from "./pages/admin/AdminLetters"
import { AdminLogin } from "./pages/admin/AdminLogin"
import { AdminPayments } from "./pages/admin/AdminPayments"
import { DocumentStep } from "./pages/send/DocumentStep"
import { PaymentStep } from "./pages/send/PaymentStep"
import { RecipientStep } from "./pages/send/RecipientStep"
import { ReviewStep } from "./pages/send/ReviewStep"
import { SenderStep } from "./pages/send/SenderStep"
import { SuccessStep } from "./pages/send/SuccessStep"

export default function App() {
  return (
    <AuthProvider>
      <SendLetterWizardProvider>
        <Routes>
          <Route element={<PublicLayout />}>
            <Route path="/" element={<Home />} />
            <Route path="/send" element={<Navigate to="/send/sender" replace />} />
            <Route path="/send/sender" element={<SenderStep />} />
            <Route path="/send/recipient" element={<RecipientStep />} />
            <Route path="/send/document" element={<DocumentStep />} />
            <Route path="/send/review" element={<ReviewStep />} />
            <Route path="/send/payment" element={<PaymentStep />} />
            <Route path="/send/success" element={<SuccessStep />} />
            <Route path="/track" element={<TrackSearch />} />
            <Route path="/track/:reference" element={<TrackResult />} />
            <Route path="/access/:token" element={<Access />} />
          </Route>

          <Route path="/admin/login" element={<AdminLogin />} />
          <Route
            path="/admin"
            element={
              <ProtectedRoute>
                <AdminLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<AdminDashboard />} />
            <Route path="letters" element={<AdminLetters />} />
            <Route path="letters/:id" element={<AdminLetterDetail />} />
            <Route path="deliveries" element={<AdminDeliveries />} />
            <Route path="deliveries/:id" element={<AdminDeliveryDetail />} />
            <Route path="delivery-agents" element={<AdminDeliveryAgents />} />
            <Route path="payments" element={<AdminPayments />} />
            <Route path="events" element={<AdminEvents />} />
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </SendLetterWizardProvider>
    </AuthProvider>
  )
}
