import csv
from datetime import date

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import EtudiantForm, RechercheForm
from .models import Etudiant


def appliquer_recherche(qs, params):
    """Applique les critères de recherche multicritères à un queryset.

    Partagé entre la liste HTML et l'export CSV pour garantir des résultats identiques.
    """
    form = RechercheForm(params or None)
    if not form.is_valid():
        return qs
    mot_cle = form.cleaned_data.get("mot_cle", "").strip()
    numero = form.cleaned_data.get("numero", "").strip()
    niveau = form.cleaned_data.get("niveau", "")
    inscrit_apres = form.cleaned_data.get("inscrit_apres")

    if mot_cle:
        qs = qs.filter(
            Q(nom__icontains=mot_cle)
            | Q(prenom__icontains=mot_cle)
            | Q(email__icontains=mot_cle)
        )
    if numero:
        qs = qs.filter(numero_etudiant__icontains=numero)
    if niveau:
        qs = qs.filter(niveau=niveau)
    if inscrit_apres:
        qs = qs.filter(date_inscription__date__gte=inscrit_apres)
    return qs


class EtudiantListView(LoginRequiredMixin, ListView):
    """Liste des étudiants avec recherche multicritères."""
    model = Etudiant
    template_name = "etudiants/liste.html"
    context_object_name = "etudiants"
    paginate_by = 10

    def get_queryset(self):
        return appliquer_recherche(super().get_queryset(), self.request.GET)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_recherche"] = RechercheForm(self.request.GET or None)
        context["nb_resultats"] = self.get_queryset().count()
        return context


class ExportCSVView(LoginRequiredMixin, View):
    """Exporte en CSV les étudiants correspondant aux filtres de recherche actifs."""

    def get(self, request, *args, **kwargs):
        etudiants = appliquer_recherche(Etudiant.objects.all(), request.GET)

        reponse = HttpResponse(content_type="text/csv; charset=utf-8")
        # utf-8-sig ajoute le BOM : Excel ouvre le fichier avec les accents corrects
        reponse.write("\ufeff")
        nom_fichier = f"etudiants_{date.today().isoformat()}.csv"
        reponse["Content-Disposition"] = f'attachment; filename="{nom_fichier}"'

        writer = csv.writer(reponse, delimiter=";")
        writer.writerow([
            "Numéro étudiant", "Nom", "Prénom", "E-mail",
            "Date de naissance", "Niveau", "Inscrit le",
        ])
        for e in etudiants:
            writer.writerow([
                e.numero_etudiant, e.nom, e.prenom, e.email,
                e.date_naissance.isoformat(), e.get_niveau_display(),
                e.date_inscription.strftime("%d/%m/%Y %H:%M"),
            ])
        return reponse


class EtudiantDetailView(LoginRequiredMixin, DetailView):
    model = Etudiant
    template_name = "etudiants/detail.html"
    context_object_name = "etudiant"


class EtudiantCreateView(LoginRequiredMixin, CreateView):
    model = Etudiant
    form_class = EtudiantForm
    template_name = "etudiants/formulaire.html"
    success_url = reverse_lazy("etudiants:liste")

    def form_valid(self, form):
        messages.success(self.request, f"L'étudiant {form.instance.prenom} {form.instance.nom} a été inscrit avec succès.")
        return super().form_valid(form)


class EtudiantUpdateView(LoginRequiredMixin, UpdateView):
    model = Etudiant
    form_class = EtudiantForm
    template_name = "etudiants/formulaire.html"
    success_url = reverse_lazy("etudiants:liste")

    def form_valid(self, form):
        messages.success(self.request, f"Le profil de {form.instance.prenom} {form.instance.nom} a été modifié.")
        return super().form_valid(form)


class EtudiantDeleteView(LoginRequiredMixin, DeleteView):
    model = Etudiant
    template_name = "etudiants/suppression.html"
    success_url = reverse_lazy("etudiants:liste")

    def form_valid(self, form):
        etudiant = self.get_object()
        messages.success(self.request, f"L'étudiant {etudiant.prenom} {etudiant.nom} a été supprimé.")
        return super().form_valid(form)
