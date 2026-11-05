import calendar
from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from .forms import DevoirForm, EvenementForm
from .models import Devoir, Evenement
from .rappels import envoyer_rappels_utilisateur

NOMS_MOIS = ["", "janvier", "février", "mars", "avril", "mai", "juin",
            "juillet", "août", "septembre", "octobre", "novembre", "décembre"]


class CalendrierView(LoginRequiredMixin, View):
    """Calendrier mensuel de l'utilisateur + calcul des heures de révision/cours du mois."""

    def get(self, request):
        aujourdhui = date.today()
        try:
            annee = int(request.GET.get("annee", aujourdhui.year))
            mois = int(request.GET.get("mois", aujourdhui.month))
            if not 1 <= mois <= 12:
                raise ValueError
        except (TypeError, ValueError):
            annee, mois = aujourdhui.year, aujourdhui.month

        semaines = calendar.Calendar(firstweekday=0).monthdayscalendar(annee, mois)
        evenements = Evenement.objects.filter(
            utilisateur=request.user, date__year=annee, date__month=mois
        )
        par_jour = {}
        for e in evenements:
            par_jour.setdefault(e.date.day, []).append(e)

        # calcul des heures par type sur le mois affiché
        heures = {"cours": 0.0, "revision": 0.0, "examen": 0.0, "autre": 0.0}
        for e in evenements:
            heures[e.type] = heures.get(e.type, 0.0) + e.duree_heures

        # navigation mois précédent / suivant
        if mois == 1:
            prec = (annee - 1, 12)
        else:
            prec = (annee, mois - 1)
        if mois == 12:
            suiv = (annee + 1, 1)
        else:
            suiv = (annee, mois + 1)

        # devoirs urgents (non rendus, échéance dans les 30 jours)
        devoirs_urgents = Devoir.objects.filter(
            utilisateur=request.user,
            rendu=False,
            date_echeance__lte=timezone.now() + timedelta(days=30),
        ).order_by("date_echeance")[:5]
        nb_en_retard = Devoir.objects.filter(
            utilisateur=request.user, rendu=False, date_echeance__lt=timezone.now()
        ).count()

        return render(request, "planning/calendrier.html", {
            "annee": annee,
            "mois": mois,
            "nom_mois": NOMS_MOIS[mois],
            "semaines": semaines,
            "par_jour": par_jour,
            "aujourdhui": aujourdhui,
            "prec": prec,
            "suiv": suiv,
            "heures": heures,
            "heures_total": round(sum(heures.values()), 2),
            "devoirs_urgents": devoirs_urgents,
            "nb_en_retard": nb_en_retard,
        })


# ---------- Événements (cours, révisions, examens) ----------

class EvenementListView(LoginRequiredMixin, ListView):
    model = Evenement
    template_name = "planning/evenement_list.html"
    context_object_name = "evenements"

    def get_queryset(self):
        return Evenement.objects.filter(
            utilisateur=self.request.user, date__gte=date.today()
        ).order_by("date", "heure_debut")


class EvenementCreateView(LoginRequiredMixin, CreateView):
    model = Evenement
    form_class = EvenementForm
    template_name = "revision/formulaire_generique.html"
    success_url = reverse_lazy("planning:calendrier")
    extra_context = {"titre_page": "📅 Nouvel événement"}

    def get_initial(self):
        initial = super().get_initial()
        if self.request.GET.get("date"):
            initial["date"] = self.request.GET["date"]
        return initial

    def form_valid(self, form):
        form.instance.utilisateur = self.request.user
        messages.success(self.request, f"Événement « {form.instance.titre} » planifié.")
        return super().form_valid(form)


class EvenementUpdateView(LoginRequiredMixin, UpdateView):
    model = Evenement
    form_class = EvenementForm
    template_name = "revision/formulaire_generique.html"
    success_url = reverse_lazy("planning:calendrier")
    extra_context = {"titre_page": "✏️ Modifier l'événement"}

    def get_queryset(self):
        return Evenement.objects.filter(utilisateur=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, "Événement modifié.")
        return super().form_valid(form)


