BRAND_COLOR = "#1E3A5F"
ACCENT_COLOR = "#2F855A"


def render_email_shell(title: str, body_html: str) -> str:
    return f"""\
<!DOCTYPE html>
<html lang="fr">
<head><meta charset="utf-8"><title>{title}</title></head>
<body style="margin:0;padding:0;background-color:#f4f5f7;font-family:Arial,Helvetica,sans-serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f5f7;padding:24px 0;">
    <tr><td align="center">
      <table role="presentation" width="480" cellpadding="0" cellspacing="0" style="background-color:#ffffff;border-radius:8px;overflow:hidden;">
        <tr><td style="background-color:{BRAND_COLOR};padding:20px 32px;">
          <span style="color:#ffffff;font-size:20px;font-weight:bold;">Courrier+</span>
        </td></tr>
        <tr><td style="padding:32px;color:#1a1a1a;font-size:15px;line-height:1.6;">
          {body_html}
        </td></tr>
        <tr><td style="padding:20px 32px;background-color:#f4f5f7;color:#6b7280;font-size:12px;line-height:1.5;">
          Courrier+ est un prototype technique de courrier recommandé numérique pour la Tunisie.
          Cette confirmation n'a pas, en l'état, la valeur légale d'un courrier recommandé postal officiel.
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>
"""
