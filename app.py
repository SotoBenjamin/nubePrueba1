#!/usr/bin/env python3
# -*-coding:utf-8 -*-
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dataclasses import dataclass
from datetime import date
from flask_cors import CORS
from flask import render_template, jsonify, request, redirect, url_for, flash, session
import base64
from datetime import datetime
from sqlalchemy import and_

app = Flask(__name__)
CORS(app, supports_credentials=True)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'my_secret_key'

app.config['SESSION_TYPE'] = 'filesystem'

db = SQLAlchemy(app)



@dataclass
class User(db.Model):
    id: int
    username: str
    email: str
    firstname: str
    lastname: str
    fechaNac: str
    pais: str
    password: str
    wallet : float


    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    firstname = db.Column(db.String(80), nullable=False)
    lastname = db.Column(db.String(80), nullable=False)
    fechaNac = db.Column(db.String(10), nullable=False)
    pais = db.Column(db.String(80), nullable=False)
    password = db.Column(db.String(80), nullable=False)
    wallet = db.Column(db.Float)
    comentarios = db.relationship('Comentario', backref='user_a', lazy=True)
    compras_user = db.relationship('Compra', backref='user_b', lazy=True)
    profile_picture = db.relationship('User_pfp', backref='user_image', lazy=True)

    def __init__(self, username, email, firstname, lastname, fechaNac, pais, password , wallet):
        self.username = username
        self.email = email
        self.firstname = firstname
        self.lastname = lastname
        self.fechaNac = fechaNac
        self.pais = pais
        self.password = password
        self.wallet= wallet

    def __repr__(self):
        return f'<User {self.username}>'

