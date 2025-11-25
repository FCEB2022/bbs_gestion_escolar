from app import create_app
app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
import os

# Determinar ambiente (development, production, testing)
FLASK_ENV = os.getenv("FLASK_ENV", "development")

from app import create_app

if FLASK_ENV == "production":
    from app.config import ProductionConfig
    app = create_app(config_class=ProductionConfig)
elif FLASK_ENV == "testing":
    from app.config import TestingConfig
    app = create_app(config_class=TestingConfig)
else:
    from app.config import DevelopmentConfig
    app = create_app(config_class=DevelopmentConfig)

if __name__ == "__main__":
    # En desarrollo, usar debug mode
    debug_mode = FLASK_ENV == "development"
    app.run(debug=debug_mode, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
