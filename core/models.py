from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from django.db.models.query_utils import tree
from django.utils.text import slugify
from django.utils import timezone
from django.contrib.auth.models import User


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
    ('male', 'Male'),
    ('female', 'Female'),
    ('other', 'Other'),
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
    description = models.TextField(null=True, blank=True)
    care_type = models.TextField(null=True, blank=True)
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
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
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
    name = models.CharField(max_length=255, null=True, blank=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, null=True, blank=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    json_data = models.TextField(null=True, blank=True)
    reference = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Personal Information
    status = models.CharField(max_length=10, choices=MERITAL_STATUS, null=True, blank=True)
    occupation = models.CharField(max_length=255, null=True, blank=True)
    has_insurance = models.BooleanField(default=False)
    is_conventioned = models.BooleanField(default=True)
    insurance_provider = models.CharField(max_length=255, null=True, blank=True)
    convention_provider = models.CharField(max_length=255, null=True, blank=True)
    nationality = models.CharField(max_length=255, null=True, blank=True)

    consultation_status = models.CharField(max_length=255, choices=CONSULTATION_STATUS, default="En attente de consultation")

    # Emergency Contact Information
    relative_name = models.CharField(max_length=255, null=True, blank=True)
    relative_phone = models.CharField(max_length=20, null=True, blank=True)
    relative_mobile = models.CharField(max_length=20, null=True, blank=True)
    relative_same_address = models.BooleanField(default=False)

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
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name="consultations", null=True, blank=True)
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
        ('En attente', 'Pending'),
        ('terminé', 'Completed'),
        ('Annulé', 'Cancelled'),
        ('En consultation', 'In consultation'),
        ('Terminé', 'Done')
    ]
    patient = models.OneToOneField(Patients, on_delete=models.CASCADE, related_name="medical_record")
    consultations = models.ManyToManyField(Consultation, blank=True)
    sign_vitals = models.ManyToManyField(VitalSigns, blank=True)
    examinations = models.ManyToManyField(Examen, blank=True)
    prescriptions = models.ManyToManyField(Prescription, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    file = models.FileField(upload_to='media/medical_records/', null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    number = models.CharField(max_length=12, unique=True, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', null=True, blank=True)

    def generate_number(self):

        if not self.number:

            last_number = MedicalRecord.objects.all().order_by('-created_at').first().number

            if not last_number:

                last_number = 0

            self.number = f"{self.patient.last_name.upper()}{self.patient.first_name[0].upper()}{str(int(last_number) + 1).zfill(6)}"
            

    def __str__(self):
        return f"Dossier Médical de {self.patient}"

class Appoitement(models.Model):
    patient = models.ForeignKey(Patients, on_delete=models.CASCADE, related_name="patient")
    doctor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField(null=True, blank=True)
    statut = models.CharField(
        max_length=20,
        choices=[('En attente', 'En attente'), ('Confirmé', 'Confirmé'), ('Annulé', 'Annulé')],
        default='En attente'
    )
    note = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.patient.user.get_full_name()} - {self.doctor.user.get_full_name()} ({self.date})"