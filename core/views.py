from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.db.models import Q
from .models import *
import re
from rest_framework import serializers
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from datetime import datetime
from django.utils.timezone import make_aware
import joblib
import pandas as pd
import os
from django.conf import settings
from django.db import IntegrityError
from django.template.loader import get_template
from django.http import HttpResponse
from django.template import Context, Template
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from django.contrib.auth import get_user_model

# others imports 

import random
import string
from django.core.mail import send_mail
from django.contrib.auth.hashers import make_password
from django.conf import settings


User = get_user_model()

def index(request):
    return render(request, 'core/index.html')

def render_page(request, page):
    try:
        template_name = f'core/{page}.html'
        context = {}

        if page == 'dashboard':
            template_name = 'core/dashboard.html'
            return render(request, template_name, context)

        elif page == 'register_docteur':

            departments = Department.objects.all()

            context = {
                'departments': departments
            }

            template_name = 'core/register_docteur.html'

            if request.method == 'POST':

                try:
                    # Nettoyer et valider les données
                    name = request.POST.get('name', '').strip()
                    first_name = request.POST.get('first_name', '').strip()
                    last_name = request.POST.get('last_name', '').strip()
                    gender = request.POST.get('gender', '').strip()
                    birth_date = request.POST.get('birth_date', '').strip()
                    phone_number = request.POST.get('phone_number', '').strip()
                    email = request.POST.get('email', '').strip()
                    order_number = request.POST.get('order_number', '').strip()
                    department_id = request.POST.get('department', '').strip()
                    address = request.POST.get('address', '').strip()

                    # Validation des champs obligatoires

                    if not all([name, first_name, last_name, gender, birth_date, 
                              phone_number, email, order_number, department_id, address]):
                        messages.error(request, 'Tous les champs sont obligatoires')
                        return render(request, template_name, context)

                    # Validation du format email

                    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                        messages.error(request, "Format d'email invalide")
                        return render(request, template_name, context)

                    # Vérifier si l'email existe déjà

                    if Doctor.objects.filter(email=email).exists():
                        messages.error(request, 'Un médecin avec cet email existe déjà')
                        return render(request, template_name, context)

                    # Vérifier si le numéro d'ordre existe déjà

                    if Doctor.objects.filter(order_number=order_number).exists():
                        messages.error(request, "Ce numéro d'ordre est déjà utilisé")
                        return render(request, template_name, context)

                    # Récupérer le département de manière sécurisée

                    try:
                        department = Department.objects.get(id=department_id)
                    except Department.DoesNotExist:
                        messages.error(request, 'Département invalide')
                        return render(request, template_name, context)

                    # Créer le médecin avec les données validées

                    doctor = Doctor.objects.create(
                        name=name,
                        first_name=first_name,
                        last_name=last_name,
                        gender=gender,
                        birth_date=birth_date,
                        phone_number=phone_number,
                        email=email,
                        order_number=order_number,
                        department=department,
                        address=address,
                    )

                    messages.success(request, 'Médecin enregistré avec succès')
                    return redirect('render_page', page='dashboard')

                except Exception as e:
                    messages.error(request, f'Une erreur est survenue: {str(e)}')
                    return render(request, template_name, context)

            return render(request, template_name, context)
        
        elif page == 'liste_medecin':

            doctors = Doctor.objects.all()

            context = {
                'doctors': doctors
            }

            template_name = 'core/liste_medecin.html'

            return render(request, template_name, context)

        return render(request, template_name, context)

    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)
    
def liste_patient(request, *args, **kwargs):

    patients = Patients.objects.all()

    context = {
        'patients': patients
    }

    return render(request, "core/liste_patient.html", context)

def recherche_patient(request, *args, **kwargs):

    query = request.POST.get("q", '')
    patients = Patients.objects.filter(name__icontains=query) if query else Patients.objects.all()

    context ={
        'patients': patients,
        'query': query
    }

    return render(request, "core/liste_patient.html", context)

def detail_patient(request, id):

    patient = Patients.objects.get(id=id)

    signes_vitaux = VitalSigns.objects.filter(patient=patient)

    context = {
        'patient': patient,
        'signes_vitaux': signes_vitaux
    }
    return render(request, 'core/detail_patient.html', context)

