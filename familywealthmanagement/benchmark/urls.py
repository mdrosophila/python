from django.urls import path

from . import views

urlpatterns = [
    path('annualized-return/', views.annualized_return, name='annualized_return'),
]
