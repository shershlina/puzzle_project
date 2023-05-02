from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, Client

from posts.models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group
        )

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        user_author = PostURLTests.user
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(user_author)
        self.user = User.objects.create_user(username='Shershon')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_all_url_exists_at_desired_location(self):
        """Тестирование страниц, доступных любому пользователю."""
        pages = (
            '/',
            f'/group/{self.group.slug}/',
            f'/profile/{self.user.username}/',
            f'/posts/{self.post.id}/'
        )
        for page in pages:
            with self.subTest(page=page):
                response = self.guest_client.get(page)
                self.assertEqual(response.status_code, 200)

    def test_create_url_exists_at_desired_location(self):
        """Страница /create/ доступна авторизованному пользователю."""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, 200)

    def test_post_edit_url_exists_at_desired_location_authorized(self):
        """Страница /posts/37/edit/ доступна автору поста."""
        response = self.authorized_client_author.get(
            f'/posts/{self.post.id}/edit/')
        self.assertEqual(response.status_code, 200)

    def test_urls_redirect_anonymous_on_login(self):
        """Страницы создания, редактирования и комментирования поста
        перенаправят анонимного пользователя на страницу логина.
        """
        pages = (
            '/create/',
            f'/posts/{self.post.id}/edit/',
            f'/posts/{self.post.id}/comment/',
            f'/profile/{self.user.username}/follow/'
        )
        for page in pages:
            with self.subTest(page=page):
                response = self.guest_client.get(page, follow=True)
                self.assertRedirects(response, f'/auth/login/?next={page}')

    def test_post_edit_url_redirect_not_author_on_login(self):
        """Страница posts/post_id/edit/ перенаправит пользователя,
        который авторизован, но не является автором поста,
        на страницу просмотра этого поста.
        """
        response = self.authorized_client.get(
            f'/posts/{self.post.id}/edit/', follow=True)
        self.assertRedirects(
            response, f'/posts/{self.post.id}/')

    def test_nonexistent_pages_show_not_found(self):
        """Несуществующая страница выдаст ошибку 404."""
        not_exist_pages = (
            '/posts/group_not_exist/',
            '/posts/author_not_exist/',
            '/posts/author_not_exist/1/'
        )
        for page in not_exist_pages:
            with self.subTest(page=page):
                response = self.guest_client.get(page)
                self.assertEqual(response.status_code, 404)
                self.assertTemplateUsed(response, 'core/404.html')

    def test_urls_uses_correct_template(self):
        """URL-адреса используют соответствующие шаблоны."""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user.username}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            f'/posts/{self.post.id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
            '/follow/': 'posts/follow.html'
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client_author.get(url)
                self.assertTemplateUsed(response, template)
