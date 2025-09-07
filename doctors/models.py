from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from core.models import Doctor as CoreDoctor, Patients, Patient  # Renommé pour éviter les conflits

User = get_user_model()

class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor_profile')
    phone = models.CharField(max_length=20, blank=True)
    specialty = models.CharField(max_length=100)
    license_number = models.CharField(max_length=50, unique=True)
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='doctors/profile_pictures/', blank=True, null=True)
    consultation_duration = models.IntegerField(default=30)  # en minutes
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    video_consultation = models.BooleanField(default=True)
    physical_consultation = models.BooleanField(default=True)

    def __str__(self):
        return f"Dr. {self.user.first_name} {self.user.last_name}"

    class Meta:
        verbose_name = "Médecin"
        verbose_name_plural = "Médecins"

class Consultation(models.Model):
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('in_progress', 'En cours'),
        ('completed', 'Terminée'),
        ('cancelled', 'Annulée'),
    ]

    TYPE_CHOICES = [
        ('video', 'Consultation vidéo'),
        ('physical', 'Consultation en cabinet'),
    ]

    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='doctor_consultations')
    patient = models.ForeignKey(Patients, on_delete=models.CASCADE, related_name='patient_consultations')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField(null=True, blank=True)
    type_consultation = models.CharField(max_length=20, choices=TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    prescriptions = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Consultation {self.get_type_display()} - {self.patient} - {self.date}"

    class Meta:
        verbose_name = "Consultation"
        verbose_name_plural = "Consultations"

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('confirmed', 'Confirmé'),
        ('completed', 'Terminé'),
        ('cancelled', 'Annulé'),
    ]

    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='doctor_appointments')
    patient = models.ForeignKey('core.Patient', on_delete=models.CASCADE, related_name='patient_appointments')
    datetime = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"RDV - {self.patient} - {self.datetime}"

    class Meta:
        verbose_name = "Rendez-vous"
        verbose_name_plural = "Rendez-vous"

class WorkingHours(models.Model):
    DAYS_OF_WEEK = [
        (0, 'Lundi'),
        (1, 'Mardi'),
        (2, 'Mercredi'),
        (3, 'Jeudi'),
        (4, 'Vendredi'),
        (5, 'Samedi'),
        (6, 'Dimanche'),
    ]

    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    day_of_week = models.IntegerField(choices=DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Horaire de travail"
        verbose_name_plural = "Horaires de travail"
        unique_together = ['doctor', 'day_of_week']

    def __str__(self):
        return f"{self.get_day_of_week_display()} {self.start_time}-{self.end_time}"

class ConsultationMessage(models.Model):
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_system_message = models.BooleanField(default=False)  # Pour les messages système (ex: "X a rejoint la consultation")
    
    class Meta:
        ordering = ['timestamp']
        
    def __str__(self):
        return f"{self.sender.get_full_name()} - {self.timestamp.strftime('%H:%M:%S')}"
