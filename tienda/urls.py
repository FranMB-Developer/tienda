"""
URL configuration for tienda project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from gestionpedidos import views

urlpatterns = [
    path('', views.home, name='home'),
    path('admin/', admin.site.urls),
    path('buscar_productos/', views.busqueda_productos, name='buscar_productos'),
    path('buscar/', views.buscar, name='buscar'),
    path('formulario_articulo/', views.formulario_articulo, name='formulario_articulo'),
    path('borrar_articulo/', views.borrar_articulo, name='borrar_articulo'),
    path('scrap/', views.scrap_view, name='scrap_view'),
]
