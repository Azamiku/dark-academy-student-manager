from  conectar_logger import connect_to_mysql
import mysql.connector
from mysql.connector import errorcode
from config import config

def drop_database(cur, db_name):
    '''Borra una BDA si existe.
    Args:
        cursor(mysql.connector.cursor.MySQLCursor):cursor
        db_name(str):nombre de la BDA a borrar
    Returns:
        True si todo va bien. En otro caso retorna None e informa del error por consola
    '''
    SQL = f"drop database if exists {db_name}"
    try:
        cur.execute(SQL)
    except mysql.connector.Error as err:
        print(f"Fallo al borrar la BDA: {err} (seguramente no existe)")
    else:
        print(f"BDA {DB_NAME} borrada")
        return True


def create_database(cur, db_name, cset, col):
    '''Compone un CREATE DATABASE estilo MySQL y lo ejecuta.
    Args:
        cur(mysql.connector.cursor.MySQLCursor):cursor
        db_name(str):Nombre de la BDA
        cset(str):charset de la BDA
        col(str):colación de la BDA
    Returns:
        True si va todo bien. En otro caso sale del programa informando del error por consola
    '''
    SQL = f"create database if not exists {db_name} \
        character set {cset} \
        collate {col}"
    try:
        cur.execute(SQL)
    except mysql.connector.Error as err:
        print(f"Fallo al crear la BDA: {err}")
        exit(1)
    else: return True

def use_database(cur, DB_NAME):
    '''Cambia a la BDA que se pasa como parámetro.
    Args:
        cur(mysql.connector.cursor.MySQLCursor): cursor con el que se trabaja
        DB_NAME(str): Nombre de la BDA con la que se pretende trabajar
    Returns:
        True si se pudo usar la BDA correctamente
        None si la BDA no existe o hay algún error
    '''
    # Construimos la sentencia SQL para cambiar de base de datos
    SQL = f"USE {DB_NAME}"
    
    try:
        # Ejecutamos el USE
        cur.execute(SQL)
        
    except mysql.connector.Error as err:
        # Si la BDA no existe o hay algún error, imprimimos error
        print(f"La BDA {DB_NAME} no existe: {err}")
        return None  # Retornamos None para indicar que falló
        
    else:
        # Si todo salió bien, retornamos True
        return True

def insert_multiple(cur, tabla, valores):
    '''Inserta en una tabla una lista de tuplas
    Args:
        cur(mysql.connector.cursor.MySQLCursor):cursor
        tabla(str):Nombre de una tabla de la BDA en uso
        valores(list[tuple]):Lista de registros a insertar 
    Returns:
        True o None informando del error por consola
    '''
    N_CAMPOS = len(valores[0])
    SQL_INSERT = f"insert into {tabla} values ({'%s, ' * (N_CAMPOS -1) + '%s'})"

    try:
        cur.executemany(SQL_INSERT, valores)
    except mysql.connector.Error as Err:
        print(Err.msg)
    else:
        return True


def obtener_tablas(cur, bda):
    '''Obtiene una lista de tuplas con los nombres de las tablas de la BDA
    Args:
        cur(mysql.connector.cursor.MySQLCursor):cursor
        bda(str):Nombre de la BDA
    Returns:
        list[tuple] | None con información del error por consola
    '''
    try:
        use_database(cur, bda)
        SQL = f'show tables'
        cur.execute(SQL)
        tablas = cur.fetchall() #obtenemos lista de nombres de tablas
    except mysql.connector.Error as Err:
        print(Err.msg)
    else:
        return tablas


def obtener_cabecera(cur, tabla):
    '''Obtiene los nombres de las columnas de la tabla
    Args:
        cur(mysql.connector.cursor.MySQLCursor):cursor
        tabla(str):Nombre de la tabla
    Returns:
        list[str] | None con mensaje de error por consola
    '''
    try:
        SQL = f'select * from {tabla} limit 1'
        cur.execute(SQL)
        cols = cur.column_names
    except mysql.connector.Error as Err:
        print(Err.msg)
    else:
        return cols


