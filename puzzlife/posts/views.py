from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.cache import cache_page
from .models import Post, Group, User, Follow, Comment, Like
from .forms import PostForm, CommentForm
from .utils import get_page



def index(request):
    page_obj = get_page(Post.objects.all(), page=request.GET.get('page'))
    context = {
        'page_obj': page_obj
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    page_obj = get_page(group.posts.all(), page=request.GET.get('page'))
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    page_obj = get_page(author.posts.all(), page=request.GET.get('page'))
    following = request.user.is_authenticated and Follow.objects.filter(
        user=request.user, author=author).exists()
    context = {
        'author': author,
        'page_obj': page_obj,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    comments = post.comments.all()
    comment_form = CommentForm(request.POST or None)
    liked = request.user.is_authenticated and Like.objects.filter(
        user=request.user, post=post).exists()
    context = {
        'post': post,
        'form': comment_form,
        'comments': comments,
        'liked': liked
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    create_form = PostForm(request.POST or None, files=request.FILES or None)
    if create_form.is_valid():
        create_post = create_form.save(commit=False)
        create_post.author = request.user
        create_post.save()
        return redirect('posts:profile', request.user)
    return render(request, 'posts/create_post.html', {'form': create_form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id)
    update_form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if update_form.is_valid():
        update_form.save()
        return redirect('posts:post_detail', post_id)
    context = {
        'post': post,
        'form': update_form,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def post_delete(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id)
    post.delete()
    return redirect('posts:profile', post.author.username)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    comment_form = CommentForm(request.POST or None)
    if comment_form.is_valid():
        comment = comment_form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id)


@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)
    if comment.author != request.user:
        return redirect('posts:post_detail', comment.post.id)
    comment.delete()
    return redirect('posts:post_detail', comment.post.id)


@login_required
def follow_index(request):
    follow_posts = Post.objects.filter(author__following__user=request.user)
    page_obj = get_page(follow_posts, page=request.GET.get('page'))
    context = {
        'page_obj': page_obj
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get_or_create(
            user=request.user,
            author=author,
        )
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    follow = Follow.objects.get(
        user=request.user,
        author=author,
    )
    follow.delete()
    return redirect('posts:profile', username)


@login_required
def add_like(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    Like.objects.get_or_create(
        user=request.user,
        post=post
    )
    return redirect('posts:post_detail', post_id)


@login_required
def delete_like(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    like = Like.objects.get(
        user=request.user,
        post=post
    )
    like.delete()
    return redirect('posts:post_detail', post_id)
