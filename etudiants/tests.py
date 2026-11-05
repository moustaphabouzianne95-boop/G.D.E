from datetime import date

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Etudiant


class EtudiantModelTest(TestCase):
    def setUp(self):
        self.etudiant = Etudiant.objects.create(
            numero_etudiant="ETU-001", prenom="Youssef", nom="Alaoui",
            email="youssef@etu.ma", date_naissance=date(2003, 5, 12), niveau="L2",
        )

    def test_str(self):
        self.assertIn("Alaoui", str(self.etudiant))
        self.assertIn("ETU-001", str(self.etudiant))

    def test_email_unique(self):
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            Etudiant.objects.create(
                numero_etudiant="ETU-002", prenom="A", nom="B",
                email="youssef@etu.ma", date_naissance=date(2000, 1, 1),
            )

    def test_numero_unique(self):
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            Etudiant.objects.create(
                numero_etudiant="ETU-001", prenom="A", nom="B",
                email="autre@etu.ma", date_naissance=date(2000, 1, 1),
            )


class EtudiantViewsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user("demo", "demo@etu.ma", "demo1234")
        cls.e1 = Etudiant.objects.create(numero_etudiant="ETU-001", prenom="Youssef", nom="Alaoui", email="youssef@etu.ma", date_naissance=date(2003, 5, 12), niveau="L2")
        cls.e2 = Etudiant.objects.create(numero_etudiant="ETU-002", prenom="Salma", nom="Benani", email="salma@etu.ma", date_naissance=date(2004, 1, 28), niveau="L1")

    def setUp(self):
        self.client.force_login(self.user)

    def test_liste_requiert_connexion(self):
        self.client.logout()
        r = self.client.get(reverse("etudiants:liste"))
        self.assertEqual(r.status_code, 302)
        self.assertIn("/comptes/connexion/", r.url)

    def test_liste_affiche_etudiants(self):
        r = self.client.get(reverse("etudiants:liste"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Alaoui")
        self.assertContains(r, "Benani")

    def test_recherche_mot_cle(self):
        r = self.client.get(reverse("etudiants:liste"), {"mot_cle": "alaoui"})
        self.assertContains(r, "Alaoui")
        self.assertNotContains(r, "Benani")

    def test_recherche_niveau(self):
        r = self.client.get(reverse("etudiants:liste"), {"niveau": "L1"})
        self.assertContains(r, "Benani")
        self.assertNotContains(r, "Alaoui")

    def test_recherche_combinee(self):
        r = self.client.get(reverse("etudiants:liste"), {"mot_cle": "etu.ma", "niveau": "L2"})
        self.assertContains(r, "Alaoui")
        self.assertNotContains(r, "Benani")

    def test_creer_etudiant(self):
        r = self.client.post(reverse("etudiants:creer"), {
            "numero_etudiant": "ETU-003", "prenom": "Omar", "nom": "Fassi",
            "email": "omar@etu.ma", "date_naissance": "2001-09-03", "niveau": "M1",
        }, follow=True)
        self.assertEqual(r.status_code, 200)
        self.assertTrue(Etudiant.objects.filter(numero_etudiant="ETU-003").exists())

    def test_modifier_etudiant(self):
        r = self.client.post(reverse("etudiants:modifier", args=[self.e1.pk]), {
            "numero_etudiant": "ETU-001", "prenom": "Youssef", "nom": "Alaoui-Modifie",
            "email": "youssef@etu.ma", "date_naissance": "2003-05-12", "niveau": "L3",
        }, follow=True)
        self.assertEqual(r.status_code, 200)
        self.e1.refresh_from_db()
        self.assertEqual(self.e1.nom, "Alaoui-Modifie")
        self.assertEqual(self.e1.niveau, "L3")

    def test_supprimer_etudiant(self):
        r = self.client.post(reverse("etudiants:supprimer", args=[self.e2.pk]), follow=True)
        self.assertEqual(r.status_code, 200)
        self.assertFalse(Etudiant.objects.filter(pk=self.e2.pk).exists())

    def test_detail(self):
        r = self.client.get(reverse("etudiants:detail", args=[self.e1.pk]))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "youssef@etu.ma")


class ExportCSVTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user("demo", "demo@etu.ma", "demo1234")
        for i in range(3):
            Etudiant.objects.create(
                numero_etudiant=f"ETU-{i:03d}", prenom=f"Prenom{i}", nom=f"Nom{i}",
                email=f"e{i}@etu.ma", date_naissance=date(2000, 1, 1), niveau="L1" if i < 2 else "M2",
            )

    def test_export_requiert_connexion(self):
        r = self.client.get(reverse("etudiants:export_csv"))
        self.assertEqual(r.status_code, 302)

    def test_export_complet(self):
        self.client.force_login(self.user)
        r = self.client.get(reverse("etudiants:export_csv"))
        self.assertEqual(r.status_code, 200)
        self.assertIn("text/csv", r["Content-Type"])
        self.assertIn("attachment", r["Content-Disposition"])
        lignes = r.content.decode("utf-8-sig").strip().splitlines()
        self.assertEqual(len(lignes), 4)  # en-tête + 3 étudiants
        self.assertIn("Numéro étudiant", lignes[0])

    def test_export_filtre(self):
        self.client.force_login(self.user)
        r = self.client.get(reverse("etudiants:export_csv"), {"niveau": "M2"})
        lignes = r.content.decode("utf-8-sig").strip().splitlines()
        self.assertEqual(len(lignes), 2)  # en-tête + 1 étudiant M2
