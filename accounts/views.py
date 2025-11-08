from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils import timezone
from .models import User, RegistrationAttempt, AuthToken, Post, Comment
from .serializers import (UserSerializer, RegistrationSerializer, 
                         LoginSerializer, ChangePasswordSerializer,
                         PostSerializer, CreatePostSerializer, 
                         CreateCommentSerializer, CommentSerializer)
import secrets




def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

@api_view(['POST'])
def register(request):
    ip_address = get_client_ip(request)
    
    # Проверяем ограничение по времени
    if not RegistrationAttempt.can_register(ip_address):
        return Response(
            {"error": "Слишком много попыток регистрации. Попробуйте через 10 минут."},
            status=status.HTTP_429_TOO_MANY_REQUESTS
        )
    
    serializer = RegistrationSerializer(data=request.data)
    if serializer.is_valid():
        login = serializer.validated_data['login']
        
        # Проверяем, не занят ли логин
        if User.objects.filter(login=login).exists():
            return Response(
                {"error": "Этот логин уже занят"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Генерируем случайный пароль
        generated_password = User.generate_password()
        
        # Создаем пользователя с хешированным паролем
        user = User.objects.create(login=login)
        user.set_password(generated_password)
        
        # Создаем токен авторизации
        token = AuthToken.objects.create(user=user)
        
        # Фиксируем попытку регистрации
        RegistrationAttempt.objects.create(ip_address=ip_address)
        
        return Response({
            "message": "Регистрация успешна",
            "user": UserSerializer(user).data,
            "token": token.token,
            "generated_password": generated_password
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def check_login(request):
    """Проверяет существование логина"""
    serializer = RegistrationSerializer(data=request.data)
    if serializer.is_valid():
        login = serializer.validated_data['login']
        
        user_exists = User.objects.filter(login=login).exists()
        return Response({
            "exists": user_exists,
            "login": login
        })
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def login(request):
    """Авторизация с логином и паролем"""
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        login = serializer.validated_data['login']
        password = serializer.validated_data['password']
        
        try:
            user = User.objects.get(login=login)
            
            # Проверяем пароль
            if user.check_password(password):
                token = AuthToken.objects.create(user=user)
                
                return Response({
                    "message": "Вход выполнен успешно",
                    "user": UserSerializer(user).data,
                    "token": token.token
                })
            else:
                return Response(
                    {"error": "Неверный пароль"},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
        except User.DoesNotExist:
            return Response(
                {"error": "Пользователь с таким логином не найден"},
                status=status.HTTP_404_NOT_FOUND
            )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def verify_token(request):
    token = request.data.get('token')
    try:
        auth_token = AuthToken.objects.get(token=token)
        return Response({
            "valid": True,
            "user": UserSerializer(auth_token.user).data
        })
    except AuthToken.DoesNotExist:
        return Response({"valid": False}, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['POST'])
def change_password(request):
    serializer = ChangePasswordSerializer(data=request.data)
    if serializer.is_valid():
        token = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']
        
        try:
            auth_token = AuthToken.objects.get(token=token)
            user = auth_token.user
            user.set_password(new_password)
            
            return Response({
                "message": "Пароль успешно изменен"
            })
            
        except AuthToken.DoesNotExist:
            return Response(
                {"error": "Неверный токен"},
                status=status.HTTP_401_UNAUTHORIZED
            )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def get_posts(request):
    """Получить все посты"""
    posts = Post.objects.all()
    serializer = PostSerializer(posts, many=True, context={'request': request})
    return Response(serializer.data)

@api_view(['POST'])
def create_post(request):
    """Создать новый пост"""
    token = request.data.get('token')
    if not token:
        return Response({"error": "Токен обязателен"}, status=status.HTTP_401_UNAUTHORIZED)
    
    try:
        auth_token = AuthToken.objects.get(token=token)
        user = auth_token.user
        
        serializer = CreatePostSerializer(data=request.data)
        if serializer.is_valid():
            post = serializer.save(user=user)
            
           
            
            return Response(PostSerializer(post, context={'request': request}).data, 
                          status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    except AuthToken.DoesNotExist:
        return Response({"error": "Неверный токен"}, status=status.HTTP_401_UNAUTHORIZED)
    


@api_view(['POST'])
def toggle_like(request):
    """Поставить/убрать лайк"""
    token = request.data.get('token')
    post_id = request.data.get('post_id')
    
    if not token or not post_id:
        return Response({"error": "Токен и post_id обязательны"}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    try:
        auth_token = AuthToken.objects.get(token=token)
        user = auth_token.user
        post = Post.objects.get(id=post_id)
        
        if post.is_liked_by(user):
            post.likes.remove(user)
            liked = False
        else:
            post.likes.add(user)
            liked = True
        
        
        return Response({
            "liked": liked,
            "like_count": post.like_count()
        })
        
    except (AuthToken.DoesNotExist, Post.DoesNotExist):
        return Response({"error": "Неверный токен или пост"}, 
                       status=status.HTTP_404_NOT_FOUND)
    



@api_view(['POST'])
def add_comment(request):
    print("=== ADD COMMENT REQUEST ===")
    print("Request data:", request.data)
    
    token = request.data.get('token')
    post_id = request.data.get('post_id')
    content = request.data.get('content')
    
    print(f"Token: {token}, Post ID: {post_id}, Content: {content}")
    
    if not token or not post_id or not content:
        print("Missing required fields")
        return Response({"error": "Все поля обязательны"}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    try:
        auth_token = AuthToken.objects.get(token=token)
        user = auth_token.user
        post = Post.objects.get(id=post_id)
        
        print(f"User: {user}, Post: {post}")
        
        serializer = CreateCommentSerializer(data={'content': content})
        if serializer.is_valid():
            comment = serializer.save(post=post, user=user)
            print(f"Comment saved: {comment}")
            
           
            
            return Response(CommentSerializer(comment).data, 
                          status=status.HTTP_201_CREATED)
        
        print(f"Serializer errors: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    except AuthToken.DoesNotExist:
        print("AuthToken does not exist")
        return Response({"error": "Неверный токен"}, 
                       status=status.HTTP_401_UNAUTHORIZED)
    except Post.DoesNotExist:
        print("Post does not exist")
        return Response({"error": "Пост не найден"}, 
                       status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(f"Unexpected error: {e}")
        return Response({"error": "Внутренняя ошибка сервера"}, 
                       status=status.HTTP_500_INTERNAL_SERVER_ERROR)