#!/usr/bin/env python3

import os
import re
import sys
import subprocess
import requests
import pandas as pd
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import markdown
from openai import OpenAI

# 📦 Vérifie et installe les modules nécessaires
required = ['openai', 'markdown', 'bs4', 'openpyxl', 'flask', 'python-dotenv']
for pkg in required:
    try:
        __import__(pkg)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

# 🔐 Chargement des variables
df_path = "keywords.xlsx"
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
LARAVEL_API = os.getenv("LARAVEL_API")
IMAGE_PATH = "storage/photos/1/Google I/Google IO 2025.png"

# 🧠 Génération d'article long et SEO
def generate_article(keyword):
    print(f"🧠 Génération de contenu pour : {keyword}")
    prompt = f"""Tu es un rédacteur web senior, expert en SEO et UX, spécialisé dans la rédaction d’articles optimisés pour Google et agréables à lire.

Ta mission : rédiger un article HTML de **plus de 1000 mots** (au moins 6000 caractères), sur le sujet suivant : **{keyword}**.

### Structure attendue :
- Commence par un **titre principal SEO** (servira de <title> mais ne doit pas être une balise <h1>)
    - Doit inclure le mot-clé principal
    - Ne doit pas dépasser 65 caractères
    - Doit inciter au clic (ex. : “Comment…”, “Top 10…”, “Pourquoi…”)
- Ajoute une **balise meta-description HTML** (<160 caractères) contenant le mot-clé principal
- Structure l’article avec **au moins 7 sections H2** :
  <h2 class=\"section__title\"><em>...</em></h2>
- Ajoute des sous-sections H3 si nécessaire :
  <h3 class=\"section__title\"><em>...</em></h3>
- Utilise des listes <ul><li>...</li></ul> si pertinent
- Utilise des paragraphes courts (<p>) optimisés pour la lecture web

### Contraintes SEO :
- Le mot-clé principal doit apparaître :
  - dans au moins un <h2>
  - dans deux paragraphes
  - dans une liste <ul>
  - dans la meta-description
- Évite toute suroptimisation : densité naturelle (~1% à 2%)
- Intègre des variantes sémantiques et expressions longue traîne
- N’utilise pas de titres "Introduction" ou "Conclusion"
- Ne commence pas par "Dans cet article…"
- Ne dis jamais que tu es une IA
- Rédige dans un style fluide, humain et informatif
- Adopte un **ton à la fois persuasif et technique** : démontre l’expertise sur le sujet tout en incitant à lire, à s’informer ou à agir.
- Utilise un vocabulaire professionnel, précis et argumenté.
- Mets en avant des bénéfices concrets ou des points différenciateurs pour convaincre l’internaute.

- Écris pour une intention de recherche **informationnelle**
- Ne crée pas de tableau HTML
- Génère uniquement le contenu HTML (pas de <html>, <head>, <body>)"""
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Tu écris comme un rédacteur humain SEO confirmé."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2500
        )
        html = response.choices[0].message.content
        title = extract_title_from_html(html)
        clean_html = sanitize_html(html)
        return title, clean_html
    except Exception as e:
        print(f"❌ Erreur GPT : {e}")
        return None, None

# 🔎 Extraction du premier H2
def extract_title_from_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    h2 = soup.find('h2')
    return h2.get_text(strip=True) if h2 else "Article sans titre"

# 🧼 Nettoyage HTML
def sanitize_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    for tag in soup.find_all(['h2', 'h3']):
        tag['class'] = 'section__title'
        text = tag.get_text(strip=True)
        tag.clear()
        em = soup.new_tag("em")
        em.string = text
        tag.append(em)
    return str(soup)

# 📄 Envoi Laravel
def send_to_laravel(title, content, keyword):
    print(f"📄 Envoi à Laravel : {title}")
    try:
        data = {
            "title": title,
            "content": content,
            "key_words": keyword,
            "cover_image": IMAGE_PATH,
            "thumbnail_image": IMAGE_PATH
        }
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "SEOArticleBot/1.0"
        }
        response = requests.post(LARAVEL_API, data=data, headers=headers, timeout=30)
        response.raise_for_status()
        if "application/json" in response.headers.get("Content-Type", ""):
            return True, response.json().get("post_id")
        print("⚠️ Réponse non-JSON :", response.text[:500])
        return False, None
    except Exception as e:
        print("❌ Erreur envoi Laravel :", str(e))
        return False, None

# ▶️ Script principal
def main():
    try:
        df = pd.read_excel(df_path, engine='openpyxl')
    except Exception as e:
        print("❌ Erreur lecture Excel :", e)
        return

    if 'envoye' not in df.columns:
        df['envoye'] = 0
    if 'post_id' not in df.columns:
        df['post_id'] = None

    for idx, row in df.iterrows():
        if row.get("envoye", 0) == 1:
            continue

        keyword = str(row.get("mot_cle", "")).strip()
        if not keyword:
            continue

        title, content = generate_article(keyword)
        if not title or not content or len(content) < 6000:
            print(f"⚠️ Contenu insuffisant pour : {keyword} ({len(content) if content else 0} caractères)")
            continue

        success, post_id = send_to_laravel(title, content, keyword)
        if success:
            df.at[idx, 'envoye'] = 1
            df.at[idx, 'post_id'] = post_id
            print("✅ Article publié.")
        else:
            backup_path = f"article_backup_{keyword.replace(' ', '_')}.html"
            with open(backup_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"💾 Article sauvegardé localement dans {backup_path}")

    try:
        df.to_excel(df_path, index=False, engine='openpyxl')
        print("💾 Fichier Excel mis à jour.")
    except Exception as e:
        print("❌ Erreur sauvegarde Excel :", e)

    print("✅ Script terminé avec succès.")

if __name__ == '__main__':
    main()
