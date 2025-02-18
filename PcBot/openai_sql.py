# Archivo que llama a un agente de openai y hace las consultas a la base de datos
import openai
import pyodbc
import os
import re
from dotenv import load_dotenv
from langdetect import detect  # Importamos langdetect

# Cargar variables desde el archivo .env
load_dotenv()

# Configuración de Azure OpenAI
openai.api_type = "azure"
openai.api_base = os.getenv("OPENAI_API_ENDPOINT")
openai.api_version = "2023-06-01-preview"
openai.api_key = os.getenv("OPENAI_API_KEY")
deployment_name = os.getenv("DEPLOYMENT_NAME")

# Configuración de conexión a Azure SQL
server = os.getenv("DB_SERVER")
database = os.getenv("DB_NAME")
username = os.getenv("DB_USERNAME")
password = os.getenv("DB_PASSWORD")
driver = os.getenv("DB_DRIVER")

# Función para obtener consulta SQL desde Azure OpenAI
def obtener_consulta_sql(pregunta):
    idioma = detect(pregunta)

    # Ajuste del prompt para generar consultas compatibles con SQL Server
    prompt = (
        f"Convierte esta pregunta en una consulta SQL para Microsoft SQL Server.\n"
        f"Trabaja con la tabla 'ordenadores' que tiene las siguientes columnas:\n"
        f"marca, precio, modelo, codigo_ordenador, garantia, modelo_grafica, procesador, frecuencia_procesador, "
        f"tamaño, tipo_pantalla, resolucion, color, RAM, sistema_operativo, tarjeta_grafica.\n"
        f"No uses comillas invertidas (`), utiliza corchetes [] solo si es necesario.\n"
        f"Devuelve solo la consulta SQL, sin ningún texto adicional ni etiquetas de código.\n"
        f"Pregunta: '{pregunta}'"
    )
    response = openai.ChatCompletion.create(
        engine=deployment_name,
        messages=[
            {"role": "system", "content": "Eres un asistente que convierte preguntas en consultas SQL para Microsoft SQL Server."},
            {"role": "user", "content": prompt}
        ]
    )
    consulta_sql = response['choices'][0]['message']['content']

    # Limpiar la consulta SQL
    consulta_sql = limpiar_consulta_sql(consulta_sql)

    # Llamada a funciones específicas de cada columna para limpiar consulta
    consulta_sql = limpiar_marca(consulta_sql)
    consulta_sql = limpiar_RAM(consulta_sql)
    consulta_sql = limpiar_precio(consulta_sql)
    consulta_sql = limpiar_garantia(consulta_sql)
    consulta_sql = limpiar_frecuencia_procesador(consulta_sql)
    consulta_sql = limpiar_tamano(consulta_sql)

    return consulta_sql.strip()

# Función para limpiar etiquetas innecesarias en la consulta SQL
def limpiar_consulta_sql(consulta_sql):
    consulta_sql = re.sub(r"```sql", "", consulta_sql)  # Eliminar etiquetas ```sql
    consulta_sql = re.sub(r"```", "", consulta_sql)     # Eliminar etiquetas ```
    consulta_sql = re.sub(r"\[\[\[sql", "", consulta_sql)  # Eliminar [[[sql
    consulta_sql = re.sub(r"\[\[\[", "", consulta_sql)     # Eliminar [[[  
    return consulta_sql

# Función para limpiar la columna 'marca'
def limpiar_marca(consulta_sql):
    if "marca" in consulta_sql:
        if "marca LIKE" in consulta_sql:
            # Extraemos la palabra después de "marca LIKE", quitando comillas simples
            marca = consulta_sql.split("marca LIKE")[1].strip().split()[0].replace("'", "").strip()
            consulta_sql = consulta_sql.replace(f"marca LIKE '{marca}'", f"marca LIKE '%{marca}%'")
        elif "marca =" in consulta_sql:
            # Extraemos la palabra después de "marca =", quitando comillas simples
            marca = consulta_sql.split("marca =")[1].strip().split()[0].replace("'", "").strip()
            consulta_sql = consulta_sql.replace(f"marca = '{marca}'", f"marca LIKE '%{marca}%'")
    return consulta_sql

# Función para limpiar la columna 'RAM' (elimina unidades 'GB' y convierte a INT)
def limpiar_RAM(consulta_sql):
    if "RAM" in consulta_sql:
        # Si la columna es RAM, limpiamos las unidades y caracteres no numéricos
        consulta_sql = consulta_sql.replace('RAM >', "CAST(REPLACE(REPLACE(RAM, 'GB', ''), '/', '') AS INT) >")
    return consulta_sql

# Función para limpiar la columna 'precio' que contiene símbolo €
def limpiar_precio(consulta_sql):
    if "precio" in consulta_sql:  # Verificamos si 'precio' está en la consulta
        # Reemplazar 'precio' con la conversión segura a FLOAT
        consulta_sql = consulta_sql.replace(
            "precio", 
            "TRY_CAST(REPLACE(REPLACE(REPLACE(precio, '€', ''), '.', ''), ',', '.') AS FLOAT)"
        )
    return consulta_sql

# Función para limpiar la columna 'garantia' que en la base de datos se guarda como "meses"
def limpiar_garantia(consulta_sql):
    if "garantia" in consulta_sql:  # Verificamos si 'garantia' está en la consulta
        # Limpiar la columna garantia y convertirla a años
        consulta_sql = consulta_sql.replace(
            "garantia", 
            "TRY_CAST(REPLACE(REPLACE(garantia, 'meses', ''), 'mese', '') AS INT) / 12.0"
        )
    return consulta_sql

