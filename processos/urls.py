from django.urls import path

from . import views

app_name = "processos"

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("painel/", views.painel, name="painel"),
    path("protocolo/<str:protocolo>/", views.protocolo_detalhe, name="protocolo_detalhe"),
]
