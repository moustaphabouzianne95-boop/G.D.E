from datetime import date, time, timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from etudiants.models import Etudiant
from planning.models import Devoir, Evenement
from revision.models import Flashcard, Question, Quiz, TentativeQuiz, Thematique


class APIBaseTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user("admin", "admin@etu.ma", "admin1234")
        cls.demo = User.objects.create_user("demo", "demo@etu.ma", "demo1234")
        cls.theme = Thematique.objects.create(nom="Maths", createur=cls.admin)
        cls.quiz = Quiz.objects.create(titre="Quiz API", thematique=cls.theme, createur=cls.admin, est_public=True)
        cls.quiz_prive = Quiz.objects.create(titre="Privé", thematique=cls.theme, createur=cls.admin, est_public=False)
        for i, bonne in enumerate([2, 3], 1):
            q = Question.objects.create(quiz=cls.quiz, enonce=f"Q{i}", ordre=i)
            for j in range(1, 5):
                q.choix.create(texte=f"c{j}", est_correcte=(j == bonne))
        cls.flash = Flashcard.objects.create(thematique=cls.theme, recto="R?", verso="V", createur=cls.admin)
        Etudiant.objects.create(numero_etudiant="ETU-1", prenom="A", nom="B", email="a@b.ma", date_naissance=date(2000, 1, 1), niveau="L1")
        Evenement.objects.create(utilisateur=cls.demo, titre="Cours demo", type="cours", date=date.today(), heure_debut=time(8, 0), heure_fin=time(10, 0))
        Evenement.objects.create(utilisateur=cls.admin, titre="Cours admin", type="cours", date=date.today(), heure_debut=time(9, 0), heure_fin=time(11, 0))
        Devoir.objects.create(utilisateur=cls.demo, titre="Devoir demo", date_echeance=timezone.now() + timedelta(days=2))


class AuthRequiredTest(APIBaseTest):
    def test_anonyme_refuse(self):
        for url in ["/api/etudiants/", "/api/quiz/", "/api/evenements/", "/api/"]:
            r = self.client.get(url)
            self.assertIn(r.status_code, (401, 403), url)


class EtudiantsAPITest(APIBaseTest):
    def setUp(self):
        self.client.force_login(self.demo)

    def test_liste(self):
        r = self.client.get("/api/etudiants/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["results"][0]["nom"], "B")

    def test_recherche(self):
        r = self.client.get("/api/etudiants/", {"search": "ETU-1"})
        self.assertEqual(len(r.json()["results"]), 1)

    def test_creer(self):
        r = self.client.post("/api/etudiants/", {
            "numero_etudiant": "ETU-2", "prenom": "S", "nom": "C",
            "email": "s@c.ma", "date_naissance": "2001-02-02", "niveau": "L2",
        }, content_type="application/json")
        self.assertEqual(r.status_code, 201)
        self.assertTrue(Etudiant.objects.filter(numero_etudiant="ETU-2").exists())

    def test_supprimer(self):
        e = Etudiant.objects.get(numero_etudiant="ETU-1")
        r = self.client.delete(f"/api/etudiants/{e.pk}/")
        self.assertEqual(r.status_code, 204)


class QuizAPITest(APIBaseTest):
    def setUp(self):
        self.client.force_login(self.demo)

    def test_liste_voit_public_pas_prive(self):
        r = self.client.get("/api/quiz/")
        titres = [q["titre"] for q in r.json()["results"]]
        self.assertIn("Quiz API", titres)
        self.assertNotIn("Privé", titres)

    def test_detail_inclut_nb_questions(self):
        r = self.client.get(f"/api/quiz/{self.quiz.pk}/")
        self.assertEqual(r.json()["nb_questions"], 2)

    def test_submit_tout_juste(self):
        answers = {}
        for q in self.quiz.questions.all():
            answers[str(q.id)] = q.bonne_reponse().pk
        r = self.client.post(f"/api/quiz/{self.quiz.pk}/submit/",
                             {"answers": answers, "duree_secondes": 42}, content_type="application/json")
        self.assertEqual(r.status_code, 201)
        data = r.json()
        self.assertEqual(data["score"], 2)
        self.assertEqual(data["pourcentage"], 100)
        self.assertEqual(data["duree_secondes"], 42)
        self.assertEqual(len(data["detail"]), 2)
        self.assertTrue(TentativeQuiz.objects.filter(utilisateur=self.demo, quiz=self.quiz).exists())

    def test_submit_score_partiel(self):
        answers = {}
        for i, q in enumerate(self.quiz.questions.all()):
            bonne = q.bonne_reponse().pk
            mauvaise = [c.pk for c in q.choix.all() if c.pk != bonne][0]
            answers[str(q.id)] = bonne if i == 0 else mauvaise
        r = self.client.post(f"/api/quiz/{self.quiz.pk}/submit/", {"answers": answers}, content_type="application/json")
        self.assertEqual(r.json()["score"], 1)

    def test_tentatives_isolees(self):
        TentativeQuiz.objects.create(utilisateur=self.demo, quiz=self.quiz, score=2, nb_questions=2, detail=[])
        TentativeQuiz.objects.create(utilisateur=self.admin, quiz=self.quiz, score=0, nb_questions=2, detail=[])
        r = self.client.get("/api/tentatives/")
        self.assertEqual(len(r.json()["results"]), 1)
        self.assertEqual(r.json()["results"][0]["quiz_titre"], "Quiz API")

    def test_question_non_createur_refuse(self):
        r = self.client.post("/api/questions/", {
            "quiz": self.quiz.pk, "enonce": "X?", "ordre": 9,
            "choix": [{"texte": "a", "est_correcte": True}, {"texte": "b", "est_correcte": False},
                      {"texte": "c", "est_correcte": False}, {"texte": "d", "est_correcte": False}],
        }, content_type="application/json")
        self.assertEqual(r.status_code, 403)


class PlanningAPITest(APIBaseTest):
    def setUp(self):
        self.client.force_login(self.demo)

    def test_evenements_isoles_par_utilisateur(self):
        r = self.client.get("/api/evenements/")
        titres = [e["titre"] for e in r.json()["results"]]
        self.assertIn("Cours demo", titres)
        self.assertNotIn("Cours admin", titres)

    def test_evenement_avec_duree(self):
        r = self.client.get("/api/evenements/")
        self.assertEqual(r.json()["results"][0]["duree_heures"], 2.0)

    def test_evenement_horaire_invalide(self):
        r = self.client.post("/api/evenements/", {
            "titre": "Bad", "type": "cours", "date": str(date.today()),
            "heure_debut": "20:00", "heure_fin": "18:00",
        }, content_type="application/json")
        self.assertEqual(r.status_code, 400)

    def test_devoirs_isoles(self):
        r = self.client.get("/api/devoirs/")
        self.assertEqual(len(r.json()["results"]), 1)
        self.assertEqual(r.json()["results"][0]["titre"], "Devoir demo")
