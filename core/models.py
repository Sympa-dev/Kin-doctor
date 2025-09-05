from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.conf import settings
from django.db.models.query_utils import tree
from django.utils.text import slugify
from django.utils import timezone
from django.contrib.auth.models import User
import uuid
import os


# Choices for various fields
CATEGORY_CHOICES = (
    ('OTC', 'Over the Counter'),
    ('PRE', 'Prescription'),
    ('GEN', 'Generic'),
)

STOCK_STATUS_CHOICES = (
    ('IN', 'In Stock'),
    ('OUT', 'Out of Stock'),
    ('LOW', 'Low Stock'),
)

COMPANY_TYPES = (
    ('insurance', 'Insurance'),
    ('pharmacy', 'Pharmacy'),
    ('hospital', 'Hospital'),
    ('conventioned', 'Conventioned'),
    ('other', 'Other'),
)

GENDER_CHOICES = (
    ('H', 'Homme'),
    ('F', 'Femme'),
)

ROLES = (
    ('doctor', 'Doctor'),
    ('receptionist', 'Receptionist'),
    ('pharmacist', 'Pharmacist'),
    ('nurse', 'Nurse'),
    ('accountant', 'Accountant'),
    ('seller', 'Seller'),
)

CURRENCY_CHOICES = (
    ('usd', 'US Dollar'),
    ('eur', 'Euro'),
    ('gbp', 'British Pound'),
    ('cdf', 'Congolese Franc'),
)


class Organization(models.Model):
    name = models.CharField(max_length=255)
    logo = models.ImageField(upload_to='logos/', null=True, blank=True)
    address = models.TextField()
    country = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Company(models.Model):
    company_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20)
    address = models.JSONField(null=True, blank=True)
    contact = models.JSONField(null=True, blank=True)
    percentage = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    description = models.TextField(null=True, blank=True)
    type = models.CharField(max_length=20, choices=COMPANY_TYPES)
    email_address = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.company_name

