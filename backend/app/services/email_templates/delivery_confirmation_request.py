from app.services.email_templates.base import ACCENT_COLOR, render_email_shell


def render_delivery_confirmation_request(reference: str, confirm_url: str) -> tuple[str, str]:
    subject = "Courrier+ — Veuillez confirmer la réception de votre courrier"
    body = f"""
      <p>Bonjour,</p>
      <p>Un courrier physique Courrier+ (référence <strong>{reference}</strong>) vient d'être déposé dans votre boîte aux lettres.</p>
      <p>Merci de confirmer que vous l'avez bien reçu en cliquant sur le bouton ci-dessous.</p>
      <p><a href="{confirm_url}" style="background-color:{ACCENT_COLOR};color:#ffffff;padding:10px 20px;border-radius:6px;text-decoration:none;display:inline-block;">Confirmer la réception</a></p>
      <p style="color:#6b7280;font-size:13px;">Si vous n'avez pas encore trouvé ce courrier, vérifiez à nouveau votre boîte aux lettres avant de confirmer.</p>
    """
    return subject, render_email_shell(subject, body)
