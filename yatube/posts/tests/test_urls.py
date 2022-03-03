from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

from ..models import Post, Group


User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='author')
        cls.admin = User.objects.create(username='admin')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая пост',
        )
        cls.group = Group.objects.create(
            title='Test group',
            slug='test-slug',
            description='Test description')
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.auth_admin = Client()
        cls.auth_admin.force_login(cls.admin)

    def test_homepage(self):
        # guest_client = Client()
        response = self.guest_client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_post_edit_url(self):
        response = self.authorized_client.get(
            f'/posts/{self.post.id}/edit/')
        self.assertEqual(response.status_code, 200)

    def test_post_edit_auth_not_author(self):
        response = self.auth_admin.get(
            f'/posts/{self.post.id}/edit/')
        self.assertRedirects(response, f'/posts/{self.post.id}/')

    def test_post_edit_guest(self):
        response = self.guest_client.get(
            f'/posts/{self.post.id}/edit/')
        self.assertRedirects(response, '/auth/login/?next=/posts/1/edit/')

    def test_post_create_url(self):
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, 200)

    def test_guest_urls(self):
        dict_match = {
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}): 200,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}): 200,
            reverse('posts:index'): 200,
            '/unexpected-page/': 404,
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username}): 200
        }
        for url, status_code in dict_match.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, status_code)

    def test_create_page_url_redirect_anonymous_on_login(self):
        response = self.guest_client.get(
            reverse('posts:post_create'),
            follow=True)
        self.assertRedirects(response, '/auth/login/?next=/create/')
