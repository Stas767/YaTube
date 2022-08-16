from django.test import TestCase, Client
from http import HTTPStatus


class AboutURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_static_urls_about(self):
        available_addresses = ('/about/author/', '/about/tech/')
        for address in available_addresses:
            response = self.guest_client.get(address)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_about_urls_uses_correct_template(self):
        available_template = {
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html',
        }
        for address, temlpate in available_template.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, temlpate)
