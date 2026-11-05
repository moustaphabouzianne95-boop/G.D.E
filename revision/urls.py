from django.urls import path

from . import views

app_name = "revision"

urlpatterns = [
    # Thématiques
    path("themes/", views.ThematiqueListView.as_view(), name="themes"),
    path("themes/nouveau/", views.ThematiqueCreateView.as_view(), name="theme_creer"),
    path("themes/<int:pk>/", views.ThematiqueDetailView.as_view(), name="theme_detail"),
    # Quiz
    path("quiz/", views.QuizListView.as_view(), name="quiz_liste"),
    path("quiz/nouveau/", views.QuizCreateView.as_view(), name="quiz_creer"),
    path("quiz/<int:pk>/", views.QuizDetailView.as_view(), name="quiz_detail"),
    path("quiz/<int:quiz_pk>/ajouter-question/", views.QuestionCreateView.as_view(), name="question_ajouter"),
    path("quiz/<int:quiz_pk>/passer/", views.PasserQuizView.as_view(), name="quiz_passer"),
    path("quiz/<int:pk>/supprimer/", views.QuizDeleteView.as_view(), name="quiz_supprimer"),
    path("resultat/<int:pk>/", views.ResultatView.as_view(), name="resultat"),
    path("mes-scores/", views.MesScoresView.as_view(), name="mes_scores"),
    # Flashcards
    path("flashcards/", views.FlashcardListView.as_view(), name="flashcards"),
    path("flashcards/nouvelle/", views.FlashcardCreateView.as_view(), name="flashcard_creer"),
    path("flashcards/reviser/", views.RevisionFlashcardsView.as_view(), name="flashcards_reviser"),
    path("flashcards/<int:pk>/supprimer/", views.FlashcardDeleteView.as_view(), name="flashcard_supprimer"),
]
