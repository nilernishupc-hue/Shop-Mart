"""
generate_data.py
----------------
Populates the SQLite database with:
  - 50 diverse products across 5 categories
  - 20 users (User1 - User20)
  - Realistic interaction histories (views, purchases, ratings)
"""

import sqlite3
import random
import os
from models import init_db, DB_NAME

# Seed for reproducibility
random.seed(42)

# ---------------------------------------------------------------------------
# Product catalogue – 10 items per category = 50 total
# ---------------------------------------------------------------------------
PRODUCT_CATALOGUE = [
    # Electronics (10)
    ("Sony WH-1000XM5 Headphones",      "Electronics", 279.99, "Industry-leading noise cancelling headphones with 30-hour battery life, crystal-clear hands-free calling and Alexa voice control.", 4.8),
    ("Samsung Galaxy S24 Ultra",         "Electronics", 1199.99,"Powerful flagship smartphone with a 200MP camera, built-in S Pen, 5000mAh battery and a stunning 6.8-inch AMOLED display.", 4.7),
    ("Apple MacBook Pro 14-inch M3",     "Electronics", 1999.99,"The most powerful MacBook Pro ever, featuring the M3 Pro chip for extraordinary performance, a stunning Liquid Retina XDR display.", 4.9),
    ("iPad Air (M2)",                    "Electronics", 749.99, "Supercharged by the M2 chip, iPad Air is a versatile powerhouse perfect for creativity and productivity.", 4.6),
    ("Bose QuietComfort 45",             "Electronics", 199.99, "Wireless noise-cancelling headphones with high-fidelity audio, 22-hour battery life and a lightweight, comfortable design.", 4.5),
    ("Kindle Paperwhite 11th Gen",       "Electronics", 139.99, "The thinnest, lightest Kindle Paperwhite yet, with a 6.8-inch display and adjustable warm light for a comfortable reading experience.", 4.7),
    ("Apple Watch Series 9",             "Electronics", 399.99, "The smartwatch with the most advanced dual-core chip ever in Apple Watch for a magical new way to interact with your watch.", 4.7),
    ("Garmin Fenix 7 Pro",               "Electronics", 699.99, "Premium GPS multisport smartwatch with TopoActive maps, multiband GPS technology, and industry-leading battery life.", 4.6),
    ("Anker 737 Power Bank",             "Electronics", 89.99,  "High-capacity 24,000 mAh power bank with 140W fast charging to power your laptop, smartphone and more on the go.", 4.5),
    ("Logitech MX Master 3S Mouse",      "Electronics", 99.99,  "Advanced wireless mouse with near-silent clicks, ultrafast scrolling and ergonomic design for professionals.", 4.8),

    # Books (10)
    ("Atomic Habits – James Clear",      "Books",       14.99,  "A revolutionary system for building good habits and breaking bad ones. #1 Sunday Times bestseller with practical life-changing strategies.", 4.9),
    ("Dune – Frank Herbert",             "Books",       12.99,  "Set in the far future amidst a feudal interstellar society, Dune tells the story of young Paul Atreides, the heir of a noble family.", 4.8),
    ("The Midnight Library – Matt Haig", "Books",       11.99,  "A novel about all the choices we make and the infinite possibilities of life. Nora Seed finds a library between life and death.", 4.7),
    ("Project Hail Mary – Andy Weir",    "Books",       13.99,  "A lone astronaut must save Earth, but first he has to figure out where he is and what happened. A gripping sci-fi thriller.", 4.9),
    ("Sapiens – Yuval Noah Harari",      "Books",       15.99,  "A brief history of humankind, from the Stone Age to the modern age. A thrilling and thought-provoking book.", 4.7),
    ("The Psychology of Money",          "Books",       13.99,  "Morgan Housel shares 19 short stories exploring the strange ways people think about money and teaches you how to make better sense of it.", 4.8),
    ("Fourth Wing – Rebecca Yarros",     "Books",       16.99,  "Enter the brutal and elite world of a war college for dragon riders. A romantic fantasy epic that will leave you breathless.", 4.6),
    ("The Body – Bill Bryson",           "Books",       14.99,  "A tour of the human body, taking stock of the incredible, baffling, and frustrating facts of our physical existence.", 4.7),
    ("Deep Work – Cal Newport",          "Books",       13.99,  "Rules for focused success in a distracted world. Newport provides a compelling case for cultivating a deep-work ethic.", 4.6),
    ("Educated – Tara Westover",         "Books",       12.99,  "A memoir about a young girl who, kept out of school, leaves her survivalist family and goes on to earn a PhD from Cambridge University.", 4.8),

    # Clothing (10)
    ("Levi's 501 Original Jeans",        "Clothing",    79.99,  "The original jeans since 1873. A timeless, iconic straight-leg fit crafted from durable denim that looks great on everybody.", 4.6),
    ("Nike Air Max 270",                 "Clothing",    149.99, "The Nike Air Max 270 features Nike's biggest heel Air unit yet for a super-soft ride that feels as impossible as it looks.", 4.5),
    ("Patagonia Nano Puff Jacket",       "Clothing",    229.99, "Lightweight, compressible and warm, the Nano Puff Jacket is made with 100% recycled insulation and shell fabrics.", 4.8),
    ("Adidas Ultraboost 23 Trainers",    "Clothing",    179.99, "Experience extraordinary comfort with BOOST cushioning and Primeknit upper for a snug, sock-like fit.", 4.7),
    ("Under Armour Tech Polo Shirt",     "Clothing",    44.99,  "A classic polo shirt with UA Tech fabric that provides superior soft feel and natural stretch to keep you comfortable.", 4.4),
    ("Barbour Wax Cotton Jacket",        "Clothing",    329.99, "An iconic British waxed jacket that has been an emblem of countryside living since 1894. Timeless style and rugged protection.", 4.9),
    ("Columbia Fleece Hoodie",           "Clothing",    69.99,  "Super-soft, warm fleece with the Columbia logo on the front chest. Perfect for layering on cool days.", 4.5),
    ("Tommy Hilfiger Slim Chinos",       "Clothing",    89.99,  "Smart chino trousers in a slim fit cut, crafted from stretch cotton for all-day comfort and a polished look.", 4.4),
    ("Ray-Ban Aviator Classic",          "Clothing",    149.99, "The iconic aviator with crystal lenses that provide 100% UV protection. Made in Italy with the finest materials.", 4.8),
    ("New Balance 990v6 Sneakers",       "Clothing",    184.99, "Made in the USA. The 990v6 offers the same premium quality and classic styling the series has been known for since 1982.", 4.7),

    # Home & Garden (10)
    ("Nespresso Vertuo Next Coffee Machine","Home & Garden", 149.99,"Enjoy barista-quality coffee at home with Centrifusion technology and over 30 blends to choose from.", 4.7),
    ("Dyson V15 Detect Cordless Vacuum", "Home & Garden", 649.99,"The most powerful Dyson cordless vacuum. A laser reveals microscopic dust, an acoustic sensor proves it's been removed.", 4.8),
    ("Le Creuset Cast Iron Casserole",   "Home & Garden", 289.99, "Made in France since 1925. Excellent heat distribution and retention for unparalleled cooking performance.", 4.9),
    ("Philips Hue White & Colour Bulb",  "Home & Garden", 44.99,  "Smart LED bulb with 16 million colours and a range of white light. Control with the Hue app or your voice.", 4.6),
    ("KitchenAid Stand Mixer",           "Home & Garden", 449.99, "The iconic 4.8L tilt-head stand mixer with a 10-speed motor and a full metal construction that's built to last.", 4.9),
    ("Instant Pot Duo 7-in-1",           "Home & Garden", 89.99,  "Pressure cook, slow cook, rice cook, sauté, steam, warm and make yogurt in one multi-use appliance.", 4.7),
    ("Silentnight Memory Foam Pillow",   "Home & Garden", 29.99,  "Perfectly shaped memory foam pillow that provides optimal support for your head and neck for a great night's sleep.", 4.5),
    ("Weber Q1200 Portable Grill",       "Home & Garden", 189.99, "Compact and powerful portable gas grill with porcelain-enameled cast-iron cooking grates and infinite ignition system.", 4.7),
    ("Roomba i7+ Robot Vacuum",          "Home & Garden", 799.99, "Smarter cleaning with Imprint Smart Mapping. Learns your home layout, empties itself for 60 days and works with Alexa.", 4.6),
    ("Yankee Candle Large Jar",          "Home & Garden", 24.99,  "Premium scented candle made with pure cotton wicks and carefully selected fragrance oils for a clean, even burn.", 4.7),

    # Sports & Outdoors (10)
    ("Lululemon Align Leggings",         "Sports & Outdoors", 98.00, "Our most buttery-soft feeling fabric. A barely-there sensation that makes these leggings perfect for yoga and low-impact activity.", 4.8),
    ("Coleman 6-Person Tent",            "Sports & Outdoors", 149.99, "Spacious 6-person tent with WeatherTec system to keep you protected from the elements. Easy to set up in 15 minutes.", 4.6),
    ("Wahoo KICKR Snap Turbo Trainer",   "Sports & Outdoors", 499.99, "Wheel-on smart trainer with Bluetooth and ANT+ connectivity for cycling at home with realistic road feel.", 4.7),
    ("Garmin Edge 540 Cycling Computer", "Sports & Outdoors", 349.99, "GPS cycling computer with ClimbPro pacing guidance, mapping, and Garmin Coach adaptive training plans.", 4.7),
    ("Bowflex SelectTech 552 Dumbbells", "Sports & Outdoors", 399.99, "Innovative dial system lets you adjust from 2.3kg to 23.6kg in seconds. Replace 15 sets of weights.", 4.8),
    ("Osprey Atmos AG 65L Backpack",     "Sports & Outdoors", 269.99, "Award-winning Anti-Gravity suspension system for the most comfortable carry on long backpacking adventures.", 4.9),
    ("Fitbit Charge 6",                  "Sports & Outdoors", 149.99, "Advanced health and fitness tracker with built-in GPS, 24/7 heart rate monitoring and up to 7 days battery.", 4.5),
    ("SKLZ Pro Mini Basketball Hoop",    "Sports & Outdoors", 49.99,  "Professional-quality mini basketball hoop with an unbreakable polycarbonate backboard and flexible rim.", 4.4),
    ("TRX Home2 Suspension Trainer",     "Sports & Outdoors", 199.99, "The original and most versatile workout system. Train anywhere with bodyweight exercises for every fitness level.", 4.7),
    ("Yeti Rambler 20oz Tumbler",        "Sports & Outdoors", 34.99,  "Double-wall vacuum insulated stainless steel tumbler that keeps drinks hot or cold for hours wherever you go.", 4.8),
]

