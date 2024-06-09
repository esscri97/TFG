from flask import Flask, render_template, url_for, request, session, redirect, flash, send_from_directory
import os
from werkzeug.utils import secure_filename
import requests
import config
import bcrypt
from flask_mysqldb import MySQL #Necesario pip install flask_mysqldb
import os
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy



app = Flask(__name__)

# Configuración de la base de datos PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://festival_whtt_user:HghpwIHwamviE0xtak6vejdrehzI4wGe@dpg-cpiqqp21hbls73blh9f0-a.oregon-postgres.render.com/festival_whtt'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar la extensión SQLAlchemy
db = SQLAlchemy(app)

# Configuración para subir archivos
UPLOAD_FOLDER = 'static/images/productos'  # Carpeta donde se almacenarían las imágenes (no la usaremos en este caso)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}  # Extensiones de archivo permitidas
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Definir el modelo de usuario
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    rol = db.Column(db.String(50), nullable=False)

# Define el modelo de producto
class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_edicion = db.Column(db.Integer, db.ForeignKey('editions.id'), nullable=False)
    nombre = db.Column(db.String(255), nullable=False)
    imagen = db.Column(db.String(500), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    descripcion = db.Column(db.String(500), nullable=False)
    precio = db.Column(db.Float, nullable=False)

# Define el modelo de edición
class Edition(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, nullable=False)
    products = db.relationship('Product', backref='edition', lazy=True)

class Peticion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_edicion = db.Column(db.Integer, nullable=False)
    nombre = db.Column(db.String(255), nullable=False)
    AKA = db.Column(db.String(255), nullable=False)
    telefono = db.Column(db.String(20), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)

# Configuración para subir archivos
UPLOAD_FOLDER = 'static/images/productos'  # Carpeta donde se almacenarían las imágenes (no la usaremos en este caso)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}  # Extensiones de archivo permitidas
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

""" david97escriva@gmail.com
Davidprueba """

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
            session['name'] = user.name
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
            user = User(name=name, email=email, password=hashed_password.decode(), rol=rol)
            db.session.add(user)
            db.session.commit()

        return redirect(url_for('login'))
    elif request.method == 'GET':
        return render_template('register.html')

# Ruta para cerrar sesión
@app.route('/logout')
def logout():
    # Eliminar todas las variables de sesión
    session.clear()
    # Redirigir a la página de inicio
    return redirect(url_for('home'))

# Define la ruta para manejar la búsqueda de artistas
@app.route('/artistas', methods=['POST', 'GET'])
def buscar_artista():
    if request.method == 'POST':
        # Obtiene el nombre del artista desde el formulario
        nombre_artista = request.form['nombre_artista']
        
        # Llama a la función para obtener información del artista desde Spotify
        info_artista = obtener_informacion_artista(nombre_artista)
        
        if info_artista:
            return render_template('resultado_artista.html', info_artista=info_artista)
        else:
            return render_template('artistas.html', error='Artista no encontrado.')
    elif request.method == 'GET':
        return render_template('artistas.html')

def obtener_informacion_artista(nombre_artista):
    # Define tu client_id y client_secret de Spotify
    client_id = '00c2a60a76ac41f39d30afefccc5ddf2'
    client_secret = '797983182a9f4160b34c98d69eca0b2c'
    
    # Realiza la solicitud de autorización
    auth_response = requests.post('https://accounts.spotify.com/api/token', {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
    })
    
    # Verifica si la autenticación fue exitosa
    if auth_response.status_code != 200:
        print("Error de autenticación:", auth_response.text)
        return None
    
    # Obtiene el token de acceso
    access_token = auth_response.json().get('access_token')
    
    if not access_token:
        print("No se pudo obtener el token de acceso.")
        return None
    
    # Configura los headers para la solicitud de búsqueda de artista
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    
    # Realiza la solicitud para buscar el artista
    response = requests.get('https://api.spotify.com/v1/search', 
                            headers=headers, 
                            params={'q': nombre_artista, 'type': 'artist'})
    
    if response.status_code != 200:
        print("Error en la solicitud de búsqueda:", response.text)
        return None
    
    # Verifica si se encontraron artistas
    data = response.json()
    if 'artists' not in data or not data['artists']['items']:
        return None
    
    # Obtiene la información del primer artista encontrado
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
        # Obtener datos del formulario
        nombre = request.form['nombre']
        tipoArtista = request.form['tipoArtista']
        aka = request.form['aka']
        telefono = request.form['telefono']

        # Validar los datos
        if not nombre or not tipoArtista or not aka or not telefono:
            flash('Por favor, complete todos los campos.', 'error')
            return redirect('/edicion3')

        try:
            # Crear una nueva instancia de Peticion
            peticion = Peticion(id_edicion=4, nombre=nombre, AKA=aka, telefono=telefono, tipo=tipoArtista)
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
        # Procesar el formulario y enviar el correo electrónico
        return redirect('https://formspree.io/allorofestival@gmail.com')
    else:
        return render_template('contacto.html')

# Función para comprobar si la extensión del archivo es permitida
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Ruta para manejar el merchandising (obtener, añadir, editar y eliminar productos)
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
        
        return redirect(url_for('merchandising'))
    
    elif request.method == 'GET':
        products = Producto.query.all()
        
        if 'rol' in session and session['rol'] == 'admin':
            return render_template('crud_merchan.html', products=products)
        elif 'rol' in session and session['rol'] == 'user':
            return render_template('merchandising.html', products=products)
        else:
            return render_template('merchandising.html', products=products)

# Función para comprobar si la extensión del archivo es permitida
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Ruta para mostrar la imagen cargada
@app.route('/productos/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Ruta para editar un producto de merchandising
@app.route('/merchandising/edit/<int:id>', methods=['POST'])
def edit_product(id):
    edicion = request.form['id_edicion']
    nombre = request.form['nombre']
    cantidad = request.form['cantidad']
    descripcion = request.form['descripcion']
    precio = request.form['precio']

    # Actualizar los detalles del producto en la base de datos
    product = Producto.query.get_or_404(id)
    product.id_edicion = edicion
    product.nombre = nombre
    product.cantidad = cantidad
    product.descripcion = descripcion
    product.precio = precio
    
    try:
        db.session.commit()
        flash('Producto actualizado correctamente', 'success')
    except:
        db.session.rollback()
        flash('Hubo un error al actualizar el producto', 'error')
    
    return redirect(url_for('merchandising'))

@app.route('/merchandising/delete/<int:id>', methods=['POST'])
def delete_product(id):
    product = Producto.query.get_or_404(id)
    
    try:
        db.session.delete(product)
        db.session.commit()
        flash('Producto eliminado correctamente', 'success')
    except:
        db.session.rollback()
        flash('Hubo un error al eliminar el producto', 'error')
    
    return redirect(url_for('merchandising'))

@app.route('/producto/<int:producto_id>', methods=['GET', 'POST'])
def producto(producto_id):
    product = Producto.query.get_or_404(producto_id)

    if request.method == 'POST':
        cantidad = int(request.form['cantidad'])
        talla = request.form.get('talla', 'S')
        item = (product.id, product.nombre, product.precio, cantidad, talla)
        carrito = session.get('carrito', [])
        carrito.append(item)
        session['carrito'] = carrito
        flash('Producto añadido al carrito.', 'success')
        return redirect(url_for('ver_carrito'))

    return render_template('producto.html', product=product)

@app.route('/carrito')
def ver_carrito():
    carrito = session.get('carrito', [])
    total = sum(float(product[6]) * float(product[7]) for product in carrito) #arreglar
    return render_template('carrito.html', carrito=carrito, total=total, enumerate=enumerate)

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

if __name__ == '__main__':
    app.run(debug=True)