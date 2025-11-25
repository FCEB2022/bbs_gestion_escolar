# 📚 Guía de Sincronización con GitHub

## Configuración Completada ✅

Tu repositorio está configurado en:
- **URL**: https://github.com/FCEB2022/bbs_gestion_escolar.git
- **Rama Principal**: main
- **Remoto**: origin

## Flujo de Trabajo Diario

### 1️⃣ Ver cambios locales
```bash
git status
```

### 2️⃣ Revisar diferencias
```bash
# Ver cambios sin staging
git diff

# Ver cambios en staging
git diff --cached
```

### 3️⃣ Agregar cambios al staging
```bash
# Agregar archivo específico
git add ruta/del/archivo

# Agregar todos los cambios
git add .
```

### 4️⃣ Hacer commit
```bash
git commit -m "Mensaje descriptivo del cambio"
```

**Formato recomendado de mensajes:**
- `feat: Agregar nueva funcionalidad`
- `fix: Corregir bug en módulo X`
- `docs: Actualizar documentación`
- `refactor: Mejorar estructura de código`
- `style: Ajustar formato de código`
- `test: Agregar o mejorar tests`

### 5️⃣ Subir a GitHub
```bash
git push origin main
```

## 🌿 Trabajo con Ramas (Recomendado)

Para cambios importantes o nuevas funcionalidades, usa ramas:

### Crear rama de feature
```bash
git checkout -b feature/nombre-descriptivo
```

### Trabajar en la rama
```bash
git add .
git commit -m "Mensaje del cambio"
```

### Subir rama a GitHub
```bash
git push -u origin feature/nombre-descriptivo
```

### Fusionar en main (después de revisión)
```bash
git checkout main
git pull origin main
git merge feature/nombre-descriptivo
git push origin main
git branch -d feature/nombre-descriptivo
```

## 📥 Sincronizar cambios remotos

Si otros colaboradores subieron cambios:

```bash
# Traer cambios del remoto
git pull origin main
```

## 🔍 Historial de cambios

```bash
# Ver último commit
git log -1

# Ver últimos 5 commits
git log -5 --oneline

# Ver historial completo
git log --oneline --graph --all
```

## ⚠️ Deshacer cambios

```bash
# Deshacer cambios no staged
git checkout -- archivo.py

# Deshacer todos los cambios locales
git reset --hard

# Deshacer último commit (mantener cambios)
git reset --soft HEAD~1

# Deshacer último commit (descartar cambios)
git reset --hard HEAD~1
```

## 🚨 Errores Comunes

### Error: "untracked files would be overwritten"
```bash
git clean -fd
git reset --hard origin/main
```

### Error: "Your branch is behind"
```bash
git pull origin main
```

### Error: "Authentication failed"
GitHub requiere autenticación. Se abrirá un navegador automáticamente.
Si no, genera un token personal en GitHub: https://github.com/settings/tokens

## 💡 Consejos

- ✅ Haz commits frecuentes con mensajes claros
- ✅ Usa ramas para cambios importantes
- ✅ Sincroniza regularmente con `git pull`
- ✅ Revisa el estado antes de hacer push
- ❌ No hagas commits de archivos sensibles (.env, .db, etc - ya están en .gitignore)
- ❌ No forces push a main sin causa importante

## 📊 Dashboard de Commits

Ver tu historial en GitHub: https://github.com/FCEB2022/bbs_gestion_escolar/commits/main

---

**¡Todo listo para sincronizar! Cualquier cambio que hagas localmente puede enviarse a GitHub con `git add .` → `git commit -m "mensaje"` → `git push origin main`**
