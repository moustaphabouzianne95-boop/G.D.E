from django import forms

from .models import Flashcard, Quiz, Thematique


class ThematiqueForm(forms.ModelForm):
    class Meta:
        model = Thematique
        fields = ["nom", "description"]


class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ["thematique", "titre", "description", "est_public"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }


class QuestionForm(forms.Form):
    """Ajout d'une question QCM : énoncé + 4 choix + indication de la bonne réponse."""
    enonce = forms.CharField(label="Énoncé de la question", widget=forms.Textarea(attrs={"rows": 2}))
    choix_1 = forms.CharField(label="Choix 1")
    choix_2 = forms.CharField(label="Choix 2")
    choix_3 = forms.CharField(label="Choix 3")
    choix_4 = forms.CharField(label="Choix 4")
    bonne_reponse = forms.ChoiceField(
        label="Numéro de la bonne réponse",
        choices=[("1", "Choix 1"), ("2", "Choix 2"), ("3", "Choix 3"), ("4", "Choix 4")],
    )


class FlashcardForm(forms.ModelForm):
    class Meta:
        model = Flashcard
        fields = ["thematique", "recto", "verso", "est_publique"]
        widgets = {
            "verso": forms.Textarea(attrs={"rows": 3}),
        }
