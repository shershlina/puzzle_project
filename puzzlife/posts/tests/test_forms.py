import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Group, Post, Comment
from posts.forms import PostForm

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='Shershon')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Проверка создания нового поста."""
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        post_for_test = {
            'text': 'Созданный тестовый пост',
            'group': self.group.id,
            'image': uploaded
        }
        response = self.authorized_client.post(reverse('posts:post_create'),
                                               data=post_for_test,
                                               follow=True)
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(Post.objects.filter(
            text=post_for_test['text'],
            group=self.group.id,
            author=self.user,
            image='posts/small.gif'
        ).exists())
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': self.user.username}))

    def test_create_post_form_field_error(self):
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_response = response.context.get('form')
        self.assertIsInstance(form_response, PostForm)

    def test_upload_other_file_instead_of_image(self):
        video = SimpleUploadedFile('file.mp4', b'content',
                                   content_type='video/mp4')
        post_video = {
            'text': 'Попытка загрузить видео вместо картинки',
            'image': video
        }
        response = self.authorized_client.post(reverse('posts:post_create'),
                                               data=post_video,
                                               follow=True)
        self.assertFormError(response, 'form', 'image',
                             ('Загрузите правильное изображение. '
                              'Файл, который вы загрузили, поврежден '
                              'или не является изображением.'))

    def test_create_post_without_group_and_image(self):
        """Проверка создания нового поста без указания группы и изображения."""
        posts_count = Post.objects.count()
        post_without = {
            'text': 'Созданный тестовый пост',
            'group': '',
            'image': ''
        }
        response = self.authorized_client.post(reverse('posts:post_create'),
                                               data=post_without,
                                               follow=True)
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(Post.objects.filter(
            text=post_without['text'],
            author=self.user
        ).exists())
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': self.user.username}))

    def test_edit_post(self):
        """Проверка редактирования поста автором."""
        self.post = Post.objects.create(
            text='Тестовый пост',
            author=self.user
        )
        posts_count = Post.objects.count()
        edited_post = {
            'text': 'Отредактированный тестовый пост',
            'group': self.group.id
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=edited_post, follow=True)
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(Post.objects.get(
            pk=self.post.id).text, edited_post['text'])
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id}))

    def test_create_comment(self):
        """Проверка создания нового комментария
        авторизованным пользователем.
        """
        self.post = Post.objects.create(
            text='Тестовый пост',
            author=self.user
        )
        comments_count = Comment.objects.count()
        comment_for_test = {
            'text': 'Тестовый комментарий',
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=comment_for_test, follow=True)
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertTrue(Comment.objects.filter(
            text=comment_for_test['text']).exists())
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id}))
