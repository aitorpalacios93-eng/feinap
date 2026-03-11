"""
Sistema de Alertas por Email para Ofertas de Empleo Audiovisual
"""

import os
import sys
from pathlib import Path

# Añadir directorio padre al path
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from db.connection import get_supabase_client
from config.settings import settings


class AlertManager:
    """Gestiona alertas por email de ofertas laborales"""

    def __init__(self):
        self.client = get_supabase_client()

        # Configuración de email desde settings
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.email_from = settings.ALERT_EMAIL_FROM
        self.email_to = settings.ALERT_EMAIL_TO
        self.email_password = settings.ALERT_EMAIL_PASSWORD

        # Criterios de alerta personalizables
        self.criterios = {
            "roles_prioritarios": [
                "editor",
                "realizador",
                "cámara",
                "cameraman",
                "ayudante producción",
                "operador",
                "fotógrafo",
                "iluminador",
                "sonido",
                "montador",
            ],
            "ubicaciones": [
                "Barcelona",
                "Madrid",
                "Valencia",
                "Sevilla",
                "Bilbao",
                "Remoto",
                "Teletrabajo",
                "Híbrido",
            ],
            "min_score": 3,
            "max_dias": 3,
            "min_confianza": 0.6,
        }

    def obtener_ofertas_recientes(self) -> List[Dict[str, Any]]:
        """Obtiene ofertas de los últimos N días"""
        dias_atras = datetime.now() - timedelta(days=self.criterios["max_dias"])

        try:
            response = (
                self.client.table("ofertas_empleo")
                .select(
                    "titulo_puesto,empresa,ubicacion,rol_canonico,score_confianza,"
                    "modalidad,pais,source_domain,enlace_fuente,last_seen_at,descripcion,"
                    "fecha_publicacion,first_seen_at,remoto_espana,tipo_fuente,activo"
                )
                .gte("last_seen_at", dias_atras.isoformat())
                .order("last_seen_at", desc=True)
                .execute()
            )

            return response.data or []
        except Exception as e:
            print(f"❌ Error obteniendo ofertas: {e}")
            return []

    def filtrar_ofertas_relevantes(
        self, ofertas: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Filtra ofertas según criterios personalizados"""
        relevantes = []

        for oferta in ofertas:
            titulo = (oferta.get("titulo_puesto") or "").lower()
            ubicacion = (oferta.get("ubicacion") or "").lower()
            rol = (oferta.get("rol_canonico") or "").lower()
            score = oferta.get("score_confianza", 0) or 0

            # Verificar rol prioritario
            rol_match = any(
                rol_p in titulo or rol_p in rol
                for rol_p in self.criterios["roles_prioritarios"]
            )

            # Verificar ubicación deseada
            ubicacion_match = any(
                ubi.lower() in ubicacion for ubi in self.criterios["ubicaciones"]
            )

            # Verificar score mínimo
            score_match = score >= self.criterios["min_confianza"]

            # Considerar relevante si cumple 2 de 3 criterios
            criterios_cumplidos = sum([rol_match, ubicacion_match, score_match])

            if criterios_cumplidos >= 2:
                oferta["_prioridad"] = criterios_cumplidos
                relevantes.append(oferta)

        # Ordenar por prioridad
        relevantes.sort(key=lambda x: x["_prioridad"], reverse=True)

        return relevantes

    def generar_html_email(self, ofertas: List[Dict[str, Any]]) -> str:
        """Genera contenido HTML del email con información detallada"""
        if not ofertas:
            return "<p>No hay ofertas nuevas que coincidan con tus criterios hoy.</p>"

        html_parts = []
        html_parts.append("<html><head><style>")
        html_parts.append(
            "body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; }"
        )
        html_parts.append(
            ".header { background: #00796b; color: white; padding: 20px; text-align: center; }"
        )
        html_parts.append(
            ".oferta { border: 1px solid #ddd; margin: 15px 0; padding: 20px; border-radius: 8px; background: #fafafa; }"
        )
        html_parts.append(
            ".titulo { font-size: 20px; font-weight: bold; color: #00796b; margin-bottom: 10px; }"
        )
        html_parts.append(
            ".empresa { font-weight: bold; color: #333; font-size: 16px; margin: 5px 0; }"
        )
        html_parts.append(".ubicacion { color: #555; font-size: 14px; margin: 5px 0; }")
        html_parts.append(
            ".descripcion { color: #444; font-size: 14px; margin: 10px 0; padding: 10px; background: #fff; border-left: 3px solid #00796b; }"
        )
        html_parts.append(".tags { margin: 10px 0; }")
        html_parts.append(
            ".tag { display: inline-block; background: #e0f2f1; color: #00796b; padding: 4px 10px; border-radius: 12px; font-size: 12px; margin: 2px; }"
        )
        html_parts.append(".tag.highlight { background: #00796b; color: white; }")
        html_parts.append(
            ".boton { display: inline-block; background: #00796b; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; margin-top: 15px; font-weight: bold; }"
        )
        html_parts.append(
            ".footer { margin-top: 30px; padding: 20px; background: #f5f5f5; text-align: center; font-size: 12px; color: #777; }"
        )
        html_parts.append(
            ".stats { background: #e3f2fd; padding: 15px; margin: 20px 0; border-radius: 5px; }"
        )
        html_parts.append(".meta { font-size: 12px; color: #666; margin-top: 10px; }")
        html_parts.append("</style></head><body>")

        html_parts.append(
            '<div class="header"><h1>🎬 Alertas de Empleo Audiovisual</h1>'
        )
        html_parts.append("<p>Nuevas oportunidades encontradas para ti</p></div>")

        html_parts.append('<div class="stats"><strong>📊 Resumen:</strong> ')
        html_parts.append(str(len(ofertas)))
        html_parts.append(" ofertas nuevas coinciden con tus criterios<br>")
        html_parts.append(
            "<small>Roles prioritarios: "
            + ", ".join(self.criterios["roles_prioritarios"][:3])
        )
        html_parts.append(
            " | Ubicaciones: " + ", ".join(self.criterios["ubicaciones"][:3])
        )
        html_parts.append("</small></div>")

        for i, oferta in enumerate(ofertas[:10], 1):
            score = oferta.get("score_confianza", 0)
            score_pct = int((score or 0) * 100)
            score_emoji = (
                "🟢"
                if score and score >= 0.8
                else "🟡"
                if score and score >= 0.5
                else "🔴"
            )

            # Extraer información adicional
            descripcion = str(oferta.get("descripcion", "") or "")[:250]
            if len(descripcion) == 250:
                descripcion += "..."

            modalidad = str(oferta.get("modalidad", "") or "No especificado")
            remoto = "🌐 Remoto España" if oferta.get("remoto_espana") else ""
            tipo_fuente = str(oferta.get("tipo_fuente", "") or "Web")
            fecha = str(oferta.get("fecha_publicacion", "") or "Fecha no especificada")
            activo = "✅ Activa" if oferta.get("activo") else "⚠️ Estado desconocido"

            html_parts.append('<div class="oferta">')

            # Título y número
            html_parts.append(
                '<div class="titulo">'
                + str(i)
                + ". "
                + str(oferta.get("titulo_puesto", "Sin título"))
                + "</div>"
            )

            # Empresa
            html_parts.append(
                '<div class="empresa">🏢 '
                + str(oferta.get("empresa", "Empresa no especificada"))
                + "</div>"
            )

            # Ubicación y rol
            html_parts.append(
                '<div class="ubicacion">📍 '
                + str(oferta.get("ubicacion", "Ubicación no especificada"))
                + " | 🏷️ "
                + str(oferta.get("rol_canonico", "Rol no clasificado"))
                + "</div>"
            )

            # Descripción
            if descripcion:
                html_parts.append('<div class="descripcion">')
                html_parts.append("📝 <strong>Descripción:</strong><br>")
                html_parts.append(descripcion)
                html_parts.append("</div>")

            # Tags
            html_parts.append('<div class="tags">')
            html_parts.append('<span class="tag">💼 ' + modalidad + "</span>")
            if remoto:
                html_parts.append('<span class="tag highlight">' + remoto + "</span>")
            html_parts.append('<span class="tag">📅 ' + fecha + "</span>")
            html_parts.append(
                '<span class="tag">'
                + score_emoji
                + " "
                + str(score_pct)
                + "% confianza</span>"
            )
            html_parts.append('<span class="tag">📡 ' + tipo_fuente + "</span>")
            html_parts.append("</div>")

            # Meta info
            html_parts.append('<div class="meta">' + activo + "</div>")

            # Botón
            html_parts.append(
                '<a href="'
                + str(oferta.get("enlace_fuente", "#"))
                + '" class="boton">Ver Oferta →</a>'
            )
            html_parts.append("</div>")

        if len(ofertas) > 10:
            html_parts.append("<p style='text-align: center; color: #777;'>...y ")
            html_parts.append(str(len(ofertas) - 10))
            html_parts.append(
                " ofertas más. <a href='https://docs.google.com/spreadsheets/d/1U3gq9vUia0fr9YFXXw5Evp4zEF-Ikw4M6li2cIfSZXg'>Ver todas en Google Sheets</a></p>"
            )

        html_parts.append(
            '<div class="footer"><p>Este email se envía automáticamente cada 6 horas.</p>'
        )
        html_parts.append(
            '<p><a href="https://docs.google.com/spreadsheets/d/1U3gq9vUia0fr9YFXXw5Evp4zEF-Ikw4M6li2cIfSZXg">Ver todas las ofertas en Google Sheets</a></p>'
        )
        html_parts.append("</div></body></html>")

        return "".join(html_parts)

    def enviar_alerta(self, ofertas: List[Dict[str, Any]]) -> bool:
        """Envía email con las ofertas filtradas"""
        if not self.email_from or not self.email_password:
            print("⚠️  Configuración de email incompleta. Añade a .env:")
            print("   ALERT_EMAIL_FROM=tu_email@gmail.com")
            print("   ALERT_EMAIL_PASSWORD=tu_app_password")
            print("   ALERT_EMAIL_TO=aitorpalacios93@gmail.com")
            return False

        if not ofertas:
            print("ℹ️  No hay ofertas relevantes para enviar alerta")
            return True

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = (
                "🎬 "
                + str(len(ofertas))
                + " Ofertas Audiovisual - "
                + datetime.now().strftime("%d/%m/%Y %H:%M")
            )
            msg["From"] = self.email_from
            msg["To"] = self.email_to

            html_content = self.generar_html_email(ofertas)
            msg.attach(MIMEText(html_content, "html"))

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_from, self.email_password)
                server.send_message(msg)

            print(f"✅ Alerta enviada a {self.email_to} con {len(ofertas)} ofertas")
            return True

        except Exception as e:
            print(f"❌ Error enviando email: {e}")
            return False

    def ejecutar(self) -> bool:
        """Ejecuta el ciclo completo de alertas"""
        print("🔍 Buscando ofertas para alertas...")

        ofertas = self.obtener_ofertas_recientes()
        print(
            f"   📄 {len(ofertas)} ofertas encontradas en últimos {self.criterios['max_dias']} días"
        )

        ofertas_relevantes = self.filtrar_ofertas_relevantes(ofertas)
        print(f"   🎯 {len(ofertas_relevantes)} ofertas coinciden con tus criterios")

        if ofertas_relevantes:
            return self.enviar_alerta(ofertas_relevantes)
        else:
            print("ℹ️  No se envía alerta (sin ofertas relevantes)")
            return True


def enviar_alerta_email():
    """Función de conveniencia para integrar en el pipeline"""
    alert_manager = AlertManager()
    return alert_manager.ejecutar()


if __name__ == "__main__":
    enviar_alerta_email()
