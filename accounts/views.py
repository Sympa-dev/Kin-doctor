from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from django.db import IntegrityError
from .models import User

# ----------------------------
# Vue d'inscription (Patient & Doctor)
# ----------------------------
def register(request, *args, **kwargs):
    if request.method == 'POST':
        try:
            username = request.POST.get('username', '').strip()
            email = request.POST.get('email', '').strip().lower()
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            password = request.POST.get('password', '')
            password_confirm = request.POST.get('password_confirm', '')
            role = request.POST.get('role', '').strip()  # patient | doctor

            # -------------------
            # VALIDATIONS
            # -------------------
            if not username:
                messages.error(request, "Le nom d'utilisateur est requis.")
                return redirect('accounts:register')

            if not email:
                messages.error(request, "L'adresse email est requise.")
                return redirect('accounts:register')

            if not password or not password_confirm:
                messages.error(request, "Le mot de passe et sa confirmation sont requis.")
                return redirect('accounts:register')

            if password != password_confirm:
                messages.error(request, "Les mots de passe ne correspondent pas.")
                return redirect('accounts:register')

            if role not in ['patient', 'doctor']:
                messages.error(request, "Le rôle choisi est invalide.")
                return redirect('accounts:register')

            # Vérifier unicité
            if User.objects.filter(username=username).exists():
                messages.error(request, "Ce nom d'utilisateur est déjà pris.")
                return redirect('accounts:register')

            if User.objects.filter(email=email).exists():
                messages.error(request, "Cette adresse email est déjà utilisée.")
                return redirect('accounts:register')

            # Vérification du mot de passe
            try:
                validate_password(password)
            except ValidationError as e:
                messages.error(request, " ".join(e.messages))
                return redirect('accounts:register')

            # -------------------
            # CRÉATION UTILISATEUR
            # -------------------
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )

            # Initialiser les rôles
            user.is_patient = (role == 'patient')
            user.is_doctor = (role == 'doctor')
            # user.is_admin n'est pas géré ici car non proposé dans le formulaire

            user.is_active = True
            user.save()

            messages.success(request, "Compte créé avec succès. Connectez-vous maintenant.")
            return redirect('accounts:login')

        except IntegrityError:
            messages.error(request, "Erreur interne: doublon dans la base de données.")
            return redirect('accounts:register')

        except Exception as e:
            messages.error(request, f"Erreur inattendue: {str(e)}")
            return redirect('accounts:register')

    # GET → afficher formulaire
    return render(request, 'accounts/register.html', {
        'role': [
            {'value': 'patient', 'label': 'Patient'},
            {'value': 'doctor', 'label': 'Docteur'},
        ]
    })

# ----------------------------
# Vue de connexion
# ----------------------------
def login_view(request, *args, **kwargs):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        if not username or not password:
            messages.error(request, "Nom d'utilisateur et mot de passe requis.")
            return redirect('accounts:login')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.is_active:
                login(request, user)

                # Redirection selon rôle
                if getattr(user, 'is_patient', False):
                    return redirect('patient:dashboard')
                elif getattr(user, 'is_doctor', False):
                    return redirect('doctors:dashboard')
                # Si tu veux gérer un admin, décommente la ligne suivante et adapte la vue cible
                # elif getattr(user, 'is_admin', False):
                #     return redirect('admin_dashboard')
                else:
                    messages.error(request, "Votre rôle est invalide, contactez l’administrateur.")
                    return redirect('accounts:login')
            else:
                messages.error(request, "Votre compte est désactivé.")
                return redirect('accounts:login')
        else:
            messages.error(request, "Identifiants incorrects.")
            return redirect('accounts:login')

    return render(request, 'accounts/login.html')

# ----------------------------
# Vue de déconnexion
# ----------------------------
def logout_view(request, *args, **kwargs):
    logout(request)
    messages.success(request, "Vous avez été déconnecté avec succès.")
    return redirect('accounts:login')
