from django.shortcuts import render, redirect
from django.urls import reverse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .serializers import UserSerializer
from .models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError


# Create your views here.
@api_view(['POST', 'GET'])
@permission_classes([AllowAny])
def register(request):
    if request.method == 'POST':
        try:
            # Get and validate data from request
            username = request.POST.get('username')
            email = request.POST.get('email')
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            password = request.POST.get('password')
            password_confirm = request.POST.get('password_confirm')
            user_type = request.POST.get('user_type')

            # Validate required fields
            if not username:
                return render(request, 'accounts/register.html', {
                    'messages': ['Le nom d\'utilisateur est requis'],
                    'message_tags': ['danger']
                })
                
            if not password:
                return render(request, 'accounts/register.html', {
                    'messages': ['Le mot de passe est requis'],
                    'message_tags': ['danger']
                })

            if not user_type or user_type.strip() == '':
                return render(request, 'accounts/register.html', {
                    'messages': ['Le type d\'utilisateur est requis'],
                    'message_tags': ['danger'],
                    'user_types': [
                        {'value': 'doctor', 'label': 'Docteur'},
                        {'value': 'nurse', 'label': 'Infirmier(e)'},
                        {'value': 'receptionist', 'label': 'Réceptionniste'},
                        {'value': 'pharmacist', 'label': 'Pharmacien(ne)'},
                        {'value': 'lab_technician', 'label': 'Technicien(ne) de laboratoire'},
                        {'value': 'admin', 'label': 'Administrateur'}
                    ]
                })

            if password != password_confirm:
                return render(request, 'accounts/register.html', {
                    'messages': ['Les mots de passe ne correspondent pas'],
                    'message_tags': ['danger']
                })

            # Check if username already exists

            if User.objects.filter(username=username).exists():
                return render(request, 'accounts/register.html', {
                    'messages': ['Ce nom d\'utilisateur est déjà pris'],
                    'message_tags': ['danger']
                })

            if email and User.objects.filter(email=email).exists():
                return render(request, 'accounts/register.html', {
                    'messages': ['Cette adresse email est déjà utilisée'],
                    'message_tags': ['danger']
                })

            # Validate user type
            valid_user_types = {
                'doctor': 'Docteur',
                'nurse': 'Infirmier(e)', 
                'receptionist': 'Réceptionniste',
                'pharmacist': 'Pharmacien(ne)',
                'lab_technician': 'Technicien(ne) de laboratoire',
                'admin': 'Administrateur'
            }
            
            if user_type not in valid_user_types:
                return render(request, 'accounts/register.html', {
                    'messages': [f'Type d\'utilisateur invalide. Veuillez choisir parmi: {", ".join(valid_user_types.values())}'],
                    'message_tags': ['danger']
                })

            # Create user based on type using dictionary mapping
            user_create_methods = {
                'doctor': User.objects.create_doctor,
                'nurse': User.objects.create_nurse,
                'receptionist': User.objects.create_receptionist,
                'pharmacist': User.objects.create_pharmacist,
                'lab_technician': User.objects.create_lab_technician,
                'admin': User.objects.create_admin
            }

            create_method = user_create_methods[user_type]
            user = create_method(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            
            # Update boolean fields based on user type
            boolean_fields = {
                'doctor': 'is_doctor',
                'nurse': 'is_nurse',
                'receptionist': 'is_receptionist',
                'pharmacist': 'is_pharmacist',
                'lab_technician': 'is_laboratory_technician',
                'admin': 'is_admin'
            }
    
            # Reset all fields to False
            for field in boolean_fields.values():
                setattr(user, field, False)
    
            # Set corresponding field to True
            setattr(user, boolean_fields[user_type], True)
            
            user.is_active = True
            user.save()

            messages.success(request, 'Votre compte a été créé avec succès. Veuillez vous connecter.')
            return redirect('login')

        except ValidationError as e:
            return render(request, 'accounts/register.html', {
                'messages': ['Erreur de validation: ' + str(e)],
                'message_tags': ['danger']
            })

        except IntegrityError as e:
            return render(request, 'accounts/register.html', {
                'messages': ['Erreur d\'intégrité de la base de données'],
                'message_tags': ['danger']
            })

        except Exception as e:
            return render(request, 'accounts/register.html', {
                'messages': ['Une erreur inattendue s\'est produite'],
                'message_tags': ['danger']
            })

    elif request.method == 'GET':
        return render(request, 'accounts/register.html', {
            'user_types': [
                {'value': 'doctor', 'label': 'Docteur'},
                {'value': 'nurse', 'label': 'Infirmier(e)'},
                {'value': 'receptionist', 'label': 'Réceptionniste'},
                {'value': 'pharmacist', 'label': 'Pharmacien(ne)'},
                {'value': 'lab_technician', 'label': 'Technicien(ne) de laboratoire'},
                {'value': 'admin', 'label': 'Administrateur'}
            ]
        })

@api_view(['POST', 'GET'])
@permission_classes([AllowAny])
def login_view(request):
    try:
        if request.method == 'POST':
            username = request.data.get('username')
            password = request.data.get('password')

            # Valider les champs obligatoires
            if not username:
                return Response({
                    'error': 'Le nom d\'utilisateur est requis'
                }, status=status.HTTP_400_BAD_REQUEST)

            if not password:
                return Response({
                    'error': 'Le mot de passe est requis'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Authentifier l'utilisateur
            user = authenticate(request, username=username, password=password)

            if user is not None:
                if user.is_active:

                    login(request, user)

                    # Générer le token d'authentification
                    
                    token, created = Token.objects.get_or_create(user=user)

                    if user.is_doctor:

                        return redirect('doctor_dashboard')

                    elif user.is_nurse:

                        return redirect('nurse_dashboard')

                    elif user.is_admin:

                        return redirect('dashboard')

                    else:

                        # Redirection par défaut pour les autres utilisateurs

                        return redirect('dashboard')
                else:
                    return Response({
                        'error': 'Votre compte n\'est pas actif'
                    }, status=status.HTTP_401_UNAUTHORIZED)
            else:
                return Response({
                    'error': 'Nom d\'utilisateur ou mot de passe incorrect'
                }, status=status.HTTP_401_UNAUTHORIZED)

        # Handle GET request
        return render(request, 'accounts/login.html')

    except Exception as e:
        """
        Gestion des erreurs inattendues
        :param e: L'exception levée
        :type e: Exception
        """
        print(f"Erreur de connexion: {str(e)}")
        return Response({
            'error': 'Une erreur inattendue s\'est produite'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
def logout_view(request):
    logout(request)
    return redirect('login')
