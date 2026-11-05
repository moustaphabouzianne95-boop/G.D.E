from django import forms

from .models import Etudiant


class EtudiantForm(forms.ModelForm):
    class Meta:
        model = Etudiant
        fields = ["numero_etudiant", "prenom", "nom", "email", "date_naissance", "niveau"]
        widgets = {
            "date_naissance": forms.DateInput(attrs={"type": "date"}),
        }
        labels = {
            "numero_etudiant": "Numéro étudiant",
            "prenom": "Prénom",
            "nom": "Nom",
            "email": "Adresse e-mail",
            "date_naissance": "Date de naissance",
            "niveau": "Niveau d'études",
        }


class RechercheForm(forms.Form):
    """Formulaire de recherche multicritères (tous les champs sont optionnels)."""
    mot_cle = forms.CharField(
        label="Nom, prénom ou e-mail contient",
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "ex. : Martin, sorbon, alice@…"}),
    )
    numero = forms.CharField(
        label="Numéro étudiant",
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "ex. : ETU-2026-001"}),
    )
    niveau = forms.ChoiceField(
        label="Niveau d'études",
        required=False,
        choices=[("", "Tous les niveaux")] + Etudiant.NIVEAUX,
    )
    inscrit_apres = forms.DateField(
        label="Inscrit après le",
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
    )