class Department(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, null=True, blank=True)
    reference = models.CharField(max_length=255, unique=True, editable=False, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        if not self.reference:
            count = Department.objects.count()
            self.reference = f'DPT-{count + 1:02d}'
        super().save(*args, **kwargs)

    class Meta:
        ordering = ["-created_at"]


class Employee(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    middle_name = models.CharField(max_length=255, blank=True, null=True)
    birth_date = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, null=True, blank=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    email_address = models.EmailField(null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    role = models.CharField(max_length=20, choices=ROLES)
    reference = models.CharField(max_length=255, unique=True, editable=False, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def save(self, *args, **kwargs):
        if not self.reference:
            count = Employee.objects.count()
            self.reference = f'PERSNL-{count + 1:02d}'
        super().save(*args, **kwargs)

    class Meta:
        ordering = ["-created_at"]


class Doctor(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)
    first_name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, null=True, blank=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='core_doctor')
    order_number = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    reference = models.CharField(max_length=255, unique=True, editable=False, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name}"

    def save(self, *args, **kwargs):
        if not self.reference:
            count = Doctor.objects.count()
            self.reference = f'MDCN-{count + 1:02d}'
        super().save(*args, **kwargs)

    class Meta:
        ordering = ["-created_at"]

class Patients(models.Model):
    MERITAL_STATUS = [
        ("Single","Célibataire"),
        ("Married","Marié(e)"),
        ("Widowed","Veuf(vue)"),
        ("Divorced","Divorcé(e)"),
    ]

    CONSULTATION_STATUS = [
        ("En attente de consultation","En attente de consultation"),
        ("Consultation effectuée","Consultation effectuée"),
        ("Consultation annulée","Consultation annulée"),
        ("Consultation terminée","Consultation terminée"),
    ]
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='patient', null=True, blank=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, null=True, blank=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    reference = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # Personal Information
    status = models.CharField(max_length=10, choices=MERITAL_STATUS, null=True, blank=True)
    occupation = models.CharField(max_length=255, null=True, blank=True)
    nationality = models.CharField(max_length=255, null=True, blank=True)

    consultation_status = models.CharField(max_length=255, choices=CONSULTATION_STATUS, default="En attente de consultation")

    # Emergency Contact Information
    emergency_contact_name = models.CharField(max_length=255, null=True, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    
    # Medical Information
    medical_history = models.TextField(null=True, blank=True)
    allergies = models.TextField(null=True, blank=True)
    blood_group = models.CharField(max_length=10, null=True, blank=True)
    
    # Insurance Information
    insurance_provider = models.CharField(max_length=255, null=True, blank=True)
    insurance_number = models.CharField(max_length=255, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def save(self, *args, **kwargs):
        if not self.reference:
            current_year = timezone.now().year
            count = Patients.objects.filter(reference__startswith=f'PAT-{current_year}').count()
            self.reference = f'PAT-{current_year}{count + 1:02d}'
        super().save(*args, **kwargs)

    class Meta:
        ordering = ["-created_at"]

# models de consultation

class Specialty(models.Model):
    SPECIALTY_CHOICES = [
        ('general_medicine', 'Médecine générale'),
        ('pediatrics', 'Pédiatrie'),
        ('cardiology', 'Cardiologie'),
        ('neurology', 'Neurologie'),
        ('dermatology', 'Dermatologie'),
        ('psychiatry', 'Psychiatrie'),
        ('gynecology', 'Gynécologie-obstétrique'),
        ('orthopedics', 'Orthopédie'),
        ('ophthalmology', 'Ophtalmologie'),
        ('ent', 'Oto-rhino-laryngologie (ORL)'),
        ('general_surgery', 'Chirurgie générale'),
        ('plastic_surgery', 'Chirurgie plastique et reconstructrice'),
        ('cardiovascular_surgery', 'Chirurgie cardiovasculaire'),
        ('pediatric_surgery', 'Chirurgie pédiatrique'),
        ('thoracic_surgery', 'Chirurgie thoracique'),
        ('gastroenterology', 'Gastro-entérologie'),
        ('endocrinology', 'Endocrinologie et diabétologie'),
        ('nephrology', 'Néphrologie'),
        ('urology', 'Urologie'),
        ('hematology', 'Hématologie'),
        ('oncology', 'Oncologie'),
        ('rheumatology', 'Rhumatologie'),
        ('radiology', 'Radiologie'),
        ('emergency_medicine', 'Médecine d\'urgence'),
        ('internal_medicine', 'Médecine interne'),
        ('anesthesiology', 'Anesthésie et réanimation'),
        ('allergology', 'Allergologie'),
        ('infectiology', 'Infectiologie'),
        ('sports_medicine', 'Médecine du sport'),
        ('rehabilitation', 'Médecine physique et de réadaptation'),
        ('public_health', 'Santé publique et médecine sociale'),
        ('geriatrics', 'Gériatrie'),
        ('clinical_immunology', 'Immunologie clinique'),
    ]
     
    name = models.CharField(max_length=100, choices=SPECIALTY_CHOICES, unique=True)

    def __str__(self):
        return self.name

class ConsultationType(models.Model):
    CONSULTATION_TYPE_CHOICES = [
        ('in_person', 'Consultation en présentiel'),
        ('teleconsultation', 'Consultation à distance (téléconsultation)'),
        ('emergency', 'Consultation d\'urgence'),
        ('follow_up', 'Consultation de suivi'),
        ('preventive', 'Consultation préventive (bilan de santé)'),
        ('specialized', 'Consultation spécialisée'),
        ('diagnostic', 'Consultation de diagnostic'),
        ('prenatal', 'Consultation prénatale'),
        ('postnatal', 'Consultation postnatale'),
        ('pediatric', 'Consultation pédiatrique'),
        ('geriatric', 'Consultation gériatrique'),
        ('screening', 'Consultation de dépistage'),
        ('vaccination', 'Consultation de vaccination'),
        ('therapeutic_education', 'Consultation d\'éducation thérapeutique'),
        ('preoperative', 'Consultation préopératoire'),
        ('postoperative', 'Consultation postopératoire'),
        ('rehabilitation', 'Consultation de réadaptation'),
        ('psychological', 'Consultation psychologique ou psychiatrique'),
        ('dietetic', 'Consultation diététique ou nutritionnelle'),
        ('occupational_health', 'Consultation de médecine du travail'),
    ]
    name = models.CharField(max_length=100, choices=CONSULTATION_TYPE_CHOICES, unique=True)

    def __str__(self):
        return self.name


class Consultation(models.Model):
    CONSULTATION_STATUS = [
        ('En attente de consultation', 'En attente de consultation'),
        ('En cours de consultation', 'En cours de consultation'),
        ('Consultation terminée', 'Consultation terminée'),
        ('Consultation annulée', 'Consultation annulée'),
    ]

    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]

    patient = models.ForeignKey(Patients, on_delete=models.CASCADE, related_name="consultations")
    symptoms = models.TextField(null=True, blank=True)
    diagnosis = models.TextField(null=True, blank=True)
    doctor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    specialty = models.ForeignKey(Specialty, on_delete=models.CASCADE, related_name="consultations", null=True, blank=True)
    consultation_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=50, choices=CONSULTATION_STATUS, default='En attente de consultation')
    notes = models.TextField(blank=True, null=True)
    type = models.ForeignKey(ConsultationType, on_delete=models.CASCADE, related_name="consultations", null=True, blank=True)

    def __str__(self):
        return f"Consultation {self.id} ({self.consultation_date})"

    class Meta:
        ordering = ["-consultation_date"]

class ConsultationDetail(models.Model):
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE, related_name="details")
    type = models.ForeignKey(ConsultationType, on_delete=models.CASCADE, related_name="details")
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Detail for Consultation {self.consultation.id}: {self.type.name}"
    
# Historique de consultation

class Prescription(models.Model):
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE)
    medication = models.CharField(max_length=100, null=True, blank=True)
    dosage = models.CharField(max_length=100, null=True, blank=True)
    duration = models.CharField(max_length=50, null=True, blank=True)

class TestResult(models.Model):
    BLOOD_TESTS = 'Blood Tests'
    URINE_TESTS = 'Urine Tests'
    IMAGING_TESTS = 'Imaging Tests'
    CARDIOVASCULAR_TESTS = 'Cardiovascular Tests'
    RESPIRATORY_TESTS = 'Respiratory Tests'
    INFECTIOUS_TESTS = 'Infectious Tests'
    ENDOCRINE_TESTS = 'Endocrine Tests'
    GENETIC_TESTS = 'Genetic Tests'
    ALLERGY_TESTS = 'Allergy Tests'
    COAGULATION_TESTS = 'Coagulation Tests'
    GASTROINTESTINAL_TESTS = 'Gastrointestinal Tests'
    OTHER = 'Other'

    TEST_CHOICES = [
        (BLOOD_TESTS, 'Blood Tests'),
        (URINE_TESTS, 'Urine Tests'),
        (IMAGING_TESTS, 'Imaging Tests'),
        (CARDIOVASCULAR_TESTS, 'Cardiovascular Tests'),
        (RESPIRATORY_TESTS, 'Respiratory Tests'),
        (INFECTIOUS_TESTS, 'Infectious Tests'),
        (ENDOCRINE_TESTS, 'Endocrine Tests'),
        (GENETIC_TESTS, 'Genetic Tests'),
        (ALLERGY_TESTS, 'Allergy Tests'),
        (COAGULATION_TESTS, 'Coagulation Tests'),
        (GASTROINTESTINAL_TESTS, 'Gastrointestinal Tests'),
        (OTHER, 'Other'),
    ]

    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE, related_name='test_results')
    test_category = models.CharField(max_length=50, choices=TEST_CHOICES, default=OTHER)
    test_name = models.CharField(max_length=255)
    result_value = models.CharField(max_length=255, null=True, blank=True)  # Exemple : "120 mg/dL"
    normal_range = models.CharField(max_length=255, null=True, blank=True)  # Exemple : "70-110 mg/dL"
    date = models.DateField(auto_now_add=True)
    remarks = models.TextField(null=True, blank=True)  # Pour des commentaires supplémentaires

    def __str__(self):
        return f"{self.test_category}: {self.test_name} - {self.result_value}"

