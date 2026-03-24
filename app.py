from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///prode_mundial.db'
db = SQLAlchemy(app)

# MODELOS DE BASE DE DATOS
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    puntos = db.Column(db.Integer, default=0)
    exactos = db.Column(db.Integer, default=0)

class Partido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    equipo_a = db.Column(db.String(50))
    equipo_b = db.Column(db.String(50))
    fecha_hora = db.Column(db.DateTime)
    fase = db.Column(db.String(20)) # 'grupos', '8vos', etc.

class Prediccion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    partido_id = db.Column(db.Integer, db.ForeignKey('partido.id'))
    goles_a = db.Column(db.Integer)
    goles_b = db.Column(db.Integer)
    dorsal_jugador = db.Column(db.Integer) # Tu pedido: búsqueda por número

# MOTOR DE CÁLCULO (Regla 2: Bloqueo 5 min antes)
@app.route('/guardar_pronostico', methods=['POST'])
def guardar_pronostico():
    data = request.json
    partido = Partido.query.get(data['partido_id'])
    
    # REGLA 2: Validar tiempo
    limite = partido.fecha_hora - timedelta(minutes=5)
    if datetime.now() > limite:
        return jsonify({"error": "Tiempo agotado para este partido"}), 403
    
    # Guardar en DB...
    return jsonify({"status": "Pronóstico guardado con éxito"})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
