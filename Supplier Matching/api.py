from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
from main_pipeline import main

app = FastAPI()

# Optional CORS (for browser-based use)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Welcome to the Supplier Matching API. Go to /run_pipeline to execute."}

@app.get("/run_pipeline")
def run_pipeline():
    pdf_folder = "uploaded_pdfs"

    if not os.path.exists(pdf_folder):
        return JSONResponse(status_code=400, content={"error": "Folder 'uploaded_pdfs' does not exist."})

    try:
        results_json, pdf_df, supplier_df = main(pdf_folder, translate_suppliers=False)
        return {"message": "Success", "results": results_json}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
