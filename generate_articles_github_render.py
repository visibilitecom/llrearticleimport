import os
import re
import sys
import subprocess
import requests
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI
import markdown
from bs4 import BeautifulSoup

# 📦 Vérifie et installe openpyxl
try:
    import openpyxl
except ImportError:
    print("📦 Installation de openpyxl...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "openpyxl"])
    import openpyxl

# 🔐 Chargement des variables d’environnement
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
LARAVEL_API = os.getenv("LARAVEL_API")  # ex : https://tonsite.fr/api/generate-articles
IMAGE_PATH = "storage/photos/1/Google I/Google IO 2025.png"

# 🧠 Génère un article optimisé SEO
def generate_article(keyword):
    print(f"🧠 Génération de contenu : {keyword}")
    prompt = f"""
Tu es un rédacteur web expert en SEO. Rédige un article de blog de plus de 1000 mots, structuré pour le web, 
avec des titres H2 et H3 optimisés (pas d’introduction formelle). Utilise des listes à puces si pertinent.

- Ne commence pas par un titre 'Introduction'
- Ne dis jamais que tu es une IA
- Structure l’article pour la lisibilité web

Thème : {keyword}
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Tu es un expert en rédaction humaine optimisée SEO."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.6
        )
        content = response.choices[0].message.content
        title = extract_title(content)
        html_content = format_content_with_lists(content)
        return title, html_content
    except Exception as e:
        print(f"❌ Erreur génération GPT : {e}")
        return None, None

# 🧪 Extrait le premier titre du contenu comme titre d’article
def extract_title(markdown_text):
    lines = markdown_text.strip().split("\n")
    for line in lines:
        if line.startswith("#"):
            return line.lstrip("#").strip()
    return "Article sans titre"

# 🧹 Convertit le Markdown GPT → HTML formaté (avec <h2 class="section__title"><em>)
def format_content_with_lists(markdown_text):
    html = markdown.markdown(markdown_text)

    # Parse le HTML
    soup = BeautifulSoup(html, 'html.parser')

    # Formatage H2
    for h2 in soup.find_all('h2'):
        h2['class'] = 'section__title'
        h2.string = f"{h2.get_text(strip=True)}"
        new_tag = soup.new_tag("em")
        new_tag.string = h2.string
        h2.string = ''
        h2.append(new_tag)

    # Formatage H3
    for h3 in soup.find_all('h3'):
        h3['class'] = 'section__title'
        h3.string = f"{h3.get_text(strip=True)}"
        new_tag = soup.new_tag("em")
        new_tag.string = h3.string
        h3.string = ''
        h3.append(new_tag)

    return str(soup)

# 📤 Envoie à Laravel via API
def send_to_laravel(title, content, keyword):
    print(f"📤 Envoi à Laravel : {title}")
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
            json_response = response.json()
            print("✅ Réponse Laravel :", json_response)
            return True, json_response.get("post_id")
        else:
            print("⚠️ Réponse non-JSON :", response.text[:500])
            return False, None

    except requests.exceptions.HTTPError as e:
        print("❌ Erreur HTTP Laravel :", e.response.status_code, e.response.text[:500])
        return False, None
    except Exception as e:
        print("❌ Erreur générale :", str(e))
        return False, None

# ▶️ Script principal
def main():
    excel_file = "keywords.xlsx"
    try:
        df = pd.read_excel(excel_file, engine='openpyxl')
    except Exception as e:
        print("❌ Impossible d’ouvrir le fichier Excel :", e)
        return

    # Colonnes de suivi si absentes
    if 'envoye' not in df.columns:
        df['envoye'] = 0
    if 'post_id' not in df.columns:
        df['post_id'] = None

    for idx, row in df.iterrows():
        if row.get("envoye", 0) == 1:
            continue

        keyword = str(row.get("mot_cle", "")).strip()
        if not keyword:
            print("⚠️ Mot-clé manquant. Ignoré.")
            continue

        title, content = generate_article(keyword)
        if not title or not content:
            print("⚠️ Article non généré.")
            continue

        success, post_id = send_to_laravel(title, content, keyword)
        if success:
            df.at[idx, 'envoye'] = 1
            df.at[idx, 'post_id'] = post_id
            print("✅ Article publié.\n")
        else:
            print("❌ Échec d'envoi.\n")

    try:
        df.to_excel(excel_file, index=False, engine='openpyxl')
        print("💾 Fichier Excel mis à jour.")
    except Exception as e:
        print("❌ Erreur sauvegarde Excel :", e)

if __name__ == "__main__":
    main()