@dataclass
class User_pfp(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    size = db.Column(db.Integer)
    data = db.Column(db.LargeBinary)
    user_id= db.Column(db.Integer , db.ForeignKey('user.id', ondelete="CASCADE") , nullable= False )
    def __repr__(self):
        return f"Image('{self.name}', '{self.size}', '{self.uploaded_at}')"




@dataclass
class Autor(db.Model):
    id: int
    firstname: str
    lastname: str
    fechaNac: date

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    firstname = db.Column(db.String(80), nullable=False)
    lastname = db.Column(db.String(80), nullable=False)
    fechaNac = db.Column(db.Date, nullable=False)

    mangas = db.relationship('Manga', backref='autor', lazy=True)

    def __repr__(self):
        return f'<Autor {self.id}>'


@dataclass
class Manga(db.Model):
    id: int
    nombre: str
    edicion: int
    cant_stock: int
    genero: str
    autor_id: int
    precio: float
    link: str

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    edicion = db.Column(db.Integer, nullable=False)
    cant_stock = db.Column(db.Integer, nullable=False)
    genero = db.Column(db.String(100), nullable=False)
    precio = db.Column(db.Float, nullable=False)
    link = db.Column(db.String(500), nullable=False, unique=True)
    autor_id = db.Column(db.Integer, db.ForeignKey('autor.id'))

    __table_args__ = (db.UniqueConstraint('nombre', 'edicion', name='identificadorManga'),)

    comentarios_m = db.relationship('Comentario', backref='manga', lazy=True,
                                    primaryjoin="and_(Manga.nombre == Comentario.manga_nombre, Manga.edicion == Comentario.manga_edicion)",
                                    foreign_keys="[Comentario.manga_nombre, Comentario.manga_edicion]")
    compras_manga = db.relationship('Compra', backref='manga', lazy=True,
                                    primaryjoin="and_(Manga.nombre == Compra.manga_nombre, Manga.edicion == Compra.manga_edicion)",
                                    foreign_keys="[Compra.manga_nombre, Compra.manga_edicion]")

    def __repr__(self):
        return f'<Manga {self.id},{self.nombre}, {self.edicion}>'


@dataclass
class Comentario(db.Model):
    id: int
    contenido: str
    user_id: int
    manga_nombre: str
    manga_edicion: int
    id = db.Column(db.Integer, primary_key=True)
    contenido = db.Column(db.String(1000), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    manga_nombre = db.Column(db.String(100), db.ForeignKey('manga.nombre', ondelete="CASCADE"), nullable=False)
    manga_edicion = db.Column(db.Integer, db.ForeignKey('manga.edicion', ondelete="CASCADE"), nullable=False)

    def __repr__(self):
        return f'<Comentario {self.contenido}>'


@dataclass
class Compra(db.Model):
    id: int
    id_user: int
    manga_nombre: str
    manga_edicion: int
    fecha: date

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_user = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    manga_nombre = db.Column(db.String(100), db.ForeignKey('manga.nombre', ondelete="CASCADE"), nullable=False)
    manga_edicion = db.Column(db.Integer, db.ForeignKey('manga.edicion', ondelete="CASCADE"), nullable=False)
    fecha = db.Column(db.Date, nullable=False)




userCache = {}

with app.app_context():
    db.create_all()

app.app_context().push()


@app.route('/upload/<user_id>', methods=['POST'])
def upload(user_id):
    if request.method == 'POST':
        file = request.files['image']

        # Procesar el archivo y extraer información
        file_data = file.read()
        file_name = file.filename
        file_size = len(file_data)

        # Crear una nueva instancia de User_pfp
        user_pfp = User_pfp(
            name=file_name,
            size=file_size,
            data=file_data,
            user_id=user_id  # ID del usuario asociado, debes proporcionar el ID correcto aquí
        )
        # Agregar la instancia a la sesión y realizar la inserción en la base de datos
        db.session.add(user_pfp)
        db.session.commit()

        return 'SUCCESS'



@app.route('/image/<user_id>', methods=['GET'])
def get_image_data(user_id):
    image_data = User_pfp.query.filter_by(user_id=user_id).first()
    if image_data:
        image_data_dict = {
            'id': image_data.id,
            'name': image_data.name,
            'size': image_data.size,
            'data': base64.b64encode(image_data.data).decode('utf-8'),
            'user_id': image_data.user_id
        }
        return jsonify(image_data_dict)
    else:
        return jsonify(error='Image not found'), 404


@app.route('/signup', methods=['POST'])
def signup():
    username = request.json.get("username")
    email = request.json.get("email")
    firstname = request.json.get("firstname")
    lastname = request.json.get("lastname")
    fechaNac = request.json.get("fechaNac")
    pais = request.json.get("pais")
    password = request.json.get("password")

    user_exists = User.query.filter_by(email=email).first() is not None

    if user_exists:
        return jsonify({"error": "El correo electrónico ya está en uso"}), 409

    new_user = User(username=username, email=email, firstname=firstname, lastname=lastname, fechaNac=fechaNac,
                    pais=pais, password=password)

    db.session.commit()

    return jsonify({
        "id": new_user.id,
        "username": new_user.username,
        "email": new_user.email,
        "firstname": new_user.firstname,
        "lastname": new_user.lastname,
        "fechaNac": new_user.fechaNac,
        "pais": new_user.pais,
        "password": new_user.password
    })


@app.route("/login", methods=["POST"])
def login_user():
    email = request.json["email"]
    password = request.json["password"]

    global userCache

    if (email in userCache.keys()):
        user = {
            "id": userCache[email]["id"],
            "username": userCache[email]["username"],
            "email": userCache[email]["email"],
            "firstname": userCache[email]["firstname"],
            "lastname": userCache[email]["lastname"],
            "fechaNac": userCache[email]["fechaNac"],
            "pais": userCache[email]["pais"],
            "password": userCache[email]["password"],
            "wallet": userCache[email]["wallet"]
        }

        if user is None:
            return jsonify({"error": "Unauthorized Access"}), 401

        if not (password == user["password"]):
            return jsonify({"error": "Unauthorized"}), 401

        print(userCache)
        return jsonify({
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "firstname": user["firstname"],
            "lastname": user["lastname"],
            "fechaNac": user["fechaNac"],
            "pais": user["pais"],
            "wallet": user["wallet"]
        })


    else:
        user = User.query.filter_by(email=email).first()

        if user is None:
            return jsonify({"error": "Unauthorized Access"}), 401

        if not (password == user.password):
            return jsonify({"error": "Unauthorized"}), 401

        userCache.update({
            email: {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "firstname": user.firstname,
                "lastname": user.lastname,
                "fechaNac": user.fechaNac,
                "pais": user.pais,
                "password": user.password,
                "wallet": user.wallet
            }
        })
        print(userCache)
        return jsonify({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "firstname": user.firstname,
            "lastname": user.lastname,
            "fechaNac": user.fechaNac,
            "pais": user.pais,
            "wallet": user.wallet
        })


@app.route('/users', methods=['GET', 'POST'])
def route_users():
    if request.method == 'GET':
        users = User.query.all()
        return jsonify(users)

    elif request.method == 'POST':
        data = request.get_json()
        fecha_nac_string = data['fechaNac']
        fecha_nac = datetime.strptime(fecha_nac_string, '%Y-%m-%d').date()
        new_user = User(username=data['username'], email=data['email'], firstname=data['firstname'],
                        lastname=data['lastname'], fechaNac=fecha_nac, pais=data['pais'], password=data['password'])
        db.session.add(new_user)
        db.session.commit()
        return 'SUCCESS'


@app.route('/users/<users_id>', methods=['GET', 'PUT', 'DELETE'])
def route_user_id(users_id):
    global userCache

    if request.method == 'GET':
        user = User.query.get_or_404(users_id)
        return jsonify(user)

    elif request.method == 'PUT':
        data = request.get_json()
        current_user = User.query.get_or_404(users_id)
        fecha_nac_string = data['fechaNac']
        fecha_nac = datetime.strptime(fecha_nac_string, '%Y-%m-%d').date()

        if current_user.email in userCache.keys():
            del userCache[current_user.email]

        current_user.username = data['username']
        current_user.email = data['email']
        current_user.firstname = data['firstname']
        current_user.lastname = data['lastname']
        current_user.fechaNac = fecha_nac
        current_user.pais = data['pais']
        current_user.wallet = data['wallet']

        db.session.commit()
        user=User.query.get_or_404(users_id)
        return jsonify(user)

    elif request.method == 'DELETE':
        user = User.query.get_or_404(users_id)
        db.session.delete(user)
        db.session.commit()
        return 'SUCCESS'


@app.route('/autor', methods=['GET', 'POST'])
def route_autor():
    if request.method == 'GET':
        autores = Autor.query.all()
        return jsonify(autores)
    elif request.method == 'POST':
        data = request.get_json()
        string_fec = data['fechaNac']
        fecha = datetime.strptime(string_fec, '%Y-%m-%d').date()
        new_autor = Autor(firstname=data['firstname'], lastname=data['lastname'], fechaNac=fecha)
        db.session.add(new_autor)
        db.session.commit()
        return 'SUCCESS'


@app.route('/autor/<autor_id>', methods=['GET', 'PUT', 'DELETE'])
def route_autor_id(autor_id):
    if request.method == 'GET':
        autor = Autor.query.get_or_404(autor_id)
        return jsonify(autor)
    elif request.method == 'PUT':
        data = request.get_json()
        autor = Autor.query.get_or_404(autor_id)
        string_fec = data['fechaNac']
        fecha = datetime.strptime(string_fec, '%Y-%m-%d').date()
        autor.firstname = data['firstname']
        autor.lastname = data['lastname']
        autor.fechaNac = fecha
        db.session.commit()
        return 'SUCCESS'


@app.route('/manga', methods=['GET', 'POST'])
def route_manga():
    if request.method == 'GET':
        mangas = Manga.query.all()
        return jsonify(mangas)


    elif request.method == 'POST':
        data = request.get_json()
        new_manga = Manga(nombre=data['nombre'], edicion=data['edicion'], cant_stock=data['cant_stock'],
                          genero=data['genero'], autor_id=data['autor_id'], precio=data['precio'], link=data['link'])

        db.session.add(new_manga)
        db.session.commit()
        return 'SUCCESS'


@app.route('/manga/by/<genre>', methods=['GET'])
def route_manga_by_genre(genre):
    manga = Manga.query.filter_by(genero=genre).all()
    return jsonify(manga)


@app.route('/manga/byn/<name>', methods=['GET'])
def route_manga_by_name(name):
    manga = Manga.query.filter_by(nombre=name).all()
    return jsonify(manga)


@app.route('/manga/<manga_id>', methods=['GET', 'PUT', 'DELETE'])
def route_manga_id(manga_id):

    if request.method == 'GET':
        manga = Manga.query.get_or_404(manga_id)
        return jsonify(manga)

    elif request.method == 'PUT':
        data = request.get_json()
        current_manga = Manga.query.get_or_404(manga_id)
        current_manga.nombre = data['nombre']
        current_manga.edicion = data['edicion']
        current_manga.cant_stock = data['cant_stock']
        current_manga.genero = data['genero']
        current_manga.autor_id = data['autor_id']
        current_manga.precio = data['precio']
        current_manga.link = data['link']
        db.session.commit()
        return 'SUCCESS'

    elif request.method == 'DELETE':
        manga = Manga.query.get_or_404(manga_id)
        db.session.delete(manga)
        db.session.commit()
        return 'SUCCESS'


@app.route('/comentario', methods=['GET', 'POST'])
def route_comentario():
    if request.method == 'GET':
        comentarios = Comentario.query.all()
        return jsonify(comentarios)
    elif request.method == 'POST':
        data = request.get_json()
        new_comentario = Comentario(contenido=data['contenido'], user_id=data['user_id'],
                                    manga_nombre=data['manga_nombre'], manga_edicion=data['manga_edicion'])
        db.session.add(new_comentario)
        db.session.commit()
        return 'SUCCESS'





@app.route('/comentario/by/<manga_id>', methods=['GET'])
def route_comentario_name(manga_id):
    manga = Manga.query.get_or_404(manga_id)
    comentarios = Comentario.query.filter(
        and_(Comentario.manga_nombre == manga.nombre, Comentario.manga_edicion == manga.edicion)).all()
    return jsonify(comentarios)


@app.route('/comentario/<comentario_id>', methods=['GET', 'PUT', 'DELETE'])
def route_comentario_id(comentario_id):
    if request.method == 'GET':
        comentario = Comentario.query.get_or_404(comentario_id)
        return jsonify(comentario)
    elif request.method == 'PUT':
        data = request.get_json()
        current_comentario = Comentario.query.get_or_404(comentario_id)
        current_comentario.contenido = data['contenido']
        current_comentario.user_id = data['user_id']
        current_comentario.manga_nombre = data['manga_nombre']
        current_comentario.manga_edicion = data['manga_edicion']
        db.session.commit()
        return 'SUCCESS'
    elif request.method == 'DELETE':
        comentario = Comentario.query.get_or_404(comentario_id)
        db.session.delete(comentario)
        db.session.commit()
        return 'SUCCESS'


@app.route('/compra', methods=['GET', 'POST'])
def route_compra():
    if request.method == 'GET':
        compras = Compra.query.all()
        return jsonify(compras)
    elif request.method == 'POST':
        data = request.get_json()
        fecha_string = data['fecha']
        fecha = datetime.strptime(fecha_string, '%Y-%m-%d').date()
        id_usuario = data['id_user']
        manga_nombre = data['manga_nombre']
        manga_edicion = data['manga_edicion']
        new_compra = Compra(id_user=data['id_user'], manga_nombre=data['manga_nombre'],
                            manga_edicion=data['manga_edicion'], fecha=fecha)
        db.session.add(new_compra)
        db.session.commit()
        return 'SUCCESS'


@app.route('/compra/<compra_id>', methods=['GET', 'PUT', 'DELETE'])
def route_compra_id(compra_id):
    if request.method == 'GET':
        compra = Compra.query.get_or_404(compra_id)
        return jsonify(compra)
    elif request.method == 'PUT':
        data = request.get_json()
        current_compra = Compra.query.get_or_404(compra_id)
        current_compra.id_user = data['id_user']
        current_compra.manga_nombre = data['manga_nombre']
        current_compra.manga_edicion = data['manga_edicion']
        current_compra.fecha = datetime.strptime(data['fecha'], '%Y-%m-%d').date()
        db.session.commit()
        return 'SUCCESS'
    elif request.method == 'DELETE':
        compra = Compra.query.get_or_404(compra_id)
        db.session.delete(compra)
        db.session.commit()
        return 'SUCCESS'

@app.route('/compraUser/<user_id>', methods= ["GET"])
def get_compras_by_user_id(user_id):
    if request.method == 'GET':
        compras = Compra.query.filter_by(id_user = user_id).all()
        return jsonify(compras)


