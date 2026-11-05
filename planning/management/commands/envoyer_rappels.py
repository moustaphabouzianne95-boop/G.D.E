"""Commande à planifier (cron) : envoie les rappels de devoirs par e-mail.

Usage : python3 manage.py envoyer_rappels
"""
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from planning.rappels import envoyer_rappels_utilisateur


class Command(BaseCommand):
    help = "Envoie un e-mail de rappel pour chaque devoir non rendu échu dans moins de 24 h (ou en retard)."

    def handle(self, *args, **options):
        total = 0
        for utilisateur in User.objects.all():
            envoyes = envoyer_rappels_utilisateur(utilisateur)
            if envoyes:
                self.stdout.write(f"✉️  {envoyes} rappel(s) envoyé(s) à {utilisateur.username} ({utilisateur.email})")
                total += envoyes
        self.stdout.write(self.style.SUCCESS(f"Terminé : {total} rappel(s) envoyé(s) au total."))
