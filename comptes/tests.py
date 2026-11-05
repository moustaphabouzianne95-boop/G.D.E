from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class AuthentificationTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user("demo", "demo@etu.ma", "demo1234")

    def test_page_connexion(self):
        r = self.client.get(reverse("comptes:connexion"))
        self.assertEqual(r.status_code, 200)

    def test_connexion_reussie(self):
        r = self.client.post(reverse("comptes:connexion"), {"username": "demo", "password": "demo1234"})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r.url, reverse("etudiants:liste"))

    def test_connexion_echouee(self):
        r = self.client.post(reverse("comptes:connexion"), {"username": "demo", "password": "mauvais"})
        self.assertEqual(r.status_code, 200)  # reste sur la page avec l'erreur
        self.assertFalse(r.wsgi_request.user.is_authenticated)

    def test_deconnexion(self):
        self.client.force_login(self.user)
        r = self.client.post(reverse("comptes:deconnexion"))
        self.assertEqual(r.status_code, 302)
        self.assertIn("/comptes/connexion/", r.url)

    def test_inscription_cree_et_connecte(self):
        r = self.client.post(reverse("comptes:inscription"), {
            "username": "nouveau", "password1": "TestPass123!", "password2": "TestPass123!",
        }, follow=True)
        self.assertEqual(r.status_code, 200)
        self.assertTrue(User.objects.filter(username="nouveau").exists())
        self.assertTrue(r.wsgi_request.user.is_authenticated)

    def test_inscription_mots_de_passe_differents(self):
        r = self.client.post(reverse("comptes:inscription"), {
            "username": "x", "password1": "TestPass123!", "password2": "Autre123!",
        })
        self.assertEqual(r.status_code, 200)
        self.assertFalse(User.objects.filter(username="x").exists())
