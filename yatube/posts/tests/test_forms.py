from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from ..models import Post, Group
from ..forms import PostForm


User = get_user_model()


class PostCreateFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='Anonimus')
        cls.form = PostForm()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

    @classmethod
    def setUp(self):
        self.group = Group.objects.create(
            title='Test group',
            slug='test-slug',
            description='Test description')
        self.post = Post.objects.create(
            author=self.user,
            text='Тестовый пост',
            image=self.uploaded
        )
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
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
        post_count = Post.objects.count()
        form_data = {
            'text': 'Новый текст из формы',
            'image': uploaded
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username}))
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            Post.objects.filter(
                text='Новый текст из формы').exists())

    def test_create_form_for_guest(self):
        """Проверяем редирект гостя при попытке зайти на страницу /create/."""
        post_count = Post.objects.count()
        form_data = {
            'text': 'Текст из формы',
            'image': self.uploaded
        }
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, '/auth/login/?next=/create/')
        self.assertEqual(Post.objects.count(), post_count)
        self.assertEqual(response.status_code, 200)

    def test_post_edit(self):
        form_data = {
            'text': 'New text',
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.context['post'].text, 'New text')
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}))

    def test_form_label(self):
        field = PostCreateFormTest.form.fields
        dict_match = {
            f'{field["text"].label}': 'Текст поста',
            f'{field["group"].label}': 'Название сообщества',
            f'{field["text"].help_text}': 'Введите текст поста',
            f'{field["group"].help_text}': 'Выбирите группу',
            f'{field["image"].help_text}': 'Выберите файл с изображением',
            f'{field["image"].label}': 'Изображение'
        }
        for field, value in dict_match.items():
            self.assertEqual(field, value)