class ExamenType(models.Model):
    TYPE_EXAMEN = [
        ('Radiography', 'Radiography'),
        ('Blood Test', 'Blood Test'),
        ('Ultrasound', 'Ultrasound'),
        ('MRI', 'MRI'),
        ('CT Scan', 'CT Scan'),
        ('ECG', 'ECG'),
        ('Lung Function Test', 'Lung Function Test'),
        ('Skin Biopsy', 'Skin Biopsy'),
        ('Eye Examination', 'Eye Examination'),
        ('Blood Pressure Test', 'Blood Pressure Test'),
        ('X-Ray', 'X-Ray'),
        ('Blood Sugar Test', 'Blood Sugar Test'),
        ('Liver Function Test', 'Liver Function Test'),
        ('PCR Test', 'PCR Test'),
    ]

    name = models.CharField(max_length=100, choices=TYPE_EXAMEN)

    def __str__(self):
        return self.name

class Examen(models.Model):
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE, related_name="examens")
    exam_type = models.ForeignKey(ExamenType, on_delete=models.CASCADE, related_name="examens")
    exam_date = models.DateField(null=True, blank=True)
    result = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=50, choices=[('pending', 'Pending'), ('completed', 'Completed')], default='pending')
    laborantin = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="examens", limit_choices_to={'is_laborantin': True})

    def __str__(self):
        return f"Examen {self.exam_type} for {self.consultation.patient}"
    
    class Meta:
        ordering = ['-exam_date']
        verbose_name = "Analyse de laboratoire"
        verbose_name_plural = "Analyses de laboratoire"

