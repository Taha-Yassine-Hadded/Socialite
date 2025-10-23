from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.db import IntegrityError
from .mongo import get_db
from django.conf import settings
from django.core.files.storage import FileSystemStorage
import os
import uuid
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, login
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json
from django.contrib.auth import logout
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .mongo import get_db
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .mongo import get_db
from django.contrib.auth.decorators import login_required 

# ROUTE USER CONNECTÉ
@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_info(request):
    """Retourne les infos du user connecté"""
    user = request.user
    
    # Récupérer profil MongoDB
    db = get_db()
    profile = db.profiles.find_one({'user_id': user.id})
    
    return JsonResponse({
        'success': True,
        'user': {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'profile_image': profile.get('profile_image') if profile else None,
            'date_of_birth': profile.get('date_of_birth') if profile else None,
            'is_staff': user.is_staff,  # ← AJOUTÉ !
        }
    })

@csrf_exempt
def login_page(request):
    if request.method == 'GET':
        return render(request, 'login.html')
    
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        
        user = authenticate(request, username=email, password=password)
        
        if user:
            login(request, user)
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            
            return JsonResponse({
                'success': True,
                'message': 'Login successful',
                'token': access_token,  # ← SEUL "token"
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Invalid email or password'
            }, status=400)

@csrf_exempt
def logout_view(request):
    if request.method == 'POST':
        logout(request)
        return JsonResponse({
            'success': True,
            'message': 'Logged out successfully'
        })
    return JsonResponse({'error': 'Method not allowed'}, status=405)


def register_page(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        date_of_birth = request.POST.get('date_of_birth', '').strip()
        profile_image = request.FILES.get('profile_image')

        errors = []
        if not first_name or not last_name:
            errors.append('First name and last name are required.')
        if not email:
            errors.append('Email is required.')
        if password1 != password2 or not password1:
            errors.append('Passwords must match and not be empty.')

        if errors:
            return render(request, 'register.html', {
                'errors': errors,
                'form': {
                    'first_name': first_name,
                    'last_name': last_name,
                    'email': email,
                    'date_of_birth': date_of_birth,
                }
            })

        username = email  # use email as username
        try:
            user = User.objects.create_user(username=username, email=email, password=password1,
                                            first_name=first_name, last_name=last_name)
        except IntegrityError:
            return render(request, 'register.html', {
                'errors': ['A user with that email already exists.'],
                'form': {
                    'first_name': first_name,
                    'last_name': last_name,
                    'email': email,
                }
            })

        # Save profile image to MEDIA_ROOT if provided
        profile_image_path = None
        if profile_image:
            fs = FileSystemStorage(location=settings.MEDIA_ROOT, base_url=settings.MEDIA_URL)
            name, ext = os.path.splitext(profile_image.name)
            unique_name = f"profiles/{uuid.uuid4().hex}{ext}"
            saved_name = fs.save(unique_name, profile_image)
            profile_image_path = saved_name  # relative path within MEDIA_ROOT

        # Save profile to MongoDB
        db = get_db()
        db.profiles.insert_one({
            'user_id': user.id,
            'email': email,
            'first_name': first_name,
            'last_name': last_name,
            'date_of_birth': date_of_birth or None,
            'profile_image': profile_image_path,
        })

        return redirect('login_page')

    return render(request, 'register.html')

# Timeline pages
@login_required(login_url='/login/')
def timeline(request):
    return render(request, 'timeline.html')

@login_required(login_url='/login/')
def timeline_event(request):
    return render(request, 'timeline-event.html')

@login_required(login_url='/login/')
def timeline_funding(request):
    return render(request, 'timeline-funding.html')

@login_required(login_url='/login/')
def timeline_group(request):
    return render(request, 'timeline-group.html')

@login_required(login_url='/login/')
def timeline_page(request):
    return render(request, 'timeline-page.html')

# Feed
@login_required(login_url='/login/')
def feed(request):
    return render(request, 'feed.html')

# Groups pages
@login_required(login_url='/login/')
def groups(request):
    return render(request, 'groups.html')

@login_required(login_url='/login/')
def groups_2(request):
    return render(request, 'groups-2.html')

# Pages
@login_required(login_url='/login/')
def pages(request):
    return render(request, 'pages.html')

# Messages
@login_required(login_url='/login/')
def messages_view(request):
    return render(request, 'messages.html')

# Events
@login_required(login_url='/login/')
def event(request):
    return render(request, 'event.html')

@login_required(login_url='/login/')
def event_2(request):
    return render(request, 'event-2.html')

# Market/Shopping
@login_required(login_url='/login/')
def market(request):
    return render(request, 'market.html')

@login_required(login_url='/login/')
def product_view_1(request):
    return render(request, 'product-view-1.html')

@login_required(login_url='/login/')
def product_view_2(request):
    return render(request, 'product-view-2.html')

# Video pages
@login_required(login_url='/login/')
def video(request):
    return render(request, 'video.html')

@login_required(login_url='/login/')
def video_watch(request):
    return render(request, 'video-watch.html')

# Blog pages
@login_required(login_url='/login/')
def blog(request):
    return render(request, 'blog.html')

@login_required(login_url='/login/')
def blog_2(request):
    return render(request, 'blog-2.html')

@login_required(login_url='/login/')
def blog_read(request):
    return render(request, 'blog-read.html')

# Games
@login_required(login_url='/login/')
def games(request):
    return render(request, 'games.html')

# Funding
@login_required(login_url='/login/')
def funding(request):
    return render(request, 'funding.html')

# Settings and account
@login_required(login_url='/login/')
def setting(request):
    return render(request, 'setting.html')


@login_required(login_url='/login/')
def upgrade(request):
    return render(request, 'upgrade.html')

# Single page (could be profile or post single)
@login_required(login_url='/login/')
def single(request):
    return render(request, 'single.html')