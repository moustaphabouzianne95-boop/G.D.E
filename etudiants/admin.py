from django.contrib import admin

from .models import Etudiant


@admin.register(Etudiant)
class EtudiantAdmin(admin.ModelAdmin):
    list_display = ("numero_etudiant", "nom", "prenom", "email", "niveau", "date_inscription")
    list_filter = ("niveau", "date_inscription")
    search_fields = ("nom", "prenom", "email", "numero_etudiant")
    ordering = ("nom", "prenom")