class VitalSigns(models.Model):
    patient = models.ForeignKey(Patients, on_delete=models.CASCADE, related_name='vital_signs', verbose_name="Patient")
    temperature = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Température (°C)", null=True, blank=True)
    blood_pressure_systolic = models.IntegerField(verbose_name="Pression artérielle (systolique)", null=True, blank=True)
    blood_pressure_diastolic = models.IntegerField(verbose_name="Pression artérielle (diastolique)", null=True, blank=True)
    pulse = models.IntegerField(verbose_name="Pouls (bpm)", null=True, blank=True)
    respiratory_rate = models.IntegerField(verbose_name="Fréquence respiratoire (resp/min)", null=True, blank=True)
    oxygen_saturation = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Saturation en O2 (%)", null=True, blank=True)
    weight = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Poids (kg)", null=True, blank=True)
    height = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Taille (cm)", null=True, blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True, verbose_name="Enregistré le")

    def __str__(self):
        return f"Signes vitaux de {self.patient.first_name} {self.patient.last_name} ({self.recorded_at})"

    class Meta:
        verbose_name = "Signes vitaux"
        verbose_name_plural = "Signes vitaux"


# Modèle Dossier Médical
class MedicalRecord(models.Model):
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('active', 'Actif'),
        ('in_consultation', 'En consultation'),
        ('completed', 'Terminé'),
        ('archived', 'Archivé'),
        ('cancelled', 'Annulé')
    ]
    
    patient = models.OneToOneField(Patients, on_delete=models.CASCADE, related_name="medical_record")
    consultations = models.ManyToManyField(Consultation, blank=True, related_name="medical_records")
    sign_vitals = models.ManyToManyField(VitalSigns, blank=True, related_name="medical_records")
    examinations = models.ManyToManyField(Examen, blank=True, related_name="medical_records")
    prescriptions = models.ManyToManyField(Prescription, blank=True, related_name="medical_records")
    
    # Métadonnées du dossier
    number = models.CharField(max_length=20, unique=True, db_index=True, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.IntegerField(default=0, help_text="Priorité du dossier (0 = normale)")
    
    # Fichiers et notes
    files = models.ManyToManyField('MedicalFile', related_name='medical_records', blank=True)
    notes = models.TextField(null=True, blank=True)
    last_modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='modified_records')
    
    # Dates de suivi
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    archived_at = models.DateTimeField(null=True, blank=True)

    def generate_number(self):
        """Génère un numéro unique pour le dossier médical."""
        if not self.number:
            current_year = timezone.now().year
            # Utilise les initiales du nom complet
            patient_name = f"{self.patient.last_name[:2]}{self.patient.first_name[:2]}".upper()
            
            # Format: ABCD-2025-000001
            prefix = f"{patient_name}-{current_year}"
            
            # Chercher le dernier numéro pour cette année
            last_record = MedicalRecord.objects.filter(
                number__startswith=prefix
            ).order_by('-number').first()
            
            if last_record:
                try:
                    last_sequence = int(last_record.number.split('-')[-1])
                    new_sequence = last_sequence + 1
                except (ValueError, IndexError):
                    new_sequence = 1
            else:
                new_sequence = 1
            
            self.number = f"{prefix}-{str(new_sequence).zfill(6)}"

    def clean(self):
        """Validation personnalisée pour le dossier médical."""
        if self.status == 'archived' and not self.archived_at:
            self.archived_at = timezone.now()
        
        if self.archived_at and self.status != 'archived':
            raise ValidationError("Un dossier archivé doit avoir le statut 'archived'")

    def save(self, *args, **kwargs):
        if not self.number:
            self.generate_number()
        self.full_clean()  # Lance la validation
        super().save(*args, **kwargs)

    def archive(self, user=None):
        """Archive le dossier médical."""
        self.status = 'archived'
        self.archived_at = timezone.now()
        if user:
            self.last_modified_by = user
        self.save()

    def reactivate(self, user=None):
        """Réactive un dossier archivé."""
        if self.status == 'archived':
            self.status = 'active'
            self.archived_at = None
            if user:
                self.last_modified_by = user
            self.save()

    def __str__(self):
        return f"Dossier Médical {self.number} - {self.patient.first_name} {self.patient.last_name} ({self.status})"
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['number']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['patient', 'status']),
            models.Index(fields=['archived_at']),
        ]
        verbose_name = "Dossier médical"
        verbose_name_plural = "Dossiers médicaux"
        permissions = [
            ("archive_medical_record", "Peut archiver un dossier médical"),
            ("reactivate_medical_record", "Peut réactiver un dossier médical"),
            ("view_archived_records", "Peut voir les dossiers archivés"),
        ]