def print_patient_pdf(request, id):
    try:
        # Récupérer le patient
        patient = get_object_or_404(Patients, id=id)
        
        # Créer la réponse HTTP avec le type de contenu PDF
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="patient_{patient.last_name}_{patient.reference}_{datetime.now().strftime("%Y%m%d")}.pdf"'
        # Créer le PDF
        p = canvas.Canvas(response, pagesize=letter)
        
        # En-tête du document
        p.setFont("Helvetica-Bold", 20)
        p.drawString(200, 800, "DOCTAPLUS")
        
        p.setFont("Helvetica", 12)
        p.drawString(200, 780, "Centre Médical")
        p.drawString(200, 765, "123 Avenue de la Santé")
        p.drawString(200, 750, "Kinshasa, RD Congo")
        p.drawString(200, 735, "Tel: +243 123 456 789")
        
        # Ligne de séparation
        p.line(50, 720, 550, 720)
        
        # Titre de la fiche
        p.setFont("Helvetica-Bold", 16)
        p.drawString(50, 700, "Fiche Patient")
        
        # Date d'impression
        p.setFont("Helvetica", 10)
        p.drawString(400, 700, f"Date d'impression: {datetime.now().strftime('%d/%m/%Y')}")
        
        # Informations du patient
        p.setFont("Helvetica", 12)
        y = 650  # Position verticale initiale ajustée
        
        # Informations personnelles
        p.drawString(50, y, f"Nom: {patient.last_name}")
        p.drawString(50, y-20, f"Prénom: {patient.first_name}")
        p.drawString(50, y-40, f"Date de naissance: {patient.birth_date}")
        p.drawString(50, y-60, f"Genre: {patient.gender}")
        p.drawString(50, y-80, f"Téléphone: {patient.phone_number}")
        p.drawString(50, y-100, f"Email: {patient.email or 'Non renseigné'}")
        
        # Contact d'urgence
        p.setFont("Helvetica-Bold", 14)
        p.drawString(50, y-260, "Contact d'urgence")
        p.setFont("Helvetica", 12)
        p.drawString(50, y-280, f"Nom: {patient.relative_name}")
        p.drawString(50, y-300, f"Téléphone: {patient.relative_phone}")
        p.drawString(50, y-320, f"Mobile: {patient.relative_mobile or 'Non renseigné'}")
        
        # Ligne de séparation
        p.line(50, y-340, 550, y-340)
        
        # Finaliser le PDF
        p.showPage()
        p.save()
        
        return response
        
    except Exception as e:
        messages.error(request, f'Erreur lors de la génération du PDF: {str(e)}')
        return redirect('detail_patient', id=id)
    
def edit_patient(request, id):
    try:
        patient = Patients.objects.get(id=id)

        if request.method == 'POST':
            patient.first_name = request.POST.get('first_name')
            patient.middle_name = request.POST.get('name') 
            patient.last_name = request.POST.get('last_name')
            patient.gender = request.POST.get('gender')
            patient.birth_date = request.POST.get('birth_date')
            patient.phone_number = request.POST.get('phone_number')
            patient.email_address = request.POST.get('email')
            patient.marital_status = request.POST.get('marital_status')
            patient.street_address = request.POST.get('street_address')
            patient.house_number = request.POST.get('house_number')
            patient.province = request.POST.get('province')
            patient.district = request.POST.get('district') 
            patient.municipality = request.POST.get('municipality')
            patient.neighborhood = request.POST.get('neighborhood')

            patient.save()
            return redirect('detail_patient', id=id)

        context = {
            'patient': patient
        }
        return render(request, 'core/edit_patient.html', context)

    except Exception as e:
        messages.error(request, f'Une erreur est survenue: {str(e)}')
        return redirect('detail_patient', id=id)
    
def plan_consultation(request):

    patients = Patients.objects.all()
    doctors = Doctor.objects.all()
    specialties = Specialty.objects.all()
    consultation_types = ConsultationType.objects.all()


    consulted = Patients.objects.filter(consultation_status="Consultation effectuée")
    not_consulted = Patients.objects.filter(consultation_status="En attente de consultation")

    if request.method == 'POST':
        consultation_type_id = request.POST.get('consultation_type')
        specialty_id = request.POST.get('specialty')
        doctor_id = request.POST.get('doctor')
        consultation_date = request.POST.get('consultation_date')
        patient_id = request.POST.get('patient')

        patient = get_object_or_404(Patients, id=patient_id)

        # Validation des données
        if not (consultation_type_id and specialty_id and doctor_id and consultation_date, patient):
            messages.error(request, "Veuillez remplir tous les champs obligatoires.")
        else:
            try:
                # Récupérer les objets associés
                consultation_type = get_object_or_404(ConsultationType, id=consultation_type_id)
                specialty = get_object_or_404(Specialty, id=specialty_id)
                doctor = get_object_or_404(Doctor, id=doctor_id)

                # Créer la consultation
                Consultation.objects.create(
                    type=consultation_type,
                    patient=patient,
                    specialty=specialty,
                    doctor=doctor,
                    consultation_date=consultation_date,
                )

                messages.success(request, "Consultation planifiée avec succès.")
                return redirect('liste_patient')

            except Exception as e:
                messages.error(request, f"Une erreur s'est produite : {e}")

    context = {
        'doctors': doctors,
        'specialties': specialties,
        'patients': patients,
        'consulted': consulted,
        'not_consulted': not_consulted,
        'consultation_types': consultation_types
    }
    return render(request, 'core/plan_consultation.html', context)

