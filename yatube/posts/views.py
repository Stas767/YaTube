from django.views.decorators.cache import cache_page
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required

from posts.forms import CommentForm, PostForm

from . models import Follow, Post, Group, User, Comment


SELECT_LIMIT = 10  # количество записей на странице


@cache_page(20, key_prefix='index_page')
def index(request):
    templates = 'posts/index.html'
    title = 'Последние обновления на сайте'
    post_list = Post.objects.all()
    context = {
        'title': title,
        'page_obj': paginator(request, post_list),
    }
    return render(request, templates, context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    templates = 'posts/group_list.html'
    title = f'Записи сообщества {group}'
    post_list = Post.objects.all()
    context = {
        'title': title,
        'page_obj': paginator(request, post_list),
        'group': group,
    }
    return render(request, templates, context)


def paginator(request, post_list):
    paginator = Paginator(post_list, SELECT_LIMIT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj


def profile(request, username):
    author = get_object_or_404(User, username=username)
    author_post = Post.objects.filter(author_id=author)
    count_post = author_post.count()
    title = f'Профайл пользователя {username}'

    context = {
        'page_obj': paginator(request, author_post),
        'title': title,
        'author': author,
        'count_post': count_post,
    }

    if request.user.is_authenticated:
        following = Follow.objects.filter(
            user=request.user,
            author=User.objects.get(username=username)
        )
        context.update({'following': following})
        return render(request, 'posts/profile.html', context)
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    count_post = post.author.posts.count()
    form = CommentForm()
    comments = Comment.objects.select_related('post')
    context = {
        'comments': comments,
        'form': form,
        'post': post,
        'count_post': count_post,
        'title': post,
    }
    return render(request, 'posts/post_detail.html', context)


@ login_required
def post_create(request):
    author = Post(author=request.user)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=author
    )
    if request.method != 'POST' or not form.is_valid():
        return render(request, 'posts/create_post.html', {'form': form})
    form.save()
    return redirect('posts:profile', username=request.user)


@ login_required
def post_edit(request, post_id):
    post = Post.objects.get(pk=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if request.user != post.author:
        return redirect('posts:post_detail', post_id=post_id)
    if not request.method == 'POST' or not form.is_valid():
        return render(request,
                      'posts/create_post.html',
                      {'form': form, 'is_edit': True}
                      )
    form.save()
    return redirect('posts:post_detail', post_id=post_id)


@ login_required
def add_comment(request, post_id):
    post = Post.objects.get(pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@ login_required
def follow_index(request):
    # информация о текущем пользователе доступна в переменной request.user
    title = 'Лента избранных авторов'
    post_list = Post.objects.filter(author__following__user=request.user)
    context = {
        'title': title,
        'page_obj': paginator(request, post_list),
    }
    return render(request, 'posts/follow.html', context)


@ login_required
def profile_follow(request, username):
    # Подписаться на автора
    author = get_object_or_404(User, username=username)
    if request.user != author:
        if not Follow.objects.filter(
            user=request.user,
            author=author
        ):
            Follow.objects.create(user=request.user, author=author)
            return redirect('posts:profile', username=author)
    return redirect('posts:profile', username=request.user)


@ login_required
def profile_unfollow(request, username):
    # Дизлайк, отписка
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('posts:profile', username=author)
