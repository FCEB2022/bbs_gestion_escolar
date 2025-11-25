from app import create_app
app = create_app()
import os

# Usar ProductionConfig si FLASK_ENV es production
FLASK_ENV = os.getenv("FLASK_ENV", "development")

if FLASK_ENV == "production":
	from app.config import ProductionConfig
	app = create_app(config_class=ProductionConfig)
else:
	app = create_app()
