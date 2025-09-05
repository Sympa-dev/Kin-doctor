from django.db import models
from django.utils import timezone
from django.conf import settings
from core.models import Doctor

class ExtendedPrescription(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('completed', 'Terminée'),
        ('cancelled', 'Annulée'),
    )

    prescription = models.OneToOneField('core.Prescription', on_delete=models.CASCADE, related_name='extended_details')
    patient = models.ForeignKey('core.Patients', on_delete=models.CASCADE, related_name='extended_prescriptions')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='given_extended_prescriptions')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    date = models.DateField(default=timezone.now)
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    file = models.FileField(upload_to='prescriptions/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"Ordonnance de {self.patient} par Dr. {self.doctor} du {self.date}"

class Medication(models.Model):
    prescription = models.ForeignKey(ExtendedPrescription, on_delete=models.CASCADE, related_name='medications')
    name = models.CharField(max_length=200)
    dosage = models.CharField(max_length=100)
    frequency = models.CharField(max_length=100)
    duration = models.CharField(max_length=100)
    instructions = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} - {self.dosage}"

class Invoice(models.Model):
    STATUS_CHOICES = (
        ('pending', 'En attente'),
        ('paid', 'Payée'),
        ('cancelled', 'Annulée'),
        ('refunded', 'Remboursée'),
    )

    number = models.CharField(max_length=50, unique=True)
    patient = models.ForeignKey('core.Patients', on_delete=models.CASCADE, related_name='invoices')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='issued_invoices')
    appointment = models.OneToOneField('core.Appointment', on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    date = models.DateField(default=timezone.now)
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    pdf = models.FileField(upload_to='invoices/', blank=True, null=True)
    payment_method = models.CharField(max_length=50, blank=True)
    payment_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"Facture #{self.number} - {self.patient}"

    def save(self, *args, **kwargs):
        if not self.number:
            last_invoice = Invoice.objects.order_by('-id').first()
            if last_invoice:
                last_number = int(last_invoice.number[3:])
                self.number = f'INV{str(last_number + 1).zfill(6)}'
            else:
                self.number = 'INV000001'
        super().save(*args, **kwargs)

class Refund(models.Model):
    STATUS_CHOICES = (
        ('pending', 'En attente'),
        ('processing', 'En cours'),
        ('completed', 'Terminé'),
        ('rejected', 'Rejeté'),
    )

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='refunds')
    patient = models.ForeignKey('core.Patients', on_delete=models.CASCADE, related_name='refunds')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    requested_date = models.DateTimeField(auto_now_add=True)
    processed_date = models.DateTimeField(null=True, blank=True)
    processed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-requested_date']

    def __str__(self):
        return f"Remboursement de {self.amount} FC pour {self.patient}"
