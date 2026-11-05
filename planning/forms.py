from django import forms
from django.core.exceptions import ValidationError

from .models import Devoir, Evenement


class EvenementForm(forms.ModelForm):
    class Meta:
        model = Evenement
        fields = ["titre", "matiere", "type", "date", "heure_debut", "heure_fin", "lieu"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "heure_debut": forms.TimeInput(attrs={"type": "time"}),
            "heure_fin": forms.TimeInput(attrs={"type": "time"}),
        }

    def clean(self):
        cleaned = super().clean()
        debut = cleaned.get("heure_debut")
        fin = cleaned.get("heure_fin")
        if debut and fin and fin <= debut:
            raise ValidationError("L'heure de fin doit être après l'heure de début.")
        return cleaned


class DevoirForm(forms.ModelForm):
    class Meta:
        model = Devoir
        fields = ["titre", "matiere", "description", "date_echeance", "rendu"]
        widgets = {
            "date_echeance": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "description": forms.Textarea(attrs={"rows": 3}),
        }
