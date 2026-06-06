# Invitación de Boda Única - CapRover

Este proyecto es para una sola boda. No es una plataforma SaaS ni un sistema de múltiples plantillas.

Incluye:

- Una sola plantilla premium con estética playa / arena / elegante.
- Panel de administración.
- Configuración de textos del evento.
- Foto principal de la pareja.
- Dos fotos secundarias de la pareja.
- Imagen del lugar del evento.
- Galería adicional.
- Cuenta regresiva.
- Google Maps URL.
- Dress code.
- Música externa opcional.
- Invitados con enlace único.
- QR automático por invitado.
- RSVP / confirmación de asistencia.
- Dockerfile y captain-definition para CapRover.

## Variables de entorno en CapRover

```env
FLASK_SECRET_KEY=coloca_una_clave_larga_y_privada
ADMIN_PASSWORD=coloca_una_contraseña_para_el_panel
DATA_DIR=/app/data
UPLOAD_DIR=/app/static/uploads
QR_DIR=/app/static/qr
```

## Persistent directories

```txt
/app/data
/app/static/uploads
/app/static/qr
```

## Puerto interno

```txt
5000
```

## Rutas

```txt
/admin
/invite/<token>
```

## Push al repo

```bash
git init
git add .
git commit -m "Build single wedding invitation with admin panel"
git branch -M main
git remote add origin https://github.com/appgruard/invitaciones_boda_github_caprover.git
git push -u origin main
```
