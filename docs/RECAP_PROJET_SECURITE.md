# Recapitulatif du projet Mission Impossible - Blue Team

## 1. Objectif du projet

Ce projet correspond a une phase Blue Team de remediation d'une application volontairement vulnerable.

Le but etait de :

- corriger les failles exploitees pendant la phase Red Team ;
- reduire l'exposition des secrets ;
- durcir l'environnement d'execution Docker ;
- ajouter des controles automatises dans la pipeline ;
- documenter la maniere de lancer, verifier et tester la securite.

## 2. Architecture du projet

Le depot est compose de trois briques principales :

- `web/` : application Flask exposee sur le port `5001` cote machine hote ;
- `vault/` : service interne Flask non expose a l'hote, utilise pour stocker un secret ;
- `scripts/` et `.github/workflows/` : partie pipeline DevSecOps.

### Flux prevu

1. L'utilisateur accede au service `web`.
2. Le service `web` propose plusieurs routes :
   - `/status`
   - `/whoami`
   - `/fetch`
   - `/admin`
3. Le service `vault` reste accessible seulement depuis le reseau Docker interne.

Cette separation limite deja une partie de la surface d'attaque.

## 3. Securites mises en place

### 3.1 Protection contre la SSRF

La route `/fetch` a ete durcie dans `web/app.py` avec plusieurs controles :

- seuls les schemas `http` et `https` sont autorises ;
- les noms d'hote internes sensibles sont bloques : `localhost`, `127.0.0.1`, `vault` ;
- les IP privees sont refusees apres resolution DNS ;
- un timeout reseau est applique ;
- les erreurs upstream sont gerees proprement avec un retour `502`.

Objectif : empecher l'application web d'etre utilisee pour atteindre un service interne comme `vault`.

### 3.2 Protection de la route admin

La route `/admin` n'accepte plus un simple parametre dans l'URL.

Le controle actuel repose sur :

- un header `Authorization: Bearer <token>` obligatoire ;
- une comparaison avec la variable d'environnement `ADMIN_TOKEN` ;
- un refus explicite en `401`, `403` ou `500` selon le cas.

Objectif : sortir le secret de l'URL et imposer une authentification plus propre.

### 3.3 Protection des secrets

Les secrets ne sont pas hardcodes dans le code source.

Ils passent par des variables d'environnement :

- `ADMIN_TOKEN`
- `JWT_SECRET`
- `VAULT_TOKEN`
- `FLAG_SUPPLY`
- `FLAG_VAULT`

Le fichier `.env.example` fournit une base de configuration sans exposer de vraies valeurs.

Objectif : separer le code et les secrets, et permettre une gestion plus sure selon l'environnement.

### 3.4 Isolation du service vault

Dans `docker-compose.yml`, le service `vault` :

- n'est pas mappe sur un port de la machine hote ;
- reste disponible uniquement sur le reseau interne Docker ;
- depend d'un token `VAULT_TOKEN` pour acceder a `/secret`.

Objectif : reduire l'exposition directe du composant le plus sensible.

### 3.5 Durcissement du conteneur Docker

Le `Dockerfile` a ete durci avec plusieurs bonnes pratiques :

- image de base epinglee par digest ;
- image `python:3.11-slim` plus legere ;
- installation minimale des paquets systeme ;
- nettoyage du cache `apt` ;
- creation d'un utilisateur non-root ;
- execution finale du conteneur avec `USER appuser`.

Objectif : limiter l'impact d'une compromission et reduire la surface d'attaque du conteneur.

### 3.6 Gestion plus propre des erreurs cote vault

Le service `vault/app.py` renvoie maintenant des erreurs JSON pour :

- `403`
- `404`
- `500`

Objectif : eviter des reponses par defaut peu maitrisees et garder un comportement API coherent.

### 3.7 Cookie plus securise sur `/whoami`

La route `/whoami` definit un cookie avec :

- `HttpOnly`
- `SameSite=Strict`

Objectif : montrer une hygiene de base cote session et limiter certains usages abusifs du cookie.

### 3.8 Debut d'automatisation DevSecOps

La pipeline lancee via `scripts/pipeline.sh` et `.github/workflows/ci.yml` met en place :

- execution de `pytest` ;
- audit des dependances avec `pip-audit --strict` ;
- build de l'image Docker ;
- scan securite de l'image avec Trivy ;
- execution automatique dans GitHub Actions.

Objectif : detecter plus tot les regressions de securite et les dependances vulnerables.

## 4. Comment lancer le projet

### 4.1 Preparer l'environnement

Creer un fichier `.env` a la racine du projet, par exemple :

```env
ADMIN_TOKEN=super-admin-token
JWT_SECRET=jwt-secret-dev
VAULT_TOKEN=vault-secret-token
FLAG_SUPPLY=FLAG{blue_team_supply}
FLAG_VAULT=FLAG{blue_team_vault}
```

### 4.2 Lancer avec Docker Compose

```powershell
docker compose up --build
```

