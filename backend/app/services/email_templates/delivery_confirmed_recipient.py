from app.services.email_templates.base import render_email_shell


def render_delivery_confirmed_recipient(
    reference: str, tracking_number: str, delivered_date: str, delivered_time: str
) -> tuple[str, str]:
    subject = "Courrier+ — Votre courrier a été livré"
    body = f"""
      <p>Bonjour,</p>
      <p>Nous vous informons que votre courrier physique Courrier+ a été livré.</p>
      <table role="presentation" width="100%" style="margin:16px 0;font-size:14px;">
        <tr><td style="color:#6b7280;padding:4px 0;">Référence</td><td style="font-weight:bold;">{reference}</td></tr>
        <tr><td style="color:#6b7280;padding:4px 0;">Numéro de suivi</td><td>{tracking_number}</td></tr>
        <tr><td style="color:#6b7280;padding:4px 0;">Date de livraison</td><td>{delivered_date}</td></tr>
        <tr><td style="color:#6b7280;padding:4px 0;">Heure</td><td>{delivered_time}</td></tr>
      </table>
      <p>Cordialement,<br>Courrier+</p>
    """
    return subject, render_email_shell(subject, body)