class EvenementDeleteView(LoginRequiredMixin, DeleteView):
    model = Evenement
    template_name = "revision/suppression.html"
    success_url = reverse_lazy("planning:calendrier")

    def get_queryset(self):
        return Evenement.objects.filter(utilisateur=self.request.user)


# ---------- Devoirs ----------

class DevoirListView(LoginRequiredMixin, ListView):
    model = Devoir
    template_name = "planning/devoir_list.html"
    context_object_name = "devoirs"

    def get_queryset(self):
        qs = Devoir.objects.filter(utilisateur=self.request.user)
        if self.request.GET.get("filtre") == "a_faire":
            qs = qs.filter(rendu=False)
        return qs.order_by("rendu", "date_echeance")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["filtre"] = self.request.GET.get("filtre", "")
        ctx["nb_en_retard"] = Devoir.objects.filter(
            utilisateur=self.request.user, rendu=False, date_echeance__lt=timezone.now()
        ).count()
        return ctx


class DevoirCreateView(LoginRequiredMixin, CreateView):
    model = Devoir
    form_class = DevoirForm
    template_name = "revision/formulaire_generique.html"
    success_url = reverse_lazy("planning:devoirs")
    extra_context = {"titre_page": "📄 Nouveau devoir à rendre"}

    def form_valid(self, form):
        form.instance.utilisateur = self.request.user
        messages.success(self.request, f"Devoir « {form.instance.titre} » enregistré.")
        return super().form_valid(form)


class DevoirUpdateView(LoginRequiredMixin, UpdateView):
    model = Devoir
    form_class = DevoirForm
    template_name = "revision/formulaire_generique.html"
    success_url = reverse_lazy("planning:devoirs")
    extra_context = {"titre_page": "✏️ Modifier le devoir"}

    def get_queryset(self):
        return Devoir.objects.filter(utilisateur=self.request.user)

    def form_valid(self, form):
        # si on coche "rendu", on enregistre la date de rendu
        if form.instance.rendu and not form.instance.date_rendu:
            form.instance.date_rendu = timezone.now()
        elif not form.instance.rendu:
            form.instance.date_rendu = None
        messages.success(self.request, "Devoir mis à jour.")
        return super().form_valid(form)


class DevoirDeleteView(LoginRequiredMixin, DeleteView):
    model = Devoir
    template_name = "revision/suppression.html"
    success_url = reverse_lazy("planning:devoirs")

    def get_queryset(self):
        return Devoir.objects.filter(utilisateur=self.request.user)


class DevoirToggleRenduView(LoginRequiredMixin, View):
    """Coche/décoche rapidement un devoir comme rendu (depuis la liste)."""

    def post(self, request, pk):
        devoir = get_object_or_404(Devoir, pk=pk, utilisateur=request.user)
        devoir.rendu = not devoir.rendu
        devoir.date_rendu = timezone.now() if devoir.rendu else None
        devoir.save(update_fields=["rendu", "date_rendu"])
        messages.success(request, f"« {devoir.titre} » marqué comme {'rendu ✅' if devoir.rendu else 'non rendu'}.")
        return redirect("planning:devoirs")


# ---------- Rappels par e-mail ----------

class RappelsView(LoginRequiredMixin, View):
    """Page des rappels : devoirs à rendre bientôt + envoi manuel des e-mails de rappel."""

    def get(self, request):
        devoirs = Devoir.objects.filter(utilisateur=request.user, rendu=False).order_by("date_echeance")
        return render(request, "planning/rappels.html", {
            "devoirs": devoirs,
            "nb_a_rappeler": sum(1 for d in devoirs if d.a_rappeler),
        })

    def post(self, request):
        envoyes = envoyer_rappels_utilisateur(request.user)
        if envoyes:
            messages.success(request, f"✉️ {envoyes} e-mail(s) de rappel envoyé(s) à {request.user.email or request.user.username}.")
        else:
            messages.success(request, "Aucun rappel à envoyer pour le moment.")
        return redirect("planning:rappels")
