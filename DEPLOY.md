# Guide de deploiement sur Vercel

Le projet est pret a etre deploye (fichiers prepares), mais le token Vercel connecte a cette conversation a une portee limitee (`limited: true`) : les appels `list_projects`, `list_deployments` et `create_deployment` sont refuses (Access denied). La validation des credentials reussit.

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
