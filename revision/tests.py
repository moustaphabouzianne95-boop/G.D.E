from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Flashcard, Question, Quiz, TentativeQuiz, Thematique


class RevisionBaseTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user("admin", "admin@etu.ma", "admin1234")
        cls.demo = User.objects.create_user("demo", "demo@etu.ma", "demo1234")
        cls.theme = Thematique.objects.create(nom="Mathématiques", createur=cls.admin)
        cls.quiz_public = Quiz.objects.create(titre="Quiz public", thematique=cls.theme, createur=cls.admin, est_public=True)
        cls.quiz_prive = Quiz.objects.create(titre="Quiz privé admin", thematique=cls.theme, createur=cls.admin, est_public=False)
        # 3 questions avec 4 choix chacune
        for i, (enonce, bonne) in enumerate([("2+2 ?", 2), ("3×3 ?", 3), ("10-4 ?", 1)], 1):
            q = Question.objects.create(quiz=cls.quiz_public, enonce=enonce, ordre=i)
            for j in range(1, 5):
                q.choix.create(texte=f"choix{j}", est_correcte=(j == bonne))
        cls.flash_publique = Flashcard.objects.create(thematique=cls.theme, recto="Q1", verso="R1", createur=cls.admin, est_publique=True)
        cls.flash_privee = Flashcard.objects.create(thematique=cls.theme, recto="Q-privée", verso="R-privée", createur=cls.admin, est_publique=False)


class ModelTest(RevisionBaseTest):
    def test_nb_questions(self):
        self.assertEqual(self.quiz_public.nb_questions, 3)

    def test_bonne_reponse(self):
        q = self.quiz_public.questions.first()
        self.assertEqual(q.bonne_reponse().texte, "choix2")

    def test_tentative_pourcentage_et_duree(self):
        t = TentativeQuiz.objects.create(utilisateur=self.demo, quiz=self.quiz_public, score=2, nb_questions=4, duree_secondes=95, detail=[])
        self.assertEqual(t.pourcentage, 50)
        self.assertEqual(t.duree_formatee, "01:35")


class VisibilitePartageTest(RevisionBaseTest):
    def test_quiz_public_visible_par_tous(self):
        self.client.force_login(self.demo)
        r = self.client.get(reverse("revision:quiz_liste"))
        self.assertContains(r, "Quiz public")

    def test_quiz_prive_invisible_pour_les_autres(self):
        self.client.force_login(self.demo)
        r = self.client.get(reverse("revision:quiz_liste"))
        self.assertNotContains(r, "Quiz privé admin")

    def test_quiz_prive_visible_pour_createur(self):
        self.client.force_login(self.admin)
        r = self.client.get(reverse("revision:quiz_liste"))
        self.assertContains(r, "Quiz privé admin")

    def test_flashcard_privee_invisible_pour_les_autres(self):
        self.client.force_login(self.demo)
        r = self.client.get(reverse("revision:flashcards"))
        self.assertNotContains(r, "Q-privée")
        self.assertContains(r, "Q1")