def consultation_detail(request, id):
    consultation = Consultation.objects.get(id=id)
    context = {
        'consultation': consultation
    }
    return render(request, 'core/consultation_detail.html', context)

def edit_consultation(request, id):
    """
    View to edit an existing consultation, with proper handling of dates and time zones.
    """
    consultation = get_object_or_404(Consultation, id=id)
    
    if request.method == 'POST':
        consultation_type_id = request.POST.get('consultation_type')
        specialty_id = request.POST.get('specialty')
        doctor_id = request.POST.get('doctor')
        consultation_date = request.POST.get('consultation_date')
        notes = request.POST.get('notes')
        
        if not (consultation_type_id and specialty_id and doctor_id and consultation_date):
            messages.error(request, "Veuillez remplir tous les champs obligatoires.")
        else:
            try:
                # Mise à jour des champs de la consultation
                consultation.type = get_object_or_404(ConsultationType, id=consultation_type_id)
                consultation.specialty = get_object_or_404(Specialty, id=specialty_id)
                consultation.doctor = get_object_or_404(Doctor, id=doctor_id)
                
                # Conversion de la date avec gestion des fuseaux horaires
                try:
                    parsed_date = datetime.strptime(consultation_date, "%Y-%m-%d")  # Format attendu : YYYY-MM-DD
                    consultation.consultation_date = make_aware(parsed_date)
                except ValueError:
                    messages.error(request, "La date fournie est invalide. Veuillez utiliser le format AAAA-MM-JJ.")
                    return redirect('edit_consultation', id=id)

                consultation.notes = notes
                consultation.save()

                messages.success(request, "La consultation a été modifiée avec succès.")
                return redirect('detail_consultation', id=consultation.id)

            except Exception as e:
                messages.error(request, f"Une erreur s'est produite lors de la modification : {str(e)}")
    
    # Pré-remplir les données existantes pour GET
    context = {
        'consultation': consultation,
        'doctors': Doctor.objects.all(),
        'specialties': Specialty.objects.all(), 
        'consultation_types': ConsultationType.objects.all()
    }
    return render(request, 'core/edit_consultation.html', context)

def detail_consultation(request, id):
    consultation = Consultation.objects.get(id=id)
    context = {
        'consultation': consultation
    }
    return render(request, 'core/detail_consultation.html', context)

def consultation_list(request):

    consultations = Consultation.objects.filter(doctor=True)

    context = {
        'consultations': consultations
    }
    return render(request, 'core/consultation_list.html', context)

def examen(request, id):
    
    consultation = Consultation.objects.all()
    exam_types = ExamenType.objects.all()

    if request.method == 'POST':
        exam_type_id = request.POST.get('exam_type')
        exam_date = request.POST.get('exam_date')
        exam_id = request.POST.get('exam_id')

        if not exam_type_id or not exam_date:
            messages.error(request, "Veuillez remplir tous les champs obligatoires.")
            return redirect('examen', id=id)

        try:
            # Conversion de la date
            parsed_date = datetime.strptime(exam_date, "%Y-%m-%d")
            aware_date = make_aware(parsed_date)
            
            exam_type = get_object_or_404(ExamenType, id=exam_type_id)

            if exam_id:
                # Modification d'un examen existant
                examen = get_object_or_404(Examen, id=exam_id)
                examen.exam_type = exam_type
                examen.exam_date = aware_date
                examen.save()
                messages.success(request, "L'examen a été modifié avec succès.")
            else:
                # Création d'un nouvel examen
                Examen.objects.create(
                    consultation=consultation,
                    exam_type=exam_type,
                    exam_date=aware_date,
                    status='pending'
                )
                messages.success(request, "L'examen a été créé avec succès.")


        except ValueError:
            messages.error(request, "La date fournie est invalide. Veuillez utiliser le format AAAA-MM-JJ.")
            return redirect('examen', id=id)
        except Exception as e:
            messages.error(request, f"Une erreur s'est produite : {str(e)}")
            return redirect('examen', id=id)

    context = {
        'consultation': consultation,
        'exam_types': exam_types
    }
    
    return render(request, 'core/examen.html', context)

def detail_examen(request, id):
    examen = get_object_or_404(Examen, id=id)
    context = {
        'examen': examen
    }
    return render(request, 'core/detail_examen.html', context)

