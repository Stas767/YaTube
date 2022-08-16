from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Group',
            slug='Slug',
            description='Описание',
        )
        cls.long_post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='Не более 15 символов может поместиться в превью поста',
        )
        cls.short_post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='Короткий пост',
        )

    def test_post_str_returns_text_no_longer_15_symbols(self):
        self.assertEqual('Не более 15 сим', f"{self.long_post}")
        self.assertEqual('Короткий пост', f"{self.short_post}")

    def test_group_str_returns_text_title(self):
        self.assertEqual('Group', self.group.title)

    def test_verbose_name(self):
        field_verboses = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.long_post._meta.get_field(field).verbose_name,
                    expected_value
                )

    def test_help_text(self):
        field_help_texts = {
            'text': 'Введите текст поста',
            'group': 'Группа, к которой будет относиться пост',
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.long_post._meta.get_field(field).help_text,
                    expected_value
                )
