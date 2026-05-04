"""
app_web_plantilla.py
--------------------
Aplicación web de Dark Academy usando Flask y MySQL.

Funcionalidades:
- Login seguro con sesiones y hash de contraseñas
- Registro de usuarios
- CRUD de alumnos, módulos y notas
- Auditoría de notas
- Mejora de seguridad de sesiones y cookies
- Mejoras de usabilidad (UX)

"""

from flask import Flask, render_template, request, redirect, url_for
from conectar_logger import connect_to_mysql
from config import config
from DA_plantilla_alumnos import use_database
import mysql.connector 
import os


# para la seguridad básica + mejoras
from flask import session, flash, redirect, url_for, render_template, request
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'clave_temporal_para_desarrollo')

# Configuración de seguridad extra para sesiones

app.permanent_session_lifetime = timedelta(minutes=30)
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax"
)



DB_NAME = "Dark_Academy"

############################################
#          SEGURIDAD (con mejoras)       #
############################################

def login_required(f):
    """
    Decorador para rutas que requieren usuario autenticado.
    Comprueba si el 'usuario' está en sesión. Si no, redirige al login.
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "usuario" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper

############################################
#                   LOGIN                  #
############################################

@app.route("/", methods=["GET", "POST"])
def login():
    """
    Ruta '/' - Login de usuario.

    GET:
        - Renderiza login.html con formulario de usuario y contraseña.
    POST:
        - Obtiene usuario y contraseña del formulario.
        - Comprueba hash de contraseña en tabla 'usuarios'.
        - Maneja intentos fallidos y bloquea tras 5 intentos.
        - Si correcto, inicia sesión y redirige a /inicio.
    
    Retorna:
        - render_template("login.html") o redirect("/inicio")
    """
    if request.method == "POST":
        usuario = request.form["usuario"]
        password = request.form["password"]

        if "intentos" not in session:
            session["intentos"] = 0

        conn = connect_to_mysql(config)
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM usuarios WHERE usuario = %s",
            (usuario,)
        )
        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session.clear()
            session["usuario"] = user["usuario"]
            session.permanent = True
            return redirect(url_for("inicio"))
        else:
            session["intentos"] += 1
            flash("Usuario o contraseña incorrectos", "error")

            if session["intentos"] >= 5:
                return "Demasiados intentos fallidos. Inténtalo más tarde."

    return render_template("login.html")


@app.route("/inicio")
@login_required
def inicio():
    """
    Ruta '/inicio' - Página principal tras login.

    Muestra la página inicio.html con las opciones de gestión de alumnos, módulos y notas.

    Retorna:
        - render_template("inicio.html", usuario=session["usuario"])
    """
    return render_template("inicio.html", usuario=session["usuario"])


@app.route("/logout")
def logout():
    """
    Ruta '/logout' - Cierra sesión del usuario.

    Borra la sesión y redirige al login.
    """
    session.clear()
    return redirect(url_for("login"))

############################################
#                 REGISTRO                 #
############################################

@app.route("/registro", methods=["GET", "POST"])
def registro():
    """
    Ruta '/registro' - Registro de nuevos usuarios.

    GET:
        - Renderiza registro.html con formulario de usuario y contraseña.
    POST:
        - Recoge usuario y contraseña del formulario.
        - Hashea la contraseña con generate_password_hash.
        - Comprueba si el usuario ya existe.
        - Inserta el nuevo usuario en tabla 'usuarios'.
        - Redirige al login tras registro exitoso.
    
    Retorna:
        - render_template("registro.html") o redirect("/login")
    """
    if request.method == "POST":
        usuario = request.form["usuario"]
        password = request.form["password"]
        
        # Hash seguro de la contraseña
        password_hash = generate_password_hash(password)
        
        conn = connect_to_mysql(config)
        cursor = conn.cursor()
        use_database(cursor, DB_NAME)
        
        # Verificar que no exista el usuario
        cursor.execute("SELECT * FROM usuarios WHERE usuario = %s", (usuario,))
        existe = cursor.fetchone()
        
        if existe:
            flash("El usuario ya existe. Elige otro nombre.", "error")
            cursor.close()
            conn.close()
            return redirect(url_for("registro"))
        
        # Insertar nuevo usuario con contraseña hasheada
        cursor.execute(
            "INSERT INTO usuarios (usuario, password) VALUES (%s, %s)",
            (usuario, password_hash)
        )
        conn.commit()
        cursor.close()
        conn.close()
        
        flash("Usuario registrado correctamente.")
        return redirect(url_for("login"))
    
    return render_template("registro.html")

############################################
#                 ALUMNOS                  #
############################################

@app.route('/alumnos')
@login_required
def alumnos():
    """
    Lista todos los alumnos de la tabla 'alumnos'.
    
    Retorna:
        - render_template("alumnos.html", alumnos=alumnos)
    """
    conn = connect_to_mysql(config)
    cursor = conn.cursor(dictionary=True)
    use_database(cursor, DB_NAME)
    cursor.execute("SELECT * FROM alumnos")
    alumnos = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("alumnos.html", alumnos=alumnos)


@app.route('/nuevo_alumno', methods=['GET', 'POST'])
@login_required
def nuevo_alumno():
    '''Crea un nuevo alumno con validación de expediente duplicado.
    
    Args:
        Ninguno (request.form en POST)
    
    Returns:
        Template o redirect
    
    Raises:
        mysql.connector.IntegrityError: Capturado si el expediente ya existe
    '''
    if request.method == 'POST':
        expediente = request.form['expediente']
        nombre = request.form['nombre']
        apellidos = request.form['apellidos']

        conn = connect_to_mysql(config)
        cursor = conn.cursor()
        use_database(cursor, DB_NAME)
        
        try:
            sql = "INSERT INTO alumnos (expediente, nombre, apellidos) VALUES (%s, %s, %s)"
            cursor.execute(sql, (expediente, nombre, apellidos))
            conn.commit()
            cursor.close()
            conn.close()
            flash(f"Alumno {nombre} {apellidos} creado correctamente", "success")
            return redirect(url_for('alumnos'))
        
        except mysql.connector.IntegrityError as err:
            cursor.close()
            conn.close()
            
            if 'PRIMARY' in str(err) or 'Duplicate' in str(err):
                flash(f"Error: El expediente '{expediente}' ya existe. Elige otro número de expediente.", "error")
            else:
                flash(f"Error al crear el alumno: {err}", "error")
            
            return render_template("alumnos_nuevo.html")
    
    return render_template("alumnos_nuevo.html")


@app.route('/editar_alumno/<expediente>', methods=['GET', 'POST'])
@login_required
def editar_alumno(expediente):
    """
    Edita un alumno existente.

    GET:
        - Muestra formulario con datos actuales del alumno.
    POST:
        - Actualiza nombre y apellidos del alumno en tabla 'alumnos'.
        - Redirige a /alumnos tras actualizar.
    """
    conn = connect_to_mysql(config)
    cursor = conn.cursor(dictionary=True)
    use_database(cursor, DB_NAME)

    if request.method == 'POST':
        nombre = request.form['nombre']
        apellidos = request.form['apellidos']

        sql = "UPDATE alumnos SET nombre=%s, apellidos=%s WHERE expediente=%s"
        cursor.execute(sql, (nombre, apellidos, expediente))
        conn.commit()

        cursor.close()
        conn.close()
        return redirect(url_for('alumnos'))

    cursor.execute("SELECT * FROM alumnos WHERE expediente=%s", (expediente,))
    alumno = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template("alumnos_editar.html", alumno=alumno)


@app.route('/eliminar_alumno/<expediente>')
@login_required
def eliminar_alumno(expediente):
    """
    Elimina un alumno de la tabla 'alumnos'.
    """
    conn = connect_to_mysql(config)
    cursor = conn.cursor()
    use_database(cursor, DB_NAME)

    cursor.execute("DELETE FROM alumnos WHERE expediente=%s", (expediente,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('alumnos'))

############################################
#                 MODULOS                  #
############################################

@app.route('/modulos')
@login_required
def modulos():
    """
    Lista todos los módulos de la base de datos.

    Retorna:
        - render_template("modulos.html", modulos=modulos)
    """
    conn = connect_to_mysql(config)
    cursor = conn.cursor(dictionary=True)
    use_database(cursor, DB_NAME)
    
    cursor.execute("SELECT * FROM modulos")
    modulos = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template("modulos.html", modulos=modulos)


@app.route('/nuevo_modulo', methods=['GET', 'POST'])
@login_required
def nuevo_modulo():
    '''Crea un nuevo módulo con validación de código duplicado.
    
    GET: Muestra formulario vacío para crear módulo.
    POST: Inserta módulo en BD. Si el código ya existe, muestra error.
    
    Args:
        Ninguno (request.form en POST)
    
    Returns:
        Template o redirect según el flujo
    
    Raises:
        mysql.connector.IntegrityError: Capturado si el código ya existe
    '''
    if request.method == 'POST':
        codigo = request.form['codigo']
        nombre = request.form['nombre']

        conn = connect_to_mysql(config)
        cursor = conn.cursor()
        use_database(cursor, DB_NAME)
        
        try:
            sql = "INSERT INTO modulos (codigo, nombre) VALUES (%s, %s)"
            cursor.execute(sql, (codigo, nombre))
            conn.commit()
            cursor.close()
            conn.close()
            flash(f"Módulo {nombre} creado correctamente", "success")
            return redirect(url_for('modulos'))
        
        except mysql.connector.IntegrityError as err:
            cursor.close()
            conn.close()
            
            if 'PRIMARY' in str(err) or 'Duplicate' in str(err):
                flash(f"Error: El código '{codigo}' ya existe. Elige otro código.", "error")
            else:
                flash(f"Error al crear el módulo: {err}", "error")
            
            return render_template("modulos_nuevo.html")
    
    return render_template("modulos_nuevo.html")


@app.route('/editar_modulo/<codigo>', methods=['GET', 'POST'])
@login_required
def editar_modulo(codigo):
    """
    Edita un módulo existente.

    GET:
        - Muestra el formulario con datos actuales del módulo.
    POST:
        - Actualiza el nombre del módulo en la tabla 'modulos'.
        - Redirige a /modulos tras actualizar.
    """
    conn = connect_to_mysql(config)
    cursor = conn.cursor(dictionary=True)
    use_database(cursor, DB_NAME)

    if request.method == 'POST':
        nombre = request.form['nombre']

        sql = "UPDATE modulos SET nombre=%s WHERE codigo=%s"
        cursor.execute(sql, (nombre, codigo))
        conn.commit()

        cursor.close()
        conn.close()
        return redirect(url_for('modulos'))

    cursor.execute("SELECT * FROM modulos WHERE codigo=%s", (codigo,))
    modulo = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template("modulos_editar.html", modulo=modulo)


@app.route('/eliminar_modulo/<codigo>')
@login_required
def eliminar_modulo(codigo):
    """
    Elimina un módulo de la base de datos.

    Args:
        codigo (str): Código del módulo a eliminar.
    
    Retorna:
        - Redirige a /modulos tras eliminar.
    """
    conn = connect_to_mysql(config)
    cursor = conn.cursor()
    use_database(cursor, DB_NAME)

    cursor.execute("DELETE FROM modulos WHERE codigo=%s", (codigo,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('modulos'))

############################################
#                   NOTAS                  #
############################################

@app.route('/notas')
@login_required
def notas():
    """
    Lista todas las notas de la base de datos.

    Retorna:
        - render_template("notas.html", notas=notas)
    """
    conn = connect_to_mysql(config)
    cursor = conn.cursor(dictionary=True)
    use_database(cursor, DB_NAME)
    
    cursor.execute("SELECT * FROM notas")
    notas = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template("notas.html", notas=notas)


@app.route('/nueva_nota', methods=['GET', 'POST'])
@login_required
def nueva_nota():
    
    '''Crea una nueva nota con validación de foreign keys.
    
    GET: Muestra formulario con listas de alumnos y módulos disponibles.
    POST: Inserta la nota en la BD. Si el expediente o código no existen,
          muestra un mensaje de error y vuelve al formulario.
    
    Args:
        Ninguno (request.form en POST)
    
    Returns:
        Template o redirect según el flujo 
    '''

    if request.method == 'POST':
        expediente = request.form['expediente']
        codigo = request.form['codigo']
        nota = request.form['nota']
        
        if nota == '':
            nota = None

        conn = connect_to_mysql(config)
        cursor = conn.cursor()
        use_database(cursor, DB_NAME)
        
        try:
            sql = "INSERT INTO notas (expediente, codigo, nota) VALUES (%s, %s, %s)"
            cursor.execute(sql, (expediente, codigo, nota))
            conn.commit()
            cursor.close()
            conn.close()
            flash("Nota creada correctamente", "success")
            return redirect(url_for('notas'))
        
        except mysql.connector.IntegrityError as err:
            cursor.close()
            conn.close()
            
            # Detectar qué foreign key falló
            if 'fk_expediente' in str(err):
                flash(f"Error: El expediente '{expediente}' no existe. Crea primero el alumno.", "error")
            elif 'fk_codigo' in str(err):
                flash(f"Error: El módulo '{codigo}' no existe. Crea primero el módulo.", "error")
            elif 'PRIMARY' in str(err):
                flash(f"Error: Ya existe una nota para el expediente '{expediente}' en el módulo '{codigo}'.", "error")
            else:
                flash(f"Error al crear la nota: {err}", "error")
            
            # Volver al formulario con los datos
            conn2 = connect_to_mysql(config)
            cursor2 = conn2.cursor(dictionary=True)
            use_database(cursor2, DB_NAME)
            cursor2.execute("SELECT * FROM alumnos")
            alumnos = cursor2.fetchall()
            cursor2.execute("SELECT * FROM modulos")
            modulos = cursor2.fetchall()
            cursor2.close()
            conn2.close()
            
            return render_template("notas_nueva.html", alumnos=alumnos, modulos=modulos)
    
    # GET: Mostrar formulario
    conn = connect_to_mysql(config)
    cursor = conn.cursor(dictionary=True)
    use_database(cursor, DB_NAME)
    
    cursor.execute("SELECT * FROM alumnos")
    alumnos = cursor.fetchall()
    
    cursor.execute("SELECT * FROM modulos")
    modulos = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template("notas_nueva.html", alumnos=alumnos, modulos=modulos)


@app.route('/editar_nota/<expediente>/<codigo>', methods=['GET', 'POST'])
@login_required
def editar_nota(expediente, codigo):
    """
    Edita una nota existente (clave compuesta: expediente + código).

    GET:
        - Muestra el formulario con la nota actual.
    POST:
        - Actualiza la nota en la tabla 'notas'.
        - Convierte notas vacías a None.
        - Redirige a /notas tras actualizar.

    Args:
        expediente (str): Expediente del alumno.
        codigo (str): Código del módulo.

    Retorna:
        - render_template("notas_editar.html", nota=nota)
    """
    conn = connect_to_mysql(config)
    cursor = conn.cursor(dictionary=True)
    use_database(cursor, DB_NAME)

    if request.method == 'POST':
        nota = request.form['nota']
        
        # Convertir nota vacía a None (NULL en BD)
        if nota == '':
            nota = None

        sql = "UPDATE notas SET nota=%s WHERE expediente=%s AND codigo=%s"
        cursor.execute(sql, (nota, expediente, codigo))
        conn.commit()

        cursor.close()
        conn.close()
        return redirect(url_for('notas'))

    cursor.execute("SELECT * FROM notas WHERE expediente=%s AND codigo=%s", (expediente, codigo))
    nota = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template("notas_editar.html", nota=nota)


@app.route('/eliminar_nota/<expediente>/<codigo>')
@login_required
def eliminar_nota(expediente, codigo):
    """
    Elimina una nota (clave compuesta: expediente + código).

    Args:
        expediente (str): Expediente del alumno.
        codigo (str): Código del módulo.

    Retorna:
        - Redirige a /notas tras eliminar.
    """
    conn = connect_to_mysql(config)
    cursor = conn.cursor()
    use_database(cursor, DB_NAME)

    cursor.execute("DELETE FROM notas WHERE expediente=%s AND codigo=%s", (expediente, codigo))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('notas'))


if __name__ == '__main__':
    """
    Arranca la aplicación Flask en modo debug.
    """
    app.run(debug=True)