def leer_fila(cur, tabla):
    '''función que retorna las filas de una tabla
    Args:
        cur(mysql.connector.cursor.MySQLCursor):cursor
        tabla(str):Nombre de la tabla
    Returns:
        list[tuple]|None :lista de filas de la tabla o None con mensaje de error por consola.
    '''
    try:
        SQL_SELECT = f'select * from {tabla}'
        cur.execute(SQL_SELECT)
        lista = cur.fetchall()
    except mysql.connector.Error as Err:
        print(Err.msg)
    else:
        return lista

def crea_funcion(cur, SQL):
    ''' función que crea una función en el servidor MySQL
    Args:
        cur(mysql.connector.cursor.MySQLCursor):cursor
        SQL(str):Cadena con el SQL para crear la función
    Returns:
        True|None con mensaje de error por consola
    '''
    try:
        cur.execute(SQL)
    except mysql.connector.Error as Err:
        print(Err.msg)
    else:
        return True

def comprueba_expediente(cur, exp):
    '''Función que ejecuta la función expediente_correcto del servidor MySQL
    Args:
        exp(str):String que representa un expediente
    Returns:
        bool|None:expediente correcto/incorrecto o None con mensaje de error por consola
    '''
    try:
        SQL = "select expediente_correcto(%s)"
        cur.execute(SQL, (exp,))
        res = cur.fetchone()
    except mysql.connector.Error as Err:
        print(Err.msg)
    else:
        return res[0]

def pasan_curso(cur):
    '''Función que obtiene alumnos que pasan a segundo y su porcentaje
    Requisitos para pasar a segundo: tener todos los módulos con nota y media >= 6
    Args:
        cur(mysql.connector.cursor.MySQLCursor):cursor
    Returns:
        dict:Diccionario con clave 'pasan':list[str] (lista de expedientes) y con clave 'porcentaje':float
    '''
    lista_expedientes_pasan = []
    SQL = '''
    select expediente, AVG(nota), count(nota)
        from notas
        where nota is not null
        group by expediente'''
    cur.execute(SQL)
    alumnos = cur.fetchall()
    total = len(alumnos)
    for alumno in alumnos:
        if alumno[2] == 5 and alumno[1] >= 6:
            lista_expedientes_pasan.append(alumno[0])
    dict = {}
    dict['pasan'] = lista_expedientes_pasan
    dict['porcentaje'] = len(lista_expedientes_pasan) / total

    return dict
    

