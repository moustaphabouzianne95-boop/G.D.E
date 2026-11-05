from rest_framework import serializers

from etudiants.models import Etudiant
from planning.models import Devoir, Evenement
from revision.models import Choix, Flashcard, Question, Quiz, TentativeQuiz, Thematique


class EtudiantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Etudiant
        fields = ["id", "numero_etudiant", "prenom", "nom", "email", "date_naissance", "niveau", "date_inscription"]
        read_only_fields = ["date_inscription"]


class ThematiqueSerializer(serializers.ModelSerializer):
    createur = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Thematique
        fields = ["id", "nom", "description", "createur", "date_creation"]
        read_only_fields = ["createur", "date_creation"]


class ChoixSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choix
        fields = ["id", "texte", "est_correcte"]


class QuestionSerializer(serializers.ModelSerializer):
    choix = ChoixSerializer(many=True)

    class Meta:
        model = Question
        fields = ["id", "quiz", "enonce", "ordre", "choix"]

    def create(self, validated_data):
        choix_data = validated_data.pop("choix")
        question = Question.objects.create(**validated_data)
        for c in choix_data:
            Choix.objects.create(question=question, **c)
        return question

    def update(self, instance, validated_data):
        choix_data = validated_data.pop("choix", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if choix_data is not None:
            instance.choix.all().delete()
            for c in choix_data:
                Choix.objects.create(question=instance, **c)
        return instance


class QuizSerializer(serializers.ModelSerializer):
    createur = serializers.StringRelatedField(read_only=True)
    nb_questions = serializers.IntegerField(read_only=True)
    thematique_nom = serializers.CharField(source="thematique.nom", read_only=True)

    class Meta:
        model = Quiz
        fields = ["id", "thematique", "thematique_nom", "titre", "description", "createur", "est_public", "nb_questions", "date_creation"]
        read_only_fields = ["createur", "date_creation"]


class FlashcardSerializer(serializers.ModelSerializer):
    createur = serializers.StringRelatedField(read_only=True)
    thematique_nom = serializers.CharField(source="thematique.nom", read_only=True)

    class Meta:
        model = Flashcard
        fields = ["id", "thematique", "thematique_nom", "recto", "verso", "createur", "est_publique", "date_creation"]
        read_only_fields = ["createur", "date_creation"]


class TentativeSerializer(serializers.ModelSerializer):
    quiz_titre = serializers.CharField(source="quiz.titre", read_only=True)
    pourcentage = serializers.IntegerField(read_only=True)
    duree_formatee = serializers.CharField(read_only=True)

    class Meta:
        model = TentativeQuiz
        fields = ["id", "utilisateur", "quiz", "quiz_titre", "score", "nb_questions", "pourcentage", "duree_secondes", "duree_formatee", "detail", "date"]
        read_only_fields = ["utilisateur", "score", "nb_questions", "detail", "date"]


class EvenementSerializer(serializers.ModelSerializer):
    utilisateur = serializers.StringRelatedField(read_only=True)
    duree_heures = serializers.FloatField(read_only=True)

    class Meta:
        model = Evenement
        fields = ["id", "utilisateur", "titre", "matiere", "type", "date", "heure_debut", "heure_fin", "lieu", "duree_heures", "date_creation"]
        read_only_fields = ["utilisateur", "date_creation"]

    def validate(self, attrs):
        if attrs.get("heure_fin") and attrs.get("heure_debut") and attrs["heure_fin"] <= attrs["heure_debut"]:
            raise serializers.ValidationError("L'heure de fin doit être après l'heure de début.")
        return attrs


class DevoirSerializer(serializers.ModelSerializer):
    utilisateur = serializers.StringRelatedField(read_only=True)
    en_retard = serializers.BooleanField(read_only=True)

    class Meta:
        model = Devoir
        fields = ["id", "utilisateur", "titre", "matiere", "description", "date_echeance", "rendu", "date_rendu", "en_retard", "dernier_rappel"]
        read_only_fields = ["utilisateur", "date_rendu", "dernier_rappel"]
