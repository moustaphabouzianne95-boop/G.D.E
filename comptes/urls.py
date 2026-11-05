from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = "comptes"

urlpatterns = [
    path("connexion/", auth_views.LoginView.as_view(template_name="registration/connexion.html"), name="connexion"),
    path("deconnexion/", auth_views.LogoutView.as_view(), name="deconnexion"),
    path("inscription/", views.InscriptionView.as_view(), name="inscription"),
]
