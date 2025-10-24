from django.urls import path
from . import views

urlpatterns = [
    # Main page
    path('', views.feed, name='feed'),
    
    # Authentication
    path('api/user/', views.user_info, name='user_info'),  # ← NOUVELLE ROUTE user connecté chabeb
    path('login/', views.login_page, name='login_page'),
    path('register/',  views.register_page, name='register_page'),
    path('logout/', views.logout_view, name='logout'),  # ← AJOUTEZ CETTE LIGNE
    # Timeline pages
    path('follow-unfollow/', views.follow_unfollow, name='follow_unfollow'),

    path('timeline/', views.timeline, name='timeline'),
    path('timeline-event/', views.timeline_event, name='timeline_event'),
    path('timeline-funding/', views.timeline_funding, name='timeline_funding'),
    path('timeline-group/', views.timeline_group, name='timeline_group'),
    path('timeline-page/', views.timeline_page, name='timeline_page'),
    
    # Feed
    path('feed/', views.feed, name='feed'),
    
    # Groups
    path('groups/', views.groups, name='groups'),
    path('groups-2/', views.groups_2, name='groups_2'),
    
    # Pages
    path('pages/', views.pages, name='pages'),
    
    # Messages
    path('messages/', views.messages_view, name='messages'),
    
    # Events
    path('event/', views.event, name='event'),
    path('event-2/', views.event_2, name='event_2'),
    
    # Market/Shopping
    path('market/', views.market, name='market'),
    path('product-view-1/', views.product_view_1, name='product_view_1'),
    path('product-view-2/', views.product_view_2, name='product_view_2'),
    
    # Videos
    path('video/', views.video, name='video'),
    path('video-watch/', views.video_watch, name='video_watch'),
    
    # Blog
    path('blog/', views.blog, name='blog'),
    path('blog-2/', views.blog_2, name='blog_2'),
    path('blog-read/', views.blog_read, name='blog_read'),
    
    # Games
    path('games/', views.games, name='games'),
    
    # Funding
    path('funding/', views.funding, name='funding'),
    
    # Settings
    path('setting/', views.setting, name='setting'),
    path('upgrade/', views.upgrade, name='upgrade'),
    
    # Single page
    path('single/', views.single, name='single'),
]