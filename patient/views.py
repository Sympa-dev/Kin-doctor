from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from core.models import Doctor, Specialty, Appointment, MedicalRecord, Prescription, Patients
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
    specialty = request.GET.get('specialty')
    availability = request.GET.get('availability')
    location = request.GET.get('location')

    doctors = Doctor.objects.all()

    if specialty:
        doctors = doctors.filter(specialty__name=specialty)
    if location:
        doctors = doctors.filter(address__icontains=location)
    if availability:
        today = timezone.now().date()
        if availability == 'today':
            doctors = doctors.filter(availability__date=today)
        elif availability == 'tomorrow':
            doctors = doctors.filter(availability__date=today + timezone.timedelta(days=1))
        elif availability == 'week':
            doctors = doctors.filter(availability__date__range=[today, today + timezone.timedelta(days=7)])

    context = {
        'doctors': doctors,
        'specialties': Specialty.objects.all(),
    }
    return render(request, "patient/find_doctor.html", context)

@login_required
@patient_required
def book_appointment(request, doctor_id, *args, **kwargs):
    doctor = get_object_or_404(Doctor, id=doctor_id)
    if request.method == 'POST':
        # Logique de réservation
        date = request.POST.get('date')
        time = request.POST.get('time')
        reason = request.POST.get('reason')
        is_video = request.POST.get('video-consultation') == 'on'
        payment_method = request.POST.get('payment-method')
        appointment = Appointment.objects.create(
            patient=request.user.patient,
            doctor=doctor,
            date_time=f"{date} {time}",
            reason=reason,
            is_video_consultation=is_video,
            payment_method=payment_method
        )
        return JsonResponse({
            'status': 'success',
            'appointment_id': appointment.id
        })
    context = {
        'doctor': doctor,
        'available_slots': doctor.get_available_slots(),
    }
    return render(request, "patient/book_appointment.html", context)

@login_required
@patient_required
def appointments(request, *args, **kwargs):
    appointments = Appointment.objects.filter(patient=request.user.patient)
    return render(request, "patient/appointments.html", {'appointments': appointments})

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
