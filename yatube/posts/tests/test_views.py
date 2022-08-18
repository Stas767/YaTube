from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, Client
from django import forms
from django.urls import reverse

from ..models import Group, Post, Comment, Follow

User = get_user_model()


class PostViewTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author_user = User.objects.create_user('Author')
        cls.autorized_user = User.objects.create_user('autorized')
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
                author=cls.author_user,
                group=cls.group,
            )

    def setUp(self):
        self.guest_client = Client()
        self.author_client = Client()
        self.author_client.force_login(self.author_user)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.autorized_user)
        self.post_id = 1
        self.needed_page = 10
        self.group_have_not_post = 0
        cache.clear()

    def test_pages_uses_correct_template(self):

        def url(url, **kwargs):
            return reverse(url, kwargs=kwargs)

        urls = [
            url('posts:index'),
            url('posts:group_list', slug=self.group.slug),
            url('posts:profile', username=self.author_user.username),
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
                response = self.author_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_home_page_uses_correct_context_and_paginator_show_10_posts(self):

        response = self.author_client.get(reverse('posts:index'))
        requested_context = response.context['page_obj'].object_list
        expected_context = list(Post.objects.all()[:self.needed_page])

        self.assertEqual(requested_context, expected_context)
        self.assertEqual(len(response.context['page_obj']), self.needed_page)
        self.assertEqual(requested_context[1], expected_context[1])

    def test_group_list_uses_correct_context_and_paginator_show_10_posts(self):

        response = self.author_client.get(
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

        response = self.author_client.get(
            reverse('posts:profile', kwargs={'username': self.author_user})
        )
        requested_context = list(
            response.context['author'].posts.all()[:self.needed_page]
        )
        expected_context = list(
            Post.objects.filter(author=self.author_user)[:self.needed_page]
        )

        self.assertEqual(requested_context, expected_context)
        self.assertEqual(len(response.context['page_obj']), self.needed_page)
        self.assertEqual(requested_context[1], expected_context[1])

    def test_post_detail_page_show_1_post_equal_post_id(self):

        response = self.author_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post_id})
        )
        requested_context = response.context['post']
        expected_context = Post.objects.get(id=self.post_id)

        self.assertEqual(requested_context, expected_context)

    def test_correct_fields_form_in_post_edit_page(self):

        response = self.author_client.get(
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

        response = self.author_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_created_post_not_entry_in_other_group(self):

        response = self.author_client.get(
            reverse('posts:group_list', kwargs={'slug': 'group2'}))
        count_post_in_group = len(
            response.context['group'].posts.all())

        self.assertEqual(count_post_in_group, self.group_have_not_post)

    def test_cache_index_correct(self):

        resp_before_created_post = self.authorized_client.get('/')
        Post.objects.create(
            text='Проверка кэша',
            author=self.autorized_user
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


class CommentViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author_user = User.objects.create_user('Author')
        cls.autorized_user = User.objects.create_user('autorized')
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.autorized_user)
        cls.first_post = Post.objects.create(
            text='Проверка коментариев',
            author=cls.author_user
        )

    def setUp(self):

        self.form_data = {
            'text': 'Созданый кометарий виден на странице'
        }
        self.count_post_before_add_comment = Comment.objects.count()
        self.resp_add_comment = self.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': self.first_post.id}
            ),
            data=self.form_data
        )
        cache.clear()

    def test_add_comment(self):

        count_post_after_add_comment = Comment.objects.count()

        self.assertEqual(self.resp_add_comment.status_code, HTTPStatus.FOUND)
        self.assertRedirects(self.resp_add_comment, reverse(
            'posts:post_detail', kwargs={'post_id': self.first_post.id})
        )
        self.assertNotEqual(
            self.count_post_before_add_comment,
            count_post_after_add_comment
        )

    def test_add_comment_authorized_users_visible_in_context(self):

        response = self.authorized_client.get(
            reverse(
                'posts:post_detail', kwargs={'post_id': self.first_post.id}
            )
        )
        self.assertEqual(
            'Созданый кометарий виден на странице',
            response.context['comments'][0].text
        )

    def test_add_comment_anon_users_redirect_on_login(self):

        response = self.guest_client.post(
            reverse(
                'posts:add_comment', kwargs={'post_id': self.first_post.id}
            ),
            data=self.form_data
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(response, ('/auth/login/?next=/posts/1/comment/'))


class FollowViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user('Author')
        cls.subscriber = User.objects.create_user('subscriber')
        cls.notsubscriber = User.objects.create_user('notsubscriber')
        cls.guest_client = Client()
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.subscriber)
        cls.notsubscriber_client = Client()
        cls.notsubscriber_client.force_login(cls.notsubscriber)
        # cls.first_post = Post.objects.create(
        #     text='Проверка коментариев',
        #     author=cls.author_user
        # )

    def test_authorized_user_can_follow_and_unfollow(self):

        count_follower_before_follow = Follow.objects.filter(
            user=self.subscriber
        ).count()
        response = self.authorized_client.get(
            reverse('posts:profile_follow', kwargs={'username': self.author})
        )
        count_follower_after_follow = Follow.objects.filter(
            user=self.subscriber
        ).count()

        self.assertRedirects(response, ('/profile/Author/'))
        self.assertNotEqual(
            count_follower_before_follow,
            count_follower_after_follow
        )

        response = self.authorized_client.get(
            reverse('posts:profile_unfollow', kwargs={'username': self.author})
        )
        count_follower_after_unfollow = Follow.objects.filter(
            user=self.subscriber
        ).count()

        self.assertRedirects(response, ('/profile/Author/'))
        self.assertNotEqual(
            count_follower_after_follow,
            count_follower_after_unfollow
        )

    def test_anon_user_cannot_follow(self):

        response = self.guest_client.get(
            reverse('posts:profile_follow', kwargs={'username': self.author})
        )
        self.assertRedirects(
            response,
            ('/auth/login/?next=/profile/Author/follow/')
        )

    def test_author_cannot_subscribe_to_himself(self):

        response = self.author_client.get(
            reverse('posts:profile_follow', kwargs={'username': self.author})
        )
        self.assertRedirects(
            response,
            ('/profile/Author/')
        )

    def test_subscriber_see_new_posts_following_author(self):

        self.authorized_client.get(
            reverse('posts:profile_follow', kwargs={'username': self.author})
        )
        Post.objects.create(
            text='Пост виден только подписчикам',
            author=self.author
        )
        response = self.authorized_client.get(reverse('posts:follow_index'))

        self.assertIn(
            'Пост виден только подписчикам',
            response.context['page_obj'][0].text
        )

    def test_notsubscriber_dont_see_new_posts_notfollowing_author(self):

        Post.objects.create(
            text='Пост виден только подписчикам',
            author=self.author
        )
        response = self.notsubscriber_client.get(reverse('posts:follow_index'))

        self.assertNotIn(
            'Пост виден только подписчикам',
            response.context['page_obj']
        )
