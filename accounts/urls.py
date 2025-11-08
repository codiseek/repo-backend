from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('check-login/', views.check_login, name='check-login'),
    path('login/', views.login, name='login'),
    path('verify-token/', views.verify_token, name='verify-token'),
    path('change-password/', views.change_password, name='change-password'),
    path('posts/', views.get_posts, name='get-posts'),
    path('posts/create/', views.create_post, name='create-post'),
    path('posts/like/', views.toggle_like, name='toggle-like'),
    path('posts/comment/', views.add_comment, name='add-comment'),
]