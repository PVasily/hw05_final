from django.test import TestCase, Client
from django.contrib.auth import get_user_model
import yatube.settings

User = get_user_model()

yatube.settings.DEBUG = False


class Custom404(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest = Client()

    def test_custom_404(self):
        response = self.guest.get('/unknown-page/')
        self.assertTemplateUsed(response, 'core/404.html')