class PasserQuizTest(RevisionBaseTest):
    def setUp(self):
        self.client.force_login(self.demo)

    def _reponses(self, nb_bonnes):
        data = {"duree_secondes": "60"}
        for i, q in enumerate(self.quiz_public.questions.all()):
            bonne = q.bonne_reponse().pk
            mauvaise = [c.pk for c in q.choix.all() if c.pk != bonne][0]
            data[f"q_{q.id}"] = str(bonne if i < nb_bonnes else mauvaise)
        return data

    def test_get_passer(self):
        r = self.client.get(reverse("revision:quiz_passer", args=[self.quiz_public.pk]))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "2+2 ?")

    def test_toutes_bonnes_reponses(self):
        r = self.client.post(reverse("revision:quiz_passer", args=[self.quiz_public.pk]), self._reponses(3))
        t = TentativeQuiz.objects.get(utilisateur=self.demo, quiz=self.quiz_public)
        self.assertEqual(t.score, 3)
        self.assertEqual(t.nb_questions, 3)
        self.assertEqual(t.duree_secondes, 60)
        self.assertEqual(len(t.detail), 3)
        self.assertTrue(all(d["correct"] for d in t.detail))
        self.assertEqual(r.status_code, 302)
        self.assertIn(f"/revision/resultat/{t.pk}/", r.url)

    def test_score_partiel(self):
        self.client.post(reverse("revision:quiz_passer", args=[self.quiz_public.pk]), self._reponses(1))
        t = TentativeQuiz.objects.get(utilisateur=self.demo, quiz=self.quiz_public)
        self.assertEqual(t.score, 1)
        self.assertEqual(t.pourcentage, 33)

    def test_resultat_visible_uniquement_par_auteur(self):
        self.client.post(reverse("revision:quiz_passer", args=[self.quiz_public.pk]), self._reponses(3))
        t = TentativeQuiz.objects.get(utilisateur=self.demo)
        r = self.client.get(reverse("revision:resultat", args=[t.pk]))
        self.assertEqual(r.status_code, 200)
        self.client.force_login(self.admin)
        r = self.client.get(reverse("revision:resultat", args=[t.pk]))
        self.assertEqual(r.status_code, 404)

    def test_mes_scores_ne_montre_que_ses_tentatives(self):
        TentativeQuiz.objects.create(utilisateur=self.demo, quiz=self.quiz_public, score=3, nb_questions=3, detail=[])
        TentativeQuiz.objects.create(utilisateur=self.admin, quiz=self.quiz_public, score=1, nb_questions=3, detail=[])
        r = self.client.get(reverse("revision:mes_scores"))
        self.assertEqual(r.context["tentatives"].count(), 1)

    def test_passer_requiert_connexion(self):
        self.client.logout()
        r = self.client.get(reverse("revision:quiz_passer", args=[self.quiz_public.pk]))
        self.assertEqual(r.status_code, 302)


class QuestionCreatePermissionTest(RevisionBaseTest):
    def test_createur_peut_ajouter(self):
        self.client.force_login(self.admin)
        r = self.client.get(reverse("revision:question_ajouter", args=[self.quiz_public.pk]))
        self.assertEqual(r.status_code, 200)
        avant = self.quiz_public.questions.count()
        r = self.client.post(reverse("revision:question_ajouter", args=[self.quiz_public.pk]), {
            "enonce": "5×5 ?", "choix_1": "20", "choix_2": "25", "choix_3": "30", "choix_4": "35", "bonne_reponse": "2",
        }, follow=True)
        self.assertEqual(self.quiz_public.questions.count(), avant + 1)
        q = self.quiz_public.questions.latest("id")
        self.assertEqual(q.bonne_reponse().texte, "25")

    def test_non_createur_bloque(self):
        self.client.force_login(self.demo)
        r = self.client.get(reverse("revision:question_ajouter", args=[self.quiz_public.pk]))
        self.assertEqual(r.status_code, 404)


class RevisionFlashcardsTest(RevisionBaseTest):
    def test_mode_revision_charge_cartes_json(self):
        self.client.force_login(self.demo)
        r = self.client.get(reverse("revision:flashcards_reviser"))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.context["cartes"]), 1)  # seule la publique est visible
        self.assertEqual(r.context["cartes"][0]["recto"], "Q1")

    def test_filtre_theme(self):
        self.client.force_login(self.admin)
        autre = Thematique.objects.create(nom="Informatique", createur=self.admin)
        Flashcard.objects.create(thematique=autre, recto="Q-info", verso="R-info", createur=self.admin)
        r = self.client.get(reverse("revision:flashcards_reviser"), {"theme": self.theme.pk})
        self.assertEqual(len(r.context["cartes"]), 2)  # publique + privée du créateur
