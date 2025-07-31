#!/usr/bin/env python3

import os
import re
import sys
import subprocess
import requests
import pandas as pd
from dotenv import load_dotenv

# 📦 Installation conditionnelle
required = ['openai', 'markdown', 'bs4', 'openpyxl']
for pkg in required:
    try:
        __import__(pkg)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

import markdown
from bs4 import BeautifulSoup
from openai import OpenAI

# 🔐 Config
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
LARAVEL_API = os.getenv("LARAVEL_API")
IMAGE_PATH = "storage/photos/1/Google I/Google IO 2025.png"

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
  <h2 class="section__title"><em>...</em></h2>
- Ajoute des sous-sections H3 si nécessaire :
  <h3 class="section__title"><em>...</em></h3>
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
- Génére uniquement le contenu HTML (pas de <html>, <head>, <body>)"""
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Tu écris du contenu SEO comme un humain."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8
        )
        html = response.choices[0].message.content
        title = extract_title_from_html(html)
        clean_html = sanitize_html(html)
        print(f"✅ Article généré pour '{keyword}' — Titre : {title}")
        return title, clean_html
    except Exception as e:
        print(f"❌ Erreur lors de la génération avec OpenAI : {e}")
        return None, None

def extract_title_from_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    h2 = soup.find('h2')
    return h2.get_text(strip=True) if h2 else "Article sans titre"

def sanitize_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    return str(soup)

def send_to_laravel(title, content, keyword):
    print(f"📤 Envoi vers Laravel pour : {keyword}")
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
            print("✅ Article envoyé à Laravel avec succès.")
            return True, response.json().get("post_id")
        print("⚠️ Réponse non-JSON :", response.text[:500])
        return False, None
    except Exception as e:
        print(f"❌ Erreur lors de l’envoi à Laravel : {e}")
        return False, None

def main():
    print("🚀 Script de génération d’articles lancé.")
    try:
        df = pd.read_excel("keywords.xlsx", engine='openpyxl')
        print("📖 Fichier Excel chargé.")
    except Exception as e:
        print(f"❌ Erreur lecture Excel : {e}")
        return

    if 'envoye' not in df.columns:
        df['envoye'] = 0
    if 'post_id' not in df.columns:
        df['post_id'] = None

    for idx, row in df.iterrows():
        if row.get("envoye", 0) == 1:
            print(f"⏩ Mot-clé déjà traité : {row.get('mot_cle')}")
            continue

        keyword = str(row.get("mot_cle", "")).strip()
        if not keyword:
            print("⚠️ Mot-clé vide, ligne ignorée.")
            continue

        title, content = generate_article(keyword)
        if not title or not content or len(content) < 2000:
            print(f"⚠️ Article trop court ou invalide pour : {keyword}")
            continue

        success, post_id = send_to_laravel(title, content, keyword)
        if success:
            df.at[idx, 'envoye'] = 1
            df.at[idx, 'post_id'] = post_id
            print("✅ Article publié et sauvegardé.")
        else:
            print("⚠️ Échec de publication Laravel.")

    try:
        df.to_excel("keywords.xlsx", index=False, engine='openpyxl')
        print("💾 Fichier Excel mis à jour avec les statuts.")
    except Exception as e:
        print(f"❌ Erreur lors de l’écriture du fichier Excel : {e}")

    print("🏁 Fin du script.")

if __name__ == "__main__":
    main()
