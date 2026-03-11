# Guía de Configuración de Alertas por Email

## PASO 1: Crear cuenta de Gmail para las alertas

1. Ve a https://gmail.com
2. Crea una cuenta nueva (ej: `audiovisual.jobs.alerts@gmail.com`)
3. **Importante**: No uses tu email personal para evitar problemas de seguridad

## PASO 2: Configurar acceso de aplicaciones (App Password)

### Opción A: App Password (Recomendado)

1. Ve a https://myaccount.google.com/
2. Seguridad → Verificación en dos pasos (actívala)
3. Vuelve a Seguridad → Contraseñas de aplicaciones
4. Genera una nueva contraseña para "Correo"
5. Copia la contraseña de 16 caracteres

### Opción B: Acceso menos seguro (No recomendado)

1. Ve a https://myaccount.google.com/
2. Seguridad → Acceso de apps menos seguras
3. Actívalo (menos seguro, pero más fácil)

## PASO 3: Configurar .env

Edita tu archivo `.env` y añade:

```bash
# Email que envía las alertas (el que creaste)
ALERT_EMAIL_FROM=audiovisual.jobs.alerts@gmail.com
ALERT_EMAIL_PASSWORD=tu_app_password_aqui

# Email que recibe las alertas (tu email)
ALERT_EMAIL_TO=aitorpalacios93@gmail.com
```

## PASO 4: Probar el sistema

```bash
cd "/Users/aitor/Documents/2. PROJECTES/AUTOMATIZACIONES/FEINA AUDIOVISUAL/audiovisual_jobs"
. venv/bin/activate
python scripts/email_alerts.py
```

Deberías recibir un email con las ofertas que coincidan con tus criterios.

## Qué recibirás en el email

✅ **Ofertas de últimos 3 días** que coincidan con:
- Roles: Editor, Realizador, Cámara, Ayudante de producción, etc.
- Ubicaciones: Barcelona, Madrid, Remoto
- Score de confianza > 60%

✅ **Formato HTML profesional** con:
- Título de la oferta
- Nombre de la empresa
- Ubicación
- Link directo para aplicar
- Indicador de confianza (🟢🟡🔴)

✅ **Frecuencia**: Automáticamente cada 6 horas (00:00, 06:00, 12:00, 18:00)

## Personalizar criterios

Edita `scripts/email_alerts.py` y modifica `self.criterios`:

```python
self.criterios = {
    'roles_prioritarios': ['editor', 'realizador', 'cámara'],  # Añade más
    'ubicaciones': ['Barcelona', 'Madrid', 'Valencia'],  # Añade más
    'min_score': 3,
    'max_dias': 3,  # Cambia a 1 para solo hoy, 7 para semana
}
```

## Solución de problemas

### "Error enviando email: Authentication failed"
- Verifica que la contraseña es correcta
- Si usas Gmail, asegúrate de usar App Password, no tu contraseña normal

### "No hay ofertas relevantes"
- Normal si no hay ofertas nuevas que coincidan
- El sistema solo envía email cuando hay coincidencias
- Prueba ampliando `max_dias` a 7 en la configuración

### "Configuración de email incompleta"
- Faltan variables en `.env`
- Asegúrate de que todas las líneas de email estén sin comentar (sin # al inicio)

## Seguridad

⚠️ **NUNCA** subas tu `.env` con contraseñas a GitHub
⚠️ **NUNCA** compartas tu App Password
✅ El archivo `.env` ya está en `.gitignore` para proteger tus datos

## Soporte

Si tienes problemas, verifica:
1. Que el email existe y puede enviar correos
2. Que la contraseña de aplicación es correcta
3. Que tu firewall no bloquea SMTP (puerto 587)
4. Los logs en `logs/app.log` para ver errores específicos
