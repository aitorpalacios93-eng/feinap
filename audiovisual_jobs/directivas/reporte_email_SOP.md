# Directiva: Generación de Reporte Visual por Email

## 1. Objetivo
Mejorar el reporte por email generado por el sistema de validación de ofertas para que sea altamente visual, profesional, y estile HTML, en lugar de simple texto/markdown básico. Debe resaltar claramente las mejores ofertas y **mostrar explícitamente las fuentes de cada oferta**.

## 2. Entradas
- Lista de ofertas filtradas y validadas (diccionarios con `title`, `company`, `location`, `url`, `score`, `role`, `source`, etc.).
- Resumen ejecutivo generado por Groq.
- Top ofertas destacadas.

## 3. Salidas
- Un correo electrónico enviado en formato HTML (MIMEText/MIMEMultipart con subtipo `html`).
- Debe incluir secciones claramente separadas mediante estilos CSS inline compatibles con el soporte de clientes de correo.

## 4. Lógica de Ejecución
1. Preparar un prompt para Groq que exija un resumen ejecutivo estructurado con elementos visuales atractivos.
2. Formatear el HTML para inyectar este resumen.
3. Iterar sobre las top 3 ofertas VIP y pintarlas como "Tarjetas" visuales (Blocks HTML o tablas con bordes/sombreado), incluyendo el campo `fuente` o `source`.
4. Iterar sobre el resto de las ofertas validadas 24h, listándolas de forma elegante (filas alternas o separadores), siempre incluyendo la `fuente`.
5. Enviar usando el cliente SMTP configurado.

## 5. Restricciones y Casos Borde
- **Soporte CSS en Email**: La mayoría de clientes de email eliminan clases CSS externas o estilos en el `<head>`. Todos los estilos clave **deben ser inline** (`style="..."`).
- Si falla la estructura, asegurar un fallback de texto plano legible en el envío `MIMEMultipart`.
- Manejar ofertas que falten campos opcionales como `source` o `location` (mostrar "N/A" o "Sin especificar").
