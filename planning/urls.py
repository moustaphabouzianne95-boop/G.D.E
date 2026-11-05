from django.urls import path

from . import views

app_name = "planning"

urlpatterns = [
    path("", views.CalendrierView.as_view(), name="calendrier"),
    path("evenements/", views.EvenementListView.as_view(), name="evenements"),
    path("evenements/nouveau/", views.EvenementCreateView.as_view(), name="evenement_creer"),
    path("evenements/<int:pk>/modifier/", views.EvenementUpdateView.as_view(), name="evenement_modifier"),
    path("evenements/<int:pk>/supprimer/", views.EvenementDeleteView.as_view(), name="evenement_supprimer"),
    path("devoirs/", views.DevoirListView.as_view(), name="devoirs"),
    path("devoirs/nouveau/", views.DevoirCreateView.as_view(), name="devoir_creer"),
    path("devoirs/<int:pk>/modifier/", views.DevoirUpdateView.as_view(), name="devoir_modifier"),
    path("devoirs/<int:pk>/supprimer/", views.DevoirDeleteView.as_view(), name="devoir_supprimer"),
    path("devoirs/<int:pk>/toggle-rendu/", views.DevoirToggleRenduView.as_view(), name="devoir_toggle"),
    path("rappels/", views.RappelsView.as_view(), name="rappels"),
]
