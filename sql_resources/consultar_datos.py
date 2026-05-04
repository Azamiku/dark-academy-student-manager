import datetime
import mysql.connector
from getpass import getpass

cnx = mysql.connector.connect(user='root', password=getpass('Contraseña: '),host='localhost', database='employees')  # uso localhost
print("¡Conectado a MySQL!")                                      # mensaje para comprobar que me he conectado correctamente
cursor = cnx.cursor()

query = ("SELECT first_name, last_name, hire_date FROM employees "
         "WHERE hire_date BETWEEN %s AND %s")

hire_start = datetime.date(1999, 1, 1)
hire_end = datetime.date(1999, 12, 31)

# como MySQL tiene al tipo Date es compatible con datetime.date() de Python
cursor.execute(query, (hire_start, hire_end))

# aquí usamos el objeto cursor como un iterador
# las tres columnas se guardan en las variables
# first_name, last_name y hire_date 
for (first_name, last_name, hire_date) in cursor:
  print("{}, {} was hired on {:%d %b %Y}".format(
    last_name, first_name, hire_date))

cursor.close()
cnx.close()