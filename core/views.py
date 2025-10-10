from django.shortcuts import render


# Authentication forms
def login_page(request):
    return render(request, 'login.html')

def register_page(request):
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