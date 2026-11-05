# Guide de deploiement sur Vercel

## ✅ DEPLOYE — URL live
**https://gd-q5sfnyf46-moustaphabouzianne95-boop.vercel.app**
- Projet Vercel : `g.d.e` (prj_0aH8fWXk24N5zBCh1oeFPv2iYtKw), branche `main` du depot GitHub `moustaphabouzianne95-boop/G.D.E`
- Deploiement : `dpl_2Mhxryid5gVKwEE3Jb9f1HNbfufy` (READY)
- Env production : `VERCEL=1`, `DEBUG=False`, `SECRET_KEY` (encrypted) — deja configurees
- Protection SSO Vercel desactivee (`ssoProtection: null`) pour un acces public
- Comptes demo crees automatiquement au cold start : `demo` / `demo1234`

## Fichiers prepares dans ce depot
- `vercel.json` — build `@vercel/python`, routes vers `api/index.py`
- `api/index.py` — entree WSGI (`app`) + bootstrap auto (migrations + comptes demo + donnees exemple dans `/tmp/db.sqlite3`)
- `requirements.txt` — `Django==5.2.19` + `djangorestframework==3.18.3`
- `gestion_etudiants/settings.py` — config pilotee par env : `SECRET_KEY`, `DEBUG`, `VERCEL=1` (SQLite dans `/tmp`, `DEBUG=False`, `*.vercel.app` dans `CSRF_TRUSTED_ORIGINS`)

## Fichiers deja prepares dans ce depot
- `vercel.json` — build `@vercel/python`, toutes les routes vers `api/index.py`
- `api/index.py` — point d'entree WSGI (`app`) + bootstrap auto (migrations + comptes demo + donnees exemple dans `/tmp/db.sqlite3`)
- `requirements.txt` — `Django==5.2.19`
- `gestion_etudiants/settings.py` — config pilotee par env : `SECRET_KEY`, `DEBUG`, `VERCEL=1` (SQLite dans `/tmp`, `DEBUG=False`, `*.vercel.app` dans `CSRF_TRUSTED_ORIGINS`)

## Pour debloquer le deploiement
1. Dashboard Vercel -> Settings -> Tokens : donner au token les scopes Full Access (ou creation de projet + deploiement), ou connecter un nouveau token.
2. Variables d'environnement du projet Vercel :
   - `VERCEL` = `1`
   - `DEBUG` = `False`
   - `SECRET_KEY` = chaine longue aleatoire
3. Deployer au choix :
   - CLI : `vercel login && vercel --prod` a la racine du projet ;
   - Dashboard : Import Git (pousser ce dossier sur GitHub) ;
   - API/connector une fois les permissions accordees.

## Une fois en ligne
- URL `*.vercel.app` -> redirection vers la connexion.
- Comptes demo (crees automatiquement au cold start) : `demo` / `demo1234` et `admin` / `admin1234`.

## Limites connues de Vercel (serverless)
- SQLite dans `/tmp` : donnees reinitialisees a chaque cold start (demo). Pour persistance : PostgreSQL externe (Neon/Supabase) via `DATABASE_URL` + `dj-database-url` + `psycopg2-binary`.
- E-mails de rappel : backend `console` (visibles dans les logs Vercel) ; passer a un backend SMTP en prod.
- Admin Django (`/admin/`) fonctionnel mais sans fichiers statiques (nos templates ont leurs styles en ligne, l'app est complete).
