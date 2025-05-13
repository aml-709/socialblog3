from django.shortcuts import render, redirect, get_object_or_404
from users.forms import PostForm, RegisterForm
from django.views.generic import TemplateView
from django.contrib.auth import authenticate, login, get_user_model
from users.forms import UserCreationForm, CommentForm, ProfileForm
from django.views import View
from django.contrib.auth.decorators import login_required
from .models import Favorite, Comment, post, Like, Dislike
from django.http import JsonResponse


User = get_user_model()

# Форма для регистрации
class Register(View):
    template_name = 'registration/register.html'

    def get(self, request):
        context = {
            'form': RegisterForm()
            }
        return render(request, self.template_name, context)


    def post(self, request):
        form = RegisterForm(request.POST)

        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            login(request, user)
            return redirect('index')
        context = {'form': form}
        return render(request, self.template_name, context)


@login_required
def favorites_view(request):
    favorites = Favorite.objects.filter(user=request.user)
    return render(request, 'favorites.html', {'favorites': favorites})

@login_required
def add_to_favorites(request, post_id):
    post_instance = get_object_or_404(post, id=post_id)
    favorite, created = Favorite.objects.get_or_create(user=request.user, post=post_instance)
    if created:
        message = "Added to favorites"
    else:
        message = "Already in favorites"
    return redirect('post_detail', id=post_instance.id)

@login_required
def remove_from_favorites(request, post_id):
    post_instance = get_object_or_404(post, id=post_id)
    favorite = get_object_or_404(Favorite, user=request.user, post=post_instance)
    favorite.delete()
    return redirect('favorites_view')

def post_list(request):
    posts = post.objects.all()  
    return render(request, 'index.html', {'posts': posts})

def post_detail(request, id):
    post_instance = get_object_or_404(post, id=id)
    comments = Comment.objects.filter(post=post_instance).order_by('-created_at')

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post_instance
            comment.user = request.user
            comment.save()
            return redirect('post_detail', id=post_instance.id)
    else:
        form = CommentForm()

    return render(request, 'post_detail.html', {
        'post': post_instance,
        'comments': comments,
        'form': form
    })


#Создание и удаление поста
@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user
            post.save()
            return redirect('index')
    else:
        form = PostForm()
    return render(request, 'create_post.html', {'form': form})

@login_required
def delete_post(request, post_id):
    post_instance = get_object_or_404(post, id=post_id)
    if request.user == post_instance.user or request.user.is_superuser:
        post_instance.delete()
        return redirect('index')

#Комментарии
@login_required
def comments(request, post_id):
    comments = Comment.objects.all().order_by('-created_at')
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.save()
            return redirect('product_detail')
    else:
        form = CommentForm()
    return render(request, 'post_comments.html', {'form': form, 'comments': comments})

#Лайки
@login_required
def toggle_like(request, post_id):
    post_instance = get_object_or_404(post, id=post_id)
    like = Like.objects.filter(user=request.user, post=post_instance).first()

    if like:
        # Если лайк существует, удаляем его и уменьшаем рейтинг
        like.delete()
        post_instance.rating -= 1
        post_instance.save()
        message = "Лайк удален"
        liked = False
    else:
        # Если лайка нет, создаем его и увеличиваем рейтинг
        Like.objects.create(user=request.user, post=post_instance)
        post_instance.rating += 1
        post_instance.save()
        message = "Лайк добавлен"
        liked = True

    return redirect(request.META.get('HTTP_REFERER', 'index'))

#Дизлайки
@login_required
def toggle_dislike(request, post_id):
    post_instance = get_object_or_404(post, id=post_id)
    dislike = Dislike.objects.filter(user=request.user, post=post_instance).first()

    if dislike:
        # Если дизлайк существует, удаляем его и увеличиваем рейтинг
        dislike.delete()
        post_instance.rating += 1
        post_instance.save()
        message = "Дизлайк удален"
        disliked = False
    else:
        # Если дизлайка нет, создаем его и уменьшаем рейтинг
        Dislike.objects.create(user=request.user, post=post_instance)
        post_instance.rating -= 1
        post_instance.save()
        message = "Дизлайк добавлен"
        disliked = True

    return redirect(request.META.get('HTTP_REFERER', 'index'))

#Профиль пользователя
@login_required
def profile_view(request, username):
    user_profile = get_object_or_404(User, username=username)
    is_following = user_profile.followers.filter(id=request.user.id).exists()
    return render(request, 'profile.html', {
        'user_profile': user_profile,
        'is_following': is_following
    })


@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('profile', username=request.user.username)
    else:
        form = ProfileForm(instance=request.user)
    return render(request, 'edit_profile.html', {'form': form})

@login_required
def toggle_follow(request, username):
    user_to_follow = get_object_or_404(User, username=username)
    if user_to_follow == request.user:
        return redirect('profile', username=username)
    if request.user in user_to_follow.followers.all():
        user_to_follow.followers.remove(request.user)
    else:
        user_to_follow.followers.add(request.user)
    return redirect('profile', username=username)


def account_view(request):
    return render(request, 'account.html')

@login_required
def profile_view(request, username):
    user_profile = get_object_or_404(User, username=username)
    is_following = request.user in user_profile.followers.all()
    return render(request, 'profile.html', {
        'user_profile': user_profile,
        'is_following': is_following
    })

@login_required
def user_posts(request, username):
    user_profile = get_object_or_404(User, username=username)
    posts = post.objects.filter(user=user_profile).order_by('-created_at')
    return render(request, 'user_posts.html', {'user_profile': user_profile, 'posts': posts})




