import shutil
import tempfile

from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile


from ..models import Group, Post, User


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user('Stas')
        Post.objects.create(
            text='Созданый пост в начале',
            author=cls.user
        )
        cls.group = Group.objects.create(
            title='Group',
            slug='group',
            description='Описание',
        )

    def setUp(self):
        self.author_post_client = Client()
        self.author_post_client.force_login(self.user)
        self.post_id = 1
        self.post_count = Post.objects.count()
        self.post_with_picture = 2
        cache.clear()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_valid_form_created_post(self):

        form_data = {
            'text': 'Тестовый пост',
            'author': self.user,
        }

        response = self.author_post_client.post(
            reverse('posts:post_create'), data=form_data
        )
        self.assertRedirects(
            response,
            reverse('posts:profile', args={self.user})
        )
        self.assertEqual(Post.objects.count(), self.post_count + 1)

    def test_valid_form_changes_post_in_post_edit(self):

        post_before_changes = Post.objects.get(id=self.post_id)
        form_data = {
            'text': 'Отредактированый тест',
            'author': self.user,
        }
        response = self.author_post_client.post(
            reverse('posts:post_edit', args={self.post_id}),
            data=form_data,
        )
        post_after_changes = Post.objects.get(id=self.post_id)

        self.assertRedirects(response,
                             reverse('posts:post_detail',
                                     args={self.post_id}
                                     ))
        self.assertEqual(Post.objects.count(), self.post_count)
        self.assertNotEqual(
            post_before_changes.text,
            post_after_changes.text
        )
        self.assertEqual(post_after_changes.text, form_data['text'])

    def test_post_with_picture_transmitted_in_context(self):

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
        form_data = {
            'text': 'Пост',
            'author': self.user,
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.author_post_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )

        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username': self.user})
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)

        urls = {
            'posts:index': {},
            'posts:group_list': {'slug': self.group.slug},
            'posts:profile': {'username': self.user},
        }
        for url_name, kwargs in urls.items():
            with self.subTest(url_name=url_name):
                response = self.author_post_client.get(
                    reverse(url_name, kwargs=kwargs)
                )

                self.assertTrue(response.context.get('page_obj')[0].image)

        response = self.author_post_client.get(
            reverse('posts:post_detail', kwargs={
                    'post_id': self.post_with_picture
                    })
        )
        self.assertTrue(response.context.get('post').image)
