from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("etudiants", views.EtudiantViewSet, basename="api-etudiants")
router.register("thematiques", views.ThematiqueViewSet, basename="api-thematiques")
router.register("quiz", views.QuizViewSet, basename="api-quiz")
router.register("questions", views.QuestionViewSet, basename="api-questions")
router.register("choix", views.ChoixViewSet, basename="api-choix")
router.register("flashcards", views.FlashcardViewSet, basename="api-flashcards")
router.register("tentatives", views.TentativeViewSet, basename="api-tentatives")
router.register("evenements", views.EvenementViewSet, basename="api-evenements")
router.register("devoirs", views.DevoirViewSet, basename="api-devoirs")

urlpatterns = [
    path("", include(router.urls)),
]
