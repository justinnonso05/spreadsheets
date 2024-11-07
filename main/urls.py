from django.urls import path
from . import views

urlpatterns = [
    path('', views.graphs, name='graphs'),
    path('data/', views.dataView, name='data'),
    path('send-emails/', views.sendEmails, name='sendEmails'),
]