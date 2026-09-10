from app.services.email_templates.base import ACCENT_COLOR, render_email_shell


def render_payment_confirmation(
    sender_first_name: str,
    reference: str,
    recipient_full_name: str,
    amount: float,
    currency: str,
    tracking_url: str,
    sent_date: str,
) -> tuple[str, str]:
    subject = f"Courrier+ — Paiement confirmé ({reference})"
    body = f"""
      <p>Bonjour {sender_first_name},</p>
      <p>Votre paiement a été confirmé et votre courrier a été créé avec succès.</p>
      <table role="presentation" width="100%" style="margin:16px 0;font-size:14px;">
        <tr><td style="color:#6b7280;padding:4px 0;">Référence</td><td style="font-weight:bold;">{reference}</td></tr>
        <tr><td style="color:#6b7280;padding:4px 0;">Destinataire</td><td>{recipient_full_name}</td></tr>
        <tr><td style="color:#6b7280;padding:4px 0;">Date</td><td>{sent_date}</td></tr>
        <tr><td style="color:#6b7280;padding:4px 0;">Montant</td><td>{amount:.2f} {currency}</td></tr>
      </table>
      <p><a href="{tracking_url}" style="background-color:{ACCENT_COLOR};color:#ffffff;padding:10px 20px;border-radius:6px;text-decoration:none;display:inline-block;">Suivre mon courrier</a></p>
    """
    return subject, render_email_shell(subject, body)
