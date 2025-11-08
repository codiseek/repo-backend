from django.db import models
from django.utils import timezone
from datetime import timedelta
import secrets
import string
from django.contrib.auth.hashers import make_password, check_password

class User(models.Model):
    login = models.CharField(max_length=30, unique=True)
    password = models.CharField(max_length=128)  # Храним хеш пароля
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.login
    
    def set_password(self, raw_password):
        """Устанавливает хешированный пароль"""
        self.password = make_password(raw_password)
        self.save()
    
    def check_password(self, raw_password):
        """Проверяет пароль"""
        return check_password(raw_password, self.password)
    
    @classmethod
    def generate_password(cls, length=12):
        """Генерирует случайный пароль"""
        characters = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(characters) for _ in range(length))

class RegistrationAttempt(models.Model):
    ip_address = models.GenericIPAddressField()
    attempt_time = models.DateTimeField(auto_now_add=True)
    
    @classmethod
    def can_register(cls, ip_address):
        ten_minutes_ago = timezone.now() - timedelta(minutes=10)
        attempts = cls.objects.filter(
            ip_address=ip_address, 
            attempt_time__gte=ten_minutes_ago
        )
        return attempts.count() < 3  # Максимум 3 попытки за 10 минут
    
class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    content = models.TextField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    likes = models.ManyToManyField(User, related_name='liked_posts', blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Post by {self.user.login} - {self.created_at}"
    
    def like_count(self):
        return self.likes.count()
    
    def is_liked_by(self, user):
        return self.likes.filter(id=user.id).exists()

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(max_length=300)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Comment by {self.user.login} on {self.post}"
    

class AuthToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=64, unique=True, default=secrets.token_hex)
    created_at = models.DateTimeField(auto_now_add=True)