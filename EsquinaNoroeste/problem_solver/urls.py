from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('transporte/', views.transporte, name='transporte'),
    path('transporte-costo-minimo/', views.transporte_costo_minimo, name='transporte_costo_minimo'),
    
    # Rutas para comentarios
    path('comentario/', views.add_comment, name='add_comment'),
    path('comentario/exito/', views.comment_success, name='comment_success'),
]