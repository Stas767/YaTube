from http import HTTPStatus
# from django.db import IntegrityError
from django.core.cache import cache
import shutil
import tempfile
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django import forms

from ..models import Group, Post, Comment, Follow


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='AuthorUser')
        cls.user_autorized = User.objects.create_user(username='HasNoName')
        cls.group = Group.objects.create(
            title='Group',
            slug='group',
            description='Описание',
        )
        cls.group2 = Group.objects.create(
            title='Group2',
            slug='group2',
            description='Описание2',
        )
        for post in range(13):
            Post.objects.create(
                text=f'Тестовый пост {post}',
                author=cls.user,
                group=cls.group,
            )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.author_post_client = Client()
        self.author_post_client.force_login(self.user)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_autorized)
        self.post_id = 1
        self.needed_page = 10
        self.group_have_not_post = 0
        self.post_with_picture = 14
        cache.clear()

    def test_pages_uses_correct_template(self):

        def url(url, **kwargs):
            return reverse(url, kwargs=kwargs)

        urls = [
            url('posts:index'),
            url('posts:group_list', slug=self.group.slug),
            url('posts:profile', username=self.user.username),
            url('posts:post_detail', post_id=self.post_id),
            url('posts:post_edit', post_id=self.post_id),
            url('posts:post_create'),
        ]

        templates = [
            'posts/index.html',
            'posts/group_list.html',
            'posts/profile.html',
            'posts/post_detail.html',
            'posts/create_post.html',
            'posts/create_post.html',
        ]

        for url, template in zip(urls, templates):
            with self.subTest(url=url):
                response = self.author_post_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_home_page_uses_correct_context_and_paginator_show_10_posts(self):

        response = self.author_post_client.get(reverse('posts:index'))
        requested_context = response.context['page_obj'].object_list
        expected_context = list(Post.objects.all()[:self.needed_page])

        self.assertEqual(requested_context, expected_context)
        self.assertEqual(len(response.context['page_obj']), self.needed_page)
        self.assertEqual(requested_context[1], expected_context[1])

    def test_group_list_uses_correct_context_and_paginator_show_10_posts(self):

        response = self.author_post_client.get(
            reverse('posts:group_list', kwargs={'slug': 'group'})
        )
        requested_context = list(
            response.context['group'].posts.all()[:self.needed_page]
        )
        expected_context = list(
            Post.objects.filter(group=self.group)[:self.needed_page]
        )

        self.assertEqual(requested_context, expected_context)
        self.assertEqual(len(response.context['page_obj']), self.needed_page)
        self.assertEqual(requested_context[1], expected_context[1])

    def test_profile_uses_correct_context_and_paginator_show_10_posts(self):

        response = self.author_post_client.get(
            reverse('posts:profile', kwargs={'username': self.user})
        )
        requested_context = list(
            response.context['author'].posts.all()[:self.needed_page]
        )
        expected_context = list(
            Post.objects.filter(author=self.user)[:self.needed_page]
        )

        self.assertEqual(requested_context, expected_context)
        self.assertEqual(len(response.context['page_obj']), self.needed_page)
        self.assertEqual(requested_context[1], expected_context[1])

    def test_post_detail_page_show_1_post_equal_post_id(self):

        response = self.author_post_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post_id})
        )
        requested_context = response.context['post']
        expected_context = Post.objects.get(id=self.post_id)

        self.assertEqual(requested_context, expected_context)

    def test_correct_fields_form_in_post_edit_page(self):

        response = self.author_post_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post_id})
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_correct_fields_form_in_post_create_page(self):

        response = self.author_post_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_created_post_not_entry_in_other_group(self):

        response = self.author_post_client.get(
            reverse('posts:group_list', kwargs={'slug': 'group2'}))
        count_post_in_group = len(
            response.context['group'].posts.all())

        self.assertEqual(count_post_in_group, self.group_have_not_post)

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

    def test_add_comment(self):
        count_post_before = Comment.objects.count()
        form_data = {
            'text': 'Созданый кометарий виден на странице'
        }

        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post_id}),
            data=form_data
        )
        count_post_after = Comment.objects.count()

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': self.post_id})
        )
        self.assertNotEqual(count_post_before, count_post_after)

        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post_id})
        )
        self.assertEqual(
            'Созданый кометарий виден на странице',
            response.context['comments'][0].text
        )

        response = self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post_id}),
            data=form_data
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(response, ('/auth/login/?next=/posts/1/comment/'))

    def test_cache_index_correct(self):

        resp_before_created_post = self.authorized_client.get('/')
        Post.objects.create(
            text='Проверка кэша',
            author=self.user_autorized
        )
        resp_after_created_post = self.authorized_client.get('/')

        self.assertEqual(
            resp_before_created_post.content,
            resp_after_created_post.content,
        )

        cache.clear()
        resp_after_clear_cache = self.authorized_client.get('/')

        self.assertNotEqual(
            resp_after_created_post.content,
            resp_after_clear_cache.content,
        )

    def test_authorized_user_can_follow_unfollow(self):

        count_follower_before_follow = Follow.objects.filter(
            user=self.user_autorized
        ).count()
        response = self.authorized_client.get(
            reverse('posts:profile_follow', kwargs={'username': self.user})
        )
        count_follower_after_follow = Follow.objects.filter(
            user=self.user_autorized
        ).count()

        self.assertRedirects(response, ('/profile/AuthorUser/'))
        self.assertNotEqual(
            count_follower_before_follow,
            count_follower_after_follow
        )

        response = self.authorized_client.get(
            reverse('posts:profile_unfollow', kwargs={'username': self.user})
        )
        count_follower_after_unfollow = Follow.objects.filter(
            user=self.user_autorized
        ).count()

        self.assertRedirects(response, ('/profile/AuthorUser/'))
        self.assertNotEqual(
            count_follower_after_follow,
            count_follower_after_unfollow
        )

        response = self.guest_client.get(
            reverse('posts:profile_follow', kwargs={'username': self.user})
        )
        self.assertRedirects(
            response,
            ('/auth/login/?next=/profile/AuthorUser/follow/')
        )

        response_follow_yourself = self.authorized_client.get(
            reverse(
                'posts:profile_follow', kwargs={
                    'username': self.user_autorized}
            )
        )
        self.assertRedirects(
            response_follow_yourself,
            ('/profile/HasNoName/')
        )

    # def test_no_self_user(self):
    #     """Нельзя подписаться на самого себя"""

    #     constraint_name = 'no_self_user'
    #     with self.assertRaisesMessage(IntegrityError, constraint_name):
    #         self.authorized_client.get(
    #             reverse(
    #                 'posts:profile_follow', kwargs={
    #                     'username': self.user_autorized}
    #             )
    #         )
    #         Follow.objects.create(
    #             user=self.user_autorized,
    #             author=self.user_autorized
        # )

    def test_follower_see_new_posts_following(self):

        not_a_follower = User.objects.create_user(username='JustUser')
        not_a_follower_client = Client()
        not_a_follower_client.force_login(not_a_follower)

        self.authorized_client.get(
            reverse('posts:profile_follow', kwargs={'username': self.user})
        )
        Post.objects.create(
            text='Пост виден только подписчикам',
            author=self.user
        )
        response = self.authorized_client.get(reverse('posts:follow_index'))

        self.assertIn(
            'Пост виден только подписчикам',
            response.context['page_obj'][0].text
        )

        response = not_a_follower_client.get(reverse('posts:follow_index'))
        self.assertNotIn(
            'Пост виден только подписчикам',
            response.context['page_obj']
        )
