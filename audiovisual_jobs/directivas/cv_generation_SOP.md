# SOP: Generación de Curriculums en PDF de Alta Calidad

Este procedimiento operativo estándar define los pasos para generar documentos PDF con calidad de diseño profesional (Editorial / High-End) a partir de datos estructurados (Markdown/JSON) utilizando tecnologías web.

## 1. Fase de Diseño (Maquetación Web)

1. **Tecnología**: HTML5 y CSS3 puro o frameworks utilitarios, asegurando un diseño "Pixel Perfect". Flexbox y CSS Grid para la estructura.
2. **Estilo**: Minimalista, limpio, utilizando tipografías modernas (ej. Inter, Roboto, Outfit cargadas vía Google Fonts). Colores corporativos sutiles, espaciados amplios y jerarquía visual clara.
3. **Flujo de Trabajo (Stitch / Agente UI)**: 
   - Se debe crear un `index.html` con sus estilos `style.css` correspondientes que representen el CV a tamaño carta o A4.
   - Todo el contenido debe ser inyectado dinámicamente o estructurado explícitamente en el HTML.

## 2. Fase de Exportación (HTML to PDF)

1. **Herramienta Principal**: **Playwright** (Python). Dado que ya está instalado en el entorno para tareas de scraping, es la opción más robusta para renderizar CSS moderno (incluyendo Flexbox/Grid y Web Fonts) y exportar a PDF tal y como se ve en el navegador.
2. **Configuración de Impresión**:
   - `print_background=True`: Esencial para que se impriman los colores de fondo y gráficos.
   - `format="A4"` o `"Letter"`.
   - Márgenes definidos (ej. `margin={"top": "0", "right": "0", "bottom": "0", "left": "0"}` si el CSS ya maneja el padding global).
   - Ocultar elementos de UI si los hubiera.

## 3. Implementación en Código

1. **Script Generador**: Crear un script (ej. `scripts/generar_cv_pdf.py`) que sirva el HTML localmente o lo cargue directamente vía `file://` y utilice Playwright para generar el PDF.
2. **Manejo de rutas absolutas**: Asegurarse de que las referencias a imágenes o fuentes locales tengan rutas absolutas al ejecutarse.

## 4. Restricciones y Aprendizajes (Memoria Viva)

- **Fuentes Web**: Playwright necesita tiempo para cargar las fuentes web antes de imprimir el PDF. Usar `page.wait_for_load_state("networkidle")` o inyectar las fuentes en Base64 en el CSS para evitar que el PDF salga con la tipografía por defecto (Times New Roman).
- **Consistencia Multiestilo**: Separar las clases CSS para distintas variantes (Ej. `theme-audiovisual`, `theme-cocina`) en el mismo HTML para instanciar PDFs distintos cambiando solo una clase del bloque contenedor.
- **Paginación**: Usar `page-break-inside: avoid;` en el CSS para que los bloques de experiencia no se corten a la mitad entre dos páginas.
