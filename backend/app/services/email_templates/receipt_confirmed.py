from app.services.email_templates.base import render_email_shell


def render_receipt_confirmed(sender_first_name: str, reference: str, confirmed_at: str) -> tuple[str, str]:
    subject = f"Courrier+ — Réception confirmée pour {reference}"
    body = f"""
      <p>Bonjour {sender_first_name},</p>
      <p>Votre destinataire a confirmé la réception de votre courrier <strong>{reference}</strong> le {confirmed_at}.</p>
      <p>Ce courrier est maintenant marqué comme reçu dans votre suivi Courrier+.</p>
    """
    return subject, render_email_shell(subject, body)
