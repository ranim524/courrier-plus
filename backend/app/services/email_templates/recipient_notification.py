from app.services.email_templates.base import ACCENT_COLOR, render_email_shell


def render_recipient_notification(
    sender_full_name: str,
    subject_line: str,
    access_url: str,
    expiration_info: str,
) -> tuple[str, str]:
    subject = "Courrier+ — Vous avez reçu un courrier recommandé numérique"
    body = f"""
      <p>Bonjour,</p>
      <p><strong>{sender_full_name}</strong> vous a envoyé un courrier recommandé numérique via Courrier+.</p>
      <p><strong>Objet :</strong> {subject_line}</p>
      <p><a href="{access_url}" style="background-color:{ACCENT_COLOR};color:#ffffff;padding:10px 20px;border-radius:6px;text-decoration:none;display:inline-block;">Consulter mon courrier</a></p>
      <p style="color:#6b7280;font-size:13px;">{expiration_info}</p>
      <p style="color:#6b7280;font-size:13px;">Ce lien est personnel et sécurisé. Ne le transférez pas.</p>
    """
    return subject, render_email_shell(subject, body)
