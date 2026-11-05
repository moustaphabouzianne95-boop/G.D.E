from django.contrib.auth.models import User
from django.db import models


class Thematique(models.Model):
    """Thématique de révision (ex. : Mathématiques, Histoire)."""
    nom = models.CharField("Nom", max_length=100, unique=True)
    description = models.TextField("Description", blank=True)
    createur = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="thematiques")
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["nom"]

    def __str__(self):
        return self.nom


class Quiz(models.Model):
    """Questionnaire à choix multiples, rattaché à une thématique."""
    thematique = models.ForeignKey(Thematique, on_delete=models.CASCADE, related_name="quiz")
    titre = models.CharField("Titre", max_length=200)
    description = models.TextField("Description", blank=True)
    createur = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="quiz_crees")
    est_public = models.BooleanField("Public (partagé)", default=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_creation"]

    def __str__(self):
        return self.titre

    @property
    def nb_questions(self):
        return self.questions.count()


class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    enonce = models.TextField("Énoncé")
    ordre = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["ordre", "id"]

    def __str__(self):
        return self.enonce[:60]

    def bonne_reponse(self):
        return self.choix.filter(est_correcte=True).first()


class Choix(models.Model):
    """Proposition de réponse pour une question (une seule est correcte)."""
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="choix")
    texte = models.CharField("Texte", max_length=255)
    est_correcte = models.BooleanField(default=False)

    def __str__(self):
        return self.texte[:60]


class Flashcard(models.Model):
    """Fiche de révision recto/verso, partageable."""
    thematique = models.ForeignKey(Thematique, on_delete=models.CASCADE, related_name="flashcards")
    recto = models.CharField("Recto (question)", max_length=255)
    verso = models.TextField("Verso (réponse)")
    createur = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="flashcards_crees")
    est_publique = models.BooleanField("Publique (partagée)", default=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.recto[:60]


class TentativeQuiz(models.Model):
    """Score enregistré d'un utilisateur sur un quiz (avec durée du chronomètre)."""
    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tentatives")
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="tentatives")
    score = models.PositiveIntegerField("Score")
    nb_questions = models.PositiveIntegerField("Nombre de questions")
    duree_secondes = models.PositiveIntegerField("Durée (secondes)", default=0)
    detail = models.JSONField("Détail des réponses", default=list)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"{self.utilisateur} — {self.quiz} : {self.score}/{self.nb_questions}"

    @property
    def pourcentage(self):
        return round(self.score * 100 / self.nb_questions) if self.nb_questions else 0

    @property
    def duree_formatee(self):
        m, s = divmod(self.duree_secondes, 60)
        return f"{m:02d}:{s:02d}"
