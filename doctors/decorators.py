from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps
from .models import Doctor

def doctor_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        try:
            # Vérifie si l'utilisateur a un profil de médecin
            doctor_profile = request.user.doctor_profile
        except:
            # Si le profil n'existe pas, on le crée
            try:
                doctor_profile = Doctor.objects.create(
                    user=request.user,
                    specialty="Non spécifiée",  # Valeur par défaut
                    license_number=f"TMP-{request.user.id}"  # Numéro temporaire
                )
            except Exception as e:
                messages.error(request, "Vous n'avez pas les autorisations nécessaires pour accéder à cette section.")
                return redirect('login')
        
        # Ajoute le profil du médecin à la requête pour un accès facile
        request.doctor = doctor_profile
        return view_func(request, *args, **kwargs)
    return _wrapped_view
