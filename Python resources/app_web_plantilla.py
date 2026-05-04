from flask import Flask, render_template, request, redirect, url_for
from conectar_logger import connect_to_mysql
from config import config
from DA_plantilla_alumnos import use_database

# para la seguridad básica
from flask import session, flash
from functools import wraps

app = Flask(__name__)
app.secret_key = "Me_Gusta_Python"

DB_NAME = "Dark_Academy"

############################################
#          SEGURIDAD (MUY BÁSICA)          #
############################################

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "usuario" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper


@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form["usuario"]
        password = request.form["password"]

        if usuario == "admin" and password == "1234":
            session["usuario"] = usuario
            return redirect(url_for("inicio"))
        else:
            flash("Usuario o contraseña incorrectos")

    return render_template("login.html")


@app.route("/inicio")
@login_required
def inicio():
    return render_template("inicio.html", usuario=session["usuario"])


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

############################################
#                 ALUMNOS                  #
############################################

@app.route('/alumnos')
@login_required
def alumnos():
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
    if request.method == 'POST':
        expediente = request.form['expediente']
        nombre = request.form['nombre']
        apellidos = request.form['apellidos']

        conn = connect_to_mysql(config)
        cursor = conn.cursor()
        use_database(cursor, DB_NAME)
        sql = "INSERT INTO alumnos (expediente, nombre, apellidos) VALUES (%s, %s, %s)"
        cursor.execute(sql, (expediente, nombre, apellidos))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('alumnos'))
    
    return render_template("alumnos_nuevo.html")


@app.route('/editar_alumno/<expediente>', methods=['GET', 'POST'])
@login_required
def editar_alumno(expediente):
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
    '''Lista todos los módulos de la base de datos'''
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
    '''Crea un nuevo módulo'''
    if request.method == 'POST':
        codigo = request.form['codigo']
        nombre = request.form['nombre']

        conn = connect_to_mysql(config)
        cursor = conn.cursor()
        use_database(cursor, DB_NAME)
        sql = "INSERT INTO modulos (codigo, nombre) VALUES (%s, %s)"
        cursor.execute(sql, (codigo, nombre))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('modulos'))
    
    return render_template("modulos_nuevo.html")


@app.route('/editar_modulo/<codigo>', methods=['GET', 'POST'])
@login_required
def editar_modulo(codigo):
    '''Edita un módulo existente'''
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
    '''Elimina un módulo'''
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
    '''Lista todas las notas de la base de datos'''
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
    '''Crea una nueva nota'''
    if request.method == 'POST':
        expediente = request.form['expediente']
        codigo = request.form['codigo']
        nota = request.form['nota']
        
        # Convertir nota vacía a None (NULL en BD)
        if nota == '':
            nota = None

        conn = connect_to_mysql(config)
        cursor = conn.cursor()
        use_database(cursor, DB_NAME)
        sql = "INSERT INTO notas (expediente, codigo, nota) VALUES (%s, %s, %s)"
        cursor.execute(sql, (expediente, codigo, nota))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('notas'))
    
    # Para el formulario, necesitamos lista de alumnos y módulos
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
    '''Edita una nota existente (clave compuesta: expediente + codigo)'''
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
    '''Elimina una nota (clave compuesta: expediente + codigo)'''
    conn = connect_to_mysql(config)
    cursor = conn.cursor()
    use_database(cursor, DB_NAME)

    cursor.execute("DELETE FROM notas WHERE expediente=%s AND codigo=%s", (expediente, codigo))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('notas'))


if __name__ == '__main__':
    app.run(debug=True)