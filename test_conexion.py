# este documento lo he creado porque he tenido muchos problemas con al conexión y lo he necesitado para ir 
# verificando la conexión mientras probaba distintas cosas...



from conectar_logger import connect_to_mysql

config = {
    'user': 'root',
    'password': '2112',
    'host': 'localhost'
}

print(f"Usuario: {config['user']}")
print(f"Password: {config['password']}")
print(f"Password length: {len(config['password'])}")
print(f"Host: {config['host']}")

conn = connect_to_mysql(config)
if conn:
    print("✅ CONEXIÓN OK")
    conn.close()
else:
    print("❌ CONEXIÓN FALLÓ")