from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Max, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, FormView, ListView

from .forms import FlashcardForm, QuestionForm, QuizForm, ThematiqueForm
from .models import Flashcard, Question, Quiz, TentativeQuiz, Thematique


# ---------- Thématiques ----------

class ThematiqueListView(LoginRequiredMixin, ListView):
    model = Thematique
    template_name = "revision/theme_list.html"
    context_object_name = "thematiques"


class ThematiqueCreateView(LoginRequiredMixin, CreateView):
    model = Thematique
    form_class = ThematiqueForm
    template_name = "revision/formulaire_generique.html"
    success_url = reverse_lazy("revision:themes")
    extra_context = {"titre_page": "🏷️ Nouvelle thématique"}

    def form_valid(self, form):
        form.instance.createur = self.request.user
        messages.success(self.request, f"Thématique « {form.instance.nom} » créée.")
        return super().form_valid(form)


class ThematiqueDetailView(LoginRequiredMixin, DetailView):
    model = Thematique
    template_name = "revision/theme_detail.html"
    context_object_name = "thematique"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["quiz_visibles"] = self.object.quiz.filter(
            Q(est_public=True) | Q(createur=self.request.user)
        )
        ctx["flashcards_visibles"] = self.object.flashcards.filter(
            Q(est_publique=True) | Q(createur=self.request.user)
        )
        return ctx


# ---------- Quiz : consultation ----------

class QuizListView(LoginRequiredMixin, ListView):
    """Quiz publics de tout le monde + mes quiz privés."""
    model = Quiz
    template_name = "revision/quiz_list.html"
    context_object_name = "quiz"
    paginate_by = 12

    def get_queryset(self):
        qs = Quiz.objects.filter(Q(est_public=True) | Q(createur=self.request.user))
        theme = self.request.GET.get("theme")
        if theme:
            qs = qs.filter(thematique_id=theme)
        return qs.select_related("thematique", "createur")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["thematiques"] = Thematique.objects.all()
        ctx["theme_selectionnee"] = self.request.GET.get("theme", "")
        return ctx


class QuizDetailView(LoginRequiredMixin, DetailView):
    model = Quiz
    template_name = "revision/quiz_detail.html"
    context_object_name = "quiz"

    def get_queryset(self):
        # un quiz privé n'est visible que par son créateur
        return Quiz.objects.filter(Q(est_public=True) | Q(createur=self.request.user))

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        mes_tentatives = TentativeQuiz.objects.filter(quiz=self.object, utilisateur=self.request.user)
        ctx["nb_tentatives"] = mes_tentatives.count()
        ctx["meilleur_score"] = mes_tentatives.aggregate(m=Max("score"))["m"]
        ctx["est_createur"] = self.object.createur == self.request.user
        return ctx


# ---------- Quiz : création ----------

class QuizCreateView(LoginRequiredMixin, CreateView):
    model = Quiz
    form_class = QuizForm
    template_name = "revision/formulaire_generique.html"
    extra_context = {"titre_page": "📝 Nouveau quiz"}

    def form_valid(self, form):
        form.instance.createur = self.request.user
        messages.success(self.request, f"Quiz « {form.instance.titre} » créé. Ajoutez maintenant des questions !")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("revision:quiz_detail", kwargs={"pk": self.object.pk})


class QuestionCreateView(LoginRequiredMixin, FormView):
    """Ajoute une question QCM (énoncé + 4 choix) à un quiz dont on est le créateur."""
    form_class = QuestionForm
    template_name = "revision/question_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.quiz = get_object_or_404(Quiz, pk=kwargs["quiz_pk"], createur=request.user)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        question = Question.objects.create(
            quiz=self.quiz,
            enonce=form.cleaned_data["enonce"],
            ordre=self.quiz.questions.count() + 1,
        )
        bonne = int(form.cleaned_data["bonne_reponse"])
        for i in range(1, 5):
            question.choix.create(
                texte=form.cleaned_data[f"choix_{i}"],
                est_correcte=(i == bonne),
            )
        messages.success(self.request, "Question ajoutée au quiz.")
        return redirect("revision:quiz_detail", pk=self.quiz.pk)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["quiz"] = self.quiz
        return ctx


class QuizDeleteView(LoginRequiredMixin, DeleteView):
    model = Quiz
    template_name = "revision/suppression.html"
    success_url = reverse_lazy("revision:quiz_liste")

    def get_queryset(self):
        return Quiz.objects.filter(createur=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, f"Quiz « {self.get_object().titre} » supprimé.")
        return super().form_valid(form)


# ---------- Quiz : passage avec chronomètre + score ----------

