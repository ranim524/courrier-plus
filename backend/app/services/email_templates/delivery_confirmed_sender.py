from app.services.email_templates.base import ACCENT_COLOR, render_email_shell


def render_delivery_confirmed_sender(
    sender_first_name: str,
    reference: str,
    tracking_number: str,
    delivered_date: str,
    delivered_time: str,
    tracking_url: str,
) -> tuple[str, str]:
    subject = "Courrier+ — Votre courrier a été livré"
    body = f"""
      <p>Bonjour {sender_first_name},</p>
      <p>Votre courrier physique Courrier+ a été livré au destinataire.</p>
      <table role="presentation" width="100%" style="margin:16px 0;font-size:14px;">
        <tr><td style="color:#6b7280;padding:4px 0;">Référence</td><td style="font-weight:bold;">{reference}</td></tr>
        <tr><td style="color:#6b7280;padding:4px 0;">Numéro de suivi</td><td>{tracking_number}</td></tr>
        <tr><td style="color:#6b7280;padding:4px 0;">Date de livraison</td><td>{delivered_date}</td></tr>
        <tr><td style="color:#6b7280;padding:4px 0;">Heure</td><td>{delivered_time}</td></tr>
        <tr><td style="color:#6b7280;padding:4px 0;">Statut</td><td>Livré</td></tr>
      </table>
      <p><a href="{tracking_url}" style="background-color:{ACCENT_COLOR};color:#ffffff;padding:10px 20px;border-radius:6px;text-decoration:none;display:inline-block;">Voir le suivi</a></p>
    """
    return subject, render_email_shell(subject, body)
