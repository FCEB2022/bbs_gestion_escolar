# ⚡ DESPLIEGUE EN RENDER - 3 MINUTOS (VALORES LISTOS)

## 🎯 Resumen

La API de Render tiene limitaciones. **Lo más rápido y seguro es hacerlo por UI** (3 minutos, visual, sin código).

Todo está preparado. Solo necesitas copiar y pegar valores.

---

## 📋 CREDENCIALES GENERADAS (CÓPIA-PEGA)

```
SECRET_KEY=75f1b2bb548023b83e7102905dca630a35246dba33f8ca59bbc336aa6f2dfa66
FLASK_ENV=production
PYTHONUNBUFFERED=True
```

---

## 🚀 PASO A PASO (3 MINUTOS)

### 1️⃣ Ir al Dashboard (30 segundos)

Abre: https://dashboard.render.com

### 2️⃣ Crear Base de Datos PostgreSQL (1 minuto)

1. Click **"New"** (esquina superior derecha)
2. Click **"PostgreSQL"**
3. Rellena:
   ```
   Name: bbs-gestion-escolar-db
   Database: bbs_db
   Region: Frankfurt (EU)
   Plan: Free
   ```
4. Click **"Create Database"**
5. **Espera 2 minutos** a que se cree
6. Una vez creada, abre la BD y **COPIA la "Internal Database URL"** (es larga, algo como `postgresql://...`)
   - Guarda ese valor, lo usarás en el paso 4

### 3️⃣ Crear Web Service (1.5 minutos)

1. Click **"New"** → **"Web Service"**
2. Busca **"bbs_gestion_escolar"** repo y conecta
   - Si no aparece, autoriza GitHub
3. En el formulario, rellena:

| Campo | Valor |
|-------|-------|
| **Name** | `bbs-gestion-escolar` |
| **Environment** | `Python 3` |
| **Region** | `Frankfurt (EU)` |
| **Branch** | `main` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn wsgi:app --bind 0.0.0.0:$PORT --timeout 60` |
| **Plan** | `Free` |

### 4️⃣ Variables de Entorno (30 segundos)

Click en **"Environment"**

Agrega estas variables:

```
FLASK_ENV = production
SECRET_KEY = 75f1b2bb548023b83e7102905dca630a35246dba33f8ca59bbc336aa6f2dfa66
PYTHONUNBUFFERED = True
DATABASE_URL = [PEGA_LA_URL_QUE_COPIASTE_EN_PASO_2]
FLASK_APP = run.py
```

*Nota: NO necesitas agregar `PORT = 5000`. Render lo asigna automáticamente y tu `Start Command` lo usa con `$PORT`.*

### 5️⃣ Disco para Uploads (opcional)

- Nota: en la pantalla de creación el control de `Disk` no siempre aparece. Si no ves la opción aquí, no te preocupes: puedes añadir un disco persistente después de crear el servicio (si tu cuenta/plan/region lo soporta).

- Para añadirlo después: abre el servicio → `Settings` → `Disks` (o `Add Disk`) y rellena:

```
Name: uploads
Size: 1 GB
Mount Path: /var/data/uploads
```

- Si Render no permite disco en tu cuenta, usa S3 (recomendado) o guarda archivos en otra solución externa. Si quieres, puedo implementar S3 en la app.

### 6️⃣ Pre-Deploy Command (recomendado)

Has expandido `Advanced` y ahí aparece el campo **Pre-Deploy Command** (exactamente como en tu captura). Este campo es ideal para ejecutar migraciones y tareas previas al arranque.

Pega esto en **Pre-Deploy Command**:

```bash
export FLASK_APP=run.py && flask db upgrade && flask seed-datos-iniciales
```

Explicación: Render ejecuta este comando antes del `Start Command`; así las migraciones y seeds corren solo una vez por despliegue.

Si por alguna razón prefieres no usar Pre-Deploy (o no aparece), usa este **Start Command** como fallback (ejecuta migraciones justo antes de arrancar):

```bash
bash -lc "export FLASK_APP=run.py && flask db upgrade && flask seed-datos-iniciales && exec gunicorn wsgi:app --timeout 60"
```

Recomendaciones rápidas:
- Asegúrate de tener la variable de entorno `FLASK_APP=run.py` en `Environment`.
- Mantén `Start Command` como `gunicorn wsgi:app --timeout 60` si usas `Pre-Deploy Command`.
- Revisa `Live Logs` para ver el resultado de las migraciones y el arranque de Gunicorn.

### 7️⃣ ¡CREAR!

1. Revisa todo
2. Click **"Create Web Service"**
3. **Espera 10 minutos** (ve a los logs en vivo)

---

## ✅ VERIFICAR QUE FUNCIONA

### Ver Logs en Vivo

En el dashboard del servicio → pestaña **"Live Logs"**

Deberías ver:
```
Starting service...
Running on http://0.0.0.0:5000
```

### Obtener URL Pública

En la parte superior del dashboard del servicio:

```
https://bbs-gestion-escolar-XXXXX.onrender.com
```

Esa es tu URL.

### Probar Login

1. Ve a esa URL
2. Login:
   - Usuario: `admin`
   - Contraseña: `admin123`

---

## 🔄 Compartir con Colaboradores

```
🎉 Plataforma en vivo:
📍 https://bbs-gestion-escolar-XXXXX.onrender.com
👤 admin / admin123

Los cambios se actualizan automáticamente cada vez que hago push a GitHub.
Repo: https://github.com/FCEB2022/bbs_gestion_escolar
```

---

## 🐛 Si Algo Falla

### Build Error
→ Ve a **"Build Logs"**  
→ Lee el error  
→ Arregla localmente, haz push, Render reintenta

### App No Inicia
→ Ve a **"Live Logs"**  
→ Busca ERROR  
→ Revisa que DATABASE_URL sea correcto

### Timeout
→ Espera más (la BD puede tardar en iniciarse)

---

## 💡 Comandos Útiles (Para Después)

Si necesitas ejecutar algo manualmente desde Render:

```bash
# Ver estado
git log --oneline -1

# Ejecutar migraciones
flask db upgrade

# Crear seeds
flask seed-datos-iniciales
```

---

## ✨ ¡ESO ES!

En 15 minutos totales (3 minutos de trabajo + 10 minutos de espera automática) tu plataforma estará en vivo en Render.

Cualquier cambio que hagas localmente y hagas push se verá en vivo automáticamente en 2-3 minutos.

**Lee el archivo `RENDER_MANUAL_DEPLOY.md` si necesitas instrucciones más detalladas.**

---

*Última actualización: Noviembre 2025*
