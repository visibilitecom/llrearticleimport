import os
import re
import sys
import subprocess
import requests
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI

# 📦 Installe openpyxl si nécessaire
try:
    import openpyxl
except ImportError:
    print("📦 Installation de openpyxl...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "openpyxl"])
    import openpyxl

# 📦 Installe BeautifulSoup si nécessaire
try:
    from bs4 import BeautifulSoup
except ImportError:
    print("📦 Installation de beautifulsoup4...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "beautifulsoup4"])
    from bs4 import BeautifulSoup

# 📦 Installe markdown si nécessaire
try:
    import markdown
except ImportError:
    print("📦 Installation de markdown...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "markdown"])
    import markdown

# 🔐 Variables d’environnement
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
LARAVEL_API = os.getenv("LARAVEL_API")
IMAGE_PATH = "storage/photos/1/Google I/Google IO 2025.png"

# 🧠 Génère un article SEO
def generate_article(keyword):
    print(f"🧠 Génération de contenu pour : {keyword}")
    prompt = f"""
Tu es un rédacteur web expert SEO. Rédige un article de blog de +1000 mots, structuré pour le web :
- Utilise titres H2 et H3 optimisés, pas de titre 'Introduction'
- Utilise des listes à puces si pertinent
- Utilise un ton naturel, fluide, pas robotique
- Pas de phrase "je suis une IA", etc.
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
        print(f"❌ Erreur GPT : {e}")
        return None, None

# 🏷️ Extrait le premier titre comme titre
def extract_title(markdown_text):
    lines = markdown_text.strip().split("\n")
    for line in lines:
        if line.startswith("#"):
            return line.lstrip("#").strip()
    return "Article sans titre"

# 🎨 Convertit Markdown → HTML et applique le style H2/H3
def format_content_with_lists(markdown_text):
    html = markdown.markdown(markdown_text, extensions=['extra'])
    soup = BeautifulSoup(html, 'html.parser')

    for tag_name in ['h2', 'h3']:
        for tag in soup.find_all(tag_name):
            tag['class'] = 'section__title'
            text = tag.get_text(strip=True)
            tag.clear()
            em = soup.new_tag("em")
            em.string = text
            tag.append(em)

    return str(soup)

# 📤 Envoie à Laravel
def send_to_laravel(title, content, keyword):
    print(f"📤 Envoi vers Laravel : {title}")
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
        print("❌ Erreur envoi Laravel :", str(e))
        return False, None

# ▶️ Script principal
def main():
    excel_file = "keywords.xlsx"
    try:
        df = pd.read_excel(excel_file, engine='openpyxl')
    except Exception as e:
        print("❌ Impossible de lire le fichier Excel :", e)
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
            print("⚠️ Mot-clé manquant.")
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
            print("❌ Envoi échoué.\n")

    try:
        df.to_excel(excel_file, index=False, engine='openpyxl')
        print("💾 keywords.xlsx mis à jour.")
    except Exception as e:
        print("❌ Erreur de sauvegarde Excel :", e)

if __name__ == "__main__":
    main()
