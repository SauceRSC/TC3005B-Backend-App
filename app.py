#Importar lo que necesitamos

from flask import *
from markupsafe import escape
from flask_db2 import DB2
from flask_cors import CORS, cross_origin
from sqlalchemy import *
import flask_login
import secrets
from argon2 import PasswordHasher
import time
import flask
import sys

#Crear objeto Flask y correr en modo debug
app = Flask(__name__)

# APLICAR CONFIG DE DB2
app.config['DB2_DATABASE'] = 'testdb'
app.config['DB2_HOSTNAME'] = 'localhost'
app.config['DB2_PORT'] = 50000
app.config['DB2_PROTOCOL'] = 'TCPIP'
app.config['DB2_USER'] = 'db2inst1'
app.config['DB2_PASSWORD'] = 'hola'

#Hacer conexion con db
db = DB2(app)

#CORS para que nos permita hacer los fetch desde el front
CORS(app)

#Se crea la llave secreta para el login
app.secret_key = secrets.token_urlsafe(16)
login_manager = flask_login.LoginManager()
login_manager.init_app(app)
VIDA_TOKEN = 1000 * 60 * 3

#Clase de usuario que usa la libreria
class Usuario(flask_login.UserMixin):
    pass

# método que se invoca para obtención de usuarios cuando se hace request
@login_manager.request_loader
def request_loader(request):
    # obtener información que nos mandan en encabezado
    key = request.headers.get('Authorization')

    if key == ":" or not key:
        return None

    processed = key.split(":")

    # recibimos token de encabezado
    usuario = processed[0]
    token = processed[1]

    # verificamos que usuario exista
    cur = db.connection.cursor()

    query = "SELECT * FROM users WHERE email=?"
    params = (usuario, )

    cur.execute(query, params)
    data = cur.fetchone()
    cur.close()

    if(not data):
        return None

    # verificamos que tenga token válido
    ph = PasswordHasher()

    try:
        ph.verify(data[3], token)
    except:
        return None    

    # verificamos que el token siga vigente
    timestamp_actual = time.time()

    if(data[4] + VIDA_TOKEN < timestamp_actual):
        return None

    # actualizar vigencia del token 
    cur = db.connection.cursor()
    query = "UPDATE users SET last_date=? WHERE email=?"
    params = (timestamp_actual, usuario)
    cur.execute(query, params)
    cur.close()

    # regresamos objeto si hubo Y token valido 
    result = Usuario()
    result.id = usuario
    result.nombre = "Memo"
    result.apellido = "Rivas"
    return result

#metodo que se invoca cuando se intenta acceder a algo sin autorizacion
@login_manager.unauthorized_handler
def handler():
    return 'No autorizado', 401

#metodo con la logica para iniciar sesion con los datos del formulario
@app.route('/login', methods=['POST'])
def login():
    
    # intro al password hasher
    ph = PasswordHasher()

    email = flask.request.form['email']
    print(email, file=sys.stdout)

    # 1. verificar existencia de usuario
    cur = db.connection.cursor()

    query = "SELECT * FROM users WHERE email=?"

    params = (email, )

    cur.execute(query, params)
    data = cur.fetchone()
    cur.close()
    print(data, file=sys.stdout)
    if(data == None):
        return "USUARIO NO VALIDO", 401

    # 2. verificar validez de password
    try:
        ph.verify(data[2], flask.request.form['pass'])
    except:
        # 3. password invalido - no login
        return "PASSWORD NO VALIDO", 401

    # 4. password valido - actualizar token y regresarlo
    token = secrets.token_urlsafe(32)
    # así se obtiene el timestamp del momento actual
    last_date = time.time()
    
    # 5. actualizar BD con entrada de usuario
    cur = db.connection.cursor()
    query = "UPDATE users SET token=?, last_date=? WHERE email=?"
    params = (ph.hash(token), last_date, email)
    cur.execute(query, params)
    cur.close()
    result = Usuario()
    result.id = email
    result.nombre = "Memo"
    result.apellido = "Rivas"
    flask_login.login_user(result)
    return jsonify(token=token, caducidad=VIDA_TOKEN), 200

#funcion con la logica para hacer el logout
@app.route('/logout')
@cross_origin()
@flask_login.login_required
def logout():
    cur = db.connection.cursor()
    query = "UPDATE users SET last_date=? WHERE email=?"
    params = (0, flask_login.current_user.id)
    cur.execute(query, params)
    cur.close()
    flask_login.logout_user()
    return 'saliste', 200

#Se crea la ruta por defecto que requiere autenticacion
@app.route("/")
@flask_login.login_required
@cross_origin()
def servicio_default():
    cur = db.connection.cursor()

    # con cursor hecho podemos ejecutar queries
    cur.execute("SELECT * FROM tarjetas")

    # obtenemos datos
    data = cur.fetchall()

    # acuerdate de cerrar el cursor
    cur.close()

    # Se hace objeto json de los datos que nos arroja la query
    resultado = []
    for current in data:
        actual = {
            "id" : current[0],
            "texto" : current[1],
            "name" : current[2]
        }
        resultado.append(actual)

    #se regresa el objeto como json
    return jsonify(resultado)

#Se crea la ruta con metodo GET y que recibe una variable en el url ID, se requiere de autenticacion
@app.route("/getData/<int:ID>", methods=["GET"])
@flask_login.login_required
@cross_origin()
def getByID(ID):
    cur = db.connection.cursor()
    # con cursor hecho podemos ejecutar queries
    cur.execute(f"SELECT * FROM tarjetas WHERE id={escape(ID)};")

    # obtenemos datos
    data = cur.fetchall()

    # acuerdate de cerrar el cursor
    cur.close()

    # Se hace objeto json de los datos que nos arroja la query
    resultado = []
    for current in data:
        actual = {
            "id" : current[0],
            "texto" : current[1],
            "name" : current[2]
        }
        resultado.append(actual)

    #se regresa el objeto como json
    return jsonify(resultado)