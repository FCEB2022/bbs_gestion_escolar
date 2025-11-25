# 🎯 DESPLIEGUE MANUAL EN RENDER (Guía Paso a Paso)

Como la API de Render es compleja, usaremos el dashboard manualmente. **Esto toma 5 minutos**.

## ✅ CREDENCIALES PREPARADAS

Se generaron automáticamente:
- **SECRET_KEY**: `75f1b2bb548023b83e7102905dca630a35246dba33f8ca59bbc336aa6f2dfa66`
- **Owner ID**: `tea-d4ikfg15pdvs73820pqg`
- Ver archivo: `RENDER_SECRETS.txt`

---

## 📋 PASO 1: Ir al Dashboard de Render

1. Abre https://dashboard.render.com
2. Inicia sesión con tu cuenta (GitHub)
3. Deberías ver tu equipo `bbs-gestion-escolar`

---

## 🗄️ PASO 2: Crear Base de Datos PostgreSQL

1. Click en **"New"** → **"PostgreSQL"**
2. Rellena:
   - **Name**: `bbs-gestion-escolar-db`
   - **Database**: `bbs_db`
   - **User**: `bbs_user` (o dejar automático)
   - **Region**: `Frankfurt (EU)`
   - **Plan**: `Free`
3. Click **"Create Database"**
4. **⏳ Espera 2-3 minutos** a que se cree
5. Una vez creada, **copia la CONNECTION STRING** (la necesitarás)

Algo como: `postgresql://usuario:pass@host:5432/bbs_db`

---

## 🚀 PASO 3: Crear Web Service

1. Click en **"New"** → **"Web Service"**
2. Elige **"Connect a repository"**
3. Busca y selecciona: `FCEB2022/bbs_gestion_escolar`
   - Si no aparece, click "Configure GitHub App" para autorizar

### Configuración Básica

| Campo | Valor |
|-------|-------|
| **Name** | `bbs-gestion-escolar` |
| **Environment** | `Python 3` |
| **Region** | `Frankfurt (EU)` |
| **Branch** | `main` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn wsgi:app --timeout 60` |
| **Plan** | `Free` |

---

## 🔧 PASO 4: Variables de Entorno

En la sección **"Environment"**, agrega estas variables:

```
FLASK_ENV=production
SECRET_KEY=75f1b2bb548023b83e7102905dca630a35246dba33f8ca59bbc336aa6f2dfa66
PYTHONUNBUFFERED=True
DATABASE_URL=<PEG
A_LA_CONNECTION_STRING_DE_LA_BD>
PORT=5000
```

**Importante**: En `DATABASE_URL`, pega la connection string de la BD PostgreSQL que copiaste en Paso 2.

---

## 💾 PASO 5: Agregar Disco para Uploads

1. Scroll a **"Disk"**
2. Click **"Add Disk"**
3. Rellena:
   - **Name**: `uploads`
   - **Size**: `1 GB`
   - **Mount Path**: `/var/data/uploads`
4. Click **"Add"**

---

## 🔗 PASO 6: Conectar Base de Datos (Render Native)

Si usas Render PostgreSQL (opción recomendada):

1. Render auto-inyectará `DATABASE_URL` en los env vars
2. No necesitas hacer nada más

Si usas una BD externa:
1. Asegúrate de que `DATABASE_URL` esté en las variables de entorno (Paso 4)

---

## ⚙️ PASO 7: Pre-deploy Command (Opcional pero Recomendado)

Si quieres que las migraciones y seeds se ejecuten automáticamente:

1. Encuentra el campo **"Deploy Hooks"** o **"Pre-deploy Command"**
2. Pega: `flask db upgrade && flask seed-datos-iniciales`
3. Esto se ejecutará cada vez que despliegues

---

## 🎯 PASO 8: Crear el Servicio

1. Revisa toda la configuración
2. Click **"Create Web Service"**
3. **⏳ Espera 5-10 minutos**

Render:
- Clonará tu repositorio
- Instalará dependencias
- Ejecutará pre-deploy (migraciones)
- Iniciará la app

---

## ✅ VERIFICAR EL DESPLIEGUE

### Ver Logs en Vivo

1. En el dashboard, click en tu servicio `bbs-gestion-escolar`
2. Click en la pestaña **"Live Logs"**
3. Deberías ver algo como:
   ```
   Starting service with 'gunicorn wsgi:app --timeout 60'
    * Running on http://0.0.0.0:5000
   ```

### Obtener la URL Pública

En el dashboard del servicio:
- En la parte superior, verás: `https://bbs-gestion-escolar-xxxxx.onrender.com`
- **Esta es tu URL para compartir**

### Acceder a la App

1. Copia la URL
2. Pégala en el navegador
3. Deberías ver la pantalla de login
4. Login:
   - **Usuario**: `admin`
   - **Contraseña**: `admin123`

---

## 🔍 Si Algo Falla

### Build Error
1. Ve a la pestaña **"Build Logs"**
2. Lee el error
3. Causas comunes:
   - Falta dependencia en `requirements.txt`
   - Syntax error en código Python
   - Variables de entorno mal configuradas

**Solución**: Arregla localmente, haz push a GitHub y Render reintentará automáticamente.

### App No Inicia
1. Ve a **"Live Logs"**
2. Busca líneas con `ERROR` o `CRITICAL`
3. Revisa que `DATABASE_URL` sea correcta

### Error de Base de Datos
- Verifica que la BD PostgreSQL esté creada
- Verifica que `DATABASE_URL` sea correcto
- Prueba las migraciones: desde Render, ejecuta el pre-deploy command manualmente

---

## 🔄 Actualizaciones Futuras

Después del despliegue inicial:

```bash
# En tu PC local
git add .
git commit -m "tu cambio"
git push origin main
```

Render **automáticamente**:
1. Detecta el push
2. Clona los cambios
3. Ejecuta build
4. Reinicia la app
5. En 2-3 minutos tus colaboradores ven los cambios

---

## 📞 URLs Importantes

- **Dashboard**: https://dashboard.render.com
- **Tu Repositorio**: https://github.com/FCEB2022/bbs_gestion_escolar
- **Documentación Render**: https://render.com/docs

---

## ✨ ¡Listo!

Una vez que la app esté en Render:
- ✅ Comparte la URL con tus colaboradores
- ✅ Ellos verán cambios en tiempo real
- ✅ Tu plataforma está en producción

**Siguiente**: Después del despliegue inicial, lee `DEPLOYMENT_COMPLETE.md` para próximos pasos.

---

*Guía actualizada: Noviembre 2025*
