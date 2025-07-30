
# 🤖 AI Article Publisher – Laravel + GPT-4 + DALL·E

Publiez automatiquement des articles optimisés SEO de haute qualité, avec génération d'images réalistes, directement dans votre site Laravel.

---

## 🚀 Fonctionnalités

- Génère **jusqu’à 10 articles par jour**
- Articles de **1000 mots minimum**, optimisés SEO (titres H2/H3, structure humaine)
- Génération de **deux images réalistes** (couverture + miniature) via DALL·E 3
- Envoi automatique à votre **API Laravel**
- Lecture à partir d’un fichier Excel `keywords.xlsx`

---

## 📁 Structure du projet

```
.
├── generate_articles_seo_1000mots.py   # Script principal
├── keywords.xlsx                       # Fichier source avec mots-clés + catégorie
└── .github/
    └── workflows/
        └── run.yml                     # GitHub Actions (exécution quotidienne)
```

---

## 📄 Format du fichier Excel (`keywords.xlsx`)

| mot_cle                               | catégorie         |
|---------------------------------------|-------------------|
| Externalisation rédaction web         | Rédacteur         |
| Immobilier à Paris                    | Immobilier        |
| Traduction juridique                  | Traduire          |

---

## 🛠️ Installation

1. Clonez le dépôt :
   ```bash
   git clone https://github.com/votre-utilisateur/ai-article-publisher.git
   cd ai-article-publisher
   ```

2. Créez un fichier `.env` :
   ```dotenv
   OPENAI_API_KEY=sk-xxxxx
   LARAVEL_API=https://votre-site.fr/api/generate-articles
   ```

3. Installez les dépendances :
   ```bash
   pip install openai requests pandas python-dotenv
   ```

4. Lancez le script localement :
   ```bash
   python generate_articles_seo_1000mots.py
   ```

---

## ⚙️ GitHub Actions (optionnel)

Déclenche automatiquement le script chaque jour.

Ajoutez vos secrets dans GitHub :

- `OPENAI_API_KEY` : votre clé OpenAI
- `LARAVEL_API` : URL de votre API Laravel

---

## 🧠 Auteur

Créé avec ❤️ par [Visibilitecom].

---

## 📬 Besoin d’aide ?

Contactez-moi si vous souhaitez personnaliser ce script ou automatiser davantage votre stratégie SEO.
