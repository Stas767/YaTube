from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, Client
from http import HTTPStatus

from ..models import Group, Post


User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author_user = User.objects.create_user('Author_post')
        cls.user = User.objects.create_user('Ivan')
        cls.group = Group.objects.create(
            title='Group',
            slug='Slug',
            description='Описание',
        )
        cls.post = Post.objects.create(
            text='Пост 1',
            author=cls.author_user,
            group=cls.group
        )

    def setUp(self):
        self.guest_client = Client()
        self.author_post_client = Client()
        self.author_post_client.force_login(self.author_user)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_url_with_guest_access(self):
        list_urls = (
            '/',
            '/group/Slug/',
            '/profile/Ivan/',
            '/posts/1/'
        )
        for url in list_urls:
            with self.subTest(url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_url_has_access_only_author(self):
        response = self.author_post_client.get('/posts/1/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        response = self.authorized_client.get('/posts/1/edit/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        response = self.guest_client.get('/posts/1/edit/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_post_create_url_has_access_authorized_user(self):
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        response = self.guest_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_unexisting_page_return_custom_not_found(self):
        response = self.guest_client.get('/unexisting_page')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')

    def test_urls_uses_correct_temlate(self):
        templates_url_names = {
            '/': 'posts/index.html',
            '/group/Slug/': 'posts/group_list.html',
            '/profile/Ivan/': 'posts/profile.html',
            '/posts/1/': 'posts/post_detail.html',
            '/posts/1/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.author_post_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_post_create_url_redirect_annonimus_on_login(self):
        response = self.guest_client.get('/create/')
        self.assertRedirects(response, ('/auth/login/?next=/create/'))
