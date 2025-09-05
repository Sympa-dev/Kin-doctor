from django.urls import path
from .views import *

app_name = 'doctors'

urlpatterns = [
    # Dashboard
    path('dashboard/', dashboard, name='dashboard'),

    # Rendez-vous
    path('appointments/', appointments, name='appointments'),
    path('appointments/<int:appointment_id>/<str:action>/', appointment_action, name='appointment_action'),
    path('appointments/<int:appointment_id>/start/', start_consultation, name='start_consultation'),

    # Patients
    path('patients/', patients, name='patients'),
    path('patients/<int:patient_id>/', patient_detail, name='patient_detail'),

    # Consultations
    path('consultations/', consultations, name='consultations'),
    path('consultations/<int:consultation_id>/', consultation_room, name='consultation_room'),

    # Profil et paramètres
    path('profile/', profile, name='profile'),
    path('profile/working-hours/', update_working_hours, name='update_working_hours'),
    path('profile/password/', update_password, name='update_password'),
]
