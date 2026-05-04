import mysql.connector
from mysql.connector import errorcode
from config import config
from getpass import getpass

# https://dev.mysql.com/doc/connector-python/en/connector-python-connectargs.html

# mediante connect (forma preferida)
'''
config = {
    'user': 'root',
    'password': 'XXXXXXXXXXXXXX',
    'host': '192.168.88.252',
    'database': '', # No pongo pq.quiero crearla
    'raise_on_warnings': True,
}
'''
try:
    cnx = mysql.connector.connect(**config)
    print('Conectado') #debug
    cnx.close()
    print('Desconectado') #debug
except mysql.connector.Error as e:
    if e.errno == errorcode.ER_ACCESS_DENIED_ERROR:
        print("Something went wrong with your name or password")
    elif e.errno == errorcode.ER_BAD_DB_ERROR:
        print("Database does not exist")
    elif e.errno == 2003:
        print("Can't connect to MySQL server on 'xxxxx'")
    else:
        print(e)
except Exception as e:
    print(f'Se produjo una excepción {type(e)}')

# también es posible crear objetos connection mediante la clase connection.MySQLConnection

from mysql.connector import (connection)

cnx = connection.MySQLConnection(user='root', password=getpass("password: "),
                                 host='192.168.88.252',
                                 database='')
print('Conectado')
cnx.close()
print('Desconectado')

# entonces la receta es

# import mysql.connector
# from mysql.connector import errorcode

try:
  cnx = mysql.connector.connect(user='root',
                                password=getpass("password: "),
                                host='192.168.88.252',
                                database='')
  print('Conectado')
except mysql.connector.Error as err:
  if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
    print("Something is wrong with your user name or password")
  elif err.errno == errorcode.ER_BAD_DB_ERROR:
    print("Database does not exist")
  else:
    print(err)
else:
  cnx.close()
  print('Desconectado')


# una vez conectados ya podemos hacer cosas según DB-API 2.0

from conectar_logger import connect_to_mysql

'''
config = {
    "host": "192.168.88.252",
    "user": "root",
    "password": "XXXXXXXXXX",
    "database": "",
}
'''
cnx = connect_to_mysql(config, attempts=3)

# NOTA: podemos usar el dialecto SQL de MySQL

if cnx and cnx.is_connected():
   
    with cnx.cursor() as cursor:
        try:
            # AVISO PARA NAVEGANTES: el driver no hace caso de IF EXISTS y de IF NOT EXISTS
            # se debe manejar con Python
            try:
                cursor.execute("drop database if exists test")
            except Exception:
                print("BDA test no existe")

            result = cursor.execute("create database if not exists test")
            print("BDA test creada")
            result = cursor.execute("use test")
            print("Cambiado contexto a BDA test")
            result = cursor.execute("create table if not exists t(id serial primary key)")
            print("TABLA t creada")
            result = cursor.execute("insert into t values (NULL), (NULL), (NULL)")
            print("Valores insertados")
            cnx.commit()
            result = cursor.execute("select * from t")
            rows = cursor.fetchall()

            for rows in rows:
                print(rows)
            
        except Exception as e:
           print(e)

    cnx.close()
    print("conexión cerrada")

else:
   print("No se pudo conectar")