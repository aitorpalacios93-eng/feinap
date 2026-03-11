import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

from config.settings import settings
from db.connection import get_supabase_client
from db.queries import insert_daily_insight

logger = logging.getLogger(__name__)

from intelligence.groq_summarizer import resumir_ofertas_con_groq

def generar_cuerpo_html(ofertas: list) -> str:
    if not ofertas:
        return "<h3>No se encontraron nuevas ofertas hoy.</h3>"

    logger.info("Solicitando resumen a Groq...")
    resumen_groq = resumir_ofertas_con_groq(ofertas)
    
    if resumen_groq:
        try:
            client = get_supabase_client()
            insert_daily_insight(client, resumen_groq)
            logger.info("Insight diario guardado en Supabase exitosamente.")
        except Exception as e:
            logger.error(f"Error guardando insight en DB: {e}")

    html = f"""
    <html>
      <head>
        <meta charset="utf-8">
      </head>
      <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6; background-color: #f4f6f8; margin: 0; padding: 20px;">
      
        <div style="max-width: 650px; margin: 0 auto; background: #ffffff; padding: 30px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <h2 style="color: #2c3e50; text-align: center; border-bottom: 2px solid #ecf0f1; padding-bottom: 15px; margin-top: 0;">🔎 Últimas Ofertas de Trabajo</h2>
            
            <div style="margin-bottom: 30px;">
                {resumen_groq if resumen_groq else "<p style='text-align:center;'>Revisa la lista inferior para ver las últimas oportunidades laborales en el mercado.</p>"}
            </div>

            <h3 style="color: #2c3e50; border-bottom: 1px solid #ecf0f1; padding-bottom: 5px; margin-bottom: 20px;">📋 Listado Completo (Últimas 24h)</h3>
    """

    for o in ofertas:
        titulo = o.get("titulo_puesto", "Sin título")
        enlace = o.get("enlace_fuente", "#")
        empresa = o.get("empresa") or "Empresa confidencial"
        ubicacion = o.get("ubicacion") or "Ubicación no especificada"
        rol = o.get("rol_canonico") or "Mixto"
        score_decimal = o.get("score_confianza", 0)
        score_entero = int(round(score_decimal * 100))
        fuente = o.get("source_domain") or o.get("tipo_fuente", "Desconocida")

        html += f"""
            <div style="border: 1px solid #e1e8ed; padding: 20px; border-radius: 6px; margin-bottom: 15px; background-color: #ffffff; transition: box-shadow 0.2s; box-shadow: 0 1px 3px rgba(0,0,0,0.02);">
                <a href="{enlace}" style="font-size: 18px; font-weight: bold; color: #2980b9; text-decoration: none; display: block; margin-bottom: 6px;">{titulo}</a>
                <div style="font-size: 14px; color: #7f8c8d; margin-bottom: 12px;">
                    <span style="font-weight: bold; color: #34495e;">{empresa}</span> | <span>📍 {ubicacion}</span>
                </div>
                <div style="font-size: 12px;">
                    <span style="display: inline-block; background-color: #f8f9fa; border: 1px solid #ddd; padding: 4px 8px; border-radius: 4px; margin-right: 6px; color: #555;">💻 Rol: {rol}</span>
                    <span style="display: inline-block; background-color: #e8f4f8; border: 1px solid #bce8f1; padding: 4px 8px; border-radius: 4px; margin-right: 6px; color: #2980b9;">🔗 Fuente: {fuente}</span>
                    <span style="display: inline-block; background-color: #fef0f0; border: 1px solid #f5c6cb; padding: 4px 8px; border-radius: 4px; color: #c0392b; font-weight: bold;">⭐ Confianza: {score_entero}/100</span>
                </div>
            </div>
        """

    html += """
        </div>
      </body>
    </html>
    """
    return html

def enviar_email_ofertas(ofertas: list):
    try:
        from_email = settings.ALERT_EMAIL_FROM
        password = settings.ALERT_EMAIL_PASSWORD
        to_email = settings.ALERT_EMAIL_TO
        
        if not from_email or not password:
            logger.warning("Faltan credenciales de email (ALERT_EMAIL_FROM o ALERT_EMAIL_PASSWORD) en .env")
            return

        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"🔎 Nuevas Ofertas Audiovisuales - {datetime.now().strftime('%d/%m/%Y')}"
        msg["From"] = from_email
        msg["To"] = to_email

        html_content = generar_cuerpo_html(ofertas)
        part = MIMEText(html_content, "html")
        msg.attach(part)

        server = smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT)
        server.starttls()
        server.login(from_email, password)
        server.sendmail(from_email, to_email, msg.as_string())
        server.quit()

        logger.info(f"Email enviado correctamente a {to_email} con {len(ofertas)} ofertas.")
    except Exception as e:
        logger.error(f"Error al enviar el email: {e}")
