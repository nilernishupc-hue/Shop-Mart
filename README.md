# AI-Powered Personalised Recommendation System

## Overview
This is a web-based prototype demonstrating various AI-powered recommendation systems for an e-commerce context. It implements Collaborative Filtering (using SVD), Content-Based Filtering (using TF-IDF + Cosine Similarity), and a Hybrid approach.

This project was built for an MSc research project to showcase how recommendation systems work, including model evaluation metrics and explainable AI features ("Because you viewed X, we recommend Y").

## Features
- **Modern UI**: Built with a clean, premium Midnight blue / Soft blue color scheme.
- **Collaborative Filtering**: Recommends items based on similar users' preferences (Surprise library).
- **Content-Based Filtering**: Recommends items similar to ones a user is currently viewing (Scikit-Learn).
- **Hybrid Recommendations**: A weighted combination on the Home page (0.6 CF + 0.4 CB).
- **Explanation Generator**: Clear reasoning for every recommendation provided.
- **Evaluation Dashboard**: Visual representation of model performances (Precision, Recall, F1).
- **Self-Contained Data**: Generates a high-quality, simulated dataset of 50 products and 20 users upon setup.

## Setup Instructions

### Prerequisites
- Python 3.8+
- pip (Python package manager)

### Installation
1. Clone or download this repository.
2. Open a terminal in the project directory.
3. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
5. Generate the mock database and data:
   ```bash
   python generate_data.py
   ```
   *Note: This script will create `ecommerce.db` and populate it with simulated products, users, and interaction histories required to train the recommendation models.*

### Running the Application
1. Start the Flask server:
   ```bash
   python app.py
   ```
2. Open your web browser and go to `http://127.0.0.1:5000/`.

### How to Use the Prototype
- **Login**: Go to the login page and use any username from `User1` to `User20` (no password required).
- **Home Page**: Once logged in, you will see a personalized "Recommended for You" section utilizing the Hybrid model.
- **Product Details**: Click on any product to view its details. At the bottom, you'll see "You May Also Like" which uses the Content-Based Filtering model to suggest similar items.
- **Rate Products**: You can rate products you view (1-5 stars) to influence future recommendations.
- **Profile**: View your interaction history (views, purchases, ratings).
- **Dashboard**: View the simulated model evaluation metrics comparing CF, CB, and Hybrid models.