def populate_database():
    """Create fresh database and populate with products, users and interactions."""
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)

    init_db()
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # -- Products -------------------------------------------------------
    print("Inserting 50 products...")
    for i, (name, cat, price, desc, rating) in enumerate(PRODUCT_CATALOGUE, start=1):
        image_url = f"https://picsum.photos/seed/{i + 200}/400/400"
        c.execute(
            "INSERT INTO products (name, category, price, description, rating, image_url) VALUES (?, ?, ?, ?, ?, ?)",
            (name, cat, price, desc, rating, image_url),
        )

    # -- Users ----------------------------------------------------------
    print("Inserting 20 users...")
    for i in range(1, 21):
        c.execute("INSERT INTO users (username) VALUES (?)", (f"User{i}",))

    conn.commit()

    # -- Interactions ---------------------------------------------------
    print("Generating interaction histories...")
    interactions = []
    for user_id in range(1, 21):
        # Each user views 5-15 products
        n_views = random.randint(5, 15)
        viewed = random.sample(range(1, 51), n_views)

        for p_id in viewed:
            interactions.append((user_id, p_id, "view", None))

        # Subset of views become purchases (2-8)
        n_purchases = min(len(viewed), random.randint(2, 8))
        purchased = random.sample(viewed, n_purchases)
        for p_id in purchased:
            interactions.append((user_id, p_id, "purchase", None))

        # Subset of views get rated (3-10)
        n_ratings = min(len(viewed), random.randint(3, 10))
        rated = random.sample(viewed, n_ratings)
        for p_id in rated:
            # Purchased items tend to get higher ratings
            rating_val = random.randint(3, 5) if p_id in purchased else random.randint(1, 5)
            interactions.append((user_id, p_id, "rate", rating_val))

    c.executemany(
        "INSERT INTO interactions (user_id, product_id, interaction_type, rating) VALUES (?, ?, ?, ?)",
        interactions,
    )
    conn.commit()
    conn.close()
    print(f"Done! Inserted {len(PRODUCT_CATALOGUE)} products, 20 users, {len(interactions)} interactions.")

if __name__ == "__main__":
    populate_database()
