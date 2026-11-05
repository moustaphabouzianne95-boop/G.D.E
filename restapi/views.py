from django.db.models import Q
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from etudiants.models import Etudiant
from planning.models import Devoir, Evenement
from revision.models import Choix, Flashcard, Question, Quiz, TentativeQuiz, Thematique

from .serializers import (ChoixSerializer, DevoirSerializer, EtudiantSerializer,
                          EvenementSerializer, FlashcardSerializer, QuestionSerializer,
                          QuizSerializer, TentativeSerializer, ThematiqueSerializer)


class EtudiantViewSet(viewsets.ModelViewSet):
    """CRUD des étudiants — toute personne connectée peut consulter/gérer."""
    queryset = Etudiant.objects.all()
    serializer_class = EtudiantSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ["nom", "prenom", "email", "numero_etudiant"]
    filterset_fields = ["niveau"]


class ThematiqueViewSet(viewsets.ModelViewSet):
    queryset = Thematique.objects.all()
    serializer_class = ThematiqueSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(createur=self.request.user)


class QuizViewSet(viewsets.ModelViewSet):
    """Quiz publics + quiz privés de l'utilisateur connecté."""
    serializer_class = QuizSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Quiz.objects.filter(Q(est_public=True) | Q(createur=self.request.user))

    def perform_create(self, serializer):
        serializer.save(createur=self.request.user)

    @action(detail=True, methods=["post"], url_path="submit")
    def submit(self, request, pk=None):
        """Soumet les réponses d'un quiz : POST {"answers": {"<question_id>": <choix_id>}, "duree_secondes": 42}
        Retourne le score et le détail de la correction."""
        quiz = self.get_object()
        answers = request.data.get("answers", {})
        try:
            duree = int(request.data.get("duree_secondes", 0))
        except (TypeError, ValueError):
            duree = 0

        score = 0
        detail = []
        for q in quiz.questions.prefetch_related("choix"):
            choix_id = answers.get(str(q.id))
            choisi = q.choix.filter(pk=choix_id).first() if choix_id else None
            bonne = q.bonne_reponse()
            correct = bool(choisi and choisi.est_correcte)
            if correct:
                score += 1
            detail.append({
                "question_id": q.id,
                "enonce": q.enonce,
                "choisi": choisi.texte if choisi else None,
                "bonne": bonne.texte if bonne else None,
                "correct": correct,
            })

        tentative = TentativeQuiz.objects.create(
            utilisateur=request.user, quiz=quiz, score=score,
            nb_questions=quiz.questions.count(), duree_secondes=max(0, duree), detail=detail,
        )
        return Response({
            "tentative_id": tentative.pk,
            "quiz": quiz.titre,
            "score": score,
            "nb_questions": tentative.nb_questions,
            "pourcentage": tentative.pourcentage,
            "duree_secondes": tentative.duree_secondes,
            "detail": detail,
        }, status=status.HTTP_201_CREATED)


class QuestionViewSet(viewsets.ModelViewSet):
    serializer_class = QuestionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Question.objects.filter(
            Q(quiz__est_public=True) | Q(quiz__createur=self.request.user)
        )

    def _verifier_createur(self, quiz):
        return quiz.createur == self.request.user

    def perform_create(self, serializer):
        quiz = serializer.validated_data["quiz"]
        if not self._verifier_createur(quiz):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Seul le créateur du quiz peut ajouter des questions.")
        serializer.save()

    def perform_update(self, serializer):
        if not self._verifier_createur(serializer.instance.quiz):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Seul le créateur du quiz peut modifier ses questions.")
        serializer.save()

    def perform_destroy(self, instance):
        if not self._verifier_createur(instance.quiz):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Seul le créateur du quiz peut supprimer ses questions.")
        instance.delete()


class ChoixViewSet(viewsets.ModelViewSet):
    queryset = Choix.objects.all()
    serializer_class = ChoixSerializer
    permission_classes = [IsAuthenticated]


class FlashcardViewSet(viewsets.ModelViewSet):
    serializer_class = FlashcardSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Flashcard.objects.filter(Q(est_publique=True) | Q(createur=self.request.user))

    def perform_create(self, serializer):
        serializer.save(createur=self.request.user)


class TentativeViewSet(viewsets.ReadOnlyModelViewSet):
    """Historique des scores — uniquement ses propres tentatives."""
    serializer_class = TentativeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return TentativeQuiz.objects.filter(utilisateur=self.request.user)


class EvenementViewSet(viewsets.ModelViewSet):
    """Emploi du temps — chaque utilisateur ne voit que ses événements."""
    serializer_class = EvenementSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Evenement.objects.filter(utilisateur=self.request.user)

    def perform_create(self, serializer):
        serializer.save(utilisateur=self.request.user)


class DevoirViewSet(viewsets.ModelViewSet):
    """Devoirs — chaque utilisateur ne gère que les siens."""
    serializer_class = DevoirSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Devoir.objects.filter(utilisateur=self.request.user)

    def perform_create(self, serializer):
        serializer.save(utilisateur=self.request.user)

    def perform_update(self, serializer):
        if serializer.validated_data.get("rendu") and not serializer.instance.date_rendu:
            serializer.save(date_rendu=timezone.now())
        elif "rendu" in serializer.validated_data and not serializer.validated_data["rendu"]:
            serializer.save(date_rendu=None)
        else:
            serializer.save()
