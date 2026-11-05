from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView


class InscriptionView(CreateView):
    """Création d'un compte utilisateur (inscription publique)."""
    form_class = UserCreationForm
    template_name = "registration/inscription.html"
    success_url = reverse_lazy("etudiants:liste")

    def form_valid(self, form):
        reponse = super().form_valid(form)
        login(self.request, self.object)  # connexion automatique après inscription
        messages.success(self.request, f"Bienvenue {self.object.username} ! Votre compte a été créé.")
        return reponse
