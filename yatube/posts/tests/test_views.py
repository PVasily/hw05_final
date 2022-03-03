from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django import forms
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

from ..models import Post, Group, Comment, Follow
from ..forms import PostForm


User = get_user_model()


class PostTemplatesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='auth')
        cls.form = PostForm
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.group = Group.objects.create(
            title='Test group',
            slug='test-slug',
            description='Test description'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group
        )

    @classmethod
    def setUp(self):
        cache.clear()

    def test_used_templates(self):
        """Сравнивает соответствие url-адресов используемым шаблонам."""
        dict_match = {
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}): 'posts/group_list.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}): 'posts/post_detail.html',
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:profile',
                kwargs={
                    'username': self.user.username}): 'posts/profile.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.id}): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html'
        }
        for address, template in dict_match.items():
            with self.subTest(address=address):
                if self.authorized_client:
                    response = self.authorized_client.get(address)
                    self.assertTemplateUsed(response, template)
                elif self.authorized_client == self.post.author:
                    response = self.authorized_client.get(address)
                    self.assertTemplateUsed(response, template)
                else:
                    response = self.guest_client.get(address)
                    self.assertTemplateUsed(response, template)

    def test_types_fields_forms(self):
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        form_context = response.context.get('form')
        self.assertTrue(form_context)
        self.assertIsInstance(form_context, self.form)
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_types_fields_forms_post_edit(self):
        response = self.authorized_client.get(reverse(
            'posts:post_edit', kwargs={'post_id': 1}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        is_edit = response.context.get('is_edit')
        form_context = response.context.get('form')
        self.assertTrue(is_edit)
        self.assertEqual(type(is_edit), bool)
        self.assertIsNotNone(form_context)
        self.assertIsInstance(form_context, self.form)
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_index_page_show_correct_context(self):
        response = self.guest_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        first_text_0 = first_object.text
        first_group_0 = first_object.group.title
        self.assertEqual(first_text_0, 'Тестовый пост')
        self.assertEqual(first_group_0, self.group.title)

    def test_group_list_belong_to_group(self):
        slug = self.group.slug
        response = self.guest_client.get(reverse(
            'posts:group_list',
            kwargs={'slug': slug}))
        choice_group = response.context['page_obj'][0].group.title
        self.assertEqual(choice_group, 'Test group')

    def test_posts_profile(self):
        response = self.guest_client.get(reverse(
            'posts:profile',
            kwargs={'username': self.user.username}))
        for i in range(len(response.context['page_obj'])):
            username = response.context['page_obj'][i].author.username
            self.assertEqual(username, 'auth')

    def test_post_detail(self):
        response = self.guest_client.get(reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.id}))
        post = response.context['post'].id
        self.assertEqual(post, 1)


class PaginatorTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='Anonimus')
        cls.guest_client = Client()
        cls.group = Group.objects.create(
            title='Test group',
            slug='test-slug',
            description='Test description')
        BATCH_SIZE = 13
        cls.list_posts = [Post(
            text=f'Тестовый пост {i}',
            author=cls.user,
            group=cls.group) for i in range(BATCH_SIZE)]
        cls.posts = Post.objects.bulk_create(cls.list_posts, BATCH_SIZE)

    @classmethod
    def setUp(self):
        cache.clear()

    def test_paginator(self):
        slug = self.group.slug
        username = self.user.username
        num_page = {'page': 2}
        qnt_per_first_page = 10
        qnt_per_last_page = 3
        tup_addr = (
            (reverse('posts:index'), '', qnt_per_first_page),
            (reverse('posts:group_list', kwargs={'slug': slug}),
                '',
                qnt_per_first_page),
            (reverse('posts:profile', kwargs={'username': username}),
                '',
                qnt_per_first_page),
            (reverse('posts:index'), num_page, qnt_per_last_page),
            (reverse('posts:profile', kwargs={'username': username}),
                num_page,
                qnt_per_last_page),
            (reverse('posts:group_list', kwargs={'slug': slug}),
                num_page,
                qnt_per_last_page)
        )
        for address, num, qnt in tup_addr:
            with self.subTest(address=address):
                response = self.guest_client.get(address, num)
                len_page = len(response.context['page_obj'])
                self.assertEqual(len_page, qnt)


class ImageViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='admin')
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
        cls.group = Group.objects.create(
            title='Test group',
            slug='test-slug',
            description='Test description')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            image=cls.uploaded
        )
        cls.guest_client = Client()
        cls.authrized_client = Client()
        cls.authrized_client.force_login(cls.user)

    def test_image_context(self):
        cache.clear()
        response = self.guest_client.get(reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.id}))
        image = response.context['post'].image
        self.assertEqual(image, self.post.image)
        urls_list = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username})
        )
        cache.clear()
        for url in urls_list:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                image = response.context['page_obj'][0].image
                self.assertEqual(image, self.post.image)


class CommentViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='admin')

    @classmethod
    def setUp(self):
        self.group = Group.objects.create(
            title='Test group',
            slug='test-slug',
            description='Test description')
        self.post = Post.objects.create(
            author=self.user,
            text='Тестовый пост',
            group=self.group
        )
        self.comment = Comment.objects.create(
            post=self.post,
            author=self.user,
            text='New comment'
        )
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_comment_only_auth(self):
        count = self.post.comments.count()
        form_data = {
            'post': self.post,
            'author': self.guest_client,
            'text': 'The newest text'
        }
        self.authorized_client.post(reverse(
            'posts:add_comment',
            kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True)
        self.assertEqual(self.post.comments.count(), count + 1)

    def test_no_allow_send_comment_guest(self):
        count = self.post.comments.count()
        form_data = {
            'post': self.post,
            'author': self.guest_client,
            'text': 'The newest text'
        }
        self.guest_client.post(reverse(
            'posts:add_comment',
            kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True)
        self.assertEqual(self.post.comments.count(), count)


class CacheTest(TestCase):
    @classmethod
    def setUp(self):
        self.user = User.objects.create(username='admin')
        self.group = Group.objects.create(
            title='Test group',
            slug='test-slug',
            description='Test description')
        self.post = Post.objects.create(
            author=self.user,
            text='Тестовый пост',
            group=self.group
        )
        self.guest_client = Client()

    def test_cache_index_page(self):
        response = self.guest_client.get(reverse('posts:index'))
        cache_check = response.content
        post = Post.objects.get(pk=1)
        post.delete()
        response = self.guest_client.get(reverse('posts:index'))
        self.assertEqual(response.content, cache_check)
        cache.clear()
        response = self.guest_client.get(reverse('posts:index'))
        self.assertNotEqual(response.content, cache_check)


class FollowTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='user')
        cls.admin = User.objects.create(username='admin')
        cls.guest = Client()
        cls.auth_user = Client()
        cls.auth_user.force_login(cls.user)

    @classmethod
    def setUp(self):
        self.group = Group.objects.create(
            title='Test group',
            slug='test-slug',
            description='Test description')
        self.post = Post.objects.create(
            author=self.admin,
            text='Тестовый пост',
            group=self.group
        )

    def test_follow(self):
        self.auth_user.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.admin.username}))
        self.assertEqual(Follow.objects.count(), 1)
        self.auth_user.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.admin.username}))
        self.assertEqual(Follow.objects.count(), 1)

    def test_unfollow(self):
        self.auth_user.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': self.admin.username}))
        self.assertEqual(Follow.objects.count(), 0)

    def test_post_view_at_follower(self):
        self.auth_user.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.admin.username}))
        response = self.auth_user.get(reverse('posts:follow_index'))
        self.assertEqual(len(response.context['page_obj']), 1)

    def test_post_view_at_not_follower(self):
        self.guest.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.admin.username}))
        response = self.guest.get(reverse('posts:follow_index'))
        self.assertIsNone(response.context)
