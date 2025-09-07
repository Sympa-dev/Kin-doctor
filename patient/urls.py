from django.urls import path
from .views import (
    dashboard, appointments, documents, messages,
    find_doctor, book_appointment, medical_records,
    prescriptions, billing, appointment_notifications, all_notifications
)

app_name = 'patient'

urlpatterns = [
    path('', dashboard, name='dashboard'),
    path('find_doctor/', find_doctor, name='find_doctor'),
    path('book-appointment/<int:doctor_id>/', book_appointment, name='appointment'),
    path('appointments/', appointments, name='appointments'),
    path('appointment-notifications/', appointment_notifications, name='appointment_notifications'),
    path('all-notifications/', all_notifications, name='all_notifications'),
    path('documents/', documents, name='documents'),
    path('messages/', messages, name='messages'),
    path('medical-records/', medical_records, name='medical_records'),
    path('prescriptions/', prescriptions, name='prescriptions'),
    path('billing/', billing, name='billing'),
]