if __name__ == '__main__': 

    # 1. Conectar al servidor MySQL
    
    import mysql.connector
    from getpass import getpass

    # Pedimos la contraseña al usuario y la añadimos al config

    password = getpass("Introduce tu contraseña de MySQL: ")
    try:
        conn = mysql.connector.connect(
            user='root',
            password=password,
            host='localhost'  
        )
        cur = conn.cursor()
        print("Conectado al servidor MySQL")

    # Si no se puede conectar,captura el error y cierra el programa

    except mysql.connector.Error as err:
        print(f"No se pudo conectar: {err}")
        exit(1)


    # 2 y 3. Crear la BDA y usarla
    # Si usais el servidor la BDA ya estará creada 

    nombre_usuario = "Cristina"     # mi nombre para el sufijo por si ya existe la BD con el nombre sin sufijo
    DB_NAME = "Dark_Academy"        #nombre de la BD
    
    # Intentamos crear la base de datos principal
    #Si da algún error, lo capturamos y se cierra el programa

    try:
        cur.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_spanish_ci")
        print(f"BDA {DB_NAME} creada o ya existía")
    except mysql.connector.Error as err:
        print(f"Error creando {DB_NAME}: {err}")

        # Si la base de datos ya existe, añado mi nombre declarado arriba, como sufijo

        DB_NAME = f"Dark_Academy_{nombre_usuario}"
        try:
            cur.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_spanish_ci")
            print(f"BDA {DB_NAME} creada con sufijo de usuario")
        except mysql.connector.Error as err2:
            print(f"No se pudo crear la BDA con sufijo: {err2}")
            exit(1)

    # Usar la BD creada (punto 3)

    try:
        cur.execute(f"USE {DB_NAME}")
        print(f"Usando la base de datos {DB_NAME}")
    except mysql.connector.Error as err:
        print(f"No se pudo utilizar la BDA {DB_NAME}: {err}")
        exit(1)


    # Borrar la BDA por comodidad durante el testeo

    # IMPORTANTE:
    # La base de datos NO se elimina para evitar pérdida de datos.
    # Solo se crea si no existe.
    #drop_database(cur, DB_NAME)

    # Crear la BDA de nuevo 
    create_database(cur, DB_NAME, 'utf8mb4', 'utf8mb4_spanish_ci')

    # Confirmar que está creada imrpimiendo el mensaje

    print(f'BDA {DB_NAME} creada')

    # Seleccionar la BDA recién creada para poder trabajar con ella
    cur.execute(f"USE {DB_NAME}")
    print(f"✓ BDA {DB_NAME} seleccionada de nuevo")
    
    # 4. Crear las tablas de la BDA

    TABLES = {}
    TABLES['alumnos'] = '''
    create table if not exists alumnos(
        expediente char(8) PRIMARY KEY,
        nombre varchar(30) NOT NULL,
        apellidos varchar(50) NOT NULL
    )'''
    TABLES['modulos'] = '''
    create table if not exists modulos(
        codigo varchar(5) PRIMARY KEY,
        nombre varchar(30) NOT NULL
    )'''
    TABLES['notas'] = '''
    create table if not exists notas(
        expediente char(8),
        codigo varchar(5),
        nota integer unsigned,
        PRIMARY KEY (expediente, codigo),
        constraint fk_expediente 
            foreign key (expediente)
            references alumnos(expediente)
            on delete cascade on update cascade,
        constraint fk_codigo
            foreign key (codigo)
            references modulos(codigo)
            on delete cascade on update cascade
    )'''
    TABLES['auditoria_notas'] = '''
    create table if not exists auditoria_notas(
        id serial PRIMARY KEY, -- clave autoincremental
        expediente_old char(8), -- expediente viejo
        codigo_old varchar(5), -- módulo viejo
        nota_old integer unsigned, -- nota antigua
        expediente_new char(8), -- expediente nuevo
        codigo_new varchar(5), -- módulo nuevo
        nota_new integer unsigned, -- nota nueva
        usuario varchar(50) not null, -- usuario que hace la modificación
        cuando datetime not null, -- fecha y hora de la modificación
        operacion enum('insert', 'update', 'delete') not null -- operación DML utilizada
    )'''

    # bucle que recorre las tablas

    for table_name in TABLES:
        
        # ejecuta el SQL para crear la tabla
        # si se crea la tabla correctamente imprime el mensaje " Tabla creada correctamente", si no imprime el error

        print(f"Creando tabla {table_name}: ", end='')
        try:
            cur.execute(TABLES[table_name])
        except mysql.connector.Error as err:
            print(f"Error: {err}")
        else:
            print("Tabla creada correctamente")      

    conn.commit()                      
        
    # 5. Crear triggers auditoría notas

    TRIGGERS_AUDITORIA = {}
    TRIGGERS_AUDITORIA['auditoria_notas_insert'] = '''
    create trigger if not exists auditoria_notas_insert after insert on notas
    for each row
        insert into auditoria_notas 
        values(null,null,null,null,new.expediente, new.codigo, new.nota, user(), now(),'insert')'''
    TRIGGERS_AUDITORIA['auditoria_notas_update'] = '''
    create trigger if not exists auditoria_notas_update after update on notas
    for each row
        insert into auditoria_notas 
        values(null, old.expediente, old.codigo, old.nota, new.expediente, new.codigo, 
        new.nota, user(), now(), 'update')'''
    TRIGGERS_AUDITORIA['auditoria_notas_delete'] = '''
    create trigger if not exists auditoria_notas_delete after delete on notas
    for each row
        insert into auditoria_notas 
        values(null, old.expediente, old.codigo, old.nota, null,null,null, user(), now(), 'delete')'''

