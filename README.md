# CoopFaso

CoopFaso est une plateforme Django de gestion et de valorisation des cooperatives agricoles. Elle permet de gerer les cooperatives, membres, produits, productions, commandes, paiements, formations et contenus publics.

## Prerequis

Avant l'installation, verifier que la machine possede :

- Python 3.12 ou plus
- PostgreSQL 16 ou plus
- Git
- Un terminal Linux

Sur Ubuntu, installer les paquets utiles :

```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip postgresql postgresql-contrib git
```

## Installation du projet

Se placer dans le dossier ou le projet doit etre installe :

```bash
cd ~/Documents/Projets
```

Cloner ou copier le projet, puis entrer dans le dossier :

```bash
cd CoopFaso
```

Creer et activer l'environnement virtuel :

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Installer les dependances :

```bash
pip install -r requirements.txt
```

## Configuration de la base PostgreSQL

Creer le fichier `.env` a partir du modele :

```bash
cp .env.example .env
```

Le fichier `.env` doit contenir les informations de connexion PostgreSQL :

```env
POSTGRES_DB=coopfaso
POSTGRES_USER=coopfaso
POSTGRES_PASSWORD=252466
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

Creer l'utilisateur et la base PostgreSQL :

```bash
sudo -u postgres psql
```

Dans le terminal PostgreSQL :

```sql
CREATE USER coopfaso WITH PASSWORD '252466';
CREATE DATABASE coopfaso OWNER coopfaso;
GRANT ALL PRIVILEGES ON DATABASE coopfaso TO coopfaso;
GRANT ALL ON SCHEMA public TO coopfaso;
ALTER SCHEMA public OWNER TO coopfaso;
\q
```

Si l'utilisateur ou la base existe deja, utiliser plutot :

```sql
ALTER USER coopfaso WITH PASSWORD '252466';
ALTER DATABASE coopfaso OWNER TO coopfaso;
GRANT ALL PRIVILEGES ON DATABASE coopfaso TO coopfaso;
GRANT ALL ON SCHEMA public TO coopfaso;
ALTER SCHEMA public OWNER TO coopfaso;
\q
```

## Initialisation de Django

Appliquer les migrations :

```bash
python manage.py migrate
```

Creer un compte administrateur :

```bash
python manage.py createsuperuser
```

Lancer le serveur :

```bash
python manage.py runserver
```

Ouvrir ensuite le site dans le navigateur :

```text
http://127.0.0.1:8000/
```

Administration Django :

```text
http://127.0.0.1:8000/admin/
```

## Lancement rapide apres installation

Pour relancer le projet les jours suivants :

```bash
cd ~/Documents/Projets/CoopFaso
source .venv/bin/activate
python manage.py runserver
```

## Remarques importantes

- Le fichier `.env` est charge automatiquement par `CoopFaso/settings.py`.
- Il n'est donc pas obligatoire de lancer `source .env` avant `runserver`.
- Si `.env` n'existe pas, Django utilise SQLite avec `db.sqlite3`.
- Les fichiers statiques principaux sont locaux afin d'eviter les lenteurs dues aux CDN.
- Le dossier `media/` contient les images et fichiers ajoutes depuis l'application.

## Depannage

### La commande `python` n'existe pas

Sur Ubuntu, utiliser :

```bash
python3 manage.py runserver
```

Ou activer l'environnement virtuel :

```bash
source .venv/bin/activate
python manage.py runserver
```

### Erreur `No module named django`

L'environnement virtuel n'est pas active ou les dependances ne sont pas installees :

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### Erreur `No module named psycopg`

Installer les dependances :

```bash
pip install -r requirements.txt
```

### Erreur `password authentication failed for user "coopfaso"`

Le mot de passe PostgreSQL ne correspond pas au fichier `.env`.

Corriger avec :

```bash
sudo -u postgres psql
```

Puis :

```sql
ALTER USER coopfaso WITH PASSWORD '252466';
\q
```

### Erreur `permission denied for schema public`

Donner les droits sur le schema PostgreSQL :

```bash
sudo -u postgres psql -d coopfaso
```

Puis :

```sql
GRANT ALL ON SCHEMA public TO coopfaso;
ALTER SCHEMA public OWNER TO coopfaso;
\q
```

### Erreur `unable to open database file`

Verifier que le projet est lance depuis le bon dossier :

```bash
cd ~/Documents/Projets/CoopFaso
python manage.py runserver
```

Verifier aussi que le fichier `.env` existe si PostgreSQL doit etre utilise.

## Verification finale

Avant de rendre le projet, lancer :

```bash
python manage.py check
python manage.py migrate
python manage.py runserver
```

Si aucune erreur n'apparait et que la page s'ouvre sur `http://127.0.0.1:8000/`, l'installation est correcte.
