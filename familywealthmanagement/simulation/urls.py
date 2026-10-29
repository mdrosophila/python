from django.urls import path

from . import views

urlpatterns = [
    path('', views.asset_simulation, name='asset_simulation'),
]
