from datetime import datetime

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class Evenement(models.Model):
    """Élément d'emploi du temps : cours, séance de révision, examen…"""
    TYPES = [
        ("cours", "📘 Cours"),
        ("revision", "📖 Révision"),
        ("examen", "📝 Examen"),
        ("autre", "📌 Autre"),
    ]

    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE, related_name="evenements")
    titre = models.CharField("Titre", max_length=200)
    matiere = models.CharField("Matière", max_length=100, blank=True)
    type = models.CharField("Type", max_length=10, choices=TYPES, default="cours")
    date = models.DateField("Date")
    heure_debut = models.TimeField("Heure de début")
    heure_fin = models.TimeField("Heure de fin")
    lieu = models.CharField("Lieu / Salle", max_length=100, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["date", "heure_debut"]

    def __str__(self):
        return f"{self.titre} ({self.date} {self.heure_debut})"

    @property
    def duree_heures(self):
        """Durée de l'événement en heures (ex. : 1.5)."""
        d1 = datetime.combine(self.date, self.heure_debut)
        d2 = datetime.combine(self.date, self.heure_fin)
        return round((d2 - d1).total_seconds() / 3600, 2)


class Devoir(models.Model):
    """Rendu de devoir avec échéance — peut déclencher un rappel par e-mail."""
    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE, related_name="devoirs")
    titre = models.CharField("Titre", max_length=200)
    matiere = models.CharField("Matière", max_length=100, blank=True)
    description = models.TextField("Description", blank=True)
    date_echeance = models.DateTimeField("Date et heure de rendu")
    rendu = models.BooleanField("Rendu", default=False)
    date_rendu = models.DateTimeField("Rendu le", null=True, blank=True)
    dernier_rappel = models.DateTimeField("Dernier rappel envoyé le", null=True, blank=True)

    class Meta:
        ordering = ["rendu", "date_echeance"]

    def __str__(self):
        return self.titre

    @property
    def en_retard(self):
        return not self.rendu and self.date_echeance < timezone.now()

    @property
    def a_rappeler(self):
        """Vrai si le devoir n'est pas rendu et échoit dans moins de 24 h (ou est en retard),
        et qu'aucun rappel n'a été envoyé dans les dernières 24 h."""
        if self.rendu:
            return False
        if self.date_echeance > timezone.now() + timezone.timedelta(hours=24):
            return False
        if self.dernier_rappel and self.dernier_rappel > timezone.now() - timezone.timedelta(hours=24):
            return False
        return True
