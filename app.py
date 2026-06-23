from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)

base_dir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(base_dir, 'quimica.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'clave_quimica'

db = SQLAlchemy(app)

class Alumno(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    id_acceso = db.Column(db.String(20), unique=True, nullable=False)
    respuestas = db.relationship('Respuesta', backref='alumno', lazy=True)

class Respuesta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    puntos = db.Column(db.Integer)
    tema = db.Column(db.String(200))
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    alumno_id = db.Column(db.Integer, db.ForeignKey('alumno.id'), nullable=False)

@app.route('/')
def index():
    return redirect(url_for('profesor_panel'))

@app.route('/profesor')
def profesor_panel():
    alumnos = Alumno.query.all()
    for a in alumnos:
        a.total = sum(r.puntos for r in a.respuestas)
    return render_template('profesor.html', alumnos=alumnos)

@app.route('/add_alumno', methods=['POST'])
def add_alumno():
    nombre = request.form.get('nombre')
    id_acceso = request.form.get('id_acceso')
    if nombre and id_acceso:
        nuevo = Alumno(nombre=nombre, id_acceso=id_acceso)
        db.session.add(nuevo)
        db.session.commit()
    return redirect(url_for('profesor_panel'))

# RUTA CORREGIDA: Acepta ambos métodos para evitar el 404
@app.route('/puntuar', methods=['GET', 'POST'])
def puntuar():
    if request.method == 'POST':
        alumno_id = request.form.get('alumno_id')
        puntos = request.form.get('puntos')
        tema = request.form.get('tema')
        
        if alumno_id and puntos:
            nueva_res = Respuesta(puntos=int(puntos), tema=tema, alumno_id=int(alumno_id))
            db.session.add(nueva_res)
            db.session.commit()
    return redirect(url_for('profesor_panel'))

@app.route('/alumno/<id_acceso>')
def alumno_panel(id_acceso):
    alumno = Alumno.query.filter_by(id_acceso=id_acceso).first_or_404()
    total_puntos = sum(r.puntos for r in alumno.respuestas)
    return render_template('alumno.html', alumno=alumno, total=total_puntos)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)