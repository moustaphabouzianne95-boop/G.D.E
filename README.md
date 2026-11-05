# 🎓 Projet Django — Gestion des Étudiants + Plateforme de Révision

Deux applications web construites avec **Django 5.2** et une base **SQLite**.

---

## 📋 Application 1 — Système de Gestion des Étudiants (CRUD)

### ✨ Fonctionnalités
- **Inscription** d'un étudiant (formulaire validé : e-mail et numéro uniques)
- **Recherche multicritères** : mot-clé (nom / prénom / e-mail), numéro, niveau, date d'inscription — combinables
- **Consultation**, **modification**, **suppression** (avec confirmation)
- **Pagination**, messages de confirmation, admin Django (`/admin/`)
- **🔐 Authentification** : connexion, inscription, déconnexion — toutes les pages protégées (`LoginRequiredMixin`)
- **📊 Export CSV** (`/export-csv/`) : résultats de la recherche active, encodage UTF-8 BOM compatible Excel

---

## 🃏 Application 2 — Plateforme de Révision Collaborative (Quiz & Flashcards)

Accessible via `/revision/` (dans la barre de navigation, une fois connecté).

### ✨ Fonctionnalités
- **Thématiques** de révision créables par les utilisateurs
- **Quiz par thématique** : création de QCM (énoncé + 4 choix + bonne réponse), réservé au créateur
- **⏱️ Chronomètre** pendant le passage du quiz (JavaScript, durée enregistrée avec le score)
- **📊 Suivi des scores** : score, pourcentage, durée, correction détaillée question par question, historique dans « Mes scores », meilleur score affiché sur chaque quiz
- **🔄 Partage** : chaque quiz/flashcard est **public** (visible et jouable par tous les utilisateurs connectés) ou **privé** (créateur seul)
- **🃏 Flashcards** recto/verso avec **mode révision interactif** (clic pour retourner la carte, navigation précédente/suivante, filtre par thématique)

### 🗂️ Modèles de l'app `revision`
`Thematique` · `Quiz` · `Question` · `Choix` · `Flashcard` · `TentativeQuiz` (score + durée + détail JSON des réponses)

### 📦 Données de démonstration
- 3 thématiques, 3 quiz (10 questions au total, dont 1 quiz privé), 9 flashcards (dont 1 privée), 2 tentatives de `demo`

---

## 📅 Application 3 — Générateur de Calendrier et Emploi du Temps

Accessible via `/planning/` (barre de navigation, connexion requise).

### ✨ Fonctionnalités
- **Calendrier mensuel** navigable (mois précédent/suivant, retour à aujourd'hui), événements colorés par type, clic sur « + » d'un jour pour pré-remplir la date
- **Planification des cours / révisions / examens** : CRUD complet avec validation (heure de fin > heure de début)
- **⏳ Calcul automatique des heures** par type sur le mois affiché (cours, révision, examens, total)
- **📄 Devoirs à rendre** : échéance date+heure, statut rendu/en retard, marquage rapide « rendu ✅ », filtre « à faire uniquement »
- **🔔 Rappels par e-mail** : page `/planning/rappels/` avec envoi manuel, anti-spam (1 rappel / 24 h / devoir), e-mails « à venir » ou « EN RETARD » ; en dev, les e-mails s'affichent dans la console (backend `console`), en prod : backend SMTP
- **Commande cron** : `python3 manage.py envoyer_rappels` envoie les rappels à tous les utilisateurs

### 🗂️ Modèles de l'app `planning`
`Evenement` (titre, type, date, horaires, durée calculée) · `Devoir` (échéance, rendu, dernier rappel)

### 📦 Données de démonstration (compte `demo`)
- 10 événements cette semaine (10 h de cours, 6 h de révision, 1 examen de 3 h), 3 devoirs (1 en retard, 1 à venir, 1 rendu)

---

## 👤 Comptes de démonstration

| Rôle | Nom d'utilisateur | Mot de passe |
|---|---|---|
| Utilisateur | `demo` | `demo1234` |
| Administrateur | `admin` | `admin1234` |

> Inscription publique : `/comptes/inscription/`. Admin Django : `/admin/`.

## 🧪 Tests automatisés

```bash
cd /home/user
python3 manage.py test        # toute la suite (67 tests)
python3 manage.py test revision   # une seule app
```

Couverture : modèles (unicité, propriétés calculées), vues CRUD, authentification,
recherche multicritères, export CSV, visibilité public/privé, passage de quiz (scores,
chronomètre), permissions créateur, rappels e-mail (backend `locmem` en test, anti-spam 24 h),
commande `envoyer_rappels`.

## ▶️ Lancer l'application

```bash
cd /home/user
python3 manage.py runserver 0.0.0.0:8000
```

## 🗂️ Structure

```
├── manage.py
├── gestion_etudiants/     # settings, urls du projet
├── comptes/               # authentification (connexion, inscription, déconnexion)
├── etudiants/             # app 1 : CRUD étudiants + recherche + export CSV
├── revision/              # app 2 : quiz, flashcards, scores, partage
└── db.sqlite3
```

## 🧠 Concepts Django pratiqués

Modèles, migrations, relations FK, vues génériques (List/Detail/Create/Update/Delete/FormView),
ModelForm et formulaires personnalisés, ORM avec `Q` et `aggregate(Max)`, `JSONField`,
pagination, messages, héritage de templates, `json_script`, `LoginRequiredMixin`,
`LoginView`/`LogoutView`/`UserCreationForm`, admin avec `inlines`, export CSV (`utf-8-sig`),
JavaScript embarqué (chronomètre, retournement de cartes),
calendrier mensuel (module `calendar`), propriétés calculées sur les modèles,
envoi d'e-mails (`django.core.mail`, backend console en dev), commande de gestion personnalisée
(`envoyer_rappels`, prête pour un cron),
tests automatisés (`TestCase`, `Client`, `force_login`, backend e-mail `locmem`, `call_command`).
