# 🚀 AI Website Builder — Local Setup Guide

This project is a **Streamlit-based AI Website Builder** with:

* MongoDB-based **user authentication** (sign in / sign up)
* **Dashboard** for managing projects per user
* **Builder** to generate, preview, and export websites
* **Persistent storage** of project data, prompts, and generated code

---

## 📦 1. Clone the repository

```bash
git clone https://github.com/yourusername/wonder.ai.git
cd wonder.ai
```

---

## 🐍 2. Create & activate virtual environment

```bash
# Create venv (Python 3.10+ recommended)
python3 -m venv wonder_env

# Activate venv
# macOS/Linux:
source wonder_env/bin/activate
# Windows:
wonder_env\Scripts\activate
```

---

## 📥 3. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 🗄️ 4. Set up MongoDB

You need a local MongoDB instance running.
Install & start MongoDB:

**macOS (Homebrew)**:

```bash
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb-community
```

**Ubuntu/Debian**:

```bash
sudo apt install -y mongodb
sudo systemctl start mongod
sudo systemctl enable mongod
```

**Windows**:
Download from [MongoDB Community Server](https://www.mongodb.com/try/download/community) and start the service.

---

## ⚙️ 5. Environment variables


Edit `.env`:

```
MONGO_URI=mongodb://localhost:27017/wonder_ai
DB_NAME=wonder_ai
HF_TOKEN=your_huggingface_api_token_here
OPENAI_API_KEY=your_openai_api_key_here
```

* **MONGO\_URI** → Your local or cloud Mongo connection string.
* **DB\_NAME** → Mongo database name.
* **HF\_TOKEN** → Hugging Face API token (for AI model calls, if used).
* **OPENAI\_API\_KEY** → OpenAI API key (if GPT models are used).

---

## ▶️ 6. Run the app locally

```bash
streamlit run app.py
```

The app will be available at:

```
http://localhost:8501
```

---

## 🔑 7. First-time login

1. Click **Sign Up** and create an account.
2. After logging in, you’ll see the **Dashboard**.
3. Create a new project and open it in the **Builder**.
4. Generate a website, preview, and export.

---

## 📁 8. Project structure

```
wonder.ai/
│
├── app.py                 # Main Streamlit app entry point
├── components/            # UI components (sidebar, login, preview, customization, dashboard)
├── data/                  # Mongo persistence (projects)
├── utils/                 # AI generation, preview creation, export handling
├── auth/                  # Mongo authentication helpers
├── .env.example           # Example environment variables
├── requirements.txt       # Python dependencies
└── README.md              # This file
```

---

## 🛠 9. Common issues

* **Mongo not running** → Ensure `mongod` service is started.
* **API key errors** → Check `.env` for valid `HF_TOKEN` / `OPENAI_API_KEY`.
* **`st.experimental_rerun()` error** → Update Streamlit to `>=1.30` and use `st.rerun()`.

---

## 🌐 10. Notes

* You can switch MongoDB to **Atlas Cloud** by replacing `MONGO_URI`.
* The app saves **each user’s projects** separately by email.
* Project data is stored persistently in MongoDB, so users can return and continue editing.

---