# Bucle que crea el trigger, lo ejecuta e imprime "OK", si ocurre un error lo captura e imprime

#Primera vuelta del bucle → ejecuta el trigger de inserción (insert)
#Segunda vuelta → ejecuta el trigger de actualización (update)
#Tercera vuelta → ejecuta el trigger de borrado (delete)

    for trigger in TRIGGERS_AUDITORIA:
        print(f"Creando trigger {trigger}: ", end='')
        try:
            cur.execute(TRIGGERS_AUDITORIA[trigger])
        except mysql.connector.Error as err:
            print(f"Error: {err}")
        else:
            print("OK")

       

    # 6. Inserción de datos en las tablas
    valores_alumnos = [
        ('11111111', 'Alexia', 'Núñez Pérez'), 
        ('22222222', 'Rosa', 'Fernández Oliva'), 
        ('33333333', 'Peter', 'Linuesa Jiménez'), 
        ('44444444', 'Juan Carlos', 'Wesnoth The Second'), 
        ('55555555', 'Federico', 'Muñoz Ferrer')
    ]
    
    if insert_multiple(cur, 'alumnos', valores_alumnos):
        print(f"registros en tabla alumnos insertados correctamente")
    
      

    valores_modulos = [
        ('QP', 'Quirománcia Práctica'),
        ('MR', 'Mortum Redivivus'),
        ('RF', 'Refactorización Zómbica'),
        ('ARF', 'Ampliación de RF'),
        ('OP', 'Orquestación de Plagas')
    ]

    if insert_multiple(cur, 'modulos', valores_modulos):
        print(f"registros en tabla modulos insertados correctamente")
    
    conn.commit() 

    # NULL debe pasarse a None (equivalente Python)
    valores_notas = [
        ('11111111', 'QP', 5), 	('11111111', 'MR', 7),
        ('11111111', 'RF', 6),	('11111111', 'ARF', 9),
        ('11111111', 'OP', 7),	('22222222', 'QP', None),
        ('22222222', 'MR', 5),	('22222222', 'RF', 5),
        ('22222222', 'ARF', 6),	('22222222', 'OP', None),
        ('33333333', 'QP', 9),	('33333333', 'MR', 5),
        ('33333333', 'RF', 6),	('33333333', 'ARF', 4),
        ('33333333', 'OP', 6),	('44444444', 'QP', 4),
        ('44444444', 'MR', 6),	('44444444', 'RF', 8),
        ('44444444', 'ARF', 6),	('44444444', 'OP', 5),
        ('55555555', 'QP', 8),	('55555555', 'MR', 4),
        ('55555555', 'RF', None),   ('55555555', 'ARF', None),
        ('55555555', 'OP', 4)
    ]

    if insert_multiple(cur, 'notas', valores_notas):
        print(f"registros en tabla notas insertados correctamente")
   

# 7. Mostrar los datos de todas las tablas

# El nombre de la tabla no está fijo, entra como parámetro.
# Captura errores
    
    def mostrar_tabla(cur, nombre_tabla):
        '''Muestra el contenido completo de una tabla de la base de datos.
    
        Args:
            cur (mysql.connector.cursor.MySQLCursor): Cursor de MySQL
            nombre_tabla (str): Nombre de la tabla a mostrar
    
        Returns:
            None: Imprime los datos por consola, no retorna nada
    '''
        try:
            cur.execute(f"SELECT * FROM {nombre_tabla}")
            filas = cur.fetchall()                         # devuelve todos los resultados sobre el cursor asociado

            print(f"\nContenido de la tabla {nombre_tabla}:")
            for fila in filas:
                print(fila)

        except mysql.connector.Error as err:
            print(f"Error mostrando la tabla {nombre_tabla}: {err}")

# Mostrar tablas

    mostrar_tabla(cur, "alumnos")
    mostrar_tabla(cur, "modulos")
    mostrar_tabla(cur, "notas")
    mostrar_tabla(cur, "auditoria_notas")


