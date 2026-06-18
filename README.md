# KiahBao.AI (🏡 仔包)

**KiahBao.AI** is a culturally aligned, zero-hallucination public housing knowledge engine and decision-support system for Singapore's HDB landscape. The name translates to the ultimate tool that *"fully covers all your housing anxieties so you don't need to be scared!"* (Hokkien: *Kiah* = Scare, *Bao* = Guarantee/Cover).

It features a 4-tier pipeline designed to demystify complex HDB housing regulations, CPF grant rules, and real-time transacted pricing without hallucinated figures.

---

## 🚀 Key Features

* **📰 HDB Pulse News Feed & Scraper**: Built-in scraper that extracts live articles and policy updates from the Next.js `__NEXT_DATA__` block on official HDB sites, caching them dynamically and serving them via a beautiful glassmorphic sidebar widget.
* **📍 @Location Live Price Bypass**: The dual router intercepts colloquial queries containing `@Location` (e.g., *What are the resale prices @Tampines?*), bypasses RAG and LLM generation entirely, and queries the official data.gov.sg API live for low-latency transaction metrics.
* **🇸🇬 PR-Specific Math Validation**: Integrates Singapore permanent resident eligibility checks (including the statutory 3-year PR durational requirement, Pure SPR couple criteria, and parent location rules) with real-time feedback.
* **🛡️ Zero-Hallucination Math Safeguard**: An independent, rules-based verification layer that intercepts LLM outputs, recalculates EHG/PHG/CPF grants based on strict statutory logic, and overrides incorrect figures with precise, verified formulas.
* **✨ Premium Dark UI**: An ultra-premium, glassmorphic dark-mode dashboard built with Next.js and Tailwind CSS featuring interactive profile editors, live metrics, and real-time chat.

---

## 📁 Repository Structure

* `web/` - Next.js (React 19) + Tailwind CSS Frontend UI
* `router/` - Context Hybrid Router, model engine configuration, and Singlish templates
* `verification/` - Python Math Validator, grant calculator, and eligibility check rules
* `ingestion/` - Python scrapers for downloading PDFs, indexing policies, and parsing HDB news
* `evaluation/` - Ragas-based faithfulness evaluator for RAG outputs
* `tests/` - pytest suite validating backend routing, ingestion, math calculations, and app flows
* `data/` - Folder structure for local raw PDFs and parsed processed guidelines (Git-ignored datasets)

---

## 🛠️ Installation & Setup

### 1. Prerequisites
* **Python 3.10+**
* **Node.js 18+**
* **Ollama** (for running local LLM inference)

### 2. Backend Setup
1. Clone the repository and navigate to the project root:
   ```bash
   git clone https://github.com/ailabs4/KiahBao.AI.git
   cd KiahBao.AI
   ```
2. Create and activate a Python virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. Install required Python packages:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy the environment template and set up your variables (if using external API evaluation layers):
   ```bash
   cp .env.example .env
   ```

### 3. Setup local LLM (Ollama)
The orchestrator connects to a custom model styled for Singlish context.
1. Download Ollama and pull the base model:
   ```bash
   ollama pull aisingapore/Gemma-SEA-LION-v4-27B-IT
   ```
2. Build the customized `kiahbao-ai` model:
   ```bash
   ollama create kiahbao-ai -f router/Modelfile
   ```

### 4. Frontend Setup
1. Navigate to the `web/` directory:
   ```bash
   cd web
   ```
2. Install npm packages:
   ```bash
   npm install
   ```

---

## 🏃 Running the Application

### 1. Run Data Ingestion (Optional)
To fetch the latest guidelines and news feeds from HDB:
```bash
source .venv/bin/activate
python ingestion/scrape_hdb_info.py
```
This writes raw/processed policy chunks and caches the top 50 HDB Pulse news articles to `data/processed/`.

### 2. Start the FastAPI Backend
Start the server from the root directory:
```bash
source .venv/bin/activate
python -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```
The API docs will be available at [http://localhost:8000/api/docs](http://localhost:8000/api/docs).

### 3. Start the Next.js Frontend
Start the web development server from the `web/` directory:
```bash
cd web
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser to view the application.

---

## 🧪 Running Tests
Verify all system integrations, math calculator bounds, and query routers using the test suite:
```bash
source .venv/bin/activate
python -m pytest
```
