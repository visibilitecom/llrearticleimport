import os
import re
import subprocess
import sys
import requests
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI

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
LARAVEL_API = os.getenv("LARAVEL_API")  # ex : https://llredac.fr/api/generate-articles

# 🧠 Génère un article optimisé SEO
def generate_article(keyword):
    try:
        print(f"🧠 Génération article SEO : {keyword}")
        prompt = f"""
Tu es un rédacteur web expert en SEO et UX. Rédige un article de blog de plus de 1000 mots, structuré pour le web, 
avec des titres H2 et H3 optimisés pour le référencement naturel. L’article doit être naturel, informatif, engageant 
(et ne jamais sembler écrit par une IA). Ajoute des paragraphes courts, des mots de transition, des titres attrayants 
et des expressions sémantiques pertinentes autour du sujet. Évite les introductions robotiques.
Thème : {keyword}
"""
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Tu es un expert en rédaction humaine optimisée pour le SEO naturel."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.6
        )
        content = response.choices[0].message.content
        lines = content.strip().split("\n")
        title = lines[0].strip("# ").strip()
        body = "\n".join(lines[1:]).strip()
        return title, body
    except Exception as e:
        print(f"❌ Erreur génération article : {e}")
        return None, None

# 📤 Envoie l'article à Laravel
def send_to_laravel(title, content, keyword):
    print(f"📤 Envoi à Laravel : {title}")
    try:
        image_path = "storage/photos/1/Google I/Google IO 2025.png"
        data = {
            "title": title,
            "content": content,
            "key_words": keyword,
            "cover_image": image_path,
            "thumbnail_image": image_path
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
            print("⚠️ Réponse non-JSON :", response.text[:1000])
            return False, None

    except requests.exceptions.HTTPError as e:
        print("❌ Erreur HTTP Laravel :", e.response.status_code, e.response.text[:500])
        return False, None
    except Exception as e:
        print("❌ Erreur d’envoi à Laravel :", str(e))
        return False, None

# ▶️ Script principal
def main():
    excel_file = "keywords.xlsx"
    try:
        df = pd.read_excel(excel_file, engine='openpyxl')
    except Exception as e:
        print("❌ Fichier Excel illisible :", e)
        return

    # Ajoute les colonnes si absentes
    if 'envoye' not in df.columns:
        df['envoye'] = 0
    if 'post_id' not in df.columns:
        df['post_id'] = None

    for idx, row in df.iterrows():
        if row.get("envoye", 0) == 1:
            continue  # déjà envoyé

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
            print("✅ Article envoyé et post_id enregistré.\n")
        else:
            print("❌ Échec d'envoi.\n")

    # Enregistre les modifications dans le fichier Excel
    try:
        df.to_excel(excel_file, index=False, engine='openpyxl')
        print("💾 Fichier Excel mis à jour avec les post_id.")
    except Exception as e:
        print("❌ Erreur lors de la sauvegarde du fichier :", e)

if __name__ == "__main__":
    main()
