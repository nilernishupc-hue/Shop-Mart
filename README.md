# Shop Mart: AI-Powered Personalised Recommendation System
**MSc Research Project & Web Prototype**  
*Ulster University*  
**Developer**: MD RAISUL ISLAM  
**Live Application**: [https://shop-mart-3xuw.onrender.com](https://shop-mart-3xuw.onrender.com)  

---

## 📌 Project Overview
Shop Mart is a full-stack, AI-powered e-commerce web application developed as an MSc research prototype. The system demonstrates advanced machine learning recommendation engines (Collaborative Filtering, Content-Based Filtering, and Hybrid models) integrated with a modern e-commerce web platform.

---

## ✨ Key Features & Capabilities

- 🤖 **Triple Recommendation Engine**:
  - **Collaborative Filtering (SVD)**: Predicts user preferences based on 3,000+ user interactions.
  - **Content-Based Filtering (TF-IDF)**: Calculates product similarity based on descriptions and metadata.
  - **Hybrid Model**: Combines Collaborative and Content-Based models (0.6 SVD + 0.4 TF-IDF) for personalized home page recommendations.

- 📊 **Model Evaluation Dashboard**:
  - Compares **5 Recommendation Models** (Random, Popularity, Collaborative Filtering, Content-Based, and Hybrid).
  - Visualizes **5 Evaluation Metrics** (Precision@5, Recall@5, F1-Score, MAP, NDCG) using interactive Chart.js grouped bar charts.

- 🛒 **Full E-Commerce Web Features**:
  - **Temu-Style 1-Click Shortcut Cart**: Instant floating `🛒` cart addition on all product cards with real-time AJAX badge updates.
  - **Product Detail Specifications**: Technical specifications table, stock status, 12-month warranty details, and service badges.
  - **Verified Photo Reviews**: Category-matched product photo customer reviews.
  - **Interactive Support Widget**: Floating live chat assistant for instant user guidance.
  - **Temu-Style Comprehensive Footer**: Company info, customer service, app downloads, social links, and security certificates.

---

## 🛠️ Technology Stack
- **Backend Framework**: Python 3.11 / Flask
- **Database**: SQLite3 (`ecommerce.db`)
- **Machine Learning**: Scikit-Learn (TF-IDF, Cosine Similarity), Surprise (SVD Matrix Factorization), Pandas, NumPy
- **Frontend**: HTML5, CSS3, JavaScript (ES6+), Chart.js
- **Cloud Deployment**: Gunicorn, WhiteNoise, Render Cloud Hosting

---

## 🚀 Local Setup & Installation

### 1. Prerequisites
- Python 3.8+ installed on your computer.

### 2. Running Locally
1. Open a terminal / command prompt in the project root folder.
2. Install required Python packages:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python app.py
   ```
4. Access the site in your browser at:
   `http://127.0.0.1:5000`

---

## 🔑 Demo Account Credentials
- **Full Name / Login**: `Vihaan Sharma` (or `Pooja Kumar`, `Sneha Singh`)
- **Password**: `password123`
- *Note*: You can also register a new account on the `/register` page and log in using your Full Name, Username, or Email.

---

## 📁 Submission File Structure
```
Web Site Files/
├── app.py                      # Flask Server & API routes
├── recommendation_engine.py    # Machine Learning Models (SVD, TF-IDF, Hybrid)
├── models.py                   # SQLite Database schema & helpers
├── ecommerce.db                # SQLite database with 60 products & 3,000+ interactions
├── import_amazon.py            # Dataset import & seed script
├── requirements.txt            # Python dependencies
├── Procfile                    # Render cloud deployment configuration
├── static/                     # CSS stylesheets, images, and upload assets
└── templates/                  # Jinja2 HTML templates (layout, home, products, detail, cart, etc.)
```

---
*Developed by **MD RAISUL ISLAM** for MSc Final Research Project & Prototype at Ulster University.*
