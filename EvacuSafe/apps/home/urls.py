from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('centers/', views.manage_center_view, name='manage_center'),
    path('centers/<int:center_id>/', views.update_center_view, name='update_center'),
    path('centers/<int:center_id>/archive/', views.archive_center_view, name='archive_center'),
    path('centers/<int:center_id>/restore/', views.restore_center_view, name='restore_center'),
    path('centers/<int:center_id>/delete/', views.delete_center_view, name='delete_center'),
    path('centers/<int:center_id>/resources/', views.update_resource_view, name='update_resource'),
    path('api/centers/live/', views.live_centers_api, name='live_centers_api'),
    path('incidents/create/', views.declare_incident_view, name='declare_incident'),
    path('incidents/<int:incident_id>/resolve/', views.resolve_incident_view, name='resolve_incident'),
]