def print_examen_pdf(request, id):
    try:
        # Récupérer l'examen
        examen = get_object_or_404(Examen, id=id)
        
        # Créer la réponse HTTP avec le type de contenu PDF
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="rapport_examen_{examen.id}_{datetime.now().strftime("%Y%m%d")}.pdf"'
        
        # Créer le PDF en format A4
        p = canvas.Canvas(response, pagesize=A4)
        
        # Logo
        try:
            logo_path = os.path.join(settings.MEDIA_ROOT, 'media/doctaplus.png')
            p.drawImage(logo_path, 50, 750, width=100, height=100)
        except:
            # Skip logo if file not found
            pass
        
        # En-tête du document
        p.setFont("Helvetica-Bold", 24)
        p.drawString(200, 800, "DOCTAPLUS")
        
        p.setFont("Helvetica", 14)
        p.drawString(200, 775, "Centre Médical")
        p.drawString(200, 755, "123 Avenue de la Santé") 
        p.drawString(200, 735, "Kinshasa, RD Congo")
        p.drawString(200, 715, "Tel: +243 123 456 789")
        
        # Ligne de séparation avec épaisseur
        p.setLineWidth(2)
        p.line(50, 695, 550, 695)
        
        # Titre du rapport avec style amélioré
        p.setFont("Helvetica-Bold", 20)
        p.drawString(50, 665, "RAPPORT D'EXAMEN")
        
        # Date d'impression avec style amélioré
        p.setFont("Helvetica-Bold", 12)
        p.drawString(350, 665, f"Date d'impression: {datetime.now().strftime('%d/%m/%Y')}")
        
        # Position verticale initiale
        y = 620
        
        # Cadre pour les détails de l'examen
        p.rect(40, y-60, 520, 50)
        p.setFont("Helvetica-Bold", 14)
        p.drawString(50, y, "DÉTAILS DE L'EXAMEN")
        p.setFont("Helvetica", 12)
        p.drawString(50, y-25, f"Type d'examen: {examen.exam_type.name}")
        p.drawString(50, y-45, f"Date de l'examen: {examen.exam_date.strftime('%d/%m/%Y')}")
        
        # Statut avec badge coloré
        status_text = f"Statut: {examen.status}"
        if examen.status == 'completed':
            p.setFillColorRGB(0, 0.5, 0)  # Vert
        elif examen.status == 'pending':
            p.setFillColorRGB(0.8, 0.6, 0)  # Orange
        else:
            p.setFillColorRGB(0.8, 0, 0)  # Rouge
        p.drawString(300, y-45, status_text)
        p.setFillColorRGB(0, 0, 0)  # Retour au noir
        
        # Mise à jour de y pour la section suivante
        y = y - 100
        
        # Cadre pour les informations du patient
        p.rect(40, y-80, 520, 80)
        p.setFont("Helvetica-Bold", 14)
        p.drawString(50, y, "INFORMATIONS DU PATIENT")
        p.setFont("Helvetica", 12)
        p.drawString(50, y-30, f"Nom complet: {examen.consultation.patient.last_name} {examen.consultation.patient.first_name}")
        p.drawString(50, y-50, f"Référence: {examen.consultation.patient.reference}")
        p.drawString(50, y-70, f"Date de naissance: {examen.consultation.patient.birth_date}")

        # Mise à jour de y pour la section suivante
        y = y - 120

        # Cadre pour les détails médicaux
        p.rect(40, y-140, 520, 120)
        p.setFont("Helvetica-Bold", 14)
        p.drawString(50, y, "DÉTAILS MÉDICAUX")
        
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y-30, "Symptômes:")
        p.setFont("Helvetica", 11)
        p.drawString(60, y-50, f"{examen.consultation.symptoms}")
        
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y-80, "Diagnostic:")
        p.setFont("Helvetica", 11)
        p.drawString(60, y-100, f"{examen.consultation.diagnosis}")
        
        # Mise à jour de y pour la section suivante
        y = y - 180
        
        # Cadre pour les informations du médecin
        p.rect(40, y-80, 520, 80)
        p.setFont("Helvetica-Bold", 14)
        p.drawString(50, y, "MÉDECIN TRAITANT")
        p.setFont("Helvetica", 12)
        p.drawString(50, y-30, f"Dr. {examen.consultation.doctor.last_name} {examen.consultation.doctor.first_name}")
        p.drawString(50, y-50, f"Spécialité: {examen.consultation.specialty.name}")
        
        # Pied de page
        p.setFont("Helvetica-Oblique", 8)
        p.drawString(50, 50, "Ce document est un rapport médical confidentiel. Toute reproduction non autorisée est strictement interdite.")
        p.drawString(50, 35, f"Document généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}")
        
        # Finaliser le PDF
        p.showPage()
        p.save()
        
        return response
        
    except Exception as e:
        messages.error(request, f'Erreur lors de la génération du PDF: {str(e)}')
        return redirect('detail_examen', id=id)
    
# Laboratoire
def new_exam(request):
    return render(request, 'core/new_exam.html')

def in_progress_exams(request):
    return render(request, 'core/in_progress_exams.html')

def finished_exams(request):
    return render(request, 'core/finished_exams.html')



# Doctor dashboard
def doctor_dashboard(request):

    consultations = Consultation.objects.count()
    patient = Patients.objects.count()

    context = {
        'consultations':consultations,
        'patient': patient
    }
    return render(request, 'core/doctor_dashboard.html', context)

