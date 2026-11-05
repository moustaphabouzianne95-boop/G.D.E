from django.contrib import admin

from .models import Devoir, Evenement


@admin.register(Evenement)
class EvenementAdmin(admin.ModelAdmin):
    list_display = ("titre", "utilisateur", "type", "date", "heure_debut", "heure_fin", "matiere")
    list_filter = ("type", "date", "utilisateur")
    search_fields = ("titre", "matiere", "lieu")


@admin.register(Devoir)
class DevoirAdmin(admin.ModelAdmin):
    list_display = ("titre", "utilisateur", "matiere", "date_echeance", "rendu", "dernier_rappel")
    list_filter = ("rendu", "matiere", "utilisateur")
    search_fields = ("titre", "matiere")
