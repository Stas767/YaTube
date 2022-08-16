from django.test import Client, TestCase
from django.urls import reverse

from ..models import Post, User


class PostFormTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='User')
        Post.objects.create(
            text='Созданый пост в начале',
            author=cls.user
        )

    def setUp(self):
        self.author_post_client = Client()
        self.author_post_client.force_login(self.user)
        self.post_id = 1
        self.post_count = Post.objects.count()

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