def patient_consultation(request, id):

    consultation = get_object_or_404(Consultation, id=id)
    sign_vital = VitalSigns.objects.filter(patient=consultation.patient).first()

    if request.method == 'POST':
        consultation.symptoms = request.POST.get('symptoms')
        consultation.diagnosis = request.POST.get('diagnosis')
        consultation.notes = request.POST.get('notes')
        consultation.status = request.POST.get('status')

        consultation.save()

        messages.success(request, "Consultation mise à jour avec succès.")
        return redirect('patient_consultation', id=id)

    context = {
        'consultation': consultation,
        'sign_vital': sign_vital
    }
    return render(request, 'core/patient_consultation.html', context)

def nurse_dashboard(request):
    patient = Patients.objects.all()

    patient_count = patient.count()

    context = {
        'patient': patient,
        'patient_count': patient_count
    }
    return render(request, 'core/nurse_dashboard.html', context)

def inscription_patient(request, *args, **kwargs):

    if request.method == 'POST':
        # Récupérer les données du formulaire
        name = request.POST.get('name')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        birth_date = request.POST.get('birth_date')
        gender = request.POST.get('gender')
        phone_number = request.POST.get('phone_number')
        email = request.POST.get('email')

        # les informations sur la tuteur
        relative_name = request.POST.get('relative_name')
        relative_phone = request.POST.get('relative_phone')
        relative_address = request.POST.get('relative_address')

        # Vérifier si les champs obligatoires sont remplis
        if not all([name, first_name, last_name, birth_date, gender, phone_number, email]):
            messages.error(request, "Veuillez remplir tous les champs obligatoires.")
            return render(request, 'core/inscription_patient.html')
        
        if Patients.objects.filter(email=email).exists():
            messages.error(request, "Cette adresse mail est déjà utilisé par un autre patient !")
            return render(request, "core/inscription_patient.html")
        
        # Vérifie que le genre du patient a été sélectionné
        if gender:
            messages.error(request, "Veuillez choisir un genre pour ce patient !")
            return render(request, "core/inscription_patient.html")

        try:
            # Création du patient
            patient = Patients.objects.create(
                name=name,
                first_name=first_name,
                last_name=last_name,
                birth_date=birth_date,
                gender=gender,
                phone_number=phone_number,
                email=email,
                relative_name=relative_name,
                relative_address=relative_address,
                relative_phone=relative_phone
            )

            messages.success(request, "Patient enregistré avec succès.")
            return redirect('vitalsign', id=patient.id)

        except IntegrityError:
            messages.error(request, "Erreur lors de l'enregistrement du patient.")
            return redirect('inscription_patient')

    return render(request, 'core/inscription_patient.html')

def vitalsign(request, id):

    # Récupérer le patient ou renvoyer une erreur 404 si non trouvé

    patient = get_object_or_404(Patients, id=id)
    sign_vital = VitalSigns.objects.filter(patient=patient).select_related('patient').first()

    if request.method == 'POST':
        # Récupérer les données du formulaire
        temperature = request.POST.get('temperature')
        blood_pressure_systolic = request.POST.get('blood_pressure_systolic')
        blood_pressure_diastolic = request.POST.get('blood_pressure_diastolic')
        pulse = request.POST.get('pulse')
        respiratory_rate = request.POST.get('respiratory_rate')
        oxygen_saturation = request.POST.get('oxygen_saturation')
        weight = request.POST.get('weight')
        height = request.POST.get('height')

        # Validation des données (optionnel, mais recommandé)
        try:
            # Convertir les valeurs en float ou int si elles existent
            temperature = float(temperature) if temperature else None
            blood_pressure_systolic = int(blood_pressure_systolic) if blood_pressure_systolic else None
            blood_pressure_diastolic = int(blood_pressure_diastolic) if blood_pressure_diastolic else None
            pulse = int(pulse) if pulse else None
            respiratory_rate = int(respiratory_rate) if respiratory_rate else None
            oxygen_saturation = float(oxygen_saturation) if oxygen_saturation else None
            weight = float(weight) if weight else None
            height = float(height) if height else None
        except (ValueError, TypeError):
            messages.error(request, "Veuillez entrer des valeurs valides pour les signes vitaux.")
            return redirect('vitalsign', id=patient.id)

        # Créer une instance et sauvegarder dans la base de données
        VitalSigns.objects.create(
            patient=patient,
            temperature=temperature,
            blood_pressure_systolic=blood_pressure_systolic,
            blood_pressure_diastolic=blood_pressure_diastolic,
            pulse=pulse,
            respiratory_rate=respiratory_rate,
            oxygen_saturation=oxygen_saturation,
            weight=weight,
            height=height,
        )

        messages.success(request, "Les signes vitaux ont été enregistrés avec succès.")
        return redirect('vitalsign', id=patient.id)

    # Contexte pour le rendu du template
    context = {
        'patient': patient,
        'sign_vital': sign_vital
    }

    return render(request, "core/vital_sign.html", context)

