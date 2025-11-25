# ⚡ Guía Rápida: Desplegar en Render (5 minutos)

## 1️⃣ Crear Cuenta en Render

Ve a https://render.com y haz click en **"Sign up with GitHub"**

## 2️⃣ Conectar tu Repositorio

1. En Render Dashboard → **"New"** → **"Web Service"**
2. Click en **"Connect a repository"**
3. Selecciona: `FCEB2022/bbs_gestion_escolar`
4. Autoriza si es necesario

## 3️⃣ Configurar el Servicio

**Llena estos campos:**

| Campo | Valor |
|-------|-------|
| **Name** | `bbs-gestion-escolar` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn wsgi:app --timeout 60` |
| **Plan** | Free |
| **Region** | Frankfurt (o cercana a ti) |

## 4️⃣ Agregar Variables de Entorno

Click en **"Add Environment Variable"**:

```
FLASK_ENV = production
PYTHONUNBUFFERED = True
SECRET_KEY = (generar automático)
```

## 5️⃣ Agregar Base de Datos PostgreSQL

Antes de crear el servicio:
1. Scroll a **"Database"**
2. **"Add Database"** → **"Create new PostgreSQL"**
3. Plan: **Free**
4. Misma región que el servicio web

## 6️⃣ ¡Crear!

Click en **"Create Web Service"** y espera 5-10 minutos.

---

## ✅ ¡Listo!

Cuando termine, tendrás una URL como:
```
https://bbs-gestion-escolar-xxxxx.onrender.com
```

**Login:**
- Usuario: `admin`
- Contraseña: `admin123`

---

## 🔄 Actualizaciones Automáticas

Cada vez que hagas esto localmente:
```bash
git push origin main
```

Render **automáticamente** actualiza en 2-3 minutos sin hacer nada más.

---

## 📖 Documentación Completa

Para más detalles, lee: **RENDER_DEPLOYMENT.md**

---

**¡Tu plataforma está lista para compartir! 🚀**
