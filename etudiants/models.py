from django.db import models


class Etudiant(models.Model):
    NIVEAUX = [
        ("L1", "Licence 1"),
        ("L2", "Licence 2"),
        ("L3", "Licence 3"),
        ("M1", "Master 1"),
        ("M2", "Master 2"),
    ]

    numero_etudiant = models.CharField("Numéro étudiant", max_length=20, unique=True)
    prenom = models.CharField("Prénom", max_length=100)
    nom = models.CharField("Nom", max_length=100)
    email = models.EmailField("Adresse e-mail", unique=True)
    date_naissance = models.DateField("Date de naissance")
    niveau = models.CharField("Niveau d'études", max_length=2, choices=NIVEAUX, default="L1")
    date_inscription = models.DateTimeField("Date d'inscription", auto_now_add=True)

    class Meta:
        ordering = ["nom", "prenom"]
        verbose_name = "Étudiant"
        verbose_name_plural = "Étudiants"

    def __str__(self):
        return f"{self.prenom} {self.nom} ({self.numero_etudiant})"

    def get_niveau_display_full(self):
        return dict(self.NIVEAUX).get(self.niveau, self.niveau)
