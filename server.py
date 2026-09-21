import pandas as pd
from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import FileResponse, JSONResponse
import uvicorn
import os
from pathlib import Path

app = FastAPI()

@app.get("/")
async def root():
    upload_html = Path(__file__).resolve().parent / "resources" / "upload.html"
    if not upload_html.exists():
        raise HTTPException(status_code=404, detail="upload.html not found")
    return FileResponse(str(upload_html), media_type="text/html")

@app.get("/help")
async def help_page():
    help_html = Path(__file__).resolve().parent / "resources" / "help.html"
    if not help_html.exists():
        raise HTTPException(status_code=404, detail="help.html not found")
    return FileResponse(str(help_html), media_type="text/html")

@app.post("/classify/")
async def classify_logs(file: UploadFile):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV.")
    
    try:
        # Read the uploaded CSV
        df = pd.read_csv(file.file)
        if "source" not in df.columns or "log_message" not in df.columns:
            raise HTTPException(status_code=400, detail="CSV must contain 'source' and 'log_message' columns.")

        # Perform classification
        from classify import classify
        df["target_label"] = classify(list(zip(df["source"], df["log_message"])))

        print("Dataframe:",df.to_dict())

        # Save the modified file
        resources_dir = Path(__file__).resolve().parent / "resources"
        resources_dir.mkdir(parents=True, exist_ok=True)
        output_file = resources_dir / "output.csv"
        df.to_csv(output_file, index=False)
        print(f"File saved to {output_file}")
        return FileResponse(str(output_file), media_type='text/csv', filename='output.csv')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        file.file.close()
        # # Clean up if the file was saved
        # if os.path.exists("output.csv"):
        #     os.remove("output.csv")

@app.get("/categories/")
async def categories():
    """
    Return total rows and counts per category from the latest classified output (resources/output.csv).
    """
    resources_dir = Path(__file__).resolve().parent / "resources"
    output_file = resources_dir / "output.csv"
    if not output_file.exists():
        raise HTTPException(status_code=404, detail="No classified output found. Run POST /classify/ first.")
    try:
        df = pd.read_csv(output_file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read output CSV: {e}")
    if "target_label" not in df.columns:
        raise HTTPException(status_code=400, detail="No 'target_label' column in output.")
    counts = df["target_label"].fillna("Unclassified").value_counts().to_dict()
    total = int(df.shape[0])
    return {"total": total, "counts": counts}


    
# Add this at the bottom of the file
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=port
    )