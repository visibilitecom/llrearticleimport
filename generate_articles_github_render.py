import os
import sys
import subprocess
import requests
import pandas as pd
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from openai import OpenAI

# 📦 Installer openpyxl si absent
try:
    import openpyxl
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "openpyxl"])
    import openpyxl

# 🔐 Chargement des variables d’environnement
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
LARAVEL_API = os.getenv("LARAVEL_API")
IMAGE_PATH = "storage/photos/1/Google I/Google IO 2025.png"

# 🧠 Génère un article
def generate_article(keyword):
    print(f"🧠 Génération de contenu : {keyword}")
    prompt = f"""
Tu es un rédacteur web expert SEO. Rédige un article de +1000 mots sans dire "introduction", en markdown clair avec H2/H3, listes, paragraphes courts.

Thème : {keyword}
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Tu rédiges comme un humain expert SEO."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.6
        )
        markdown = response.choices[0].message.content
        title = extract_title(markdown)
        html = convert_markdown_to_html(markdown)
        return title, html
    except Exception as e:
        print(f"❌ Erreur GPT : {e}")
        return None, None

# 🧪 Titre = première ligne qui commence par "#"
def extract_title(md):
    for line in md.split("\n"):
        if line.startswith("# "):
            return line.replace("#", "").strip()
    return "Titre non trouvé"

# 🔄 Convertit Markdown simplifié → HTML compatible TinyMCE
def convert_markdown_to_html(md):
    lines = md.split("\n")
    html = ""

    for line in lines:
        line = line.strip()
        if line.startswith("## "):  # H2
            h2 = line.replace("##", "").strip()
            html += f'<h2 class="section__title"><em>{h2}</em></h2>\n'
        elif line.startswith("### "):  # H3
            h3 = line.replace("###", "").strip()
            html += f'<h3 class="section__title"><em>{h3}</em></h3>\n'
        elif line.startswith("- "):  # Liste à puces
            if not html.endswith("<ul>\n"):
                html += "<ul>\n"
            html += f"<li>{line[2:].strip()}</li>\n"
        elif line == "":
            if html.endswith("<ul>\n") or html.endswith("</li>\n"):
                html += "</ul>\n"
        else:  # Paragraphe
            html += f"<p>{line}</p>\n"

    soup = BeautifulSoup(html, 'html.parser')
    return str(soup)

# 📤 Envoie à Laravel
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
            "Content-Type": "application/x-www-form-urlencoded"
        }
        response = requests.post(LARAVEL_API, data=data, headers=headers, timeout=30)
        response.raise_for_status()
        if "application/json" in response.headers.get("Content-Type", ""):
            return True, response.json().get("post_id")
        else:
            return False, None
    except Exception as e:
        print("❌ Envoi échoué :", e)
        return False, None

# ▶️ Script principal
def main():
    file = "keywords.xlsx"
    try:
        df = pd.read_excel(file, engine='openpyxl')
    except Exception as e:
        print("❌ Fichier Excel illisible :", e)
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
        if not title or not content:
            continue

        success, post_id = send_to_laravel(title, content, keyword)
        if success:
            df.at[idx, 'envoye'] = 1
            df.at[idx, 'post_id'] = post_id

    try:
        df.to_excel(file, index=False, engine='openpyxl')
        print("💾 Excel mis à jour.")
    except Exception as e:
        print("❌ Sauvegarde échouée :", e)

if __name__ == "__main__":
    main()
