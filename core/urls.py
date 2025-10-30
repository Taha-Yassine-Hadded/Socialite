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
    path('plan-together/', views.plan_together, name='plan_together'),
    path('timeline/', views.timeline, name='timeline'),
    path('timeline-event/', views.timeline_event, name='timeline_event'),
    path('timeline-funding/', views.timeline_funding, name='timeline_funding'),
    path('timeline-group/', views.timeline_group, name='timeline_group'),
    path('timeline-page/', views.timeline_page, name='timeline_page'),
    path('add_favorite/', views.add_favorite, name='add_favorite'),
    path('remove_favorite/', views.remove_favorite, name='remove_favorite'),
    path('place/', views.place, name='place'),
    path('api/add-favorite/', views.add_favorite, name='add_favorite'),
    path('api/remove-favorite/', views.remove_favorite, name='remove_favorite'),
    path('api/pass-destination/', views.pass_destination, name='pass_destination'),
    # Feed
    path('feed/', views.feed, name='feed'),
    # work
    path('work/', views.work, name='work'),
    
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
    
     # Places page
    path('place/', views.place, name='place'),

    # Profile
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/change-password/', views.change_password, name='change_password'),
    path('profile/<slug:slug>/', views.profile_view, name='profile'),
    
    # ============================================
    # POSTS : Système de publications
    # ============================================
    path('posts/create/', views.create_post, name='create_post'),
    path('posts/', views.list_posts, name='list_posts'),
    path('posts/<int:post_id>/', views.get_post_detail, name='get_post_detail'),
    path('posts/<int:post_id>/edit/', views.edit_post, name='edit_post'),
    path('posts/<int:post_id>/delete/', views.delete_post, name='delete_post'),
    
    # ============================================
    # COMMENTS : Commentaires
    # ============================================
    path('posts/<int:post_id>/comments/', views.add_comment, name='add_comment'),
    path('comments/<int:comment_id>/edit/', views.edit_comment, name='edit_comment'),
    path('comments/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),
    
    # ============================================
    # REACTIONS : Likes et réactions
    # ============================================
    path('posts/<int:post_id>/react/', views.add_reaction, name='add_reaction'),
    path('comments/<int:comment_id>/react/', views.react_to_comment, name='react_to_comment'),
    
    # ============================================
    # SHARE : Partage de posts
    # ============================================
    path('posts/<int:post_id>/share/', views.share_post, name='share_post'),
]