from django.urls import path
from . import views
from .views import obtener_respuesta
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path('', views.index, name='index'),  # Página principal
    path('upload_pdf/', views.upload_pdf, name='upload_pdf'),  # Página de subir PDF
    path('chatbot/', views.chatbot, name='chatbot'),  # Página para el chatbot
    path('get_response/', obtener_respuesta, name='get_response'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
