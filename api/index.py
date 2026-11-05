"""Point d'entrée WSGI pour Vercel (@vercel/python).

Vercel sert la variable `app` (callable WSGI) de ce module.
Au démarrage (cold start), on prépare la base SQLite dans /tmp :
migrations + comptes de démo + données d'exemple.
"""
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_etudiants.settings")
os.environ.setdefault("VERCEL", "1")

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
app = application  # nom attendu par le runtime @vercel/python


def _bootstrap_db():
    """Migre et seed la base une seule fois par instance (marqueur dans /tmp)."""
    marker = "/tmp/.django_db_ready"
    if os.path.exists(marker):
        return
    from django.core.management import call_command
    call_command("migrate", interactive=False, verbosity=0)

    from django.contrib.auth.models import User
    if not User.objects.filter(username="demo").exists():
        User.objects.create_user("demo", "demo@etu.ma", "demo1234")
    if not User.objects.filter(username="admin").exists():
        User.objects.create_superuser("admin", "admin@etu.ma", "admin1234")

    # Données de démonstration minimales si la base est vide
    from datetime import date, time, timedelta
    from django.utils import timezone
    from revision.models import Thematique, Quiz, Question, Flashcard
    from planning.models import Evenement, Devoir
    from etudiants.models import Etudiant

    if not Thematique.objects.exists():
        maths = Thematique.objects.create(nom="Mathématiques", description="Bases de révision.", createur_id=User.objects.get(username="admin").pk)
        histoire = Thematique.objects.create(nom="Histoire-Géographie", description="Dates clés.", createur_id=User.objects.get(username="admin").pk)
        admin = User.objects.get(username="admin")
        quiz = Quiz.objects.create(thematique=maths, titre="Maths de base — QCM", createur=admin, est_public=True)
        q = Question.objects.create(quiz=quiz, enonce="Combien vaut 7 × 8 ?", ordre=1)
        for i, t in enumerate(["54", "56", "63", "48"], 1):
            q.choix.create(texte=t, est_correcte=(i == 2))
        Flashcard.objects.create(thematique=maths, recto="Aire d'un disque ?", verso="π × r²", createur=admin, est_publique=True)
        Flashcard.objects.create(thematique=histoire, recto="Révolution française ?", verso="1789", createur=admin, est_publique=True)
        demo = User.objects.get(username="demo")
        lundi = date.today() - timedelta(days=date.today().weekday())
        Evenement.objects.create(utilisateur=demo, titre="Cours — Algèbre", matiere="Mathématiques", type="cours", date=lundi, heure_debut=time(8, 0), heure_fin=time(10, 0), lieu="Salle A101")
        Evenement.objects.create(utilisateur=demo, titre="Révision — QCM maths", matiere="Mathématiques", type="revision", date=lundi, heure_debut=time(18, 0), heure_fin=time(20, 0))
        Devoir.objects.create(utilisateur=demo, titre="Exercice SQL — jointures", matiere="Informatique", date_echeance=timezone.now() + timedelta(days=2))
        Etudiant.objects.create(numero_etudiant="ETU-2026-001", prenom="Youssef", nom="Alaoui", email="youssef.alaoui@etu.ma", date_naissance=date(2003, 5, 12), niveau="L2")

    with open(marker, "w") as f:
        f.write("ok")


_bootstrap_db()
