from django.urls import path

from . import views

app_name = "etudiants"

urlpatterns = [
    path("", views.EtudiantListView.as_view(), name="liste"),
    path("export-csv/", views.ExportCSVView.as_view(), name="export_csv"),
    path("nouveau/", views.EtudiantCreateView.as_view(), name="creer"),
    path("<int:pk>/", views.EtudiantDetailView.as_view(), name="detail"),
    path("<int:pk>/modifier/", views.EtudiantUpdateView.as_view(), name="modifier"),
    path("<int:pk>/supprimer/", views.EtudiantDeleteView.as_view(), name="supprimer"),
]
