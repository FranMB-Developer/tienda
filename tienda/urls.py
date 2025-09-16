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
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('scrap_demanda/', views.scrap_demanda_view, name='scrap_demanda'),
    path('scrap_generacion/', views.scrap_generacion_view, name='scrap_generacion'),
    path('scrap_almacenamiento/', views.scrap_almacenamiento_view, name='scrap_almacenamiento'),
    path('scrap_precio/', views.scrap_precio_view, name='scrap_precio'),
    path('scrap_view_graph/', views.scrap_view_graph, name='scrap_view_graph'),
    path("scrap_view_graph_precio/", views.scrap_graph_precio_view, name="scrap_view_graph_precio"),
    path("scrap_comparativa/", views.scrap_comparativa_view, name="scrap_comparativa"),
    path("scrap_view_graph_comparativa/", views.scrap_comparativa_graph_view, name="scrap_comparativa_graph_view"),
]

