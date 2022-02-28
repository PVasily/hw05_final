from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.views.decorators.cache import cache_page

from posts.forms import PostForm, CommentForm
from .models import Follow, Post, Group, User


POSTS_PER_PAGE = 10


def get_paginator(request, page, num):
    paginator = Paginator(page, num)
    page_numder = request.GET.get('page')
    page_obj: Paginator = paginator.get_page(page_numder)
    return page_obj


@cache_page(60 / 3, key_prefix='page_obj')
def index(request):
    template = 'posts/index.html'
    title = 'Последние обновления на сайте'
    posts = Post.objects.all()
    page_obj = get_paginator(request, posts, POSTS_PER_PAGE)
    context = {
        'page_obj': page_obj,
        'title': title}
    return render(request, template, context)


def group_post(request, slug):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    posts = group.groups.all()
    description = group.description
    page_obj = get_paginator(request, posts, POSTS_PER_PAGE)
    title = f'Вы в сообществе {group}'
    context = {
        'description': description,
        'page_obj': page_obj,
        'group': group,
        'title': title}
    return render(request, template, context)


def profile(request, username):
    user = get_object_or_404(User, username=username)
    posts = user.posts.all()
    count = posts.count()
    following = None
    auth = True
    if request.user.is_authenticated:
        following = Follow.objects.filter(
            user=request.user,
            author=user).exists()
    else:
        following = None
        auth = False
    page_obj = get_paginator(request, posts, POSTS_PER_PAGE)
    context = {
        'auth': auth,
        'following': following,
        'count': count,
        'page_obj': page_obj,
        'author': user
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    author_posts = post.author.posts.all()
    author_name = post.author
    form = CommentForm()
    comments = post.comments.all()
    user = request.user
    count = author_posts.count()
    context = {
        'author_name': author_name,
        'user': user,
        'count': count,
        'post': post,
        'form': form,
        'comments': comments
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    user = request.user
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = user
        post.save()
        return redirect('posts:profile', username=user.username)
    form = PostForm()
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)
    return render(request, 'posts/create_post.html',
                  {'form': form, 'post_id': post_id, 'is_edit': True})


@login_required
def add_comment(request, post_id):
    post = Post.objects.get(id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    title = 'Избранное'
    posts = Post.objects.filter(author__following__user=request.user)
    context = {
        'title': title,
        'page_obj': posts
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    # Подписаться на автора
    user = get_object_or_404(User, username=username)
    Follow.objects.create(user=request.user, author=user)
    print(Follow.objects.count())
    return redirect(f'/profile/{username}/')


@login_required
def profile_unfollow(request, username):
    user = get_object_or_404(User, username=username)
    unfollow = Follow.objects.get(user=request.user, author=user)
    unfollow.delete()
    return redirect(f'/profile/{username}/')
