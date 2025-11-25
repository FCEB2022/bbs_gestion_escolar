#!/usr/bin/env python3
"""
Script para crear servicio en Render usando la API REST
"""
import requests
import json
import secrets

API_KEY = 'rnd_1klFurcpQDTJxZCLlBWNArEjmBCq'
BASE_URL = 'https://api.render.com/v1'
HEADERS = {
    'Authorization': f'Bearer {API_KEY}',
    'Content-Type': 'application/json'
}
OWNER_ID = 'tea-d4ikfg15pdvs73820pqg'

# Generar SECRET_KEY
SECRET_KEY = secrets.token_hex(32)
print(f"🔑 SECRET_KEY generada: {SECRET_KEY}\n")

# ===== CREAR WEB SERVICE =====
print("=" * 60)
print("1️⃣  CREANDO WEB SERVICE")
print("=" * 60)

web_payload = {
    'ownerId': OWNER_ID,
    'name': 'bbs-gestion-escolar',
    'type': 'web_service',
    'runtime': 'python',
    'serviceDetails': {
        'repo': 'https://github.com/FCEB2022/bbs_gestion_escolar.git',
        'branch': 'main',
        'buildCommand': 'pip install -r requirements.txt',
        'startCommand': 'gunicorn wsgi:app --timeout 60',
        'preDeployCommand': 'flask db upgrade && flask seed-datos-iniciales'
    },
    'envVars': [
        {'key': 'FLASK_ENV', 'value': 'production'},
        {'key': 'SECRET_KEY', 'value': SECRET_KEY},
        {'key': 'PYTHONUNBUFFERED', 'value': 'True'},
        {'key': 'PORT', 'value': '5000'}
    ],
    'plan': 'free',
    'region': 'frankfurt',
    'disk': [
        {
            'name': 'uploads',
            'sizeGb': 1,
            'mountPath': '/var/data/uploads'
        }
    ]
}

try:
    web_response = requests.post(
        f'{BASE_URL}/services',
        headers=HEADERS,
        json=web_payload,
        timeout=30
    )
    
    print(f"📍 Status: {web_response.status_code}")
    
    if web_response.status_code in (200, 201):
        web_data = web_response.json()
        service_id = web_data.get('id')
        service_name = web_data.get('name')
        print(f"✅ Web Service creado exitosamente")
        print(f"   ID: {service_id}")
        print(f"   Nombre: {service_name}")
        print(f"   Rama: {web_data.get('branch')}")
        print(f"   Plan: {web_data.get('plan')}")
        print(f"   Región: {web_data.get('region')}")
    else:
        print(f"❌ Error creando servicio web:")
        print(web_response.text)
        
except Exception as e:
    print(f"❌ Error en la solicitud: {e}")

print("\n" + "=" * 60)
print("✨ PRÓXIMOS PASOS:")
print("=" * 60)
print("1. Ir a: https://dashboard.render.com")
print("2. Ver el estado de despliegue en 'bbs-gestion-escolar'")
print("3. Esperar a que compile e inicie (5-10 minutos)")
print("4. La URL pública aparecerá en el dashboard")
print("5. Notas importantes guardadas en DEPLOYMENT_COMPLETE.md")
print("=" * 60)