def edit_sign_vital(request, id):
    sign_vital = get_object_or_404(VitalSigns, id=id)

    if request.method == 'POST':
        # Récupérer les données du formulaire
        temperature = request.POST.get('temperature')
        blood_pressure_systolic = request.POST.get('blood_pressure_systolic')
        blood_pressure_diastolic = request.POST.get('blood_pressure_diastolic')
        pulse = request.POST.get('pulse')
        respiratory_rate = request.POST.get('respiratory_rate')
        oxygen_saturation = request.POST.get('oxygen_saturation')
        weight = request.POST.get('weight')
        height = request.POST.get('height')

        # Mettre à jour les signes vitaux
        sign_vital.temperature = temperature
        sign_vital.blood_pressure_systolic = blood_pressure_systolic
        sign_vital.blood_pressure_diastolic = blood_pressure_diastolic
        sign_vital.pulse = pulse
        sign_vital.respiratory_rate = respiratory_rate
        sign_vital.oxygen_saturation = oxygen_saturation
        sign_vital.weight = weight
        sign_vital.height = height
        sign_vital.save()

        messages.success(request, "Les signes vitaux ont été mis à jour avec succès.")
        return redirect('vitalsign', id=sign_vital.patient.id)

    # Contexte pour le rendu du template
    context = {
        'sign_vital': sign_vital
    }

    return render(request, "core/vital_sign.html", context)


def save_patient(request, id):
    # Récupérer le patient
    patient = get_object_or_404(Patients, id=id)

    # Vérifier la méthode de la requête
    if request.method == 'POST':
        # Récupérer ou créer un dossier médical associé au patient
        medical_record, created = MedicalRecord.objects.get_or_create(patient=patient)

        # Mettre à jour les champs du dossier médical
        medical_record.file = request.FILES.get('file', medical_record.file)  # Met à jour uniquement si un fichier est soumis
        medical_record.notes = request.POST.get('notes', medical_record.notes)  # Exemple d'ajout d'une note médicale

        # Sauvegarder les modifications
        medical_record.save()

        # Message de confirmation
        if created:
            messages.success(request, "Le dossier médical du patient a été créé et enregistré avec succès.")
        else:
            messages.success(request, "Le dossier médical du patient a été mis à jour avec succès.")

        # Redirection vers une autre vue (ex: détails du patient)
        return redirect('vitalsign', id=patient.id)

    # Contexte pour le template
    context = {
        'patient': patient,
        'medical_record': patient.medical_record if hasattr(patient, 'medical_record') else None,
    }

    # Rendu du template
    return render(request, "core/save_patient.html", context)

def medicalrecord(request, *args, **kwargs):
    medical_record = MedicalRecord.objects.all()
    return render(request, "core/MedicalRecord.html", {'medical_record': medical_record})

def detail_medicalrecord(request, id):
    medical_record = get_object_or_404(MedicalRecord, id=id)
    return render(request, "core/detail_medicalrecord.html", {'medical_record': medical_record})


def medicalrecord_pdf(request, id):
    try:
        # Récupérer le dossier médical (MedicalRecord) lié à l'id
        medical_record = get_object_or_404(MedicalRecord, id=id)
        patient = medical_record.patient  # Accéder à l'objet Patient lié au dossier médical
        
        # Créer la réponse HTTP avec le type de contenu PDF
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="rapport_patient_{patient.id}_{datetime.now().strftime("%Y%m%d")}.pdf"'
        
        # Créer le PDF en format A4
        p = canvas.Canvas(response, pagesize=A4)
         
        # Logo (vous pouvez le mettre ou non selon votre besoin)
        try:
            logo_path = os.path.join(settings.MEDIA_ROOT, 'media/doctaplus.png')
            p.drawImage(logo_path, 50, 750, width=100, height=100)
        except:
            # Skip logo if file not found
            pass
        
        # En-tête du document
        p.setFont("Helvetica-Bold", 24)
        p.drawString(200, 800, "DOCTAPLUS")
        
        p.setFont("Helvetica", 14)
        p.drawString(200, 775, "Centre Médical")
        p.drawString(200, 755, "123 Avenue de la Santé") 
        p.drawString(200, 735, "Kinshasa, RD Congo")
        p.drawString(200, 715, "Tel: +243 123 456 789")
        
        # Ligne de séparation avec épaisseur

        p.setLineWidth(2)
        p.line(50, 695, 550, 695)
        
        # Titre du rapport avec style amélioré

        p.setFont("Helvetica-Bold", 20)
        p.drawString(50, 665, "RAPPORT DE PATIENT")
        
        # Date d'impression avec style amélioré
        p.setFont("Helvetica-Bold", 12)
        p.drawString(350, 665, f"Date d'impression: {datetime.now().strftime('%d/%m/%Y')}")
        
        # Position verticale initiale
        y = 620
        
        # Informations du patient
        p.setFont("Helvetica-Bold", 14)
        p.drawString(50, y, "INFORMATIONS DU PATIENT")
        
        # Remplir les détails du patient

        p.setFont("Helvetica", 12)

        p.drawString(50, y-25, f"Nom complet: {patient.last_name} {patient.first_name}")
        p.drawString(50, y-45, f"Référence: {patient.reference}")
        p.drawString(50, y-65, f"Date de naissance: {patient.birth_date.strftime('%d/%m/%Y')}")
        
        # Mise à jour de y pour la section suivante
        y = y - 100
        
        # Détails médicaux (optionnel)
        p.setFont("Helvetica-Bold", 14)
        p.drawString(50, y, "DÉTAILS MÉDICAUX")
        
        # Mise à jour de y pour la section suivante
        y = y - 100
        
        # Pied de page
        p.setFont("Helvetica-Oblique", 8)
        p.drawString(50, 50, "Ce document est un rapport médical confidentiel. Toute reproduction non autorisée est strictement interdite.")
        p.drawString(50, 35, f"Document généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}")
        
        # Finaliser le PDF

        p.showPage()
        p.save()
        
        return response
        
    except Exception as e:
        messages.error(request, f'Erreur lors de la génération du PDF: {str(e)}')
        return redirect('detail_patient', id=id)  # Assurez-vous que la redirection vers la bonne vue est effectuée



