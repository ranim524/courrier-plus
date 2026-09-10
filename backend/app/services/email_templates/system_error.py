from app.services.email_templates.base import render_email_shell


def render_system_error(reference: str, error_summary: str) -> tuple[str, str]:
    subject = f"Courrier+ — Erreur système sur le courrier {reference}"
    body = f"""
      <p>Une erreur s'est produite pour le courrier <strong>{reference}</strong>.</p>
      <p>{error_summary}</p>
    """
    return subject, render_email_shell(subject, body)
