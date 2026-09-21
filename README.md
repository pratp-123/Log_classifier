# Log Classifier

Log Classifier is a FastAPI service that classifies CSV log messages using a tiered pipeline. It combines deterministic regex rules, a local embedding-based classifier, and an LLM for the small group of messages that need semantic interpretation.

## Classification Pipeline

Each input row must contain `source` and `log_message` columns.

1. **Regex classification**: Known patterns such as user actions, backups, uploads, and system notifications are classified immediately with deterministic rules.
2. **Local embedding classifier**: Messages that do not match a regex and are not from `LegacyCRM` are encoded with `all-MiniLM-L6-v2`. The saved logistic regression model in `models/log_classifier.joblib` predicts the category. Predictions below the confidence threshold are returned as `Unclassified`.
3. **LLM classification**: Non-regex `LegacyCRM` messages are sent to Groq for the categories `Workflow Error` and `Deprecation Warning`. The LLM returns `Unclassified` when neither category is appropriate.

## Training

The training workflow is documented in `training/log_classification.ipynb` and uses `training/dataset/synthetic_logs.csv`.

The notebook:

- Loads and explores the labeled log dataset.
- Uses MiniLM embeddings and DBSCAN clustering to discover repeated message patterns.
- Extracts deterministic patterns for the regex stage.
- Separates the small `LegacyCRM` group, where workflow and deprecation examples are sparse and better suited to an LLM.
- Encodes the remaining non-regex messages with MiniLM embeddings.
- Splits the embeddings into training and test sets, trains a scikit-learn logistic regression classifier, and prints a classification report.
- Saves the trained classifier to `models/log_classifier.joblib`.

To retrain the local classifier, open and run the notebook from the `training` directory. Keep the generated model at `models/log_classifier.joblib` so the API can load it at startup.

## Why LLM Usage and Cost Are Reduced

The service is designed to avoid an LLM request for every log:

- **Deterministic early exit**: Regex matches are classified locally with no model or API request.
- **Local ML fallback**: Most unknown non-`LegacyCRM` messages use the local MiniLM plus logistic regression model instead of the Groq API.
- **Source-based routing**: The current implementation sends LLM requests only for non-regex messages whose source is `LegacyCRM`.
- **Small label space**: The LLM is asked to choose between only `Workflow Error`, `Deprecation Warning`, or `Unclassified`, reducing prompt complexity and response length.
- **Structured output**: The response is requested inside `<category>` tags, so the service does not need a long explanation or follow-up processing.

This design keeps the paid or metered LLM path for sparse, difficult categories while handling common and well-represented patterns locally.

## Run Locally

```bash
git clone https://github.com/pratp-123/Log_classifier.git
cd Log_classifier

python -m venv venv
venv\Scripts\activate       # Windows
# source venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
```

Set the Groq credentials before using `LegacyCRM` classification:

```bash
set GROQ_API_KEY=your-api-key       # Windows Command Prompt
$env:GROQ_API_KEY="your-api-key"   # Windows PowerShell
export GROQ_API_KEY=your-api-key    # macOS/Linux
```

The model can be changed with `GROQ_MODEL`; the default is `llama-3.3-70b-versatile`.

Start the API locally:

```bash
uvicorn server:app --reload
```

The API is available at `http://127.0.0.1:8000`. Interactive documentation is available at `http://127.0.0.1:8000/docs`.

## API Endpoints

### `GET /`

Returns the web upload interface.

### `GET /help`

Returns the help page.

### `POST /classify/`

Uploads a CSV file and returns a classified CSV. The file must contain:

```text
source,log_message
```

The response adds a `target_label` column and writes the latest result to `resources/output.csv`.

Example with curl:

```bash
curl -X POST "http://127.0.0.1:8000/classify/" \
    -F "file=@resources/test.csv" \
    -o resources/output.csv
```

### `GET /categories/`

Returns the total number of classified rows and counts grouped by `target_label`, based on the latest `resources/output.csv`:

```json
{
    "total": 100,
    "counts": {
        "HTTP Status": 42,
        "System Notification": 31,
        "Unclassified": 27
    }
}
```

This endpoint returns `404` until a classification request has created an output file.

## Deploy on Render

The repository includes `render.yaml`. Render installs `requirements.txt` and starts the service with:

```bash
uvicorn server:app --host 0.0.0.0 --port $PORT
```

Set `GROQ_API_KEY` as a secret environment variable in Render. Render supplies `PORT` automatically; the service listens on `0.0.0.0` for external traffic.
