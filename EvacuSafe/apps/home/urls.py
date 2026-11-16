from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('centers/', views.manage_center_view, name='manage_center'),
]
