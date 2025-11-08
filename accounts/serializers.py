from rest_framework import serializers
from .models import User, AuthToken, Post, Comment
import re

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'login', 'created_at']

class RegistrationSerializer(serializers.Serializer):
    login = serializers.CharField(max_length=30)
    
    def validate_login(self, value):
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9]*$', value):
            raise serializers.ValidationError(
                "Логин должен содержать только латинские буквы и цифры, и начинаться с буквы"
            )
        return value.lower()

class LoginSerializer(serializers.Serializer):
    login = serializers.CharField(max_length=30)
    password = serializers.CharField(max_length=128)

class ChangePasswordSerializer(serializers.Serializer):
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=6)

class CommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Comment
        fields = ['id', 'user', 'content', 'created_at']

class PostSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    like_count = serializers.ReadOnlyField()
    is_liked = serializers.SerializerMethodField()
    comments = CommentSerializer(many=True, read_only=True)
    comments_count = serializers.ReadOnlyField(source='comments.count')
    
    class Meta:
        model = Post
        fields = ['id', 'user', 'content', 'created_at', 'updated_at', 
                 'like_count', 'is_liked', 'comments', 'comments_count']
    
    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.is_liked_by(request.user)
        return False

class CreatePostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ['content']

class CreateCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['content']