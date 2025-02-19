# ChatBot de Base de Datos de Ordenadores

## Descripción del Proyecto

Este proyecto es un chatbot que permite interactuar con una base de datos de ordenadores. Ofrece dos funcionalidades principales:

1. **Subida e interpretación de documentos:**

   - Los usuarios pueden subir archivos PDF con información sobre ordenadores.
   - Un agente procesa estos documentos, detecta entidades relevantes como modelo, marca, precio y especificaciones técnicas.
   - La información extraída se almacena automáticamente en la base de datos.

2. **Chat de consultas:**

   - Los usuarios pueden interactuar con un chatbot para realizar consultas específicas sobre los ordenadores registrados.
   - El chatbot convierte las preguntas en sentencias SQL y devuelve la información solicitada.

## Tecnologías Utilizadas

- **Django**: Framework utilizado para la parte de frontend y backend.
- **Azure Document Intelligence**: Servicio utilizado para analizar y extraer entidades de los documentos PDF.
- **Azure AI Service**: Modelo de inteligencia artificial encargado de interpretar las preguntas del usuario y traducirlas a consultas SQL.
- **PythonAnywhere**: Plataforma donde está alojada la aplicación.

## Preguntas Sugeridas

Aquí tienes algunas preguntas que puedes hacerle al chatbot:

- "¿Cuál es el ordenador más caro?"
- "Dime los ordenadores que tengan más de 16GB de RAM."
- "¿Cuáles son los ordenadores de la marca Dell?"
- "Muéstrame los portátiles con procesador Intel Core i7."

## Enlace a la Aplicación

Puedes probar la aplicación en el siguiente enlace:
[ChatBot de Ordenadores](https://pablohg2024.pythonanywhere.com/)