def get_notifications(request, *args, **kwargs):

    # Récupérer les consultations récemment créées (vous pouvez personnaliser la logique ici)

    consultations = Consultation.objects.order_by('-consultation_date')[:5]  # Les 5 dernières consultations

    notifications = [
        {
            "patient_name": f"{consultation.patient.first_name} {consultation.patient.last_name}",
            "consultation_date": consultation.consultation_date.strftime('%Y-%m-%d %H:%M:%S')
        }
        for consultation in consultations
    ]
    return JsonResponse({"notifications": notifications})

def create_patient_file_from_model(request, id):

    # Récupérer les données du modèle MedicalRecord

    medical_record = MedicalRecord.objects.get(id=id)

    # Créer un canvas pour le PDF
    
    try:
        # Récupérer l'enregistrement MedicalRecord correspondant
        medical_record = MedicalRecord.objects.get(id=id)

        output_filename = f"fiche_patient_{medical_record.id}.pdf"

        # Créer un canvas pour le fichier PDF
        pdf = canvas.Canvas(output_filename, pagesize=A4)
        width, height = A4

        # Titre et entête de l'hôpital
        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawString(30, height - 50, "Hôpital Général de Kinshasa")
        pdf.setFont("Helvetica", 10)
        pdf.drawString(30, height - 70, "123 Avenue de la Santé, Kinshasa, RDC")
        pdf.drawString(30, height - 85, "Téléphone : +243 900 123 456 | Email : contact@hopital-kinshasa.cd")

        # Ligne de séparation
        pdf.setStrokeColor(colors.black)
        pdf.line(30, height - 95, width - 30, height - 95)

        # Titre du document
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(30, height - 120, "FICHE DE MALADE")

        # Informations du patient
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(30, height - 150, "Informations du Patient")
        pdf.setFont("Helvetica", 10)
        pdf.drawString(40, height - 170, f"Nom : {medical_record.patient.name}")
        pdf.drawString(40, height - 185, f"Prenom : {medical_record.patient.first_name}")
        pdf.drawString(40, height - 200, f"Postnom : {medical_record.patient.last_name}")
        pdf.drawString(40, height - 215, f"Sexe : {medical_record.patient.gender}")
        pdf.drawString(40, height - 230, f"Numéro de dossier : {medical_record.number}")

        # Signature et Observations
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(30, height - 240, "Signature et Observations")
        pdf.setFont("Helvetica", 10)
        pdf.drawString(40, height - 260, "Signature du Médecin : ___________________________")
        pdf.drawString(40, height - 280, "Observations : ___________________________________")
        pdf.drawString(40, height - 300, "Fait à Kinshasa, le : ______________________        ___________________________________")

        # Sauvegarder et fermer le PDF

        pdf.save()

        with open(output_filename, 'rb') as pdf_file:
            response = HttpResponse(pdf_file.read(), content_type='application/pdf')

            # Modifier l'en-tête Content-Disposition pour forcer le téléchargement

            response['Content-Disposition'] = f'attachment; filename="{output_filename}"'

            return response

    except Exception as e:
        messages.error(request, f"Erreur lors de la génération du PDF : {e}")
        return redirect('detail_medicalrecord', id=id)

def add_consultation(request, id):

    if request.method == 'POST':

        try:
            patient = Patients.objects.get(id=id)

            consultation = Consultation.objects.create(
                patient=patient,
                consultation_date=datetime.now(),
            )

            messages.success(request, "Le patient a été envoyé à la consultation")
            return redirect('detail_patient', id=patient.id)

        except Exception as e:

            messages.error(request, f"Erreur lors de la génération du PDF : {e}")
            return redirect('detail_patient', id=id)

# fonction pour les medecins 

def dashboard(request, *args, **kwargs):
    return render(request, 'core/dashboard.html')

