"""Logique d'envoi des rappels de devoirs par e-mail (partagée entre la vue et la commande)."""
from django.core.mail import send_mail
from django.utils import timezone

from .models import Devoir


def envoyer_rappels_utilisateur(utilisateur):
    """Envoie un e-mail de rappel pour chaque devoir à rappeler de l'utilisateur.

    Retourne le nombre de rappels envoyés.
    """
    envoyes = 0
    devoirs = Devoir.objects.filter(utilisateur=utilisateur).order_by("date_echeance")
    for devoir in devoirs:
        if not devoir.a_rappeler:
            continue
        if devoir.en_retard:
            objet = f"⚠️ EN RETARD : rendu de « {devoir.titre} » dépassé"
            urgence = "EN RETARD"
        else:
            objet = f"⏰ Rappel : rendu de « {devoir.titre} » prévu bientôt"
            urgence = "à venir"
        message = (
            f"Bonjour {utilisateur.username},\n\n"
            f"Rappel ({urgence}) : le devoir « {devoir.titre} »"
            + (f" ({devoir.matiere})" if devoir.matiere else "")
            + f" est à rendre le {devoir.date_echeance.strftime('%d/%m/%Y à %H:%M')}.\n\n"
            + (f"Description : {devoir.description}\n\n" if devoir.description else "")
            + "Bon courage pour vos révisions ! 📚\n"
            "— La plateforme Planning"
        )
        send_mail(
            subject=objet,
            message=message,
            from_email="planning@etu.ma",
            recipient_list=[utilisateur.email or f"{utilisateur.username}@etu.ma"],
            fail_silently=True,
        )
        devoir.dernier_rappel = timezone.now()
        devoir.save(update_fields=["dernier_rappel"])
        envoyes += 1
    return envoyes
