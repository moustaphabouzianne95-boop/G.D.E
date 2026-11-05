from django.contrib import admin

from .models import Choix, Flashcard, Question, Quiz, TentativeQuiz, Thematique


class ChoixInline(admin.TabularInline):
    model = Choix
    extra = 4


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1


@admin.register(Thematique)
class ThematiqueAdmin(admin.ModelAdmin):
    list_display = ("nom", "createur", "date_creation")
    search_fields = ("nom",)


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ("titre", "thematique", "createur", "est_public", "date_creation")
    list_filter = ("est_public", "thematique")
    search_fields = ("titre",)
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("enonce", "quiz")
    inlines = [ChoixInline]


@admin.register(Flashcard)
class FlashcardAdmin(admin.ModelAdmin):
    list_display = ("recto", "thematique", "createur", "est_publique")
    list_filter = ("est_publique", "thematique")
    search_fields = ("recto", "verso")


@admin.register(TentativeQuiz)
class TentativeQuizAdmin(admin.ModelAdmin):
    list_display = ("utilisateur", "quiz", "score", "nb_questions", "duree_secondes", "date")
    list_filter = ("quiz",)