def all_doctor(request, *args, **kwargs):

    doctors = User.objects.filter(is_doctor=True)

    context = {
        'doctors': doctors
    }

    return render(request, 'core/all_doctor.html', context)

def generate_password(length=10):
    """Génère un mot de passe aléatoire"""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def registered(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        user_type = request.POST.get('user_type', '').strip()

        # Vérifier que tous les champs sont remplis
        if not all([username, first_name, last_name, email, user_type]):
            messages.error(request, "Tous les champs sont obligatoires.")
            return redirect('registered')

        # Vérifier si l'utilisateur existe déjà
        if User.objects.filter(username=username).exists():
            messages.error(request, "Ce nom d'utilisateur existe déjà.")
            return redirect('registered')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Cet email est déjà utilisé.")
            return redirect('registered')

        # Dictionnaire des types d'utilisateurs valides
        boolean_fields = {
            'doctor': 'is_doctor',
            'nurse': 'is_nurse',
            'receptionist': 'is_receptionist',
            'pharmacist': 'is_pharmacist',
            'lab_technician': 'is_laboratory_technician',
            'admin': 'is_admin'
        }

        if user_type not in boolean_fields:
            messages.error(request, "Type d'utilisateur invalide.")
            return redirect('registered')

        # Générer un mot de passe aléatoire
        
        password = generate_password()
        hashed_password = make_password(password)

        # Créer un utilisateur avec tous les rôles à False par défaut

        user = User.objects.create(
            username=username,
            email=email,
            password=hashed_password,
            first_name=first_name,
            last_name=last_name,
            must_change_password=True,  # Forcer le changement de mot de passe
            is_doctor=False,
            is_nurse=False,
            is_receptionist=False,
            is_pharmacist=False,
            is_laboratory_technician=False,
            is_admin=False
        )

        # Activer uniquement le champ correspondant au rôle choisi

        setattr(user, boolean_fields[user_type], True)
        user.save()

        # Envoyer un email avec le mot de passe temporaire

        try:
            send_mail(
                'Votre compte a été créé',
                f'Bonjour {username},\n\n'
                f'Votre compte a été créé avec succès.\n'
                f'Votre mot de passe temporaire est : {password}\n'
                f'Veuillez vous connecter et changer votre mot de passe immédiatement.\n\nMerci.',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            messages.success(request, f"Compte créé ! Un email a été envoyé à {email} avec le mot de passe.")
        except Exception:
            messages.warning(request, "Le compte a été créé, mais l'email n'a pas pu être envoyé.")

        return redirect('registered')

    return render(request, "core/registered.html", {
        'user_types': [
            {'value': 'doctor', 'label': 'Docteur'},
            {'value': 'nurse', 'label': 'Infirmier(e)'},
            {'value': 'receptionist', 'label': 'Réceptionniste'},
            {'value': 'pharmacist', 'label': 'Pharmacien(ne)'},
            {'value': 'lab_technician', 'label': 'Technicien(ne) de laboratoire'},
            {'value': 'admin', 'label': 'Administrateur'}
        ]
    })

def change_password(request):

    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if not new_password or not confirm_password:
            messages.error(request, "Tous les champs sont obligatoires.")
            return redirect('change_password')

        if new_password != confirm_password:
            messages.error(request, "Les mots de passe ne correspondent pas.")
            return redirect('change_password')

        request.user.set_password(new_password)
        request.user.must_change_password = False  # Désactiver l'obligation de changement
        request.user.save()

        update_session_auth_hash(request, request.user)  # Éviter la déconnexion
        messages.success(request, "Votre mot de passe a été mis à jour.")

        if request.user.is_doctor:

            return redirect('doctor_dashboard')

        elif request.user.is_nurse:

            return redirect('nurse_dashboard')

        elif request.user.is_admin:
            return redirect('dashboard')

    return render(request, 'change_password.html')


def appoitement(request):
    return render(request, "core/rdv.html")

def plan_appoint(request):

    patients = Patients.objects.all()
    doctors = User.objects.filter(is_doctor=True)

    if request.method == 'POST':
        date = request.POST.get('date')
        time = request.POST.get('time')
        patient_id = request.POST.get('patient')
        doctor_id = request.POST.get('doctor')
        
        patient = Patients.objects.get(id=patient_id)

        if not patient:
            messages.error(request, "Le patient sélectionné n'existe pas !")
            return redirect("plan_appoint")

        doctor = User.objects.filter(id=doctor_id, is_doctor=True).first()

        if not doctor:
            messages.error(request, "Le médecin sélectionné n'existe pas")
            return redirect("plan_appoint")
        
        Appoitement.objects.create(date=date, time=time, patient=patient, doctor=doctor)
        messages.success(request, "Rendez-vous est reservé avec succès !")
    
    context = {
        "patients": patients,
        "doctors": doctors
    }
    return render(request, "core/plan_rdv.html", context)







