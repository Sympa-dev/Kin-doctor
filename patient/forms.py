from django import forms
from core.models import MedicalRecord, Doctor, MedicalFile
from .models import ExtendedPrescription, Invoice, Refund

def handle_medical_record_upload(request):
    """
    Traite les données du formulaire d'upload de dossier médical.
    Cette fonction est appelée depuis la vue pour traiter les fichiers et notes.
    """
    if request.method == 'POST':
        files = request.FILES.getlist('medical_files')
        notes = request.POST.get('notes', '')
        medical_record = request.user.medical_record

        for file in files:
            medical_file = MedicalFile(
                file=file,
                file_type=request.POST.get('file_type', 'other'),
                description=notes,
                uploaded_by=request.user
            )
            medical_file.save()
            medical_record.files.add(medical_file)
        
        if notes:
            medical_record.notes = notes
            medical_record.save()

        return True, "Fichiers téléchargés avec succès"
    return False, "Méthode non autorisée"

class AppointmentBookingForm(forms.Form):
    date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary sm:text-sm'
        })
    )
    time = forms.TimeField(
        widget=forms.TimeInput(attrs={
            'type': 'time',
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary sm:text-sm'
        })
    )
    reason = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary sm:text-sm',
            'rows': 3,
            'placeholder': 'Raison de la consultation'
        })
    )
    is_video_consultation = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary'
        })
    )
    payment_method = forms.ChoiceField(
        choices=[
            ('card', 'Carte bancaire'),
            ('cash', 'Espèces'),
            ('insurance', 'Assurance')
        ],
        widget=forms.Select(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary sm:text-sm'
        })
    )

class PrescriptionForm(forms.ModelForm):
    class Meta:
        model = ExtendedPrescription
        fields = ['title', 'description', 'end_date', 'file']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary sm:text-sm',
                'placeholder': 'Titre de l\'ordonnance'
            }),
            'description': forms.Textarea(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary sm:text-sm',
                'rows': 3,
                'placeholder': 'Description de l\'ordonnance'
            }),
            'end_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary sm:text-sm'
            }),
            'file': forms.FileInput(attrs={
                'class': 'mt-1 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-primary-light file:text-primary hover:file:bg-primary-light'
            })
        }

class MedicationForm(forms.Form):
    name = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary sm:text-sm',
            'placeholder': 'Nom du médicament'
        })
    )
    dosage = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary sm:text-sm',
            'placeholder': 'Dosage (ex: 500mg)'
        })
    )
    frequency = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary sm:text-sm',
            'placeholder': 'Fréquence (ex: 3 fois par jour)'
        })
    )
    duration = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary sm:text-sm',
            'placeholder': 'Durée (ex: 7 jours)'
        })
    )
    instructions = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary sm:text-sm',
            'rows': 3,
            'placeholder': 'Instructions particulières'
        })
    )

class MessageForm(forms.Form):
    recipient = forms.ModelChoiceField(
        queryset=Doctor.objects.all(),
        widget=forms.Select(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary sm:text-sm'
        })
    )
    subject = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary sm:text-sm',
            'placeholder': 'Sujet du message'
        })
    )
    content = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary sm:text-sm',
            'rows': 5,
            'placeholder': 'Contenu du message'
        })
    )
    attachments = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(attrs={
            'class': 'mt-1 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-primary-light file:text-primary hover:file:bg-primary-light',
            'multiple': True
        })
    )

class RefundRequestForm(forms.ModelForm):
    class Meta:
        model = Refund
        fields = ['amount', 'reason']
        widgets = {
            'amount': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary sm:text-sm',
                'step': '0.01',
                'min': '0'
            }),
            'reason': forms.Textarea(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary sm:text-sm',
                'rows': 3,
                'placeholder': 'Raison de la demande de remboursement'
            })
        }
