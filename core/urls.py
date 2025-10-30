from django.urls import path
from . import views

urlpatterns = [
    # ============================================
    # MAIN PAGE
    # ============================================
    path('', views.feed, name='feed'),
    
    # ============================================
    # AUTHENTICATION
    # ============================================
    path('api/user/', views.user_info, name='user_info'),
    path('login/', views.login_page, name='login_page'),
    path('register/', views.register_page, name='register_page'),
    path('logout/', views.logout_view, name='logout'),
    
    # ============================================
    # SOCIAL - FOLLOW/UNFOLLOW
    # ============================================
    path('follow-unfollow/', views.follow_unfollow, name='follow_unfollow'),
    
    # ============================================
    # TIMELINE PAGES
    # ============================================
    path('timeline/', views.timeline, name='timeline'),
    path('timeline-event/', views.timeline_event, name='timeline_event'),
    path('timeline-funding/', views.timeline_funding, name='timeline_funding'),
    path('timeline-group/', views.timeline_group, name='timeline_group'),
    path('timeline-page/', views.timeline_page, name='timeline_page'),
    
    # ============================================
    # FEED
    # ============================================
    path('feed/', views.feed, name='feed'),
    
    # ============================================
    # GROUPS
    # ============================================
    path('groups/', views.groups, name='groups'),
    path('groups-2/', views.groups_2, name='groups_2'),
    
    # ============================================
    # PAGES
    # ============================================
    path('pages/', views.pages, name='pages'),
    
    # ============================================
    # MESSAGES
    # ============================================
    path('messages/', views.messages_view, name='messages'),
    
    # ============================================
    # EVENTS
    # ============================================
    path('event/', views.event, name='event'),
    path('event-2/', views.event_2, name='event_2'),
    
    # ============================================
    # MARKET/SHOPPING
    # ============================================
    path('market/', views.market, name='market'),
    path('product-view-1/', views.product_view_1, name='product_view_1'),
    path('product-view-2/', views.product_view_2, name='product_view_2'),
    
    # ============================================
    # VIDEOS
    # ============================================
    path('video/', views.video, name='video'),
    path('video-watch/', views.video_watch, name='video_watch'),
    
    # ============================================
    # BLOG
    # ============================================
    path('blog/', views.blog, name='blog'),
    path('blog-2/', views.blog_2, name='blog_2'),
    path('blog-read/', views.blog_read, name='blog_read'),
    
    # ============================================
    # GAMES
    # ============================================
    path('games/', views.games, name='games'),
    
    # ============================================
    # FUNDING
    # ============================================
    path('funding/', views.funding, name='funding'),
    
    # ============================================
    # SETTINGS & ACCOUNT
    # ============================================
    path('setting/', views.setting, name='setting'),
    path('upgrade/', views.upgrade, name='upgrade'),
    
    # ============================================
    # SUBSCRIPTION MANAGEMENT
    # ============================================
    path('subscription/status/', views.subscription_status, name='subscription_status'),
    path('subscription/manage/', views.manage_subscription, name='manage_subscription'),
    path('subscription/cancel/', views.cancel_subscription, name='cancel_subscription'),
    
    # Checkout pages
    path('subscription/checkout/<str:plan>/', views.checkout, name='checkout'),
    path('subscription/checkout/<str:plan>/<str:duration>/', views.checkout, name='checkout_duration'),
    
    # Payment processing
    path('subscription/process-stripe/', views.process_stripe_payment, name='process_stripe_payment'),
    
    # Payment success/failure
    path('subscription/success/', views.payment_success, name='payment_success'),
    path('subscription/failure/', views.payment_failure, name='payment_failure'),
    
    # Webhooks
    path('webhooks/stripe/', views.stripe_webhook, name='stripe_webhook'),
    
    # Test endpoint
    path('test-stripe/', views.test_stripe, name='test_stripe'),
    
    # ============================================
    # SINGLE PAGE
    # ============================================
    path('single/', views.single, name='single'),
    
    # ============================================
    # PROFILE
    # ============================================
    path('profile/', views.profile_view, name='profile_me'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/change-password/', views.change_password, name='change_password'),
    path('profile/<slug:slug>/', views.profile_view, name='profile'),
    path('profile/<slug:slug>/albums/', views.profile_albums, name='profile_albums'),
    path('profile/<slug:slug>/analytics/', views.profile_analytics, name='profile_analytics'),

    # Reviews
    
    # ============================================
    # REVIEWS
    # ============================================
    path('profile/<slug:slug>/reviews/', views.reviews_list, name='reviews_list'),
    path('profile/<slug:slug>/reviews/new/', views.review_create, name='review_create'),
    
    # ============================================
    # POSTS
    # ============================================
    path('posts/create/', views.create_post, name='create_post'),
    path('posts/', views.list_posts, name='list_posts'),
    path('posts/<int:post_id>/', views.get_post_detail, name='get_post_detail'),
    path('posts/<int:post_id>/edit/', views.edit_post, name='edit_post'),
    path('posts/<int:post_id>/delete/', views.delete_post, name='delete_post'),
    
    # API : Analyse d'image pour tags automatiques
    path('api/analyze-image/', views.analyze_image_for_tags, name='analyze_image_for_tags'),
    
    # ============================================
    # COMMENTS
    # ============================================
    path('posts/<int:post_id>/comments/', views.add_comment, name='add_comment'),
    path('comments/<int:comment_id>/edit/', views.edit_comment, name='edit_comment'),
    path('comments/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),
    
    # ============================================
    # REACTIONS
    # ============================================
    path('posts/<int:post_id>/react/', views.add_reaction, name='add_reaction'),
    path('comments/<int:comment_id>/react/', views.react_to_comment, name='react_to_comment'),
    
    # ============================================
    # SHARE
    # ============================================
    path('posts/<int:post_id>/share/', views.share_post, name='share_post'),

    # ============================================
    # STORIES
    # ============================================
    path('stories/create/', views.create_story, name='create_story'),
    path('stories/', views.list_stories, name='list_stories'),
    path('stories/<int:story_id>/', views.story_detail, name='story_detail'),

    # ============================================
    # ANALYTICS DASHBOARD
    # ============================================
    path('analytics/', views.analytics_dashboard, name='analytics_dashboard'),
    path('api/analytics/', views.analytics_data, name='analytics_data'),
]