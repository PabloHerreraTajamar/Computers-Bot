from django.http import JsonResponse, HttpResponse
from .openai_sql import obtener_consulta_sql, ejecutar_consulta_sql
from .to_database import analizar_pdf, conectar_db, obtener_ultimo_ordenador
import os
from django.shortcuts import render

# Vista para la página principal
def index(request):
    return render(request, 'chatbot/main.html') 

# Vista para manejar el upload de PDF
def upload_pdf(request):
    ultimo_ordenador = None  # Variable para almacenar el último ordenador subido
    
    if request.method == 'POST' and request.FILES['pdf_file']:
        # Obtener el archivo PDF directamente desde el formulario
        pdf_file = request.FILES['pdf_file']

        try:
            file_content = pdf_file.read()
            analizar_pdf(file_content)

            # Obtener el último ordenador de la base de datos
            ultimo_ordenador = obtener_ultimo_ordenador()

            return render(request, 'upload_pdf.html', {'ultimo_ordenador': ultimo_ordenador})

        except Exception as e:
            return HttpResponse(f"Error al procesar el PDF: {str(e)}")

    return render(request, 'upload_pdf.html', {'ultimo_ordenador': ultimo_ordenador})

# Vista para el chatbot
def chatbot(request):
    return render(request, 'chatbot/index.html')

def obtener_respuesta(request):
    pregunta = request.GET.get('message', '')

    if not pregunta:
        return JsonResponse({'error': 'No se proporcionó ninguna pregunta'}, status=400)

    # Generar consulta SQL a partir de la pregunta
    consulta_sql = obtener_consulta_sql(pregunta)
    print(f"Consulta SQL generada: {consulta_sql}")

    # Ejecutar la consulta en la base de datos
    resultado = ejecutar_consulta_sql(consulta_sql)
    print(f"Resultado de la consulta: {resultado}")

    # Si no se encuentra ningún resultado, retornamos un error
    if not resultado:
        return JsonResponse({'error': 'No se encontraron resultados'}, status=404)

    # Si todo salió bien, devolver el resultado en formato JSON
    return JsonResponse({'response': resultado}, safe=False)

