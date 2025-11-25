# 🚀 Despliegue en Render - BBS Gestión Escolar

## Introducción

Este documento contiene instrucciones para desplegar la plataforma BBS Gestión Escolar en **Render.com**, un servicio de hosting gratuito, seguro y con actualización automática desde GitHub.

### ✅ Ventajas de Render

- **Hosting Gratuito**: Plan free con suficiente capacidad
- **SSL/HTTPS Automático**: Conexión segura
- **Sincronización Automática**: Se actualiza automáticamente cuando haces push a GitHub
- **Base de Datos PostgreSQL**: Incluida (gratuita)
- **URL Compartible**: Para que tus colaboradores accedan
- **Logs en tiempo real**: Monitoreo de la aplicación

---

## 📋 Prerequisitos

1. **Cuenta en GitHub** - Ya tienes el repositorio: https://github.com/FCEB2022/bbs_gestion_escolar
2. **Cuenta en Render.com** - Crear en https://render.com (gratuito)
3. **Conexión a Internet** - Para sincronizar

---

## 🔧 Pasos de Configuración

### PASO 1️⃣: Crear Cuenta en Render

1. Abre https://render.com
2. Click en **"Get Started"**
3. Elige **"Sign up with GitHub"** (más fácil)
4. Autoriza la conexión con tu cuenta GitHub
5. Completa la configuración

### PASO 2️⃣: Conectar Repositorio GitHub

1. En el dashboard de Render, click en **"New"** → **"Web Service"**
2. Click en **"Connect a repository"**
3. Selecciona **"FCEB2022/bbs_gestion_escolar"**
   - Si no aparece, click en "Configure GitHub App" para autorizar
4. Autoriza el acceso al repositorio

### PASO 3️⃣: Configurar el Servicio Web

**Nombre del Servicio:**
- `bbs-gestion-escolar` (o el nombre que prefieras)

**Tipo de Rama:**
- Selecciona `main`

**Build Command** (Comando de Construcción):
```bash
pip install -r requirements.txt
```

**Start Command** (Comando de Inicio):
```bash
gunicorn wsgi:app --timeout 60
```

**Plan**: 
- Selecciona **"Free"** (plan gratuito)

**Región**:
- Elige la más cercana a tus colaboradores:
  - 🇫🇷 `Frankfurt` (Europa)
  - 🇺🇸 `Ohio` (América del Norte)
  - 🇺🇸 `Oregon` (América del Norte Oeste)

### PASO 4️⃣: Configurar Variables de Entorno

Después de llenar los datos anteriores, aparecerá una sección de **"Environment"**.

Haz click en **"Add Environment Variable"** y agregar estas variables:

| Clave | Valor | Notas |
|-------|-------|-------|
| `FLASK_ENV` | `production` | Modo producción |
| `SECRET_KEY` | (Generar automático) | Click "Generate" |
| `PYTHONUNBUFFERED` | `True` | Para ver logs en tiempo real |

**Generar SECRET_KEY automáticamente:**
1. Render ofrece generar claves aleatorias
2. O puedes generar localmente:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### PASO 5️⃣: Agregar Base de Datos PostgreSQL

En el mismo servicio web, antes de hacer click en "Create Web Service":

1. Scroll down a **"Database"**
2. Click en **"Add Database"**
3. Click en **"Create new PostgreSQL"**

**Configuración de BD:**
- **Name**: `bbs-db` (o similar)
- **Database**: `bbs_db`
- **User**: Render genera automáticamente
- **Plan**: **Free**
- **Región**: Misma que el web service

### PASO 6️⃣: Crear el Servicio

1. Revisa toda la configuración
2. Click en **"Create Web Service"**
3. Espera a que Render:
   - Clone el repositorio
   - Instale dependencias
   - Cree la base de datos
   - Ejecute las migraciones
   - Inicie la aplicación

Este proceso toma **5-10 minutos** la primera vez.

---

## ✅ Verificar que Funciona

### Ver Logs en Tiempo Real

1. Después de crear el servicio, irás al dashboard
2. Click en tu servicio "bbs-gestion-escolar"
3. Verás los **Logs** en la sección "Build Log" y "Live Logs"

Deberías ver algo como:
```
Starting service with 'gunicorn wsgi:app --timeout 60'
 * Running on http://0.0.0.0:5000
```

### Obtener tu URL Pública

