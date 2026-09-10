from app.services.email_templates.base import render_email_shell


def render_letter_opened(sender_first_name: str, reference: str, opened_at: str) -> tuple[str, str]:
    subject = f"Courrier+ — Votre courrier {reference} a été consulté"
    body = f"""
      <p>Bonjour {sender_first_name},</p>
      <p>Votre destinataire a ouvert votre courrier <strong>{reference}</strong> le {opened_at}.</p>
      <p>Vous serez notifié dès la confirmation de réception.</p>
    """
    return subject, render_email_shell(subject, body)
