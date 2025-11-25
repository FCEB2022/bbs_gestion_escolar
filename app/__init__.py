from flask import Flask
from .config import Config
from .extensions import db, migrate, login_manager,csrf
from .usuarios.models import Usuario, Role  # modelos del módulo usuarios
from .models_shared import ActividadUsuario  # modelo compartido de actividad


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)

    # Extensiones
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    # 🔹 login_manager debe apuntar al login del blueprint 'usuarios'
    login_manager.login_view = "usuarios.login"  # ✅ Debe ser "usuarios.login"
    login_manager.login_message_category = "info"

    @login_manager.user_loader
    def load_user(user_id):
        # SQLAlchemy 2.x style
        return db.session.get(Usuario, int(user_id))

    # Blueprints
    from .core import bp as core_bp
    from .usuarios import bp as usuarios_bp
    from .documentos import bp as documentos_bp
    from .cursos import bp as cursos_bp
    from .matriculas import bp as matriculas_bp
    from .pagos import bp as pagos_bp
    from .actas_expedientes import bp as actas_bp
    from .validaciones import bp as validaciones_bp
    from .proyectos import bp as proyectos_bp
    from .estadisticas import bp as estadisticas_bp
    from .perfil import bp as perfil_bp
    from .pagos.models import Pago
    from app.estadisticas import bp as estadisticas_bp



    app.register_blueprint(core_bp)  # dashboard
    app.register_blueprint(usuarios_bp, url_prefix="/usuarios")
    app.register_blueprint(documentos_bp, url_prefix="/documentos")
    app.register_blueprint(cursos_bp, url_prefix="/cursos")
    
    app.register_blueprint(pagos_bp, url_prefix="/pagos")
    app.register_blueprint(actas_bp, url_prefix="/actas-expedientes")
    app.register_blueprint(validaciones_bp, url_prefix="/validaciones")
    app.register_blueprint(proyectos_bp, url_prefix="/proyectos")
    app.register_blueprint(estadisticas_bp, url_prefix='/estadisticas')
    app.register_blueprint(perfil_bp, url_prefix="/perfil")
    app.register_blueprint(matriculas_bp, url_prefix="/admin/matriculas")

  

    # CLI seeds
    from .seed import seed_datos_iniciales
    app.cli.add_command(seed_datos_iniciales)


    # ===== Manejo personalizado de errores =====
    # En caso de 403 (Forbidden) mostramos un mensaje amigable y redirigimos al dashboard
    @app.errorhandler(403)
    def forbidden_error(error):
        from flask import flash, redirect, url_for
        flash("No tienes permisos para acceder a este módulo.", "danger")
        return redirect(url_for("core.dashboard"))

    return app