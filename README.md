# BBS Gestión Escolar

Plataforma web completa de gestión escolar desarrollada con **Flask** para la administración de cursos, matrículas, pagos, documentos y más.

## 🚀 Características Principales

- **Gestión de Usuarios**: Sistema de roles (Administrador, Administrativo, Supervisor)
- **Cursos**: Creación de cursos FP e Intensivos con módulos y programación
- **Matrículas**: Registro de estudiantes con asignación de cursos
- **Pagos**: Sistema de cuotas con validación y seguimiento
- **Calificaciones**: Registro de notas ordinarias, parciales, finales y recuperación
- **Documentos**: Entrada/salida de documentos con versionado
- **Expedientes Académicos**: Historial completo de estudiantes
- **Validaciones**: Panel de validación de cursos, matrículas y pagos
- **Estadísticas**: Dashboards con métricas del sistema
- **Auditoría**: Registro de actividades de usuarios

## 📋 Requisitos

- Python 3.8+
- pip (gestor de paquetes de Python)
- Git

## 🛠️ Instalación Local

### 1. Clonar el repositorio

```bash
git clone https://github.com/FCEB2022/bbs_gestion_escolar.git
cd bbs_gestion_escolar
```

### 2. Crear entorno virtual

**En Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**En macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Inicializar la base de datos

```bash
# Crear tablas
flask db upgrade

# Cargar datos iniciales (usuarios admin, roles)
flask seed-datos-iniciales
```

### 5. Ejecutar la aplicación

```bash
python run.py
```

La aplicación estará disponible en `http://localhost:5000`

## 👤 Credenciales Iniciales

- **Usuario**: `admin`
- **Contraseña**: `admin123`

> ⚠️ Cambiar credenciales en producción

## 📁 Estructura del Proyecto

```
bbs_gestion_escolar/
├── app/                          # Aplicación principal
│   ├── __init__.py              # Factory de la app Flask
│   ├── config.py                # Configuración
│   ├── extensions.py            # Extensiones (db, login_manager, etc)
│   ├── models_shared.py         # Modelos compartidos
│   ├── seed.py                  # Script de datos iniciales
│   ├── core/                    # Dashboard principal
│   ├── usuarios/                # Gestión de usuarios
│   ├── cursos/                  # Gestión de cursos
│   ├── matriculas/              # Gestión de matrículas
│   ├── pagos/                   # Gestión de pagos
│   ├── documentos/              # Gestión de documentos
│   ├── actas_expedientes/       # Expedientes académicos
│   ├── validaciones/            # Panel de validaciones
│   ├── estadisticas/            # Dashboards
│   ├── perfil/                  # Perfil de usuario
│   ├── proyectos/               # Placeholder para futuro
│   ├── static/                  # CSS, JS, imágenes
│   └── templates/               # Templates HTML
├── migrations/                  # Migraciones de BD (Alembic)
├── instance/                    # BD SQLite y uploads
│   ├── app.db
│   └── uploads/
├── requirements.txt             # Dependencias Python
├── run.py                       # Punto de entrada
├── wsgi.py                      # Para producción
└── README.md                    # Este archivo
```

## 🗄️ Base de Datos

Se utiliza **SQLite** con **SQLAlchemy 2.x** como ORM. Las migraciones se manejan con **Flask-Migrate** (Alembic).

### Crear migración después de cambios en modelos

```bash
flask db migrate -m "Descripción del cambio"
flask db upgrade
```

## 🔐 Seguridad

- Autenticación con Flask-Login
- Contraseñas hasheadas con Werkzeug
- Protección CSRF con Flask-WTF
- Sistema de roles y permisos

## 🚀 Desarrollo

### Cambios y Sincronización con GitHub

Una vez hayas realizado cambios locales:

```bash
# Ver estado de cambios
git status

# Agregar cambios al staging
git add .

# Hacer commit con mensaje descriptivo
git commit -m "Descripción clara del cambio"

# Subir a GitHub
git push origin main
```

### Ramas de Desarrollo

Se recomienda usar ramas para nuevas funcionalidades:

```bash
# Crear rama
git checkout -b feature/nueva-funcionalidad

# Hacer cambios y commits...

# Subir rama a GitHub
git push -u origin feature/nueva-funcionalidad

# Crear Pull Request en GitHub para revisar
```

## 📝 Archivo .gitignore

Ya está configurado para ignorar:
- `__pycache__/` y archivos `.pyc`
- Entorno virtual (`venv/`)
- Base de datos (`*.db`, `*.sqlite`)
- Archivos de uploads
- `.env` y variables de entorno
- IDE files (`.vscode/`, `.idea/`)

## 🐛 Troubleshooting

### Error de conexión a BD
```bash
rm instance/app.db
flask db upgrade
flask seed-datos-iniciales
```

### Dependencias no encontradas
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## 📄 Licencia

Proyecto de uso interno para BBS

## 👥 Contribuidores

- Equipo de Desarrollo BBS

---

**Última actualización**: Noviembre 2025
