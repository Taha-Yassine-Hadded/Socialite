from django.urls import path
from . import views

app_name = 'reviews'

urlpatterns = [
    path('profile/<slug:slug>/reviews/', views.reviews_list, name='reviews_list'),
    path('profile/<slug:slug>/reviews/new/', views.review_create, name='review_create'),
    path('profile/<slug:slug>/reviews/<int:review_id>/edit/', views.review_edit, name='review_edit'),
    path('profile/<slug:slug>/reviews/<int:review_id>/delete/', views.review_delete, name='review_delete'),
]

