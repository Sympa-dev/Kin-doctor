from django.urls import path
from .views import (
    dashboard, appointments, documents, messages,
    find_doctor, book_appointment, medical_records,
    prescriptions, billing
)

app_name = 'patient'

urlpatterns = [
    path('', dashboard, name='dashboard'),
    path('find_doctor/', find_doctor, name='find_doctor'),
    path('book-appointment/<int:doctor_id>/', book_appointment, name='appointment'),
    path('appointments/', appointments, name='appointments'),
    path('documents/', documents, name='documents'),
    path('messages/', messages, name='messages'),
    path('medical-records/', medical_records, name='medical_records'),
    path('prescriptions/', prescriptions, name='prescriptions'),
    path('billing/', billing, name='billing'),
]