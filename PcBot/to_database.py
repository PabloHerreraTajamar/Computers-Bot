# Archivo que carga el pdf y lo transforma para guardar en la base de datos
import os
import pyodbc
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Configuración Azure Document Intelligence
ENDPOINT = os.getenv("AZURE_ENDPOINT_DOCUMEN_INTELLIGENCE")
API_KEY = os.getenv("AZURE_API_KEY_DOCUMEN_INTELLIGENCE")
MODEL_ID = os.getenv("MODEL")
PDF_FOLDER_PATH = "pdfs"  # Carpeta que contiene los PDFs

# Configuración Azure SQL Database
DB_SERVER = os.getenv("DB_SERVER")
DB_NAME = os.getenv("DB_NAME")
DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_DRIVER = os.getenv("DB_DRIVER")

# Verificar que las variables de entorno se hayan cargado correctamente
if not all([ENDPOINT, API_KEY, MODEL_ID, DB_SERVER, DB_NAME, DB_USERNAME, DB_PASSWORD, DB_DRIVER]):
    raise ValueError("Faltan variables de entorno. Verifica tu archivo .env")

# Definir las entidades y nombres de columnas
ENTIDADES = [
    "Marca", "Precio", "Modelo", "Codigo_ordenador", "Garantia",
    "Modelo_grafica", "Procesador", "Modelo_procesador", "Frecuencia_procesador",
    "Tamaño", "Tipo_pantalla", "Resolucion", "Color", 
    "RAM", "Sistema_operativo", "Tarjeta_grafica"
]

# Inicializa el cliente de análisis de documentos
document_analysis_client = DocumentAnalysisClient(
    endpoint=ENDPOINT,
    credential=AzureKeyCredential(API_KEY)
)

# Función para conectarse a la base de datos
def conectar_db():
    connection_string = f"DRIVER={DB_DRIVER};SERVER={DB_SERVER};PORT=1433;DATABASE={DB_NAME};UID={DB_USERNAME};PWD={DB_PASSWORD}"
    return pyodbc.connect(connection_string)

# Función para crear la tabla principal con las columnas especificadas
def crear_tabla_principal():
    conexion = conectar_db()
    cursor = conexion.cursor()

    # Crear tabla con las columnas especificadas si no existe
    cursor.execute("""
        IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'ordenadores')
        CREATE TABLE ordenadores (
            Id INT PRIMARY KEY IDENTITY(1,1),
            Marca NVARCHAR(MAX),
            Precio NVARCHAR(MAX),
            Modelo NVARCHAR(MAX),
            Codigo_ordenador NVARCHAR(MAX),
            Garantia NVARCHAR(MAX),
            Modelo_grafica NVARCHAR(MAX),
            Procesador NVARCHAR(MAX),
            Modelo_procesador NVARCHAR(MAX),
            Frecuencia_procesador NVARCHAR(MAX),
            Tamaño NVARCHAR(MAX),
            Tipo_pantalla NVARCHAR(MAX),
            Resolucion NVARCHAR(MAX),
            Color NVARCHAR(MAX),
            RAM NVARCHAR(MAX),
            Sistema_operativo NVARCHAR(MAX),
            Tarjeta_grafica NVARCHAR(MAX)
        )
    """)
    
    conexion.commit()
    cursor.close()
    conexion.close()

# Función para actualizar la estructura de la tabla (por si se agregan nuevas columnas en el futuro)
def actualizar_tabla(entidades):
    conexion = conectar_db()
    cursor = conexion.cursor()

    for nombre_entidad in entidades:
        # Verifica si la columna ya existe
        cursor.execute(f"""
            IF NOT EXISTS (
                SELECT * 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'ordenadores' AND COLUMN_NAME = '{nombre_entidad}'
            )
            ALTER TABLE ordenadores ADD {nombre_entidad} NVARCHAR(MAX)
        """)
    
    conexion.commit()
    cursor.close()
    conexion.close()

# Función para guardar las entidades en la base de datos
def guardar_entidades(entidades):
    conexion = conectar_db()
    cursor = conexion.cursor()

    # Construir la consulta de inserción dinámicamente
    columnas = ", ".join(entidades.keys())
    valores_placeholder = ", ".join(["?"] * len(entidades))
    valores = list(entidades.values())

    query = f"""
        INSERT INTO ordenadores ({columnas})
        VALUES ({valores_placeholder})
    """
    
    cursor.execute(query, valores)
    conexion.commit()
    cursor.close()
    conexion.close()

# Función para analizar el PDF y extraer entidades
def analizar_pdf(pdf_content):
    # Ahora recibimos el contenido del PDF como un archivo en memoria (en lugar de una ruta)
    from io import BytesIO

    # Crear un objeto de archivo en memoria a partir del contenido binario del PDF
    pdf_file = BytesIO(pdf_content)

    # Procesar el archivo PDF con Azure
    poller = document_analysis_client.begin_analyze_document(
        model_id=MODEL_ID,
        document=pdf_file
    )
    result = poller.result()
    
    # Almacenar las entidades detectadas
    entidades_detectadas = {}
    
    # Asignar cada entidad a su valor, o NULL si no se encuentra
    for field_name in ENTIDADES:
        field_value = result.documents[0].fields.get(field_name)
        
        if field_value:
            entidades_detectadas[field_name] = field_value.value
        else:
            entidades_detectadas[field_name] = None
    
    # Guardar las entidades en la base de datos
    guardar_entidades(entidades_detectadas)


# Función para procesar todos los PDFs de la carpeta
def procesar_pdfs_en_carpeta():
    if not os.path.exists(PDF_FOLDER_PATH):
        print(f"La carpeta {PDF_FOLDER_PATH} no existe.")
        return
    
    archivos_pdf = [f for f in os.listdir(PDF_FOLDER_PATH) if f.endswith(".pdf")]
    
    if not archivos_pdf:
        print(f"No se encontraron archivos PDF en la carpeta {PDF_FOLDER_PATH}.")
        return
    
    # Procesar cada PDF
    for pdf_file in archivos_pdf:
        pdf_path = os.path.join(PDF_FOLDER_PATH, pdf_file)
        analizar_pdf(pdf_path)
        print(f"PDF {pdf_file} subido correctamente.")

def obtener_ultimo_ordenador():
    conexion = conectar_db()
    cursor = conexion.cursor()

    # Obtener el último ordenador de la base de datos
    cursor.execute("SELECT TOP 1 * FROM ordenadores ORDER BY Id DESC")
    row = cursor.fetchone()

    if row:
        # Si encontramos un registro, lo devolvemos como un diccionario
        ultimo_ordenador = {
            "id": row[0],
            "marca": row[1],
            "precio": row[2],
            "modelo": row[3],
            "codigo_ordenador": row[4],
            "garantia": row[5],
            "modelo_grafica": row[6],
            "procesador": row[7],
            "modelo_procesador": row[8],
            "frecuencia_procesador": row[9],
            "tamaño": row[10],
            "tipo_pantalla": row[11],
            "resolucion": row[12],
            "color": row[13],
            "ram": row[14],
            "sistema_operativo": row[15],
            "tarjeta_grafica": row[16]
        }
    else:
        ultimo_ordenador = None  # Si no hay registros, devolvemos None

    cursor.close()
    conexion.close()
    
    return ultimo_ordenador

if __name__ == "__main__":
    # Crear la tabla principal si no existe
    crear_tabla_principal()
    
    # Verificar si todas las entidades están en la tabla (y agregar columnas si es necesario)
    actualizar_tabla(ENTIDADES)
    
    # Procesar todos los PDFs en la carpeta
    procesar_pdfs_en_carpeta()