Acces utiles :

- application web : `http://localhost:5001`
- statut : `http://localhost:5001/status`
- route whoami : `http://localhost:5001/whoami`

Le service `vault` ne doit pas etre expose directement sur la machine.

### 4.3 Arreter le projet

```powershell
docker compose down
```

## 5. Comment tester les securites mises en place

### 5.1 Test fonctionnel simple

Verifier que l'application repond :

```powershell
curl http://localhost:5001/status
```

Resultat attendu :

```json
{"service":"secure-app","ok":true}
```

### 5.2 Test de la route admin sans token

```powershell
curl http://localhost:5001/admin
```

Resultat attendu : erreur `401`.

### 5.3 Test de la route admin avec mauvais token

```powershell
curl -H "Authorization: Bearer mauvais-token" http://localhost:5001/admin
```

Resultat attendu : erreur `403`.

### 5.4 Test de la route admin avec le bon token

```powershell
curl -H "Authorization: Bearer super-admin-token" http://localhost:5001/admin
```

Resultat attendu : JSON contenant `admin: true` et la valeur de `FLAG_SUPPLY`.

### 5.5 Test SSRF vers localhost

```powershell
curl "http://localhost:5001/fetch?url=http://127.0.0.1:7000/health"
```

Resultat attendu : erreur `403`.

### 5.6 Test SSRF vers le service vault

```powershell
curl "http://localhost:5001/fetch?url=http://vault:7000/secret?token=test"
```

Resultat attendu : erreur `403`.

### 5.7 Test de filtrage de schema

```powershell
curl "http://localhost:5001/fetch?url=file:///etc/passwd"
```

Resultat attendu : erreur `400`.

### 5.8 Test d'un appel externe autorise

```powershell
curl "http://localhost:5001/fetch?url=https://example.com"
```

Resultat attendu : la page distante est recuperee.

### 5.9 Test du vault depuis l'interieur du reseau Docker

Verifier d'abord que `vault` n'est pas accessible directement depuis l'hote :

```powershell
curl http://localhost:7000/health
```

Resultat attendu : echec de connexion.

Puis verifier depuis le reseau Compose :

```powershell
docker compose exec web python -c "import requests; print(requests.get('http://vault:7000/health', timeout=2).text)"
```

Resultat attendu : `{"ok":true}`.

### 5.10 Lancer la pipeline locale

Sous Linux / Git Bash :

```bash
sh scripts/pipeline.sh
```

Sous Windows, les commandes peuvent aussi etre lancees une par une si besoin.

Resultats attendus :

- les tests Python passent ;
- `pip-audit` ne remonte pas de dependance critique bloquante ;
- l'image Docker se construit ;
- Trivy scanne l'image et echoue si une vulnerabilite `HIGH` ou `CRITICAL` est detectee.

## 6. Comment on est arrives a cette version

La progression visible dans le depot montre une logique Blue Team par etapes :

1. Identification des failles exploitees pendant la phase Red Team.
2. Correction applicative prioritaire sur la SSRF dans `web/app.py`.
3. Renforcement de l'acces admin par token dans le header `Authorization`.
4. Reorganisation des secrets via variables d'environnement.
5. Isolement de `vault` dans Docker Compose sans exposition de port.
6. Durcissement du conteneur avec utilisateur non-root et image epinglee.
7. Ajout d'une pipeline securite avec tests, audit des dependances et scan d'image.
8. Documentation du projet et des verifications a realiser.

L'historique Git et les noms de branches montrent aussi une repartition du travail par themes de vulnerabilites :

- information leak ;
- SSRF ;
- acces au vault ;
- protection de la zone admin.

## 7. Ce qui est bien securise aujourd'hui

- la SSRF est nettement mieux controlee qu'au depart ;
- le service `vault` n'est plus expose directement ;
- les secrets sont sortis du code ;
- le conteneur est moins permissif ;
- une base de pipeline DevSecOps est en place.

## 8. Limites actuelles et pistes d'amelioration

Le projet est mieux securise, mais quelques points restent perfectibles :

- `tests/test_app.py` contient encore un test minimal et ne couvre pas vraiment les protections de securite ;
- `JWT_SECRET` est defini mais aucun vrai mecanisme JWT n'est implemente ;
- la protection SSRF pourrait encore etre renforcee avec une validation plus complete des IP, de l'IPv6 et des redirections ;
- les secrets sont injectes par variables d'environnement, mais pas encore geres par un coffre fort dedie ;
- le script `pipeline.sh` installe des outils a la volee et pourrait etre fiabilise davantage.

## 9. Conclusion

Le projet a ete transforme d'une application vulnerable vers une base plus robuste orientee DevSecOps.

Le travail realise combine :

- correction des failles applicatives ;
- reduction de l'exposition reseau ;
- hygiene sur les secrets ;
- durcissement de l'image Docker ;
- premiers controles automatises de securite.

Ce document peut servir de support de rendu, de base de demonstration et de guide de test.
