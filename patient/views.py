from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from core.models import Doctor, Specialty, Appointment, MedicalRecord, Prescription, Patients, TimeSlot, ConsultationReason
from django.db.models import Sum
from .models import ExtendedPrescription, Invoice, Refund
from django.utils import timezone
from functools import wraps
from django.contrib import messages


# Décorateur global patient_required
def patient_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        try:
            patient = request.user.patient
        except Patients.DoesNotExist:
            # Si l'utilisateur n'a pas de patient associé, on en crée un
            first_name = request.user.first_name if request.user.first_name else request.user.username
            last_name = request.user.last_name if request.user.last_name else ''
            try:
                patient = Patients.objects.create(
                    user=request.user,
                    first_name=first_name,
                    last_name=last_name,
                    email=request.user.email
                )
                request.session['message'] = {
                    'type': 'info',
                    'text': "Votre profil patient a été créé automatiquement. Veuillez compléter vos informations dans votre profil."
                }
            except Exception as e:
                request.session['message'] = {
                    'type': 'error',
                    'text': "Impossible de créer votre profil patient. Veuillez contacter l'administrateur."
                }
                return redirect('patient:dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

@login_required
@patient_required
def dashboard(request, *args, **kwargs):
    return render(request, "patient/index.html")

@login_required
@patient_required
def find_doctor(request, *args, **kwargs):

    doctors = Doctor.objects.all()

    # Gestion de la prise de rendez-vous via AJAX
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            doctor_id = request.POST.get('doctor_id')
            date = request.POST.get('date')
            time = request.POST.get('time')
            consultation_type = request.POST.get('consultation_type')
            reason = request.POST.get('reason')
            urgent = request.POST.get('urgent') == 'on'
            first_visit = request.POST.get('first_visit') == 'on'
            
            # Validation des données
            if not all([doctor_id, date, time, reason]):
                return JsonResponse({
                    'status': 'error',
                    'message': '⚠️ Veuillez remplir tous les champs obligatoires (date, heure, motif).'
                })
            
            doctor = get_object_or_404(Doctor, id=doctor_id)
            
            # Créer un TimeSlot temporaire pour ce rendez-vous
            from datetime import datetime
            appointment_datetime = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
            
            # Vérifier que la date n'est pas dans le passé
            if appointment_datetime.date() < timezone.now().date():
                return JsonResponse({
                    'status': 'error',
                    'message': '⚠️ Vous ne pouvez pas prendre rendez-vous dans le passé. Veuillez sélectionner une date future.'
                })
            
            # Vérifier si un créneau existe déjà
            existing_slot = TimeSlot.objects.filter(
                doctor=doctor,
                date=appointment_datetime.date(),
                start_time=appointment_datetime.time(),
                is_available=True
            ).first()
            
            if not existing_slot:
                # Créer un nouveau créneau
                time_slot = TimeSlot.objects.create(
                    doctor=doctor,
                    date=appointment_datetime.date(),
                    start_time=appointment_datetime.time(),
                    end_time=(appointment_datetime + timezone.timedelta(minutes=30)).time(),
                    is_available=False
                )
            else:
                time_slot = existing_slot
                time_slot.is_available = False
                time_slot.save()
            
            # Créer le rendez-vous
            appointment = Appointment.objects.create(
                patient=request.user.patient,
                doctor=doctor,
                time_slot=time_slot,
                patient_notes=reason,
                is_first_visit=first_visit,
                status='pending'
            )
            
            # Créer une notification pour le patient
            from core.views import create_notification
            create_notification(
                user=request.user,
                patient=request.user.patient,
                doctor=doctor,
                title="Rendez-vous confirmé",
                message=f"Votre rendez-vous avec Dr. {doctor.name} est confirmé pour le {appointment_datetime.strftime('%d/%m/%Y')} à {appointment_datetime.strftime('%H:%M')}",
                notification_type="success",
                category="appointment",
                is_important=True,
                action_url=f"/patient/appointments/",
                action_text="Voir mes rendez-vous",
                extra_data={
                    'appointment_id': appointment.id,
                    'doctor_name': doctor.name,
                    'appointment_date': appointment_datetime.strftime('%d/%m/%Y'),
                    'appointment_time': appointment_datetime.strftime('%H:%M')
                }
            )
            
            return JsonResponse({
                'status': 'success',
                'message': f'✅ Rendez-vous confirmé avec Dr. {doctor.name} le {appointment_datetime.strftime("%d/%m/%Y")} à {appointment_datetime.strftime("%H:%M")}',
                'appointment_id': appointment.id,
                'appointment_details': {
                    'doctor_name': doctor.name,
                    'date': appointment_datetime.strftime("%d/%m/%Y"),
                    'time': appointment_datetime.strftime("%H:%M"),
                    'status': 'En attente de confirmation'
                }
            })
            
        except ValueError as e:
            return JsonResponse({
                'status': 'error',
                'message': '❌ Format de date ou d\'heure invalide. Veuillez vérifier vos saisies.'
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'❌ Erreur lors de la prise de rendez-vous : {str(e)}'
            })
    
    # Gestion de la recherche de médecins
    specialty = request.GET.get('specialty')
    availability = request.GET.get('availability')
    location = request.GET.get('location')

    doctors = Doctor.objects.all()

    if specialty:
        doctors = doctors.filter(department__name__icontains=specialty)
    if location:
        doctors = doctors.filter(address__icontains=location)
    if availability:
        today = timezone.now().date()
        if availability == 'today':
            doctors = doctors.filter(time_slots__date=today, time_slots__is_available=True).distinct()
        elif availability == 'tomorrow':
            tomorrow = today + timezone.timedelta(days=1)
            doctors = doctors.filter(time_slots__date=tomorrow, time_slots__is_available=True).distinct()
        elif availability == 'week':
            week_end = today + timezone.timedelta(days=7)
            doctors = doctors.filter(time_slots__date__range=[today, week_end], time_slots__is_available=True).distinct()

    # Messages de notification pour la recherche
    if not doctors.exists():
        if any([specialty, availability, location]):
            messages.warning(request, "🔍 Aucun médecin trouvé avec ces critères. Essayez de modifier vos filtres.")
        else:
            messages.info(request, "ℹ️ Aucun médecin disponible pour le moment.")

    context = {
        'doctors': doctors,
        'consultation_reasons': ConsultationReason.objects.all(),
        'specialties': Specialty.objects.all(),
    }
    return render(request, "patient/find_doctor.html", context)

@login_required
@patient_required
def book_appointment(request, doctor_id, *args, **kwargs):
    doctor = get_object_or_404(Doctor, id=doctor_id)
    # Récupérer les créneaux disponibles pour ce médecin (date >= aujourd'hui, disponibles)
    today = timezone.now().date()
    available_slots = doctor.time_slots.filter(date__gte=today, is_available=True).order_by('date', 'start_time')
    # Récupérer les motifs de consultation possibles
    consultation_reasons = ConsultationReason.objects.all()

    if request.method == 'POST':
        time_slot_id = request.POST.get('time_slot')
        consultation_reason_id = request.POST.get('consultation_reason')
        notes = request.POST.get('notes')
        is_video = request.POST.get('video-consultation') == 'on'
        payment_method = request.POST.get('payment-method')
        is_first_visit = request.POST.get('first_visit') == 'on'

        # Vérifier la validité du créneau et du motif
        try:
            time_slot = TimeSlot.objects.get(id=time_slot_id, doctor=doctor, is_available=True)
        except TimeSlot.DoesNotExist:
            messages.error(request, "Le créneau sélectionné n'est plus disponible.")
            return redirect('patient:appointment', doctor_id=doctor.id)
        try:
            consultation_reason = ConsultationReason.objects.get(id=consultation_reason_id)
        except ConsultationReason.DoesNotExist:
            messages.error(request, "Le motif de consultation est invalide.")
            return redirect('patient:appointment', doctor_id=doctor.id)

        # Créer le rendez-vous
        appointment = Appointment.objects.create(
            patient=request.user.patient,
            doctor=doctor,
            time_slot=time_slot,
            consultation_reason=consultation_reason,
            patient_notes=notes,
            is_first_visit=is_first_visit,
            status='pending',
        )
        # Marquer le créneau comme non disponible
        time_slot.is_available = False
        time_slot.save()
        
        # Créer une notification pour le patient
        from core.views import create_notification
        create_notification(
            user=request.user,
            patient=request.user.patient,
            doctor=doctor,
            title="Rendez-vous réservé",
            message=f"Votre rendez-vous avec Dr. {doctor.name} est réservé pour le {time_slot.date.strftime('%d/%m/%Y')} à {time_slot.start_time.strftime('%H:%M')}",
            notification_type="success",
            category="appointment",
            is_important=True,
            action_url=f"/patient/appointments/",
            action_text="Voir mes rendez-vous",
            extra_data={
                'appointment_id': appointment.id,
                'doctor_name': doctor.name,
                'appointment_date': time_slot.date.strftime('%d/%m/%Y'),
                'appointment_time': time_slot.start_time.strftime('%H:%M'),
                'status': 'pending'
            }
        )
        
        messages.success(request, "Votre rendez-vous a été réservé avec succès !")
        return redirect('patient:appointments')

    context = {
        'doctor': doctor,
        'available_slots': available_slots,
        'consultation_reasons': consultation_reasons,
    }
    return render(request, "patient/book_appointment.html", context)

@login_required
@patient_required
def appointments(request, *args, **kwargs):
    
    appointments = Appointment.objects.filter(patient=request.user.patient).order_by('-booking_date')
    
    # Gestion de l'annulation de rendez-vous
    if request.method == 'POST' and 'cancel_appointment' in request.POST:
        appointment_id = request.POST.get('appointment_id')
        try:
            appointment = get_object_or_404(Appointment, id=appointment_id, patient=request.user.patient)
            
            # Vérifier si le rendez-vous peut être annulé (pas dans les 24h)
            from datetime import datetime, timedelta
            appointment_datetime = datetime.combine(appointment.time_slot.date, appointment.time_slot.start_time)
            if appointment_datetime > datetime.now() + timedelta(hours=24):
                # Libérer le créneau
                appointment.time_slot.is_available = True
                appointment.time_slot.save()
                
                # Marquer le rendez-vous comme annulé
                appointment.status = 'cancelled'
                appointment.save()
                
                # Créer une notification d'annulation
                from core.views import create_notification
                create_notification(
                    user=request.user,
                    patient=request.user.patient,
                    doctor=appointment.doctor,
                    title="Rendez-vous annulé",
                    message=f"Votre rendez-vous avec Dr. {appointment.doctor.name} du {appointment.time_slot.date.strftime('%d/%m/%Y')} a été annulé avec succès.",
                    notification_type="info",
                    category="appointment",
                    is_important=False,
                    action_url=f"/patient/appointments/",
                    action_text="Voir mes rendez-vous",
                    extra_data={
                        'appointment_id': appointment.id,
                        'doctor_name': appointment.doctor.name,
                        'appointment_date': appointment.time_slot.date.strftime('%d/%m/%Y'),
                        'status': 'cancelled'
                    }
                )
                
                messages.success(request, "Votre rendez-vous a été annulé avec succès.")
            else:
                messages.error(request, "Impossible d'annuler le rendez-vous moins de 24h à l'avance.")
                
        except Exception as e:
            messages.error(request, f"Erreur lors de l'annulation : {str(e)}")
    
    # Récupérer les médecins uniques pour le filtre
    unique_doctors = Doctor.objects.filter(
        appointments__patient=request.user.patient
    ).distinct()
    
    context = {
        'appointments': appointments,
        'unique_doctors': unique_doctors
    }
    return render(request, "patient/appointments.html", context)

@login_required
@patient_required
def documents(request, *args, **kwargs):
    return render(request, "patient/documents.html")

@login_required
@patient_required
def messages(request, *args, **kwargs):
    return render(request, "patient/messages.html")

@login_required
@patient_required
def appointment_notifications(request, *args, **kwargs):
    """Vue pour afficher les notifications spécifiques aux rendez-vous"""
    # Récupérer les notifications de rendez-vous du patient
    from core.models import Notification
    from django.db.models import Q
    
    appointment_notifications = Notification.objects.filter(
        Q(user=request.user) | Q(patient__user=request.user),
        category='appointment'
    ).order_by('-created_at')
    
    # Séparer par statut
    pending_notifications = appointment_notifications.filter(
        extra_data__status='pending'
    )
    confirmed_notifications = appointment_notifications.filter(
        extra_data__status='confirmed'
    )
    cancelled_notifications = appointment_notifications.filter(
        extra_data__status='cancelled'
    )
    
    context = {
        'pending_notifications': pending_notifications,
        'confirmed_notifications': confirmed_notifications,
        'cancelled_notifications': cancelled_notifications,
        'total_notifications': appointment_notifications.count(),
    }
    
    return render(request, "patient/appointment_notifications.html", context)

@login_required
@patient_required
def all_notifications(request, *args, **kwargs):
    """Vue pour afficher toutes les notifications du patient"""
    from core.models import Notification
    from django.db.models import Q
    
    # Récupérer toutes les notifications du patient
    notifications = Notification.objects.filter(
        Q(user=request.user) | Q(patient__user=request.user)
    ).order_by('-created_at')
    
    # Séparer par statut de lecture
    unread_notifications = notifications.filter(is_read=False)
    read_notifications = notifications.filter(is_read=True)
    
    # Séparer par catégorie
    appointment_notifications = notifications.filter(category='appointment')
    prescription_notifications = notifications.filter(category='prescription')
    billing_notifications = notifications.filter(category='billing')
    system_notifications = notifications.filter(category='system')
    
    context = {
        'unread_notifications': unread_notifications,
        'read_notifications': read_notifications,
        'appointment_notifications': appointment_notifications,
        'prescription_notifications': prescription_notifications,
        'billing_notifications': billing_notifications,
        'system_notifications': system_notifications,
        'total_unread': unread_notifications.count(),
        'total_notifications': notifications.count(),
    }
    
    return render(request, "patient/all_notifications.html", context)

@login_required
@patient_required
def medical_records(request):
    context = {
        'medical_records': MedicalRecord.objects.filter(patient=request.user.patient).order_by('-created_at')
    }
    return render(request, 'patient/medical_records.html', context)

@login_required
@patient_required
def prescriptions(request):
    active_prescriptions = ExtendedPrescription.objects.filter(
        patient=request.user.patient,
        end_date__gte=timezone.now().date()
    ).order_by('-date')
    past_prescriptions = ExtendedPrescription.objects.filter(
        patient=request.user.patient,
        end_date__lt=timezone.now().date()
    ).order_by('-date')
    context = {
        'active_prescriptions': active_prescriptions,
        'past_prescriptions': past_prescriptions,
    }
    return render(request, 'patient/prescriptions.html', context)

@login_required
@patient_required
def billing(request):
    invoices = Invoice.objects.filter(patient=request.user.patient).order_by('-date')
    total_paid = Invoice.objects.filter(
        patient=request.user.patient,
        status='paid'
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    pending_payment = Invoice.objects.filter(
        patient=request.user.patient,
        status='pending'
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    total_refunds = Refund.objects.filter(
        patient=request.user.patient,
        status='completed'
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    context = {
        'invoices': invoices,
        'total_paid': total_paid,
        'pending_payment': pending_payment,
        'total_refunds': total_refunds,
    }
    return render(request, 'patient/billing.html', context)

# Vue de détail patient pour sitemap dynamique
@login_required
@patient_required
def patient_detail(request, patient_id):
    patient = get_object_or_404(Patients, id=patient_id)
    return render(request, 'patient/patient_detail.html', {'patient': patient})
