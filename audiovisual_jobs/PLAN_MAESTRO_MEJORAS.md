# Plan Maestro de Mejoras - Sistema de Empleo Audiovisual

## FASE 1: Calidad y Limpieza de Datos (Prioridad Alta)

### 1.1 Mejorar Filtros Anti-Spam
- [ ] Ampliar lista de keywords negativas (actualmente básica)
- [ ] Añadir detección de patrones de spam por frecuencia
- [ ] Implementar scoring de confianza para Facebook/Telegram
- [ ] Añadir blacklist de dominios problemáticos

### 1.2 Normalización Inteligente
- [ ] Mejorar detección de ubicación (extraer ciudad de descripción)
- [ ] Normalizar nombres de empresa (quitar S.L., S.A., etc.)
- [ ] Clasificar mejor modalidad (detectar "híbrido" en descripción)
- [ ] Deduplicación más agresiva por similitud de texto (fuzzy matching)

### 1.3 Datos Enriquecidos
- [ ] Añadir campo "salario" si aparece en descripción
- [ ] Detectar nivel de experiencia (junior/senior)
- [ ] Extraer tecnologías/herramientas específicas
- [ ] Añadir campo "plazo" o "fecha_cierre"

## FASE 2: Cobertura de Fuentes (Prioridad Alta)

### 2.1 Reparar Fuentes Rotas
- [ ] InfoJobs: implementar anti-bot (rotación de user agents, delays)
- [ ] LinkedIn: investigar API oficial o método alternativo
- [ ] Portales con bloqueo: usar proxy rotativo

### 2.2 Nuevas Fuentes Prioritarias
- [ ] Slack communities de audiovisual
- [ ] Discord servers de casting
- [ ] Grupos WhatsApp (si es posible)
- [ ] Newsletters del sector (parsear emails)
- [ ] Twitter/X con hashtags específicos

### 2.3 Fuentes Internacionales España-friendly
- [ ] ProductionHUB
- [ ] StaffMeUp (filtrar España)
- [ ] MediaMatch
- [ ] EuroJobs

## FASE 3: Monitoreo y Alertas (Prioridad Media)

### 3.1 Sistema de Alertas
- [ ] Notificación cuando hay X ofertas nuevas de tu rol
- [ ] Alerta cuando una oferta coincide tus criterios exactos
- [ ] Reporte semanal por email con resumen
- [ ] Alerta cuando una fuente deja de funcionar

### 3.2 Dashboard Mejorado
- [ ] Gráficos de tendencias (ofertas por día/semana)
- [ ] Mapa de calor por ubicación
- [ ] Comparativa de fuentes (cuál aporta más)
- [ ] Exportar a PDF

### 3.3 Health Checks
- [ ] Monitorear tasa de éxito por fuente
- [ ] Detectar cuando una fuente está "muerta" (>7 días sin ofertas)
- [ ] Alertar si el pipeline falla 2 veces seguidas

## FASE 4: UX y Accesibilidad (Prioridad Media)

### 4.1 Google Sheets Avanzado
- [ ] Hojas separadas por rol (editor, realizador, etc.)
- [ ] Vista "Mis Favoritos" (marcar ofertas interesantes)
- [ ] Columna "Estado Postulación" (pendiente/aplicado/entrevista)
- [ ] Formato condicional (ofertas >7 días en rojo)

### 4.2 Interfaz Web Simple
- [ ] Página web básica con lista de ofertas
- [ ] Buscador por texto
- [ ] Filtros visuales (checkboxes)
- [ ] Responsive para móvil

### 4.3 Integraciones
- [ ] Botón "Compartir por WhatsApp"
- [ ] Exportar a Notion
- [ ] Webhook para Slack/Discord personal

## FASE 5: Machine Learning (Prioridad Baja)

### 5.1 Clasificación Automática
- [ ] Entrenar modelo para detectar rol exacto
- [ ] Clasificar tipo de contrato (freelance/fijo/temporal)
- [ ] Detectar idioma de la oferta

### 5.2 Recomendaciones
- [ ] "Ofertas similares a las que has visto"
- [ ] Alertas predictivas (basado en histórico)

### 5.3 Análisis de Mercado
- [ ] Salarios promedio por rol
- [ ] Tendencias de contratación
- [ ] Demanda por ubicación

## IMPLEMENTACIÓN INMEDIATA (Hoy)

### Tareas que puedo hacer ahora:
1. **Mejorar filtro de spam** con más keywords
2. **Añadir campo "días activa"** para detectar ofertas viejas
3. **Crear vista "Ofertas de hoy"** en Google Sheets
4. **Implementar soft delete** (no borrar, marcar como inactiva)
5. **Añadir logging de rechazos** (saber qué se filtra)

## PRÓXIMAS 2 SEMANAS

### Semana 1:
- Arreglar InfoJobs
- Añadir 5 nuevas fuentes
- Implementar alertas básicas

### Semana 2:
- Crear interfaz web simple
- Mejorar clasificación de roles
- Testing masivo

## MÉTRICAS DE ÉXITO

- [ ] >200 ofertas nuevas por semana
- [ ] <5% de spam en resultados
- [ ] 100% uptime del pipeline
- [ ] <2min para actualizar Google Sheets
- [ ] Cobertura de 50+ fuentes activas

## RECURSOS NECESARIOS

- **Tiempo**: 2-3 horas/semana de mantenimiento
- **Costos**: 
  - Proxies rotativos: ~10€/mes (opcional)
  - Servidor VPS: ~5€/mes (para hosting web)
  - API premium: depende de uso

## ¿QUÉ QUIERES PRIORIZAR?

Dime qué te parece más importante y empezamos por ahí:
1. **Ahora**: Arreglar InfoJobs y añadir más fuentes
2. **Ahora**: Sistema de alertas personalizadas
3. **Ahora**: Interfaz web más usable
4. **Todo el plan** pero en orden
