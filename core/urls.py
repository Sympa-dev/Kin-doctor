from django.urls import path
from .views import *

urlpatterns = [
   path('render_page/<str:page>/', render_page, name='render_page'),
   path('detail_patient/<int:id>/', detail_patient, name='detail_patient'),
   path('patient/<int:id>/pdf/', print_patient_pdf, name='print_patient_pdf'),
   path('edit_patient/<int:id>/', edit_patient, name='edit_patient'),
   path('consultation_list/', consultation_list, name="consultation_list"),
   path('detail_consultation/<int:id>/', detail_consultation, name='detail_consultation'),
   path('edit_consultation/<int:id>/', edit_consultation, name='edit_consultation'),
   path('examen/<int:id>/', examen, name='examen'),
   path('detail_examen/<int:id>/', detail_examen, name='detail_examen'),
   path('print_examen_pdf/<int:id>/', print_examen_pdf, name='print_examen_pdf'),
   # Laboratoire
   path('new_exam/', new_exam, name='new_exam'),

   # dashboard
   path('doctor_dashboard/', doctor_dashboard, name='doctor_dashboard'),
   path('nurse_dashboard/', nurse_dashboard, name='nurse_dashboard'),
   path('dashboard/', dashboard, name='dashboard'),

   # patient

   path('inscription_patient/', inscription_patient, name='inscription_patient'),
   path('liste_patient/', liste_patient, name='liste_patient'),
   path('recherche_patient/', recherche_patient, name="recherche_patient"),
   path('vitalsign/<int:id>/', vitalsign, name="vitalsign"),
   path('edit_sign_vital/<int:id>/', edit_sign_vital, name='edit_sign_vital'),
   path('save_patient/<int:id>/', save_patient, name="save_patient"),

   path('medicalrecord/', medicalrecord, name="medicalrecord"),
   path('medicalrecord_pdf/<int:id>/', medicalrecord_pdf, name="medicalrecord_pdf"),
   path('create_patient_file_from_model/<int:id>/', create_patient_file_from_model, name="create_patient_file_from_model"),
   path('notifications/', get_notifications, name='get_notifications'),
   path('detail_medicalrecord/<int:id>/', detail_medicalrecord, name='detail_medicalrecord'),

   # 
   path('add_consultation/<int:id>/', add_consultation, name='add_consultation'),
   path('plan_consultation/', plan_consultation, name='plan_consultation'),
   path('patient_consultation/<int:id>/', patient_consultation, name='patient_consultation'),
   path('registered/', registered, name='registered'),
   path('all_doctor/', all_doctor, name='all_doctor'),

   # Appointment
   path('appoitement/', appoitement, name='appoitement'),
   path('plan_rdv/', plan_appoint, name="plan_appoint")
]

