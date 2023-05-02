from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse
from django import forms

from puzzlife.settings import POSTS_NUM
from posts.models import Post, Group, Comment, Follow

User = get_user_model()
TEST_POSTS_NUM = 16


class PostsPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            author=User.objects.create_user(username='Shershon'),
            text='Тестовый пост',
            created='Тестовая дата',
            group=cls.group
        )

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.post.author)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}): 'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': self.post.author}): (
                'posts/profile.html'
            ),
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post.id}): (
                'posts/post_detail.html'
            ),
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit',
                    kwargs={'post_id': self.post.id}): (
                'posts/create_post.html'
            ),
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_posts_pages_show_correct_context(self):
        """Шаблоны страниц index, group_list, profile
        сформированы с правильным контекстом.
        """
        posts_pages_urls = {
            'posts:index': {},
            'posts:group_list': {'slug': self.group.slug},
            'posts:profile': {'username': self.post.author},
        }
        for url, kwargs in posts_pages_urls.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(
                    reverse(url, kwargs=kwargs))
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object, self.post)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.assertEqual(response.context['post'], self.post)

    def test_create_and_edit_page_show_correct_context(self):
        """Шаблоны create и post_edit сформированы с правильным контекстом."""
        posts_pages_url = {
            'posts:post_create': {},
            'posts:post_edit': {'post_id': self.post.id},
        }
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                for url, kwargs in posts_pages_url.items():
                    response = self.authorized_client.get(
                        reverse(url, kwargs=kwargs))
                    form_field = response.context['form'].fields[value]
                    self.assertIsInstance(form_field, expected)

    def test_post_with_group_added_to_pages_correctly(self):
        """Пост с группой добавляется на нужные страницы."""
        self.another_group = Group.objects.create(
            title='Другая тестовая группа',
            slug='second_slug',
            description='Другое тестовое описание',
        )
        another_url = reverse('posts:group_list',
                              kwargs={'slug': self.another_group.slug})
        posts_pages_urls = {
            'posts:index': {},
            'posts:group_list': {'slug': self.group.slug},
            'posts:profile': {'username': self.post.author},
        }
        for url, kwargs in posts_pages_urls.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(
                    reverse(url, kwargs=kwargs)).context['page_obj']
                self.assertIn(self.post, response)
        response_two = self.authorized_client.get(another_url)
        self.assertNotIn(self.post, response_two.context['page_obj'])

    def test_comment_added_to_post_detail(self):
        """Комментарий добавляется на страницу просмотра поста."""
        comment = Comment.objects.create(
            post=self.post,
            text='Тестовый_комментарий',
            author=self.post.author
        )
        response = self.authorized_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post.id})).context['comments']
        self.assertIn(comment, response)

    def test_post_in_cache(self):
        """Проверка кэша."""
        first_response = self.guest_client.get(reverse('posts:index')).content
        Post.objects.get(id=1).delete()
        second_response = self.guest_client.get(reverse('posts:index')).content
        self.assertEqual(first_response, second_response)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Shershon')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание'
        )
        cls.post = []
        for i in range(TEST_POSTS_NUM):
            cls.post.append(
                Post.objects.create(
                    author=cls.user,
                    text=f'Тестовый пост {i}',
                    group=cls.group
                )
            )

    def setUp(self):
        cache.clear()
        self.guest_client = Client()

    def test_paginator_show_correct_num_of_pages(self):
        """Паджинатор корректно работает на всех страницах."""
        pages_with_paginator = {
            'index': reverse('posts:index'),
            'group': reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}
            ),
            'profile': reverse(
                'posts:profile',
                kwargs={'username': self.user.username}
            )
        }
        for url, reverse_url in pages_with_paginator.items():
            with self.subTest(url=url):
                response_one = self.guest_client.get(reverse_url)
                self.assertEqual(len(response_one.context['page_obj']),
                                 POSTS_NUM)
                response_two = self.guest_client.get(reverse_url + '?page=2')
                self.assertEqual(len(response_two.context['page_obj']),
                                 TEST_POSTS_NUM - POSTS_NUM)


class FollowViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post = Post.objects.create(
            author=User.objects.create_user(username='author'),
            text='Тестовый пост',
        )
        cls.follower = User.objects.create(username='follower')

    def setUp(self):
        self.guest_client = Client()
        self.author = Client()
        self.author.force_login(self.post.author)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.follower)

    def test_authorized_can_follow(self):
        """Авторизованный пользователь может подписаться на автора."""
        self.authorized_client.get(
            reverse('posts:profile_follow',
                    kwargs={'username': self.post.author.username}))
        self.assertEqual(Follow.objects.all().count(), 1)

    def test_authorized_can_unfollow(self):
        """Авторизованный пользователь может отписаться от автора."""
        Follow.objects.create(
            user=self.follower,
            author=self.post.author
        )
        self.authorized_client.get(
            reverse('posts:profile_unfollow',
                    kwargs={'username': self.post.author.username}))
        self.assertEqual(Follow.objects.all().count(), 0)

    def test_guest_cant_follow(self):
        follow_page = reverse('posts:profile_follow',
                              kwargs={'username': self.post.author.username})
        self.guest_client.get(follow_page)
        self.assertEqual(Follow.objects.all().count(), 0)

    def test_user_cant_follow_author_twice(self):
        self.authorized_client.get(
            reverse('posts:profile_follow',
                    kwargs={'username': self.post.author.username}))
        self.assertEqual(Follow.objects.all().count(), 1)
        self.authorized_client.get(
            reverse('posts:profile_follow',
                    kwargs={'username': self.post.author.username}))
        self.assertEqual(Follow.objects.all().count(), 1)

    def test_post_of_following_show_on_follow_page(self):
        """Пост пользователя появляется в ленте только его подписчиков."""
        another_user = User.objects.create(username='another')
        self.another_client = Client()
        self.another_client.force_login(another_user)
        Follow.objects.create(
            user=self.follower,
            author=self.post.author
        )
        follower_response = self.authorized_client.get(
            reverse('posts:follow_index')).context['page_obj']
        another_response = self.another_client.get(
            reverse('posts:follow_index')).context['page_obj']
        self.assertIn(self.post, follower_response)
        self.assertNotIn(self.post, another_response)
