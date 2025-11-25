import os

EXCLUDE_EXT = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.txt', '.sql', '.pyc'}
EXCLUDE_DIRS = {'.venv', 'venv', 'env', '__pycache__', '.git', 'instance'}
INCLUDE_EXT = {'.py', '.html', '.css', '.js'}

OUTPUT_FILE = "export_codigo_sistema.txt"

def debe_incluir(ruta):
    base = os.path.basename(ruta)
    if base.startswith('.') or base == '.env':
        return False
    ext = os.path.splitext(ruta)[1].lower()
    if ext in EXCLUDE_EXT:
        return False
    return ext in INCLUDE_EXT

def exportar_codigo():
    with open(OUTPUT_FILE, "w", encoding="utf-8") as salida:
        salida.write("=== EXPORTACIÓN COMPLETA DEL CÓDIGO DEL SISTEMA ===\n\n")
        for carpeta, subdirs, archivos in os.walk('.'):
            subdirs[:] = [d for d in subdirs if d not in EXCLUDE_DIRS]
            for archivo in archivos:
                ruta = os.path.join(carpeta, archivo)
                if debe_incluir(ruta):
                    try:
                        with open(ruta, "r", encoding="utf-8") as f:
                            contenido = f.read()
                        salida.write(f"\n{'='*80}\n")
                        salida.write(f"📁 Archivo: {ruta}\n")
                        salida.write(f"{'='*80}\n\n")
                        salida.write(contenido)
                        salida.write("\n\n")
                    except Exception as e:
                        salida.write(f"\n[ERROR al leer {ruta}: {e}]\n")
        salida.write("\n=== FIN DE EXPORTACIÓN ===\n")

    print(f"✅ Exportación completada: {OUTPUT_FILE}")

if __name__ == "__main__":
    exportar_codigo()
