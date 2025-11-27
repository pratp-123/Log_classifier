# Log_classifier


## 📦 Clone and Run Locally

```bash
git clone https://github.com/pratp-123/Log_classifier.git

# Navigate into the project folder
cd iLog_classifier
## Directory Structure
```
## Creating environment
```
# create env on window
python -m venv venv

#activate env
venv\Scripts\activate
```
```
# create env on mac
python3 -m venv venv
#activate env
source venv/bin/activate
```

## Install Dependencies
```
pip install -r requirements.txt
```

## Run code
⚙️ Run the FastAPI Backend

Navigate to the project root (where main.py is located).
Run the API with Uvicorn:
```bash
uvicorn server:app --reload
```

Open your browser and check:
API Root: http://127.0.0.1:8000
Docs (Swagger UI): http://127.0.0.1:8000/docs
