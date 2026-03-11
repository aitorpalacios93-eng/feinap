#!/usr/bin/env python3
"""
Script para generar PDFs a partir de plantillas HTML locales usando Playwright.
Debe ejecutarse dentro del entorno virtual.
"""

import sys
import os
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

async def generate_pdf(url: str, output_path: str):
    """Generar PDF desde URL (file://) usando print_to_pdf de chromium."""
    print(f"Generando PDF para: {url} -> {output_path}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(args=["--no-sandbox", "--disable-web-security"])
        page = await browser.new_page()
        
        # Cargar URL
        await page.goto(url, wait_until="networkidle")
        
        # Esperar un poco extra explícitamente para asegurar la inyección de fuentes
        await page.wait_for_timeout(2000)
        
        # Generar PDF configurado
        await page.pdf(
            path=output_path,
            format="A4",
            print_background=True,
            margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
            prefer_css_page_size=True,
        )
        await browser.close()
        print(f"PDF generado exitosamente: {output_path}")

async def main():
    base_dir = Path(__file__).resolve().parent
    cv_audiovisual_html = f"file://{base_dir}/cv_audiovisual.html"
    cv_cocina_html = f"file://{base_dir}/cv_cocina.html"
    
    pdf_audiovisual = str(base_dir / "Aitor_Palacios_CV_Audiovisual.pdf")
    pdf_cocina = str(base_dir / "Aitor_Palacios_CV_Cocina.pdf")
    
    print("Iniciando generación de PDFs en alta resolución...")
    await generate_pdf(cv_audiovisual_html, pdf_audiovisual)
    await generate_pdf(cv_cocina_html, pdf_cocina)
    print("Proceso completado.")

if __name__ == "__main__":
    asyncio.run(main())
