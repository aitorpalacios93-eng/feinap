import os
import json
import logging
from typing import List, Dict, Any
from groq import Groq
from config.settings import settings

logger = logging.getLogger(__name__)

def resumir_ofertas_con_groq(ofertas: List[Dict[str, Any]]) -> str:
    """
    Envía las ofertas del día a Groq (Llama 3) para que genere un
    resumen ejecutivo y seleccione las mejores ofertas.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        logger.warning("GROQ_API_KEY no encontrada. Saltando resumen por IA.")
        return ""

    if not ofertas:
        return ""

    try:
        client = Groq(api_key=api_key)
        
        # Preparar un subset de datos para el prompt
        ofertas_resumidas = []
        for o in ofertas:
            desc = o.get("descripcion", "")
            # Recortar la descripción para no exceder el límite de tokens, pero darle algo de contexto
            if desc:
                desc = desc[:400] + "..."
                
            resumen = {
                "titulo": o.get("titulo_puesto"),
                "empresa": o.get("empresa") or "Dato Oculto",
                "ubicacion": o.get("ubicacion"),
                "rol": o.get("rol_canonico"),
                "score": round(o.get("score_confianza", 0) * 100),
                "fuente": o.get("source_domain") or o.get("tipo_fuente") or "Desconocida",
                "descripcion": desc
            }
            ofertas_resumidas.append(resumen)

        # Si hay demasiadas, podemos truncar la lista a las top 20 por score para que el LLM profundice
        ofertas_resumidas = sorted(ofertas_resumidas, key=lambda x: x["score"], reverse=True)[:20]

        prompt_system = """Eres un experto reclutador analizando el mercado laboral audiovisual y hostelero en España.
Tu objetivo es leer un JSON con ofertas de trabajo extraídas hoy y redactar un resumen ejecutivo (HTML) profundo exclusivo para el candidato.

Formato deseado (Usa HTML limpio, sin etiquetas html/body/head. Utiliza INLINE CSS para dar estilo, creando hermosas tarjetas visuales):
<div style="font-family: Arial, sans-serif;">
    <h3 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 5px;">🎯 Resumen Ejecutivo del Día</h3>
    <p style="font-size: 15px; color: #34495e; line-height: 1.6;">[Un párrafo resumiendo qué tipo de ofertas predominan hoy y la dinámica general]</p>
    
    <h3 style="color: #2c3e50; border-bottom: 2px solid #e74c3c; padding-bottom: 5px; margin-top: 25px;">⭐ Top Oportunidades Destacadas</h3>
    
    <!-- Iterar sobre las mejores 3-5 ofertas VIP y crear una tarjeta para cada una -->
    <div style="background-color: #f8f9fa; border-left: 5px solid #e74c3c; border-radius: 6px; padding: 15px; margin-bottom: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
        <h4 style="margin: 0 0 8px 0; color: #2980b9; font-size: 17px;">[Título de la oferta]</h4>
        <div style="margin-bottom: 8px;">
            <span style="font-weight: bold; color: #2c3e50;">🏢 [Empresa]</span> | 
            <span style="color: #7f8c8d;">📍 [Ubicación]</span>
        </div>
        <div style="margin-bottom: 12px;">
            <span style="display: inline-block; background-color: #e8f4f8; color: #2980b9; padding: 3px 8px; border-radius: 12px; font-size: 12px; font-weight: bold; margin-right: 5px;">🔗 Fuente: [Nombre de la fuente]</span>
            <span style="display: inline-block; background-color: #fef0f0; color: #e74c3c; padding: 3px 8px; border-radius: 12px; font-size: 12px; font-weight: bold;">⭐ Score: [Score]/100</span>
        </div>
        <p style="margin: 0; font-size: 14px; color: #555; line-height: 1.5;">[Un breve resumen convincente y directo de 2-3 líneas explicando por qué esta oportunidad es VIP basándote en la descripción: requisitos clave, salarios o beneficios descritos]</p>
    </div>
    <!-- Fin de iteración VIP -->
</div>

REGLAS:
- Solo redacta en español.
- NO uses markdown (ni ```html), responde ÚNICAMENTE con el código HTML crudo que se insertará directamente en el email.
- Extrae la información valiosa de la "descripcion" (beneficios, responsabilidades claras) para hacer el párrafo descriptivo de la tarjeta llamativo.
- Utiliza estrictamente el diseño de tarjeta con INLINE CSS provisto arriba. Asegúrate de pintar correctamente la fuente ('fuente').
"""

        prompt_user = "Aquí tienes las ofertas de hoy:\n" + json.dumps(ofertas_resumidas, ensure_ascii=False, indent=2)

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # Modelo moderno y disponible
            messages=[
                {"role": "system", "content": prompt_system},
                {"role": "user", "content": prompt_user}
            ],
            temperature=0.3,
            max_tokens=1000,
        )

        resumen_html = response.choices[0].message.content.strip()
        
        # Limpiar posibles bloques de markdown si el modelo se equivoca
        if resumen_html.startswith("```"):
            resumen_html = resumen_html.split("\n", 1)[1]
            if resumen_html.startswith("html"):
                resumen_html = resumen_html.split("\n", 1)[1]
            if resumen_html.endswith("```"):
                resumen_html = resumen_html[:-3]
                
        return resumen_html

    except Exception as e:
        logger.error(f"Error generando resumen con Groq: {e}")
        return ""
