from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.db import IntegrityError
from .mongo import get_db
from django.conf import settings
from django.core.files.storage import FileSystemStorage
import os
import uuid


# Authentication forms
def login_page(request):
    return render(request, 'login.html')

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
def timeline(request):
    return render(request, 'timeline.html')

def timeline_event(request):
    return render(request, 'timeline-event.html')

def timeline_funding(request):
    return render(request, 'timeline-funding.html')

def timeline_group(request):
    return render(request, 'timeline-group.html')

def timeline_page(request):
    return render(request, 'timeline-page.html')

# Feed
def feed(request):
    return render(request, 'feed.html')

# Groups pages
def groups(request):
    return render(request, 'groups.html')

def groups_2(request):
    return render(request, 'groups-2.html')

# Pages
def pages(request):
    return render(request, 'pages.html')

# Messages
def messages_view(request):
    return render(request, 'messages.html')

# Events
def event(request):
    return render(request, 'event.html')

def event_2(request):
    return render(request, 'event-2.html')

# Market/Shopping
def market(request):
    return render(request, 'market.html')

def product_view_1(request):
    return render(request, 'product-view-1.html')

def product_view_2(request):
    return render(request, 'product-view-2.html')

# Video pages
def video(request):
    return render(request, 'video.html')

def video_watch(request):
    return render(request, 'video-watch.html')

# Blog pages
def blog(request):
    return render(request, 'blog.html')

def blog_2(request):
    return render(request, 'blog-2.html')

def blog_read(request):
    return render(request, 'blog-read.html')

# Games
def games(request):
    return render(request, 'games.html')

# Funding
def funding(request):
    return render(request, 'funding.html')

# Settings and account
def setting(request):
    return render(request, 'setting.html')

def upgrade(request):
    return render(request, 'upgrade.html')

# Single page (could be profile or post single)
def single(request):
    return render(request, 'single.html')