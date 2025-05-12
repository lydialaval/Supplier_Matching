import os
import json
import requests
import pandas as pd
import pdfplumber
from pyquery import PyQuery as pq
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import openai
from dotenv import load_dotenv

# === Load Environment Variables ===
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# === CONFIGURATION ===
SUPPLIER_FILE = '/Users/lydialaval/Documents/Data_Sci/Supplier Matching/SupplierList.xlsx'
translated_file = '/Users/lydialaval/Documents/Data_Sci/Supplier Matching/translated_suppliers.csv'
COLUMNS_TO_TRANSLATE = ['Description', 'Category', 'Capability']
LINKEDIN_COLUMN = 'linkedIn'
MODEL_NAME = 'all-MiniLM-L6-v2'

# === STEP 1: Translate text using GPT-4o Mini ===
def translate_to_english(text):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Translate the following text into English."},
                {"role": "user", "content": text[:4000]}
            ]
        )
        translated_text = response.choices[0].message['content'].strip()
        return translated_text
    except Exception as e:
        print(f"Translation error: {e}")
        return text  # fallback if translation fails

# === STEP 2: Extract translated text from PDFs into DataFrame ===
def extract_translated_pdfs(pdf_folder):
    records = []
    for filename in os.listdir(pdf_folder):
        if filename.endswith(".pdf"):
            path = os.path.join(pdf_folder, filename)
            with pdfplumber.open(path) as pdf:
                raw_text = "\n".join(page.extract_text() or "" for page in pdf.pages)
                translated = translate_to_english(raw_text)
                records.append({"source_document": filename, "translated_text": translated})
    return pd.DataFrame(records)

# === STEP 3: Load and optionally translate supplier data ===
def load_and_translate_suppliers(filepath, translate_suppliers=False):
    if not translate_suppliers:
        if not os.path.exists(translated_file):
            raise FileNotFoundError(f"Expected pre-translated file '{translated_file}' not found.")
        return pd.read_csv(translated_file)

    df = pd.read_excel(filepath)
    for col in COLUMNS_TO_TRANSLATE:
        if col in df.columns:
            df[col] = df[col].astype(str).apply(translate_to_english)

    df.to_csv(translated_file, index=False)
    return df

# === STEP 4: Scrape LinkedIn About sections ===
def scrape_linkedin_about(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return ""
        d = pq(response.text)
        about = d("section:contains('About')").text()
        return about.strip() if about else ""
    except Exception:
        return ""

# === STEP 5: Combine supplier text (description + LinkedIn About) ===
def enrich_supplier_text(df):
    texts = []
    for _, row in df.iterrows():
        cat = row.get('Category', '')
        cap = row.get('Capability', '')
        linkedin_url = row.get(LINKEDIN_COLUMN, '')
        linkedin_about = scrape_linkedin_about(linkedin_url) if pd.notna(linkedin_url) else ''
        full_text = f"{cat}\n{cap}\n{linkedin_about}".strip()
        texts.append(full_text)
    df['enriched_text'] = texts
    return df

# === STEP 6: Compute similarity and rank for each document ===
def rank_suppliers_per_document(doc_names, doc_texts, supplier_df):
    model = SentenceTransformer(MODEL_NAME)
    supplier_embeddings = model.encode(supplier_df['enriched_text'].tolist())

    result = []

    for doc_name, doc_text in zip(doc_names, doc_texts):
        doc_embedding = model.encode([doc_text])[0]
        similarities = cosine_similarity([doc_embedding], supplier_embeddings)[0]

        supplier_df['score'] = similarities
        ranked = supplier_df[['Supplier Id', 'Supplier Name', 'score']].sort_values(by='score', ascending=False).reset_index(drop=True)
        top_suppliers = ranked.head(5).copy()
        top_suppliers['rank'] = top_suppliers.index + 1

        result.append({
            "source_document": doc_name,
            "top_suppliers": top_suppliers[['rank', 'score', 'Supplier Name', 'Supplier Id']].to_dict(orient='records')
        })

    return result, supplier_df

# === MAIN PIPELINE ===
def main(pdf_folder, translate_suppliers=False):
    print(f"Processing PDFs from: {pdf_folder}")
    
    # Extract and translate PDFs from the provided folder
    print("Extracting and translating sourcing PDFs...")
    pdf_df = extract_translated_pdfs(pdf_folder)

    # Load and translate supplier data
    print("Loading and translating supplier data...")
    supplier_df = load_and_translate_suppliers(SUPPLIER_FILE, translate_suppliers=translate_suppliers)

    # Enrich supplier profiles with LinkedIn data
    print("Scraping LinkedIn and enriching supplier profiles...")
    enriched_supplier_df = enrich_supplier_text(supplier_df)

    # Rank suppliers based on similarity to documents
    print("Ranking suppliers per document...")
    results_json, enriched_supplier_df = rank_suppliers_per_document(
        pdf_df['source_document'].tolist(),
        pdf_df['translated_text'].tolist(),
        enriched_supplier_df
    )

    # Save JSON output
    with open("top_suppliers_by_doc.json", "w") as f:
        json.dump(results_json, f, indent=2)

    # Save CSV files
    pdf_df.to_csv("pdf_translate.csv", index=False)
    print("\nTop suppliers per document saved to: top_suppliers_by_doc.json")

    return results_json, pdf_df, enriched_supplier_df
