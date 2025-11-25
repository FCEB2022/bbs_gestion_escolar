import os
from datetime import datetime

print("🧱 Iniciando migración automática...")

os.system("flask db migrate -m 'auto update'")
os.system("flask db upgrade")

print("✅ Migración completada exitosamente.")