1. En el dashboard del servicio, en la parte superior
2. Verás la URL: `https://tu-servicio.onrender.com`
3. Esta es la URL que compartirás con tus colaboradores

### Acceder a la Aplicación

1. Copia la URL: `https://tu-servicio.onrender.com`
2. Pégala en el navegador
3. Deberías ver la pantalla de login
4. Usa:
   - **Usuario**: `admin`
   - **Contraseña**: `admin123`

---

## 🔄 Actualizaciones Automáticas

### El Mejor Flujo

Ahora que está desplegado en Render, **cada vez que hagas push a GitHub**:

```powershell
# En tu PC local
git add .
git commit -m "feat: Agregar nueva funcionalidad"
git push origin main
```

**Render automáticamente:**
1. ✅ Detecta el nuevo push
2. ✅ Clona los cambios
3. ✅ Ejecuta `pip install -r requirements.txt`
4. ✅ Ejecuta migraciones (si las hay)
5. ✅ Reinicia la aplicación

En **2-3 minutos** tus colaboradores verán los cambios en `https://tu-servicio.onrender.com` sin hacer nada.

### Ver Despliegues

1. En tu servicio de Render
2. Click en la pestaña **"Deploys"**
3. Verás el historial de despliegues automáticos
4. Cada push = 1 nuevo despliegue

---

## 📤 Compartir con Colaboradores

Envía esto a tus colaboradores:

```
🎉 ¡La plataforma BBS está lista para pruebas!

URL: https://tu-servicio.onrender.com
Usuario: admin
Contraseña: admin123

📝 Cambios en tiempo real:
Cualquier actualización que yo haga en GitHub se refleja automáticamente
en la plataforma sin hacer nada especial.

🔗 Repositorio: https://github.com/FCEB2022/bbs_gestion_escolar
```

---

## 🐛 Solucionar Problemas

### Error: "Build Failed"

1. Ve a **"Build Log"** en Render
2. Lee el error detalladamente
3. Causas comunes:
   - Falta dependencia en `requirements.txt`
   - Syntax error en el código
   - Variable de entorno faltante

**Solución:**
```bash
# En tu PC
git push origin main
# Render reintentará automáticamente
```

### La App Muestra "Service Unavailable"

Posibles causas:
1. La base de datos no está lista (espera 5 minutos)
2. Se agotaron los recursos gratuitos
3. Error en las migraciones

**Ver logs:**
1. En Render, click en "Live Logs"
2. Busca líneas con ERROR o WARNING

### Problema: Base de Datos Vacía

Si ves error de BD vacía:
```bash
# Desde tu PC, conéctate a Render y ejecuta:
flask db upgrade
flask seed-datos-iniciales
```

O reinicia el servicio desde Render Dashboard.

---

## 🔐 Seguridad en Producción

### Recomendaciones

1. **Cambiar credenciales iniciales:**
   - Accede a `https://tu-servicio.onrender.com/usuarios`
   - Cambiar contraseña de `admin`
   - Crear nuevos usuarios administrativos

2. **Usar variables de entorno:**
   - Nunca guardes SECRET_KEY en el código
   - Render las proporciona automáticamente

3. **Backups de datos:**
   - PostgreSQL en Render hace backups automáticos
   - Puedes exportar datos desde la consola

4. **HTTPS:**
   - Render proporciona SSL automático
   - Todas las conexiones son seguras

---

## 📊 Monitoreo

### Ver Métrica de Uso

En el Dashboard de Render:
- **CPU Usage**: Cómo de intensiva es la aplicación
- **Memory Usage**: Cuánta RAM utiliza
- **Uptime**: Cuánto tiempo lleva funcionando

### Logs

- **Build Log**: Qué pasó durante la construcción
- **Live Logs**: Logs en tiempo real de la aplicación

---

## 🚀 Próximos Pasos Recomendados

1. ✅ Desplegar en Render (este documento)
2. ✅ Compartir URL con colaboradores
3. ✅ Hacer pruebas en `https://tu-servicio.onrender.com`
4. ✅ Hacer cambios locales y hacer push
5. ✅ Ver cambios reflejados automáticamente

---

## 📞 Soporte

Si tienes problemas:

1. **Documentación de Render**: https://render.com/docs
2. **Logs en Render**: Están muy detallados
3. **GitHub Issues**: https://github.com/FCEB2022/bbs_gestion_escolar/issues

---

**¡Listo! Tu plataforma está en el aire con actualizaciones en tiempo real desde GitHub** 🎉
