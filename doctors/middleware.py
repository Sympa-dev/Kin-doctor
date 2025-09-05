from .models import Consultation
from django.utils import timezone

class ActiveConsultationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if hasattr(request, 'user') and request.user.is_authenticated and hasattr(request.user, 'doctor_profile'):
            # Rechercher une consultation active pour ce médecin
            active_consultation = Consultation.objects.filter(
                doctor=request.user.doctor_profile,
                status='in_progress',
                date=timezone.now().date()
            ).first()
            request.active_consultation = active_consultation
        else:
            request.active_consultation = None

        response = self.get_response(request)
        return response