class ConsultationReason(models.Model):
    name = models.CharField(max_length=255)
    specialty = models.ForeignKey(Specialty, on_delete=models.CASCADE, related_name='consultation_reasons')
    duration = models.IntegerField(help_text='Durée en minutes')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(null=True, blank=True)
    is_teleconsultation = models.BooleanField(default=False)
    preparation_instructions = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.duration} min)"

class TimeSlot(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='time_slots')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)
    is_recurring = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    max_appointments = models.PositiveIntegerField(default=1)
    duration = models.PositiveIntegerField(help_text='Durée en minutes', default=30)
    reason = models.ForeignKey(ConsultationReason, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ['date', 'start_time']
        unique_together = ['doctor', 'date', 'start_time']
        indexes = [
            models.Index(fields=['doctor', 'date', 'is_available']),
            models.Index(fields=['date', 'is_available']),
        ]

    def __str__(self):
        return f"Dr. {self.doctor.name} - {self.date} {self.start_time}"

    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError("L'heure de début doit être antérieure à l'heure de fin")
        
        # Vérifier les chevauchements
        overlapping_slots = TimeSlot.objects.filter(
            doctor=self.doctor,
            date=self.date,
            start_time__lt=self.end_time,
            end_time__gt=self.start_time
        ).exclude(pk=self.pk)
        
        if overlapping_slots.exists():
            raise ValidationError("Ce créneau chevauche un autre créneau existant")
            
        # Vérifier que le créneau est dans le futur lors de la création
        if not self.pk and timezone.now().date() > self.date:
            raise ValidationError("Impossible de créer un créneau dans le passé")

class Appointment(models.Model):
    APPOINTMENT_STATUS = [
        ('pending', 'En attente de confirmation'),
        ('confirmed', 'Confirmé'),
        ('cancelled_by_patient', 'Annulé par le patient'),
        ('cancelled_by_doctor', 'Annulé par le médecin'),
        ('completed', 'Terminé'),
        ('missed', 'Patient non présent'),
    ]

    patient = models.ForeignKey(Patients, on_delete=models.CASCADE, related_name="appointments")
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name="appointments")
    time_slot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE, related_name="appointments")
    consultation_reason = models.ForeignKey(ConsultationReason, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, choices=APPOINTMENT_STATUS, default='pending')
    booking_date = models.DateTimeField(auto_now_add=True)
    cancellation_reason = models.TextField(null=True, blank=True)
    patient_notes = models.TextField(null=True, blank=True, help_text="Notes ou symptômes décrits par le patient")
    is_first_visit = models.BooleanField(default=True)
    reminder_sent = models.BooleanField(default=False)
    video_consultation_link = models.URLField(null=True, blank=True)

    def __str__(self):
        return f"{self.patient.first_name} {self.patient.last_name} - Dr. {self.doctor.name} ({self.time_slot.date})"

    class Meta:
        ordering = ['-time_slot__date', '-time_slot__start_time']
        
    def save(self, *args, **kwargs):
        if self.consultation_reason and self.consultation_reason.is_teleconsultation:
            # Logique pour générer le lien de téléconsultation
            if not self.video_consultation_link:
                self.video_consultation_link = f"https://consultation.example.com/{uuid.uuid4()}"
        super().save(*args, **kwargs)

