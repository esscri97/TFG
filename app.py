from flask import Flask, render_template, url_for, request, session, redirect, flash
import os
from werkzeug.utils import secure_filename
import requests
import bcrypt
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)

# Cargar variables de entorno
load_dotenv()

# Configuración de la base de datos PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'secret'
# Inicializar la extensión SQLAlchemy
db = SQLAlchemy(app)

# Definir el modelo de usuario
class User(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(155), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.String(100), nullable=False)


# Define el modelo de producto
class Producto(db.Model):
    __tablename__ = 'productos'
    id_producto = db.Column(db.Integer, primary_key=True)
    id_edicion = db.Column(db.Integer, db.ForeignKey('ediciones.id_edicion'), nullable=False)
    nombre = db.Column(db.String(255), nullable=False)
    imagen = db.Column(db.String(500), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    descripcion = db.Column(db.String(500), nullable=False)
    precio = db.Column(db.Float, nullable=False)

    def to_dict(self):
        return {
            'id_producto': self.id_producto,
            'id_edicion': self.id_edicion,
            'nombre': self.nombre,
            'imagen': self.imagen,
            'cantidad': self.cantidad,
            'descripcion': self.descripcion,
            'precio': self.precio
        }

    def restar_cantidad(self, cantidad_comprada):
        if self.cantidad >= cantidad_comprada:
            self.cantidad -= cantidad_comprada
        else:
            raise ValueError('No hay suficiente stock del producto.')

class Edition(db.Model):
    __tablename__ = 'ediciones'
    id_edicion = db.Column(db.Integer, primary_key=True)
    anyo = db.Column(db.Integer, nullable=False)
    products = db.relationship('Producto', backref='edicion', lazy=True)

class Peticion(db.Model):
    __tablename__ = 'peticiones'
    id_peticion = db.Column(db.Integer, primary_key=True)
    id_edicion = db.Column(db.Integer, nullable=False)
    nombre = db.Column(db.String(255), nullable=False)
    aka = db.Column(db.String(255), nullable=False)
    telefono = db.Column(db.Integer, nullable=False)
    tipo = db.Column(db.String(50), nullable=False)

# Configuración para subir archivos
UPLOAD_FOLDER = 'static/images/productos'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')

@app.route('/aboutus', methods=['GET'])
def aboutus():
    return render_template('aboutus.html')

# Login de usuarios
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()

        if user is not None and bcrypt.checkpw(password.encode(), user.password.encode()):
            session['email'] = email
            session['nombre'] = user.nombre  # Aquí corregimos el atributo a 'nombre'
            session['rol'] = user.rol
            return redirect(url_for('home'))
        else:
            return render_template('login.html', message='Las credenciales no son correctas')
    elif request.method == 'GET':
        return render_template('login.html')

# Registro de Usuarios
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        rol = request.form['rol']
        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

        if name and email and password:
            user = User(nombre=name, email=email, password=hashed_password.decode(), rol=rol)
            db.session.add(user)
            db.session.commit()

        return redirect(url_for('login'))
    elif request.method == 'GET':
        return render_template('register.html')

# Ruta para cerrar sesión
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# Define la ruta para manejar la búsqueda de artistas
@app.route('/artistas', methods=['POST', 'GET'])
def buscar_artista():
    if request.method == 'POST':
        nombre_artista = request.form['nombre_artista']
        info_artista = obtener_informacion_artista(nombre_artista)
        if info_artista:
            return render_template('resultado_artista.html', info_artista=info_artista)
        else:
            return render_template('artistas.html', error='Artista no encontrado.')
    elif request.method == 'GET':
        return render_template('artistas.html')

def obtener_informacion_artista(nombre_artista):
    client_id = '00c2a60a76ac41f39d30afefccc5ddf2'
    client_secret = '797983182a9f4160b34c98d69eca0b2c'
    
    auth_response = requests.post('https://accounts.spotify.com/api/token', {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
    })
    
    if auth_response.status_code != 200:
        print("Error de autenticación:", auth_response.text)
        return None
    
    access_token = auth_response.json().get('access_token')
    
    if not access_token:
        print("No se pudo obtener el token de acceso.")
        return None
    
    headers = {'Authorization': f'Bearer {access_token}'}
    
    response = requests.get('https://api.spotify.com/v1/search', 
                            headers=headers, 
                            params={'q': nombre_artista, 'type': 'artist'})
    
    if response.status_code != 200:
        print("Error en la solicitud de búsqueda:", response.text)
        return None
    
    data = response.json()
    if 'artists' not in data or not data['artists']['items']:
        return None
    
    artist_info = data['artists']['items'][0]
    return artist_info

@app.route('/edicion1')
def edicion1():
    return render_template('edicion1.html')

@app.route('/edicion2')
def edicion2():
    return render_template('edicion2.html')

@app.route('/edicion3', methods=['POST', 'GET'])
def edicion3():
    if request.method == 'GET':
        return render_template('edicion3.html')
    elif request.method == 'POST':
        nombre = request.form['nombre']
        tipoArtista = request.form['tipoArtista']
        aka = request.form['aka']
        telefono = request.form['telefono']

        if not nombre or not tipoArtista or not aka or not telefono:
            flash('Por favor, complete todos los campos.', 'error')
            return redirect('/edicion3')

        try:
            peticion = Peticion(id_edicion=4, nombre=nombre, aka=aka, telefono=telefono, tipo=tipoArtista)
            db.session.add(peticion)
            db.session.commit()
            flash('Gracias por tu solicitud. ¡Nos pondremos en contacto contigo pronto!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Hubo un error al enviar tu solicitud. Por favor, inténtalo de nuevo.', 'error')
            app.logger.error(f"Error al insertar en la base de datos: {str(e)}")
        finally:
            db.session.close()
        
        return redirect('/edicion3')

@app.route('/contacto', methods=['GET', 'POST'])
def contacto():
    if request.method == 'POST':
        return redirect('https://formspree.io/allorofestival@gmail.com')
    else:
        return render_template('contacto.html')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/merchandising', methods=['GET', 'POST'])
def merchandising():
    if request.method == 'POST':
        edicion = request.form['id_edicion']
        nombre = request.form['nombre']
        cantidad = request.form['cantidad']
        descripcion = request.form['descripcion']
        precio = request.form['precio']

        if 'imagen' not in request.files:
            flash('No se proporcionó ninguna imagen', 'error')
            return redirect(request.url)
        
        imagen = request.files['imagen']
        if imagen.filename == '':
            flash('No se seleccionó ningún archivo', 'error')
            return redirect(request.url)
        if imagen and allowed_file(imagen.filename):
            filename = secure_filename(imagen.filename)
            imagen.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            imagen_url = filename
        else:
            flash('Formato de archivo no permitido', 'error')
            return redirect(request.url)
        
        # Continuar con el resto de la lógica para insertar el producto en la base de datos
        producto = Producto(id_edicion=edicion, nombre=nombre, imagen=imagen_url, cantidad=cantidad, descripcion=descripcion, precio=precio)
        db.session.add(producto)
        db.session.commit()
        
        return redirect(url_for('merchandising'))
    
    elif request.method == 'GET':
        if 'rol' in session and session['rol'] == 'admin':
            productos = Producto.query.all()
            print(productos)
            return render_template('crud_merchan.html', productos=productos)
        else:
            productos = Producto.query.all()
            return render_template('merchandising.html', productos=productos)


@app.route('/producto/<int:producto_id>', methods=['GET', 'POST'])
def producto(producto_id):
    producto = Producto.query.get_or_404(producto_id)

    if request.method == 'POST':
        cantidad = int(request.form['cantidad'])
        talla = request.form.get('talla', 'S')
        item = {'producto_id': producto_id, 'cantidad': cantidad, 'talla': talla}
        carrito = session.get('carrito', [])
        carrito.append(item)
        session['carrito'] = carrito
        flash('Producto añadido al carrito.', 'success')
        return redirect(url_for('ver_carrito'))

    return render_template('producto.html', product=producto)

@app.route('/carrito')
def ver_carrito():
    carrito = session.get('carrito', [])
    productos_en_carrito = []
    total = 0
    for item in carrito:
        producto = Producto.query.get_or_404(item['producto_id'])
        subtotal = float(producto.precio) * float(item['cantidad'])
        total += subtotal
        productos_en_carrito.append({'producto': producto, 'cantidad': item['cantidad'], 'subtotal': subtotal})
    return render_template('carrito.html', carrito=productos_en_carrito, total=total)


@app.route('/vaciar_carrito', methods=['POST'])
def vaciar_carrito():
    session.pop('carrito', None)
    session.modified = True  # Asegurarse de que la sesión se guarde
    flash('El carrito ha sido vaciado.', 'success')
    return redirect(url_for('ver_carrito'))


@app.route('/eliminar_del_carrito', methods=['POST'])
def eliminar_del_carrito():
    productos_a_eliminar = request.form.getlist('productos_a_eliminar')
    if 'carrito' in session:
        session['carrito'] = [producto for i, producto in enumerate(session['carrito']) if str(i) not in productos_a_eliminar]
        session.modified = True  # Asegurarse de que la sesión se guarde
        flash('Producto(s) eliminado(s) del carrito.', 'success')
    return redirect(url_for('ver_carrito'))


@app.route('/merchandising/edit/<int:id>', methods=['POST'])
def edit_product(id):
    producto = Producto.query.get_or_404(id)
    edicion = request.form['id_edicion']
    nombre = request.form['nombre']
    cantidad = request.form['cantidad']
    descripcion = request.form['descripcion']
    precio = request.form['precio']

    producto.id_edicion = edicion
    producto.nombre = nombre
    producto.cantidad = cantidad
    producto.descripcion = descripcion
    producto.precio = precio

    db.session.commit()
    return redirect(url_for('merchandising'))


@app.route('/merchandising/delete/<int:id>', methods=['POST'])
def delete_product(id):
    producto = Producto.query.get_or_404(id)
    db.session.delete(producto)
    db.session.commit()
    return redirect(url_for('merchandising'))

@app.route('/comprar', methods=['POST'])
def comprar():
    carrito = session.get('carrito', [])
    total = 0
    try:
        # Calcular el total y restar las cantidades
        for item in carrito:
            producto = Producto.query.get_or_404(item['producto_id'])
            producto.restar_cantidad(item['cantidad'])
            subtotal = float(producto.precio) * float(item['cantidad'])
            total += subtotal
        
        db.session.commit()
        session.pop('carrito', None)  # Vaciamos el carrito después de la compra
        
        # Redirigir a la página de agradecimiento
        return redirect(url_for('compra_gracias'))
    except ValueError as e:
        db.session.rollback()
        flash(str(e), 'danger')
    except Exception as e:
        db.session.rollback()
        flash('Ocurrió un error al procesar la compra.', 'danger')
    
    return redirect(url_for('ver_carrito'))

@app.route('/compra-gracias')
def compra_gracias():
    return render_template('gracias-compra.html')


@app.route('/avisolegal', methods=['GET'])
def avisolegal():
    return render_template('aviso-legal.html')

@app.route('/privacidad', methods=['GET'])
def privacidad():
    return render_template('privacidad.html')

@app.route('/terminos', methods=['GET'])
def terminos():
    return render_template('terminos.html')

@app.route('/trabaja', methods=['GET'])
def trabaja():
    return render_template('trabaja.html')

@app.route('/faq', methods=['GET'])
def faq():
    return render_template('faq.html')


if __name__ == '__main__':
    app.run(debug=True)
