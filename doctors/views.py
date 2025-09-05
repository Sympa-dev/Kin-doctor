from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.core.paginator import Paginator
from django.contrib import messages
from django.db.models import Q, Count
from datetime import datetime, timedelta
from .models import Doctor, Consultation, Appointment, WorkingHours
from core.models import Patient
from .decorators import doctor_required


@login_required
@doctor_required
def dashboard(request):
    # Récupérer les statistiques du jour
    today = timezone.now().date()
    doctor = request.doctor  # Utilise le profil ajouté par le décorateur

    # Statistiques des patients
    today_patients_count = Consultation.objects.filter(
        doctor=doctor,
        date=today
    ).count()

    pending_appointments = Appointment.objects.filter(
        doctor=doctor,
        status='pending'
    ).count()

    # Prochains rendez-vous
    next_appointments = Appointment.objects.filter(
        doctor=doctor,
        datetime__gte=timezone.now(),
        status='confirmed'
    ).order_by('datetime')[:5]

    # Statistiques des consultations
    consultation_stats = Consultation.objects.filter(
        doctor=doctor
    ).aggregate(
        total=Count('id'),
        completed=Count('id', filter=Q(status='completed')),
        in_progress=Count('id', filter=Q(status='in_progress'))
    )

    # Activité récente
    recent_activity = Consultation.objects.filter(
        doctor=doctor
    ).order_by('-created_at')[:10]

    context = {
        'today_patients_count': today_patients_count,
        'pending_appointments': pending_appointments,
        'next_appointments': next_appointments,
        'consultation_stats': consultation_stats,
        'recent_activity': recent_activity,
    }
    return render(request, 'doctors/dashboard.html', context)

@login_required
@doctor_required
def appointments(request):
    doctor = request.doctor
    
    # Filtres
    status = request.GET.get('status', 'all')
    date_filter = request.GET.get('date')
    
    # Base query
    appointments = Appointment.objects.filter(doctor=doctor)
    
    # Appliquer les filtres
    if status != 'all':
        appointments = appointments.filter(status=status)
    if date_filter:
        date_obj = datetime.strptime(date_filter, '%Y-%m-%d').date()
        appointments = appointments.filter(datetime__date=date_obj)

    # Calendrier hebdomadaire
    today = timezone.now().date()
    week_start = today - timedelta(days=today.weekday())
    week_days = []
    
    for i in range(7):
        current_date = week_start + timedelta(days=i)
        day_appointments = appointments.filter(datetime__date=current_date)
        week_days.append({
            'date': current_date,
            'is_today': current_date == today,
            'appointments': day_appointments
        })

    # Pagination
    paginator = Paginator(appointments.order_by('datetime'), 10)
    page = request.GET.get('page')
    appointments_list = paginator.get_page(page)

    context = {
        'week_days': week_days,
        'appointments': appointments_list,
    }
    return render(request, 'doctors/appointments.html', context)

@login_required
@doctor_required
def appointment_action(request, appointment_id, action):
    appointment = get_object_or_404(Appointment, id=appointment_id, doctor=request.doctor)
    
    if action == 'confirm':
        appointment.status = 'confirmed'
    elif action == 'cancel':
        appointment.status = 'cancelled'
    elif action == 'complete':
        appointment.status = 'completed'
    
    appointment.save()
    return JsonResponse({'status': 'success'})

@login_required
@doctor_required
def patients(request):
    doctor = request.doctor
    search_query = request.GET.get('search', '')
    
    # Récupérer tous les patients qui ont eu une consultation avec ce médecin
    patients = Patient.objects.filter(
        patient_consultations__doctor=doctor
    ).distinct()
    
    # Appliquer le filtre de recherche
    if search_query:
        patients = patients.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone_number__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(patients.order_by('-created_at'), 10)
    page = request.GET.get('page')
    patients_list = paginator.get_page(page)
    
    context = {
        'patients': patients_list,
        'search_query': search_query,
    }
    return render(request, 'doctors/patients.html', context)

@login_required
@doctor_required
def patient_detail(request, patient_id):
    doctor = request.doctor
    patient = get_object_or_404(Patient, id=patient_id)
    
    # Historique des consultations
    consultations = Consultation.objects.filter(
        doctor=doctor,
        patient=patient
    ).order_by('-date', '-start_time')
    
    # Prochain rendez-vous
    next_appointment = Appointment.objects.filter(
        doctor=doctor,
        patient=patient,
        datetime__gte=timezone.now(),
        status='confirmed'
    ).first()
    
    context = {
        'patient': patient,
        'consultations': consultations,
        'next_appointment': next_appointment,
    }
    return render(request, 'doctors/patient_detail.html', context)