class MedicalFile(models.Model):
    FILE_TYPES = [
        ('prescription', 'Prescription'),
        ('lab_result', 'Résultat de laboratoire'),
        ('xray', 'Radiographie'),
        ('scan', 'Scanner'),
        ('mri', 'IRM'),
        ('ultrasound', 'Échographie'),
        ('other', 'Autre')
    ]

    file = models.FileField(
        upload_to='medical_records/%Y/%m/',
        verbose_name="Fichier"
    )
    file_type = models.CharField(
        max_length=20,
        choices=FILE_TYPES,
        default='other',
        verbose_name="Type de fichier"
    )
    upload_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date d'upload"
    )
    description = models.TextField(
        null=True,
        blank=True,
        verbose_name="Description"
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_medical_files'
    )

    def __str__(self):
        return f"{self.get_file_type_display()} - {self.upload_date.strftime('%Y-%m-%d')}"

    class Meta:
        ordering = ['-upload_date']
        verbose_name = "Fichier médical"
        verbose_name_plural = "Fichiers médicaux"

    def filename(self):
        return os.path.basename(self.file.name)

    def extension(self):
        name, extension = os.path.splitext(self.file.name)
        return extension

class DoctorSchedule(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='schedules')
    day_of_week = models.IntegerField(choices=[
        (0, 'Lundi'),
        (1, 'Mardi'),
        (2, 'Mercredi'),
        (3, 'Jeudi'),
        (4, 'Vendredi'),
        (5, 'Samedi'),
        (6, 'Dimanche')
    ])
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)
    break_start = models.TimeField(null=True, blank=True)
    break_end = models.TimeField(null=True, blank=True)

    class Meta:
        ordering = ['day_of_week', 'start_time']
        unique_together = ['doctor', 'day_of_week']

    def __str__(self):
        return f"{self.doctor.name} - {self.get_day_of_week_display()}"

class Patient(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    birth_date = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20)
    address = models.TextField(blank=True)
    blood_group = models.CharField(max_length=5, blank=True)
    allergies = models.TextField(blank=True)
    medical_history = models.TextField(blank=True)
    insurance_number = models.CharField(max_length=50, blank=True)
    insurance_provider = models.CharField(max_length=100, blank=True)
    emergency_contact_name = models.CharField(max_length=255, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    reference = models.CharField(max_length=255, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def save(self, *args, **kwargs):
        if not self.reference:
            count = Patient.objects.count()
            self.reference = f'PAT-{count + 1:06d}'
        super().save(*args, **kwargs)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Patient"
        verbose_name_plural = "Patients"