# 8. Función en el lado del servidor que comprueba si un expediente es correcto 

    SQL_FUNCION = '''
    create function expediente_correcto(exp char(8)) returns BOOLEAN
    DETERMINISTIC
    NO SQL
        return (exp regexp '^[0-9]{8}$')
    '''

# Borramos la función antes (DROP FUNCTION IF EXISTS) para no tener errores al probar varias veces el código.
# Capturamos errores

    try:
        cur.execute("DROP FUNCTION IF EXISTS expediente_correcto")
        cur.execute(SQL_FUNCION)
        print("Función expediente_correcto creada correctamente")

    except mysql.connector.Error as err:
        print(f"Error, no se ha creado la función: {err}")


    # 9. Probando la función
    # NOTA: si los expedientes pasan de 8 caracteres da error. Es por la función en el lado del servidor.

    # Función que comprueba si un expediente es correcto
    # Utiliza la función del servidor MySQL creada en el punto 8
    # Devuelve True si el expediente es válido, False en caso contrario

    def comprobar_expediente(cur, expediente):
        '''Comprueba si un expediente es válido usando la función del servidor MySQL.
    
        Un expediente es válido si tiene exactamente 8 dígitos numéricos.
        Utiliza la función expediente_correcto() creada en el servidor MySQL.
    
        Args:
            cur (mysql.connector.cursor.MySQLCursor): Cursor de MySQL
            expediente (str): Cadena que representa un expediente a validar
    
        Returns:
            bool: True si el expediente es válido, False en caso contrario
        '''
        try:
        # Ejecuta la función expediente_correcto del servidor MySQL
        # Se pasa el expediente como parámetro 
            cur.execute("SELECT expediente_correcto(%s)", (expediente,))
            resultado = cur.fetchone()[0]
        # Convierte el resultado a booleano y lo devuelve
            return bool(resultado)
        except mysql.connector.Error as err:
            print(f"Error comprobando expediente {expediente}: {err}")
            return False

# Prueba
# Uno correcto y otro incorrecto

    EXPEDIENTES = ['11112222', 'XXXYYYZZ']
    
    # Bucle que recorre la lista de expedientes y comprobamos cada uno
    for exp in EXPEDIENTES:
        if comprobar_expediente(cur, exp):
            print(f"Expediente {exp} correcto")
        else:
            print(f"Expediente {exp} incorrecto")
    

    # 10. Función pasan_segundo
    
    def alumnos_que_pasan(cur):
        
        '''Muestra los alumnos que pasan a segundo curso y calcula el porcentaje.
    
            Requisitos para pasar a segundo:
                - Tener todas las notas (no NULL en ningún módulo)
                - Media de notas >= 6.0
    
        Imprime por consola:
                - Lista de alumnos que pasan con sus datos y media
                - Porcentaje de alumnos que pasan sobre el total
    
        Args:
            cur (mysql.connector.cursor.MySQLCursor): Cursor de MySQL
    
        Returns:
            None: Imprime los resultados por consola, no retorna nada
        '''

        sql = '''
        SELECT a.expediente, a.nombre, a.apellidos, AVG(n.nota) AS media
        FROM alumnos a
        JOIN notas n ON a.expediente = n.expediente
        GROUP BY a.expediente
        HAVING COUNT(n.nota) = COUNT(*) AND AVG(n.nota) >= 6
        '''

        cur.execute(sql)
        alumnos = cur.fetchall()

        print("\nAlumnos que pasan a segundo de Artes Oscuras:")
        for alumno in alumnos:
            print(alumno)

        # Total alumnos
        cur.execute("SELECT COUNT(*) FROM alumnos")
        total = cur.fetchone()[0]

        pasan = len(alumnos)
        porcentaje = (pasan / total) * 100 if total > 0 else 0

        print(f"\nPorcentaje de alumnos que pasan: {porcentaje:.2f}%")
    
    # llamar a la función
    alumnos_que_pasan(cur)

    # cerrar todo
    # Cerramos el cursor y la conexión con la base de datos
    cur.close()
    conn.close()