class PasserQuizView(LoginRequiredMixin, View):
    """GET : affiche le quiz avec chronomètre. POST : corrige et enregistre le score."""

    def get(self, request, quiz_pk):
        quiz = get_object_or_404(
            Quiz.objects.filter(Q(est_public=True) | Q(createur=request.user)), pk=quiz_pk
        )
        return render(request, "revision/quiz_passer.html", {"quiz": quiz})

    def post(self, request, quiz_pk):
        quiz = get_object_or_404(
            Quiz.objects.filter(Q(est_public=True) | Q(createur=request.user)), pk=quiz_pk
        )
        questions = list(quiz.questions.prefetch_related("choix"))
        score = 0
        detail = []
        for q in questions:
            choix_id = request.POST.get(f"q_{q.id}")
            choisi = q.choix.filter(pk=choix_id).first() if choix_id else None
            bonne = q.bonne_reponse()
            correct = bool(choisi and choisi.est_correcte)
            if correct:
                score += 1
            detail.append({
                "enonce": q.enonce,
                "choisi": choisi.texte if choisi else None,
                "bonne": bonne.texte if bonne else None,
                "correct": correct,
            })
        try:
            duree = int(request.POST.get("duree_secondes", 0))
        except (TypeError, ValueError):
            duree = 0
        tentative = TentativeQuiz.objects.create(
            utilisateur=request.user,
            quiz=quiz,
            score=score,
            nb_questions=len(questions),
            duree_secondes=max(0, duree),
            detail=detail,
        )
        return redirect("revision:resultat", pk=tentative.pk)


class ResultatView(LoginRequiredMixin, DetailView):
    model = TentativeQuiz
    template_name = "revision/quiz_resultat.html"
    context_object_name = "tentative"

    def get_queryset(self):
        return TentativeQuiz.objects.filter(utilisateur=self.request.user)


class MesScoresView(LoginRequiredMixin, ListView):
    model = TentativeQuiz
    template_name = "revision/scores.html"
    context_object_name = "tentatives"
    paginate_by = 15

    def get_queryset(self):
        return TentativeQuiz.objects.filter(utilisateur=self.request.user).select_related("quiz")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["meilleur_global"] = self.get_queryset().aggregate(m=Max("score"))["m"]
        return ctx


# ---------- Flashcards ----------

class FlashcardListView(LoginRequiredMixin, ListView):
    """Flashcards publiques + mes flashcards privées, filtrables par thème."""
    model = Flashcard
    template_name = "revision/flashcard_list.html"
    context_object_name = "flashcards"
    paginate_by = 12

    def get_queryset(self):
        qs = Flashcard.objects.filter(Q(est_publique=True) | Q(createur=self.request.user))
        theme = self.request.GET.get("theme")
        if theme:
            qs = qs.filter(thematique_id=theme)
        return qs.select_related("thematique", "createur")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["thematiques"] = Thematique.objects.all()
        ctx["theme_selectionnee"] = self.request.GET.get("theme", "")
        # données sérialisées pour le mode révision (filtre json_script dans le template)
        ctx["cartes"] = [
            {"recto": f.recto, "verso": f.verso, "theme": f.thematique.nom}
            for f in self.object_list
        ]
        return ctx


class FlashcardCreateView(LoginRequiredMixin, CreateView):
    model = Flashcard
    form_class = FlashcardForm
    template_name = "revision/formulaire_generique.html"
    success_url = reverse_lazy("revision:flashcards")
    extra_context = {"titre_page": "🃏 Nouvelle flashcard"}

    def form_valid(self, form):
        form.instance.createur = self.request.user
        messages.success(self.request, "Flashcard créée.")
        return super().form_valid(form)


class FlashcardDeleteView(LoginRequiredMixin, DeleteView):
    model = Flashcard
    template_name = "revision/suppression.html"
    success_url = reverse_lazy("revision:flashcards")

    def get_queryset(self):
        return Flashcard.objects.filter(createur=self.request.user)


class RevisionFlashcardsView(LoginRequiredMixin, ListView):
    """Mode révision : une fiche à la fois, clic pour retourner recto/verso."""
    model = Flashcard
    template_name = "revision/flashcard_revision.html"
    context_object_name = "flashcards"

    def get_queryset(self):
        qs = Flashcard.objects.filter(Q(est_publique=True) | Q(createur=self.request.user))
        theme = self.request.GET.get("theme")
        if theme:
            qs = qs.filter(thematique_id=theme)
        return qs.select_related("thematique")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["thematiques"] = Thematique.objects.all()
        ctx["theme_selectionnee"] = self.request.GET.get("theme", "")
        # données sérialisées pour le mode révision (filtre json_script dans le template)
        ctx["cartes"] = [
            {"recto": f.recto, "verso": f.verso, "theme": f.thematique.nom}
            for f in self.object_list
        ]
        return ctx
