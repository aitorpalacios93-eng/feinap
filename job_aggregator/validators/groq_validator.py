"""
Segunda capa de validación con IA (Groq).

validate_and_summarize(jobs) → dict con:
  - top_offers: List — ofertas más relevantes
  - summary: str — resumen ejecutivo del mercado del día
  - validated_jobs: List — todas las ofertas con campo 'relevance' añadido
  - failed: bool — True si Groq no respondió (fallback graceful)
"""

import os
import json
import logging
from typing import List

log = logging.getLogger("groq_validator")

GROQ_MODEL = "llama-3.3-70b-versatile"
BATCH_SIZE = 20


def _serialize_jobs(jobs: List) -> List[dict]:
    """Convierte objetos JobOffer a dicts simples para el prompt."""
    out = []
    for j in jobs:
        out.append({
            "title": getattr(j, "title", "") or "",
            "company": getattr(j, "company", "") or "",
            "location": getattr(j, "location", "") or "",
            "source": getattr(j, "source", "") or "",
            "date_posted": str(getattr(j, "date_posted", "") or ""),
            "description": (getattr(j, "description", "") or "")[:300],
            "url": getattr(j, "url", "") or "",
        })
    return out


def _call_groq(client, jobs_batch: List[dict]) -> dict:
    """Llama a Groq con un batch de ofertas y retorna JSON estructurado."""
    prompt = f"""Eres un asistente experto en empleo audiovisual y marketing en España.

Analiza estas {len(jobs_batch)} ofertas de empleo y devuelve un JSON con exactamente esta estructura:
{{
  "offers": [
    {{
      "index": 0,
      "relevance": "alta|media|baja",
      "is_current": true,
      "contract_type": "indefinido|temporal|freelance|prácticas|desconocido",
      "salary_estimate": "rango estimado o null",
      "key_requirements": ["req1", "req2"],
      "summary": "1 frase descripción"
    }}
  ],
  "market_summary": "Resumen ejecutivo de 2-3 frases sobre el mercado laboral hoy"
}}

Criterios:
- relevance alta: oferta muy específica para audiovisual/marketing/freelance con buenos requisitos
- relevance media: relacionada pero genérica o con pocos detalles
- relevance baja: irrelevante, muy antigua o parece reciclada
- is_current: false si la fecha parece muy antigua (>30 días) o hay señales de oferta expirada

Ofertas a analizar:
{json.dumps(jobs_batch, ensure_ascii=False, indent=2)}

Responde SOLO con el JSON, sin markdown ni texto extra."""

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=4000,
    )
    raw = response.choices[0].message.content.strip()
    # Limpiar posibles bloques markdown
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw)


def validate_and_summarize(jobs: List) -> dict:
    """
    Valida y enriquece la lista de ofertas con IA.
    Siempre retorna un dict válido aunque Groq falle.
    """
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        log.warning("GROQ_API_KEY no definida — saltando validación IA")
        return {"top_offers": jobs[:5], "summary": "", "validated_jobs": jobs, "failed": True}

    try:
        from groq import Groq
    except ImportError:
        log.warning("groq no instalado — saltando validación IA")
        return {"top_offers": jobs[:5], "summary": "", "validated_jobs": jobs, "failed": True}

    client = Groq(api_key=api_key)
    serialized = _serialize_jobs(jobs)
    all_results = []
    market_summaries = []

    # Procesar en batches
    for i in range(0, len(serialized), BATCH_SIZE):
        batch_jobs = serialized[i:i + BATCH_SIZE]
        try:
            result = _call_groq(client, batch_jobs)
            all_results.extend(result.get("offers", []))
            if result.get("market_summary"):
                market_summaries.append(result["market_summary"])
        except Exception as e:
            log.warning(f"Groq batch {i//BATCH_SIZE + 1} falló: {e}")
            # Añadir entradas neutras para mantener índices
            for idx in range(len(batch_jobs)):
                all_results.append({
                    "index": i + idx,
                    "relevance": "media",
                    "is_current": True,
                    "contract_type": "desconocido",
                    "salary_estimate": None,
                    "key_requirements": [],
                    "summary": "",
                })

    # Enriquecer objetos originales con metadatos IA
    validated = list(jobs)
    for r in all_results:
        idx = r.get("index", -1)
        if 0 <= idx < len(validated):
            j = validated[idx]
            j._ai_relevance = r.get("relevance", "media")
            j._ai_current = r.get("is_current", True)
            j._ai_contract = r.get("contract_type", "desconocido")
            j._ai_salary = r.get("salary_estimate")
            j._ai_requirements = r.get("key_requirements", [])
            j._ai_summary = r.get("summary", "")

    # Top ofertas = relevancia alta + is_current, luego media
    top = [j for j in validated if getattr(j, "_ai_relevance", "media") == "alta" and getattr(j, "_ai_current", True)]
    if len(top) < 3:
        top += [j for j in validated if getattr(j, "_ai_relevance", "media") == "media" and getattr(j, "_ai_current", True)]
    top = top[:5]

    # Resumen ejecutivo combinado
    final_summary = " ".join(market_summaries) if market_summaries else ""

    log.info(f"Groq validó {len(validated)} ofertas — {len(top)} top, resumen: {bool(final_summary)}")
    return {
        "top_offers": top,
        "summary": final_summary,
        "validated_jobs": validated,
        "failed": False,
    }
