from datetime import date, time, timedelta

from django.contrib.auth.models import User
from django.core import mail
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Devoir, Evenement


class EvenementModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user("demo", "demo@etu.ma", "demo1234")

    def test_duree_heures(self):
        e = Evenement.objects.create(utilisateur=self.user, titre="Cours", type="cours",
                                      date=date(2026, 11, 9), heure_debut=time(8, 0), heure_fin=time(10, 30))
        self.assertEqual(e.duree_heures, 2.5)

    def test_form_validation_heure_fin_avant_debut(self):
        self.client.force_login(self.user)
        r = self.client.post(reverse("planning:evenement_creer"), {
            "titre": "Invalide", "matiere": "", "type": "cours", "date": "2026-11-09",
            "heure_debut": "20:00", "heure_fin": "18:00", "lieu": "",
        })
        self.assertEqual(r.status_code, 200)  # formulaire re-affiché avec erreur
        self.assertFalse(Evenement.objects.filter(titre="Invalide").exists())


class CalendrierTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user("demo", "demo@etu.ma", "demo1234")
        cls.ev = Evenement.objects.create(utilisateur=cls.user, titre="Cours Algo", type="cours",
                                           date=date.today(), heure_debut=time(8, 0), heure_fin=time(10, 0))

    def test_calendrier_requiert_connexion(self):
        r = self.client.get(reverse("planning:calendrier"))
        self.assertEqual(r.status_code, 302)

    def test_calendrier_affiche_evenement_et_stats(self):
        self.client.force_login(self.user)
        r = self.client.get(reverse("planning:calendrier"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Cours Algo")
        self.assertEqual(r.context["heures"]["cours"], 2.0)

    def test_navigation_mois(self):
        self.client.force_login(self.user)
        r = self.client.get(reverse("planning:calendrier"), {"annee": 2026, "mois": 12})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context["mois"], 12)

    def test_evenements_d_un_autre_utilisateur_invisibles(self):
        autre = User.objects.create_user("autre", "a@etu.ma", "pass1234")
        Evenement.objects.create(utilisateur=autre, titre="Cours privé autre", type="cours",
                                  date=date.today(), heure_debut=time(9, 0), heure_fin=time(10, 0))
        self.client.force_login(self.user)
        r = self.client.get(reverse("planning:calendrier"))
        self.assertNotContains(r, "Cours privé autre")


class DevoirTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user("demo", "demo@etu.ma", "demo1234")
        cls.devoir = Devoir.objects.create(utilisateur=cls.user, titre="TP SQL",
                                            date_echeance=timezone.now() + timedelta(hours=3))

    def test_en_retard(self):
        self.assertFalse(self.devoir.en_retard)
        en_retard = Devoir.objects.create(utilisateur=self.user, titre="Vieux",
                                           date_echeance=timezone.now() - timedelta(days=1))
        self.assertTrue(en_retard.en_retard)

    def test_toggle_rendu(self):
        self.client.force_login(self.user)
        r = self.client.post(reverse("planning:devoir_toggle", args=[self.devoir.pk]), follow=True)
        self.assertEqual(r.status_code, 200)
        self.devoir.refresh_from_db()
        self.assertTrue(self.devoir.rendu)
        self.assertIsNotNone(self.devoir.date_rendu)
        # re-toggle
        self.client.post(reverse("planning:devoir_toggle", args=[self.devoir.pk]))
        self.devoir.refresh_from_db()
        self.assertFalse(self.devoir.rendu)
        self.assertIsNone(self.devoir.date_rendu)

    def test_devoirs_d_un_autre_utilisateur_invisibles(self):
        autre = User.objects.create_user("autre", "a@etu.ma", "pass1234")
        Devoir.objects.create(utilisateur=autre, titre="Devoir privé autre", date_echeance=timezone.now() + timedelta(days=1))
        self.client.force_login(self.user)
        r = self.client.get(reverse("planning:devoirs"))
        self.assertNotContains(r, "Devoir privé autre")


class RappelsEmailTest(TestCase):
    """En test, Django remplace automatiquement le backend e-mail par locmem."""
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user("demo", "demo@etu.ma", "demo1234")

    def test_a_rappeler(self):
        bientot = Devoir.objects.create(utilisateur=self.user, titre="Bientôt", date_echeance=timezone.now() + timedelta(hours=5))
        loin = Devoir.objects.create(utilisateur=self.user, titre="Loin", date_echeance=timezone.now() + timedelta(days=10))
        rendu = Devoir.objects.create(utilisateur=self.user, titre="Rendu", date_echeance=timezone.now() - timedelta(days=1), rendu=True)
        self.assertTrue(bientot.a_rappeler)
        self.assertFalse(loin.a_rappeler)
        self.assertFalse(rendu.a_rappeler)

    def test_envoi_rappel_via_page(self):
        Devoir.objects.create(utilisateur=self.user, titre="TP Python", matiere="Info",
                              date_echeance=timezone.now() + timedelta(hours=3))
        self.client.force_login(self.user)
        r = self.client.post(reverse("planning:rappels"), follow=True)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("TP Python", mail.outbox[0].subject)
        self.assertEqual(mail.outbox[0].to, ["demo@etu.ma"])

    def test_anti_spam_24h(self):
        d = Devoir.objects.create(utilisateur=self.user, titre="TP", date_echeance=timezone.now() + timedelta(hours=3))
        self.client.force_login(self.user)
        self.client.post(reverse("planning:rappels"))
        self.client.post(reverse("planning:rappels"))
        self.assertEqual(len(mail.outbox), 1)  # pas de second e-mail
        d.refresh_from_db()
        self.assertIsNotNone(d.dernier_rappel)

    def test_commande_envoyer_rappels(self):
        Devoir.objects.create(utilisateur=self.user, titre="Devoir cron", date_echeance=timezone.now() + timedelta(hours=2))
        call_command("envoyer_rappels")
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Devoir cron", mail.outbox[0].subject)

    def test_aucun_rappel_si_rien_a_faire(self):
        Devoir.objects.create(utilisateur=self.user, titre="Loin", date_echeance=timezone.now() + timedelta(days=30))
        self.client.force_login(self.user)
        self.client.post(reverse("planning:rappels"))
        self.assertEqual(len(mail.outbox), 0)