# Función para limpiar la columna frecuencia procesador
def limpiar_frecuencia_procesador(consulta_sql):
    if "frecuencia_procesador" in consulta_sql:
        # Extraer el valor de búsqueda de la consulta SQL
        if "=" in consulta_sql:
            valor = consulta_sql.split("=")[1].strip().replace("'", "").strip()
        elif "LIKE" in consulta_sql:
            valor = consulta_sql.split("LIKE")[1].strip().replace("'", "").strip()
        else:
            return consulta_sql  # Si no hay operador, no se modifica la consulta

        # Limpiar el valor de búsqueda (eliminar espacios y convertir a minúsculas)
        valor = valor.lower().strip()

        # Limpiar la columna frecuencia_procesador para buscar coincidencias
        consulta_sql = consulta_sql.replace(
            "frecuencia_procesador", 
            "LOWER(REPLACE(REPLACE(frecuencia_procesador, ' GHZ', ''), ',', '.'))"
        )

        # Reemplazar el operador = o LIKE para buscar coincidencias parciales
        if "=" in consulta_sql:
            consulta_sql = consulta_sql.replace("=", "LIKE")
        elif "LIKE" not in consulta_sql:
            consulta_sql = consulta_sql.replace("frecuencia_procesador", "frecuencia_procesador LIKE")

        # Agregar comodines para búsqueda parcial
        consulta_sql = consulta_sql.replace(f"'{valor}'", f"'%{valor}%'")
    
    return consulta_sql

# Función para limpiar columna 'tamaño' que se guarda con 'pulgadas'
def limpiar_tamano(consulta_sql):
    if "tamaño" in consulta_sql:
        # Limpiar la columna 'tamaño' para convertirla a un número (eliminamos comillas, comas, espacios)
        consulta_sql = consulta_sql.replace(
            "tamaño", 
            "CAST(REPLACE(REPLACE(REPLACE(REPLACE(tamaño, '\"', ''), ',', '.'), ' ', ''), '\"', '') AS FLOAT)"
        )

        # Limpiar el valor de búsqueda en la consulta (si existe)
        if ">" in consulta_sql:
            valor = consulta_sql.split(">")[1].strip().replace("'", "").strip()
            valor = ''.join(filter(lambda x: x.isdigit() or x == '.', valor))  # Limpiar el valor
            consulta_sql = consulta_sql.replace(f"> '{valor}'", f"> {valor}")
        
        if "<" in consulta_sql:
            valor = consulta_sql.split("<")[1].strip().replace("'", "").strip()
            valor = ''.join(filter(lambda x: x.isdigit() or x == '.', valor))  # Limpiar el valor
            consulta_sql = consulta_sql.replace(f"< '{valor}'", f"< {valor}")
        
        if "=" in consulta_sql:
            valor = consulta_sql.split("=")[1].strip().replace("'", "").strip()
            valor = ''.join(filter(lambda x: x.isdigit() or x == '.', valor))  # Limpiar el valor
            consulta_sql = consulta_sql.replace(f"= '{valor}'", f"= {valor}")
    
    return consulta_sql

# Función para ejecutar la consulta en Azure SQL
def ejecutar_consulta_sql(consulta_sql):
    try:
        # Conectar a Azure SQL
        conexion = pyodbc.connect(
            f'DRIVER={driver};SERVER={server};PORT=1433;DATABASE={database};UID={username};PWD={password};Encrypt=yes;TrustServerCertificate=yes;'
        )
        cursor = conexion.cursor()
        cursor.execute(consulta_sql)
        filas = cursor.fetchall()
        
        # Formatear el resultado como una lista de diccionarios
        columnas = [desc[0] for desc in cursor.description]  # Obtener nombres de columnas
        resultado = [dict(zip(columnas, fila)) for fila in filas]  # Crear una lista de diccionarios
        conexion.close()
        return resultado  # Regresa el resultado estructurado
    except Exception as e:
        return f"Error al ejecutar la consulta: {e}"

# Función para traducir los resultados usando OpenAI
def traducir_texto(texto, idioma_destino):
    # Validamos si el texto está vacío
    if not texto:
        return texto
    
    prompt = f"Traduce este texto al idioma {idioma_destino}: {texto}"
    response = openai.ChatCompletion.create(
        engine=deployment_name,
        messages=[
            {"role": "system", "content": "Eres un asistente que traduce texto."},
            {"role": "user", "content": prompt}
        ]
    )
    return response['choices'][0]['message']['content']

# Función principal
def main():
    pregunta = input("¿Qué deseas consultar?: ")
    idioma_detectado = detect(pregunta)

    consulta_sql = obtener_consulta_sql(pregunta)
    print(f"Consulta SQL generada (final): {consulta_sql}")
    resultado = ejecutar_consulta_sql(consulta_sql)

    if isinstance(resultado, list) and len(resultado) > 0:
        # Traducir cada uno de los resultados al idioma detectado
        for item in resultado:
            for clave, valor in item.items():
                if isinstance(valor, str) and valor:  # Si el valor es texto, traducir
                    traducido = traducir_texto(valor, idioma_detectado)
                    item[clave] = traducido

if __name__ == '__main__':
    main()
