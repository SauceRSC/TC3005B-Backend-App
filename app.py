#Importar lo que necesitamos
from flask import Flask, jsonify
from markupsafe import escape
from flask_db2 import DB2
from flask_cors import CORS
from sqlalchemy import *
from flask_login import LoginManager

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

#Se crea la ruta por defecto 
@app.route("/")
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

#Se crea la ruta con metodo GET y que recibe una variable en el url ID
@app.route("/getData/<int:ID>", methods=["GET"])
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