## Mission 2 – Suppression des fuites d'information

# Membre
Brenda Ankoume

# Vulnérabilité identifiée
Lors de la phase Red Team, il a été découvert que le service interne `vault`
exposait un endpoint `/debug`. Cet endpoint retournait toutes les variables d'environnement avec : 
jsonify(dict(os.environ))

Cela exposait des informations sensibles telles que :
- VAULT_TOKEN
- FLAG_VAULT
- variables système

# Risque

Un attaquant pouvait exploiter la vulnérabilité SSRF de l'application web :
/fetch?url=http://vault:7000/debug

Cela permettait d'accéder au service interne `vault` et d'exfiltrer des secrets.

# Correctif appliqué

Le correctif consiste à :

- supprimer complètement l'endpoint `/debug`
- empêcher l'exposition des variables d'environnement
- ajouter des handlers d'erreurs génériques (403, 404, 500)

# Test avant correction

Commande :
curl.exe "http://localhost:5001/fetch?url=http://vault:7000/debug"

Résultat :
- exposition des variables d'environnement
- fuite de VAULT_TOKEN
- fuite de FLAG_VAULT

# Test après correction

Commande :
curl.exe "http://localhost:5001/fetch?url=http://vault:7000/debug"

Résultat :
{"error":"Not found"}

Les variables sensibles ne sont plus exposées.

# Test de bon fonctionnement

Commande :
curl.exe "http://localhost:5001/fetch?url=http://vault:7000/health"

Résultat :
{"ok": true}

Le service fonctionne toujours correctement.

# Conclusion

La suppression de l'endpoint `/debug` empêche la fuite d'informations sensibles
et réduit significativement la surface d'attaque du service `vault`.