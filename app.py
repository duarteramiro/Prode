import os
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta

app = Flask(__name__)

# Configuración de Base de Datos (Usa SQLite por defecto)
# En el futuro, aquí conectarás PostgreSQL para que no se borren los datos.
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'prode.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- MODELOS DE DATOS ---

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    puntos = db.Column(db.Integer, default=0)
    exactos = db.Column(db.Integer, default=0)
    dif_gol = db.Column(db.Integer, default=0)

class Jugador(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    seleccion = db.Column(db.String(50))
    dorsal = db.Column(db.Integer)
    posicion = db.Column(db.String(20)) # arquero, defensor, mediocampista, delantero

class Partido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    equipo_a = db.Column(db.String(50))
    equipo_b = db.Column(db.String(50))
    fecha_hora = db.Column(db.DateTime)
    fase = db.Column(db.String(20)) # grupos, 8vos, 4tos, semi, 3ro, final
    goles_a_real = db.Column(db.Integer, nullable=True)
    goles_b_real = db.Column(db.Integer, nullable=True)
    quien_pasa_real = db.Column(db.String(50), nullable=True)

class Prediccion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    partido_id = db.Column(db.Integer, db.ForeignKey('partido.id'))
    goles_a_p = db.Column(db.Integer)
    goles_b_p = db.Column(db.Integer)
    dorsal_elegido = db.Column(db.Integer)
    quien_pasa_p = db.Column(db.String(50), nullable=True)

# --- RUTAS ---

@app.route('/')
def index():
    # Esta ruta busca el archivo dentro de la carpeta /templates
    return render_template('index.html')

@app.route('/api/guardar', methods=['POST'])
def guardar():
    data = request.json
    # Lógica de bloqueo de 5 minutos antes (Regla 2)
    partido = Partido.query.get(data['partido_id'])
    if datetime.now() > (partido.fecha_hora - timedelta(minutes=5)):
        return jsonify({"error": "Carga bloqueada: faltan menos de 5 min"}), 403
    
    # Aquí iría la lógica de guardado en DB
    return jsonify({"mensaje": "Pronóstico guardado exitosamente"})

# --- MOTOR DE PUNTOS (Lógica de tus Reglas) ---

def calcular_puntos(pred, real, fase):
    p = 0
    # Regla 5: Puntos por fase
    esquema = {
        'grupos': {'ex': 9, 'df': 6, 'gn': 3, 'z': 14},
        '8vos':   {'ex': 12, 'df': 8, 'gn': 4, 'z': 18},
        '4tos':   {'ex': 15, 'df': 10, 'gn': 5, 'z': 22},
        'semi':   {'ex': 18, 'df': 12, 'gn': 6, 'z': 26},
        '3ro':    {'ex': 21, 'df': 14, 'gn': 7, 'z': 30},
        'final':  {'ex': 30, 'df': 20, 'gn': 10, 'z': 35}
    }
    f = esquema[fase]

    # Regla 6: Caso 0-0
    if pred.goles_a_p == 0 and pred.goles_b_p == 0:
        if real.goles_a_real == 0 and real.goles_b_real == 0:
            p += f['z']
    else:
        # Aciertos normales
        if pred.goles_a_p == real.goles_a_real and pred.goles_b_p == real.goles_b_real:
            p += f['ex']
        elif (pred.goles_a_p - pred.goles_b_p) == (real.goles_a_real - real.goles_b_real):
            p += f['df']
        elif (pred.goles_a_p > pred.goles_b_p and real.goles_a_real > real.goles_b_real) or \
             (pred.goles_a_p < pred.goles_b_p and real.goles_a_real < real.goles_b_real):
            p += f['gn']

    # Regla 7: Quien pasa
    if fase != 'grupos' and pred.goles_a_p == pred.goles_b_p:
        if pred.quien_pasa_p == real.quien_pasa_real:
            p += 3
            
    return p

# Crear la base de datos al arrancar
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    # En Render usamos gunicorn, pero esto permite pruebas locales
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
