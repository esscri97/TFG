from flask import Flask, render_template, url_for, request, session, redirect, flash
import requests
import config
import bcrypt
from flask_mysqldb import MySQL #Necesario pip install flask_mysqldb

app = Flask(__name__)

app.config['SECRET_KEY'] = config.HEX_SEC_KEY
app.config['MYSQL_HOST'] = config.MYSQL_HOST
app.config['MYSQL_USER'] = config.MYSQL_USER
app.config['MYSQL_PASSWORD'] = config.MYSQL_PASSWORD
app.config['MYSQL_DB'] = config.MYSQL_DB

""" david97escriva@gmail.com
Davidprueba """

mysql = MySQL(app) # Para poder usar la bbdd (consultas, etc)

@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')

    
# Login de usuarios
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute('SELECT * FROM usuarios WHERE email = %s', (email,))
        user = cur.fetchone() # Devuelve un array con las columnas en caso de que haya coincidencias
        cur.close()

        if user is not None and bcrypt.checkpw(password.encode(), user[3].encode()):
            session['email'] = email
            session['name'] = user[1]

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
            cur = mysql.connection.cursor()
            sql = 'INSERT INTO usuarios (nombre, email, password, rol) VALUES (%s, %s, %s, %s)'
            data = (name, email, hashed_password.decode(), rol)
            cur.execute(sql, data)
            mysql.connection.commit()

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
            cur = mysql.connection.cursor()
            sql = 'INSERT INTO peticiones (id_edicion, nombre, AKA, telefono, tipo) VALUES (4, %s, %s, %s, %s)'
            data = (nombre, aka, telefono, tipoArtista)
            cur.execute(sql, data)
            mysql.connection.commit()
            flash('Gracias por tu solicitud. ¡Nos pondremos en contacto contigo pronto!', 'success')
        except Exception as e:
            mysql.connection.rollback()
            flash('Hubo un error al enviar tu solicitud. Por favor, inténtalo de nuevo.', 'error')
            app.logger.error(f"Error al insertar en la base de datos: {str(e)}")
        finally:
            cur.close()
        
        return redirect('/edicion3')

@app.route('/contacto')
def contacto():
    return render_template('contacto.html')

@app.route('/merchandising', methods=['GET', 'POST'])
def merchandising():
    if request.method == 'POST':
        nombre = request.form['nombre']
        imagen = request.form['imagen']
        cantidad = request.form['cantidad']
        descripcion = request.form['descripcion']

        cur = mysql.connection.cursor()
        cur.execute('INSERT INTO productos (nombre, imagen, cantidad, descripcion) VALUES (%s, %s, %s, %s)', 
                    (nombre, imagen, cantidad, descripcion))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('merchandising'))
    
    elif request.method == 'GET':
        if 'rol' in session and session['rol'] == 'admin':
            return render_template('crud_merchan.html')
        else:
            return render_template('merchandising.html')
    

@app.route('/merchandising/edit/<int:id>', methods=['POST'])
def edit_product(id):
    nombre = request.form['nombre']
    imagen = request.form['imagen']
    cantidad = request.form['cantidad']
    descripcion = request.form['descripcion']

    cur = mysql.connection.cursor()
    cur.execute('UPDATE productos SET nombre = %s, imagen = %s, cantidad = %s, descripcion = %s WHERE id_producto = %s', 
                (nombre, imagen, cantidad, descripcion, id))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('merchandising'))

@app.route('/merchandising/delete/<int:id>', methods=['POST'])
def delete_product(id):
    cur = mysql.connection.cursor()
    cur.execute('DELETE FROM productos WHERE id_producto = %s', (id,))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('merchandising'))


#IMPORTANTE----------------
# - Hacer el front bien
# - Intentar consumir API spotify
# - Preguntar a Maribel por pasarela de pago
# - Hacer pag de usuario


if __name__ == '__main__':
    app.run(debug=True)