@login_required
@doctor_required
def consultations(request):
    doctor = request.doctor
    
    # Consultations en cours
    active_consultations = Consultation.objects.filter(
        doctor=doctor,
        status='in_progress'
    ).order_by('-start_time')
    
    # Historique des consultations
    past_consultations = Consultation.objects.filter(
        doctor=doctor
    ).exclude(
        status='in_progress'
    ).order_by('-date', '-start_time')
    
    # Pagination
    paginator = Paginator(past_consultations, 10)
    page = request.GET.get('page')
    consultations_list = paginator.get_page(page)
    
    context = {
        'active_consultations': active_consultations,
        'consultations': consultations_list,
    }
    return render(request, 'doctors/consultations.html', context)

@login_required
@doctor_required
def start_consultation(request, appointment_id):
    doctor = request.doctor
    appointment = get_object_or_404(Appointment, id=appointment_id, doctor=doctor)
    
    # Créer une nouvelle consultation
    consultation = Consultation.objects.create(
        doctor=doctor,
        patient=appointment.patient,
        type=appointment.consultation_type if hasattr(appointment, 'consultation_type') else 'video',
        date=timezone.now().date(),
        start_time=timezone.now().time(),
        status='in_progress'
    )
    
    # Mettre à jour le rendez-vous
    appointment.status = 'completed'
    appointment.save()
    
    return redirect('doctors:consultation_room', consultation_id=consultation.id)

@login_required
@doctor_required
def consultation_room(request, consultation_id):
    doctor = request.doctor
    consultation = get_object_or_404(Consultation, id=consultation_id, doctor=doctor)
    
    if request.method == 'POST':
        # Mettre à jour les notes et prescriptions
        consultation.notes = request.POST.get('notes', '')
        consultation.prescriptions = request.POST.get('prescriptions', '')
        consultation.save()
        
        if request.POST.get('action') == 'end':
            consultation.status = 'completed'
            consultation.end_time = timezone.now().time()
            consultation.save()
            return redirect('doctors:consultations')
        
        messages.success(request, 'Consultation mise à jour avec succès')
    
    context = {
        'consultation': consultation,
    }
    return render(request, 'doctors/consultation_room.html', context)

@login_required
@doctor_required
def profile(request):
    doctor = request.doctor
    
    if request.method == 'POST':
        # Mettre à jour les informations du profil
        doctor.phone = request.POST.get('phone')
        doctor.specialty = request.POST.get('specialty')
        doctor.bio = request.POST.get('bio')
        doctor.consultation_duration = request.POST.get('consultation_duration')
        doctor.consultation_fee = request.POST.get('consultation_fee')
        doctor.video_consultation = 'video_consultation' in request.POST
        doctor.physical_consultation = 'physical_consultation' in request.POST
        
        if 'profile_picture' in request.FILES:
            doctor.profile_picture = request.FILES['profile_picture']
        
        doctor.save()
        
        # Mettre à jour les informations utilisateur
        user = request.user
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.email = request.POST.get('email')
        user.save()
        
        messages.success(request, 'Profil mis à jour avec succès')
        return redirect('doctors:profile')
    
    # Récupérer les horaires de travail
    working_hours = WorkingHours.objects.filter(doctor=doctor).order_by('day_of_week')
    
    context = {
        'doctor': doctor,
        'working_hours': working_hours,
    }
    return render(request, 'doctors/profile.html', context)

@login_required
@doctor_required
def update_working_hours(request):
    if request.method == 'POST':
        doctor = request.doctor
        data = request.POST
        
        # Supprimer les anciens horaires
        WorkingHours.objects.filter(doctor=doctor).delete()
        
        # Créer les nouveaux horaires
        for day in range(7):
            if f'day_{day}_enabled' in data:
                WorkingHours.objects.create(
                    doctor=doctor,
                    day_of_week=day,
                    start_time=data[f'day_{day}_start'],
                    end_time=data[f'day_{day}_end'],
                    is_available=True
                )
        
        messages.success(request, 'Horaires mis à jour avec succès')
        return redirect('doctors:profile')
    
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def update_password(request):
    if request.method == 'POST':
        user = request.user
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        
        if user.check_password(current_password):
            user.set_password(new_password)
            user.save()
            messages.success(request, 'Mot de passe modifié avec succès')
            return redirect('login')
        else:
            messages.error(request, 'Mot de passe actuel incorrect')
            
    return redirect('doctors:profile')
