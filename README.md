
# 🧠 Supplier Matching API 

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-%F0%9F%90%8D-green)
![Status](https://img.shields.io/badge/status-active-brightgreen)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

This API matches sourcing request PDFs to relevant suppliers using
natural language processing and semantic search via SentenceTransformers
and GPT translation.

------------------------------------------------------------------------

## 📂 Project Structure 
```
supplier-matching/ 
├── api.py # FastAPI backend 
├── main_pipeline.py # Core matching logic 
├── uploaded_pdfs/ # Folder containing sourcing PDFs 
├── top_suppliers_by_doc.json # output json file 
├── pdf_translate.csv # translated uploaded pdfs (to english) 
├── translated_suppliers # File containing the SupplierList.xlsx completely translated to english 
├── SupplierList.xlsx # Original supplier list in excel format 
├── requirements.txt 
└── README.md`
```

------------------------------------------------------------------------

## 👩🏾‍🦳 Approach and Assumptions 

#### **1.Explore data :** 

I assumed and deduced that not all data given was useful to matching
such as supplier id\'s etc. Based on usefulness,
completeness/missingness, and compatibility with NLP/LLM based
approaches, I focused on the following features \..... Category,
Description, and Capability. Here we are most likely to find evidence
for similarity to suppliers

#### **2. Create for growth, especially when it is easy to do so:** 

I wasn\'t sure if the Description field was hard coded or how often this
would need to be updated, but noticed that linkedin profile of suppliers
was given, therefore I created a pyquery function to scrape the About us
section, ensuring less human labor the next go around and easier
expansion as the suppliers we work with increases. This enrichment step
was not necessary but a nice to have.

#### **3. Ensure Language Congruency** 

Additionally, I noticed that many documents had a mix of languages
(English and German). While most of the source pdfs/inquiries were in
German, Linkedin data was in a vast array of languages, which varied
accross fields. As the company grows, this diversity will increase and
should be accommodated for right away. A lack of matching languages will
make matching difficult as well.

Therfore, both input pdf files (inquiries/use cases) as well as the full
list of available suppliers are translated to English. At first, I use
the Google Translator tool from the Deep_translator, but this did not
produce good results and contained obvious errors such as translating
\'bitte\' , which should be \'please\' to \'Bi2e\'. This was a result of
the model not being context aware and reduces the ability for any model
to assess relevancy.

#### **4. LLM Translation**

For make the AI more robust despite the small amount of data, I decided
to use a pretrained LLM model for translation, as this would allow for
context awareness in the documents. I opted for GPT-4o-mini due to ease
of using the API and the relatively low token cost.

This AI approach only translates the provided use case documents with
every API call. Translating the full suppliers data with every call
drastically reduces performance, taking up to 7 minutes to match just 6
documents to relevant suppliers. This is unacceptable in a production
environment. Therefore, this task is only done once and results saved
locally in the `translated_suppliers.csv` file in the root directory. If
at any point the supplier list changes, translation for suppliers can be
re-run by calling `translate_suppliers=True` in `main()`.

#### **5. Compute Embeddings using a finetuned transformer** 

After ensuring language congruency using an LLM, I used a pre-trained
sentence transformer to generate embeddings based on my supplier data
and use cases. This model is a small model finetuned on a larger dataset
of 1 billion pairs, so contextual understanding is increased and more
nuances can be captured vs. using a classical machine learning approach.

#### **6. Compute rankings based on Cosine similarity** 

For this exercise, I produced rankings using cosine similarity, which is
most commonly used similarity index and the defualt metric for sentence
transformers, as well as symantic similarity. However, symatic
similarity was aborted after 18 minutes of run time. This is
unacceptable in a production environment, and embeddings would have to
be created each time we call the API. Cosine similarity plus caching the
translated supplier list produced a result for all 6 use cases in 27
seconds. This can be further improved likely by using the cosine
similarity function with sentence transformers rather than computing
through sci-kit learn (My hypothesis).

#### **7. Evaluation and Improvement** 

After checking each other rankings, it was clear that the top supplier
result for all 6 use cases was indeed relevant to the request. However,
to improve this, I would re-rank the top 5 using a cross-encoder model.
I would also gather a larger training dataset to create a binary
classifier of whether or not a result was actually a good match (0 or 1)
according to a human, therefore being able to generate an accuracy,
precision, and recall scores. I would code any cosine similarity score
of above 0 as positive prediction and below zero as a negative
prediction. This would be more labor intensive so the decision to do so
would be informed by key stakeholders and business priorities.


------------------------------------------------------------------------

## ⚙️ Setup Instructions 

### 1. Clone the repository or download project

```bash
git clone https://github.com/lydialaval/supplier_matching.git
cd supplier-matching
```

### 2. Create a virtual Environment 

```
python -m venv venv source venv/bin/activate \# On Windows:
venv\\Scripts\\activate
```
### 3. Install Dependencies 

```
pip install -r requirements.txt
```

### 4. Add your OpenAI API Key 

#### This directory already includes my personal API key in the .env file, but you can also create your own .env file in the root directory here: 
```
OPENAI_API_KEY=your_openai_key_here
```

### 5. Running the API

#### start the FastAPI server using
```
    uvicorn api:app --reload
```
##### The server will be live at `<http://127.0.0.1:8000>`

------------------------------------------------------------------------

## 🔁 Usage 

#### 1. Upload PDFs 

##### Make sure your sourcing PDFs are placed in the `uploaded_pdfs/` directory. 

#### 2. Go to `http://127.0.0.1:8000/run_pipeline` for results of supplier matching in JSON format 
![image.png](vertopal_612e33b93bf94068bef86691cf9dab25/image.png)


