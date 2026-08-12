"""
import_amazon.py
----------------
Reads the first 500 rows of 'Amazon Sales Data Set.xlsx', populates products,
users, and transactions into the SQLite database, and enriches top users'
data to make SVD recommendations functional and relevant.
"""

import sqlite3
import os
import pandas as pd
import random
from models import init_db, DB_NAME

# Seed for reproducibility
random.seed(42)

EXCEL_PATH = r"e:\Assessment Ulster\Final Project\Web-Based Prototype Web Site\Datasets\Amazon For Content-Based Filtering (TF-IDF) – Core Dataset\archive\Amazon Sales Data Set.xlsx"

# ── Product Metadata Mapping ──────────────────────────────────────────────
# Maps each ProductID (P00001 - P00050) to correct category, Unsplash photo ID, and description.
PRODUCT_METADATA = {
    "P00001": {
        "category": "Electronics",
        "unsplash_id": "photo-1590658268037-6bf12165a8df",
        "desc": "High-fidelity wireless earbuds featuring active noise cancellation, touch controls, and a compact charging case."
    },
    "P00002": {
        "category": "Electronics",
        "unsplash_id": "photo-1608043152269-423dbba4e7e1",
        "desc": "Portable waterproof Bluetooth speaker delivering powerful 360-degree stereo sound and up to 15 hours of battery life."
    },
    "P00003": {
        "category": "Electronics",
        "unsplash_id": "photo-1603302576837-37561b2e2302",
        "desc": "Slim, shockproof smartphone cover with a matte finish and reinforced drop protection."
    },
    "P00004": {
        "category": "Electronics",
        "unsplash_id": "photo-1583863788434-e58a36330cf0",
        "desc": "Fast-charging USB-C wall charger with multiple ports, compatible with laptops, tablets, and smartphones."
    },
    "P00005": {
        "category": "Electronics",
        "unsplash_id": "photo-1585776245991-cf89dd7fc73a",
        "desc": "Water-resistant padded laptop sleeve offering premium scratch and bump protection."
    },
    "P00006": {
        "category": "Electronics",
        "unsplash_id": "photo-1615663245857-ac93bb7c39e7",
        "desc": "Ergonomic gaming mouse with customizable RGB backlighting, adjustable DPI levels, and precision tracking."
    },
    "P00007": {
        "category": "Electronics",
        "unsplash_id": "photo-1587829741301-dc798b83add3",
        "desc": "Tactile mechanical keyboard featuring durable switches, backlit keys, and an anti-ghosting layout."
    },
    "P00008": {
        "category": "Electronics",
        "unsplash_id": "photo-1527443224154-c4a3942d3acf",
        "desc": "Ultra HD 4K computer monitor with thin bezels, vibrant IPS display panel, and HDR support."
    },
    "P00009": {
        "category": "Electronics",
        "unsplash_id": "photo-1544244015-0df4b3ffc6b0",
        "desc": "Pocket-sized ultra-fast portable external solid-state drive (SSD) with 1TB capacity."
    },
    "P00010": {
        "category": "Electronics",
        "unsplash_id": "photo-1508685096489-7aacd43bd3b1",
        "desc": "Multifunctional smartwatch offering heart-rate tracking, sleep analysis, notification alerts, and GPS."
    },
    "P00011": {
        "category": "Electronics",
        "unsplash_id": "photo-1575311373937-040b8e1fd5b6",
        "desc": "Sleek fitness tracker band monitoring daily steps, calories burned, and active workouts."
    },
    "P00012": {
        "category": "Electronics",
        "unsplash_id": "photo-1505740420928-5e560c06d30e",
        "desc": "Over-ear noise-cancelling headphones featuring studio-quality sound and ultra-soft memory foam earcups."
    },
    "P00013": {
        "category": "Electronics",
        "unsplash_id": "photo-1526170375885-4d8ecf77b99f",
        "desc": "Rugged, waterproof action camera capturing ultra-smooth 4K footage of outdoor sports and adventures."
    },
    "P00014": {
        "category": "Electronics",
        "unsplash_id": "photo-1527977966376-1c8408f9f108",
        "desc": "Ultra-lightweight mini quadcopter drone with 1080p camera, GPS auto-return, and smart flight modes."
    },
    "P00015": {
        "category": "Home & Kitchen",
        "unsplash_id": "photo-1584269600464-37b1b58a9fe7",
        "desc": "Multi-use programmable electric pressure cooker, slow cooker, rice cooker, and yogurt maker."
    },
    "P00016": {
        "category": "Home & Kitchen",
        "unsplash_id": "photo-1621972750749-0fbb1abb7736",
        "desc": "Compact digital air fryer that cooks crispy meals using up to 85% less oil than traditional frying."
    },
    "P00017": {
        "category": "Home & Kitchen",
        "unsplash_id": "photo-1585771724684-38269d6639fd",
        "desc": "Rapid-boil cordless electric kettle made of durable stainless steel with automatic shut-off."
    },
    "P00018": {
        "category": "Home & Kitchen",
        "unsplash_id": "photo-1558317374-067fb5f30001",
        "desc": "Lightweight cordless stick vacuum cleaner with powerful suction for carpets and hard floors."
    },
    "P00019": {
        "category": "Home & Kitchen",
        "unsplash_id": "photo-1507473885765-e6ed057f782c",
        "desc": "Dimmable LED desk lamp with adjustable arm, USB charging port, and multiple lighting modes."
    },
    "P00020": {
        "category": "Home & Kitchen",
        "unsplash_id": "photo-1505797149-43b0069ec26b",
        "desc": "Ergonomic mesh office chair with lumbar support, adjustable height, and smooth swivel wheels."
    },
    "P00021": {
        "category": "Clothing",
        "unsplash_id": "photo-1553062407-98eeb64c6a62",
        "desc": "Durable, water-resistant canvas backpack with dedicated laptop compartment and ergonomic straps."
    },
    "P00022": {
        "category": "Sports & Outdoors",
        "unsplash_id": "photo-1602143407151-7111542de6e8",
        "desc": "Double-walled vacuum insulated stainless steel water bottle keeping drinks ice cold or piping hot."
    },
    "P00023": {
        "category": "Home & Kitchen",
        "unsplash_id": "photo-1584269600464-37b1b58a9fe7",
        "desc": "Non-stick cookware set including frying pans, saucepans, and stockpots with tempered glass lids."
    },
    "P00024": {
        "category": "Sports & Outdoors",
        "unsplash_id": "photo-1592432678016-e910b452f9a2",
        "desc": "Eco-friendly non-slip yoga mat providing comfortable cushioning and joint support."
    },
    "P00025": {
        "category": "Clothing",
        "unsplash_id": "photo-1542291026-7eec264c27ff",
        "desc": "Breathable, lightweight running shoes with responsive cushioning for ultimate comfort."
    },
    "P00026": {
        "category": "Clothing",
        "unsplash_id": "photo-1572635196237-14b3f281503f",
        "desc": "Classic unisex polarized sunglasses with UV400 protection and a durable metal frame."
    },
    "P00027": {
        "category": "Clothing",
        "unsplash_id": "photo-1551028719-00167b16eac5",
        "desc": "Insulated winter jacket with a windproof shell, fleece-lined hood, and multiple pockets."
    },
    "P00028": {
        "category": "Clothing",
        "unsplash_id": "photo-1541099649105-f69ad21f3246",
        "desc": "Classic straight-leg blue denim jeans crafted from stretch cotton blend for durability."
    },
    "P00029": {
        "category": "Clothing",
        "unsplash_id": "photo-1521572267360-ee0c2909d518",
        "desc": "Soft, breathable 100% organic cotton crewneck t-shirt, perfect for casual daily wear."
    },
    "P00030": {
        "category": "Clothing",
        "unsplash_id": "photo-1598033129183-c4f50c736f10",
        "desc": "Wrinkle-resistant cotton dress shirt offering a tailored slim fit and elegant styling."
    },
    "P00031": {
        "category": "Toys & Games",
        "unsplash_id": "photo-1596461404969-9ae70f2830c1",
        "desc": "Die-cast scale model toy car with openable doors and realistic pull-back motor action."
    },
    "P00032": {
        "category": "Toys & Games",
        "unsplash_id": "photo-1610890716171-6b1bb98ffd09",
        "desc": "Exciting strategy board game for families and parties, designed for 2 to 6 players."
    },
    "P00033": {
        "category": "Toys & Games",
        "unsplash_id": "photo-1606166325683-e6deb697d301",
        "desc": "High-quality 1000-piece jigsaw puzzle featuring a beautiful, detailed scenic landscape print."
    },
    "P00034": {
        "category": "Home & Kitchen",
        "unsplash_id": "photo-1593642632559-0c6d3fc62b89",
        "desc": "Compact desk organizer with multiple compartments for pens, paperclips, and office essentials."
    },
    "P00035": {
        "category": "Home & Kitchen",
        "unsplash_id": "photo-1545241047-6083a3684587",
        "desc": "Miniature potted artificial plant, adding a touch of refreshing green life to your desk or shelf."
    },
    "P00036": {
        "category": "Electronics",
        "unsplash_id": "photo-1565814329452-e1efa11c5b89",
        "desc": "Smart LED light bulb compatible with voice assistants, supporting millions of colors and schedules."
    },
    "P00037": {
        "category": "Electronics",
        "unsplash_id": "photo-1544244015-0df4b3ffc6b0",
        "desc": "High-speed dual-band Wi-Fi router offering extensive coverage and stable connections."
    },
    "P00038": {
        "category": "Electronics",
        "unsplash_id": "photo-1531403009284-440f080d1e12",
        "desc": "High-capacity external hard disk drive (HDD) with 2TB storage for automated data backups."
    },
    "P00039": {
        "category": "Electronics",
        "unsplash_id": "photo-1585776245991-cf89dd7fc73a",
        "desc": "Digital graphics drawing tablet featuring a battery-free stylus and customizable shortcut keys."
    },
    "P00040": {
        "category": "Electronics",
        "unsplash_id": "photo-1590602847861-f357a9332bbc",
        "desc": "High-sensitivity studio condenser USB microphone, perfect for podcasts, gaming, and recording."
    },
    "P00041": {
        "category": "Electronics",
        "unsplash_id": "photo-1612198188060-c7c2a3b66eae",
        "desc": "Full HD 1080p autofocus webcam with dual noise-reducing microphones for virtual meetings."
    },
    "P00042": {
        "category": "Electronics",
        "unsplash_id": "photo-1535016120720-40c646be5580",
        "desc": "Portable mini projector supporting full HD playback, ideal for home theater movie nights."
    },
    "P00043": {
        "category": "Electronics",
        "unsplash_id": "photo-1583863788434-e58a36330cf0",
        "desc": "High-speed HDMI 2.0 cable with gold-plated connectors, supporting 4K resolutions and 3D media."
    },
    "P00044": {
        "category": "Electronics",
        "unsplash_id": "photo-1583863788434-e58a36330cf0",
        "desc": "High-density 20,000mAh external power bank with fast charging outputs for various devices."
    },
    "P00045": {
        "category": "Electronics",
        "unsplash_id": "photo-1585776245991-cf89dd7fc73a",
        "desc": "Adjustable smartphone tripod stand with wireless remote control for perfect selfies and videos."
    },
    "P00046": {
        "category": "Electronics",
        "unsplash_id": "photo-1583863788434-e58a36330cf0",
        "desc": "Dual-port high-output USB car charger, perfect for charging devices on the road."
    },
    "P00047": {
        "category": "Electronics",
        "unsplash_id": "photo-1544244015-0df4b3ffc6b0",
        "desc": "Ultra-reliable Class 10 micro SD memory card offering 128GB storage expansion."
    },
    "P00048": {
        "category": "Electronics",
        "unsplash_id": "photo-1591370874773-6702e8f12fd8",
        "desc": "Fast wireless charging pad with intelligent temp control and slip-resistant surface."
    },
    "P00049": {
        "category": "Books",
        "unsplash_id": "photo-1512820790803-83ca734da794",
        "desc": "Beautifully illustrated storybook for children, encouraging reading and imagination."
    },
    "P00050": {
        "category": "Books",
        "unsplash_id": "photo-1543002588-bfa74002ed7e",
        "desc": "An engaging, bestselling modern fiction novel filled with mystery and suspense."
    }
}


def get_product_keyword(name):
    name_lower = name.lower()
    # Mobile Phones
    if "iphone" in name_lower or "galaxy" in name_lower or "pixel" in name_lower or "oneplus" in name_lower or "phone" in name_lower or "smartphone" in name_lower or "xiaomi" in name_lower or "motorola" in name_lower or "nokia" in name_lower or "oppo" in name_lower or "realme" in name_lower or "asus" in name_lower or "sony" in name_lower or "razr" in name_lower or "poco" in name_lower or "tcl" in name_lower:
        return "smartphone"
    # Electronics
    if "headphone" in name_lower or "airpods" in name_lower or "earbuds" in name_lower or "headset" in name_lower:
        return "headphones"
    if "macbook" in name_lower or "laptop" in name_lower or "computer" in name_lower or "dell" in name_lower or "asus" in name_lower:
        return "laptop"
    if "watch" in name_lower or "smartwatch" in name_lower or "fitbit" in name_lower or "garmin" in name_lower:
        return "smartwatch"
    if "tv" in name_lower or "television" in name_lower:
        return "television"
    if "monitor" in name_lower:
        return "monitor"
    if "mouse" in name_lower or "keyboard" in name_lower:
        return "keyboard"
    if "speaker" in name_lower or "sonos" in name_lower or "jbl" in name_lower or "soundcore" in name_lower:
        return "speaker"
    if "camera" in name_lower or "gopro" in name_lower or "canon" in name_lower or "eos" in name_lower:
        return "camera"
    if "drone" in name_lower or "dji" in name_lower:
        return "drone"
    if "ipad" in name_lower or "tablet" in name_lower:
        return "tablet"
    if "microphone" in name_lower or "yeti" in name_lower or "shure" in name_lower or "vocal" in name_lower:
        return "microphone"
    if "vr" in name_lower or "quest" in name_lower:
        return "virtualreality"
    if "console" in name_lower or "switch" in name_lower or "playstation" in name_lower or "xbox" in name_lower:
        return "gamingconsole"
    # Home & Kitchen
    if "coffee" in name_lower or "espresso" in name_lower or "nespresso" in name_lower or "barista" in name_lower:
        return "coffee"
    if "fryer" in name_lower:
        return "airfryer"
    if "blender" in name_lower or "vitamix" in name_lower or "processor" in name_lower or "cuisinart" in name_lower:
        return "blender"
    if "mixer" in name_lower or "kitchenaid" in name_lower:
        return "mixer"
    if "vacuum" in name_lower or "roomba" in name_lower or "dyson" in name_lower:
        return "vacuum"
    if "dutch oven" in name_lower or "cookware" in name_lower or "pan" in name_lower or "skillet" in name_lower or "pot" in name_lower or "knife" in name_lower:
        return "cookware"
    if "kettle" in name_lower:
        return "kettle"
    if "toaster" in name_lower:
        return "toaster"
    if "pillow" in name_lower or "blanket" in name_lower or "curtain" in name_lower or "sheet" in name_lower:
        return "bedding"
    if "plant" in name_lower or "monstera" in name_lower:
        return "houseplant"
    if "lamp" in name_lower or "diffuser" in name_lower or "candle" in name_lower or "mirror" in name_lower:
        return "homedecor"
    # Sports & Outdoors
    if "dumbbell" in name_lower or "kettlebell" in name_lower or "weight" in name_lower or "workout" in name_lower or "rope" in name_lower or "roller" in name_lower:
        return "dumbbells"
    if "yoga" in name_lower or "mat" in name_lower:
        return "yogamat"
    if "bottle" in name_lower or "hydro flask" in name_lower or "tumbler" in name_lower or "stanley" in name_lower or "nalgene" in name_lower:
        return "waterbottle"
    if "tent" in name_lower or "sleeping" in name_lower or "hammock" in name_lower or "stove" in name_lower or "camping" in name_lower:
        return "camping"
    if "backpack" in name_lower or "osprey" in name_lower:
        return "backpack"
    if "bike" in name_lower or "bicycle" in name_lower or "cycling" in name_lower:
        return "bicycle"
    if "treadmill" in name_lower or "rower" in name_lower or "gym" in name_lower:
        return "treadmill"
    if "ball" in name_lower or "basketball" in name_lower or "soccer" in name_lower or "golf" in name_lower or "tennis" in name_lower or "racket" in name_lower:
        return "sportsball"
    # Toys & Games
    if "lego" in name_lower or "technic" in name_lower:
        return "lego"
    if "board game" in name_lower or "catan" in name_lower or "monopoly" in name_lower or "scrabble" in name_lower or "game" in name_lower or "jenga" in name_lower:
        return "boardgame"
    if "puzzle" in name_lower or "rubik" in name_lower:
        return "puzzle"
    if "car" in name_lower or "truck" in name_lower or "wagon" in name_lower or "scooter" in name_lower or "hot wheels" in name_lower:
        return "toycar"
    if "doll" in name_lower or "barbie" in name_lower or "figure" in name_lower or "plush" in name_lower or "bear" in name_lower:
        return "toy"
    # Books
    if "book" in name_lower or "habits" in name_lower or "psychology" in name_lower or "sapiens" in name_lower or "novel" in name_lower or "dune" in name_lower or "code" in name_lower or "history" in name_lower or "guide" in name_lower:
        return "book"
    # Clothing
    if "shoes" in name_lower or "sneakers" in name_lower or "boots" in name_lower or "sandals" in name_lower:
        return "shoes"
    if "sunglasses" in name_lower:
        return "sunglasses"
    if "hoodie" in name_lower or "sweatshirt" in name_lower or "jumper" in name_lower or "sweater" in name_lower or "cardigan" in name_lower:
        return "sweater"
    if "jacket" in name_lower or "coat" in name_lower or "parka" in name_lower or "blazer" in name_lower or "vest" in name_lower:
        return "jacket"
    if "jeans" in name_lower or "pants" in name_lower or "trousers" in name_lower or "cargo" in name_lower or "shorts" in name_lower:
        return "pants"
    if "dress" in name_lower or "gown" in name_lower or "skirt" in name_lower:
        return "dress"
    if "shirt" in name_lower or "tee" in name_lower or "blouse" in name_lower or "top" in name_lower:
        return "shirt"
    return "product"


def populate_from_excel():
    # Remove existing database if it exists
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
        print(f"Removed existing database: {DB_NAME}")

    # Re-initialize empty SQLite tables
    init_db()

    # Read the first 3000 rows from Excel
    print(f"Reading Excel file: {EXCEL_PATH}")
    df = pd.read_excel(EXCEL_PATH, nrows=3000)

    # 1. Deduplicate products and map metadata
    print("Processing products...")
    raw_products = df[['ProductID', 'ProductName']].drop_duplicates().sort_values('ProductID')
    
    # Let's map unique ProductIDs to autoincremented SQLite IDs (1 to 50)
    product_id_map = {}  # maps ProductID string -> integer SQLite ID
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    for idx, row in enumerate(raw_products.itertuples(), start=1):
        pid_str = row.ProductID
        name = row.ProductName
        
        # Look up category, unsplash ID, and description
        meta = PRODUCT_METADATA.get(pid_str, {
            "category": "Electronics",
            "unsplash_id": "photo-1505740420928-5e560c06d30e",
            "desc": "Premium quality product."
        })
        
        # Build image URL using matching photo ID
        image_url = f"https://images.unsplash.com/{meta['unsplash_id']}?auto=format&fit=crop&w=400&h=400&q=80"
        
        # Filter all prices for this product to find a representative price
        product_rows = df[df['ProductID'] == pid_str]
        representative_price = float(product_rows['UnitPrice'].mean())
        if pd.isna(representative_price) or representative_price <= 0:
            representative_price = 29.99
            
        # Give it a realistic rating
        rating_avg = round(random.uniform(4.2, 4.9), 1)

        c.execute(
            "INSERT INTO products (name, category, price, description, rating, image_url) VALUES (?, ?, ?, ?, ?, ?)",
            (name, meta["category"], representative_price, meta["desc"], rating_avg, image_url)
        )
        # Store SQLite database ID
        product_id_map[pid_str] = idx

    # Inject custom high-quality mobile phones/smartphones
    print("Injecting custom mobile phones...")
    custom_mobiles = [
        ("iPhone 15 Pro Max", 1199.99, "photo-1695048133142-1a20484d2569", "Apple flagship smartphone with titanium design, A17 Pro chip, and advanced 48MP camera system."),
        ("Samsung Galaxy S24 Ultra", 1299.99, "photo-1610945265064-0e34e5519bbf", "Flagship Android smartphone with 200MP camera, built-in S Pen, and Galaxy AI features."),
        ("Google Pixel 8 Pro", 999.00, "photo-1598327105666-5b89351aff97", "Google flagship phone with advanced AI photo editing, custom Tensor G3 chip, and smooth display."),
        ("OnePlus 12", 799.99, "photo-1565630916779-e303be97b6f5", "High-performance smartphone with Snapdragon 8 Gen 3, 100W fast charging, and Hasselblad camera."),
        ("iPhone 15", 799.99, "photo-1695048133142-1a20484d2569", "Apple smartphone with Dynamic Island, 48MP main camera, and USB-C port."),
        ("Samsung Galaxy Z Fold 5", 1799.99, "photo-1511707171634-5f897ff02aa9", "Innovative folding smartphone with massive 7.6-inch main display and multi-tasking optimizations."),
        ("Google Pixel 7a", 499.00, "photo-1598327105666-5b89351aff97", "Affordable Google phone with incredible camera performance and clean Android experience."),
        ("Xiaomi 14 Pro", 899.99, "photo-1511707171634-5f897ff02aa9", "Premium phone with Leica professional optical lenses and Snapdragon 8 Gen 3 processor."),
        ("iPhone SE (3rd Gen)", 429.00, "photo-1510557880182-3d4d3cba35a5", "Compact and powerful Apple smartphone with A15 Bionic chip and 5G connectivity."),
        ("Samsung Galaxy A54", 449.99, "photo-1610945265064-0e34e5519bbf", "Mid-range Samsung smartphone with 120Hz AMOLED display and multi-day battery life.")
    ]

    for m_idx, (name, price, photo_id, desc) in enumerate(custom_mobiles, start=51):
        image_url = f"https://images.unsplash.com/{photo_id}?auto=format&fit=crop&w=400&h=400&q=80"
        rating_val = round(random.uniform(4.3, 4.9), 1)
        c.execute(
            "INSERT INTO products (name, category, price, description, rating, image_url) VALUES (?, ?, ?, ?, ?, ?)",
            (name, "Mobile Phone", price, desc, rating_val, image_url)
        )

    # 100 Custom Matching Clothing Products
    custom_clothing = [
        # Jackets & Outerwear (20 items)
        ("Leather Biker Jacket", 149.99, "photo-1551028719-00167b16eac5", "Premium genuine leather biker jacket with asymmetrical zip closure and quilted lining."),
        ("Denim Trucker Jacket", 79.99, "photo-1576995853123-5a10305d93c0", "Classic vintage wash denim jacket with button chest pockets and durable brass hardware."),
        ("Waterproof Windbreaker", 59.99, "photo-1544441893-675973e31985", "Lightweight hooded rain jacket with sealed seams and breathable mesh interior."),
        ("Winter Parka Coat", 129.99, "photo-1539533018447-63fcce2678e3", "Heavyweight insulated winter coat with faux-fur trim hood and deep fleece-lined pockets."),
        ("Puffer Down Jacket", 99.99, "photo-1548883354-7622d03aca27", "Quilted puffer jacket packed with lightweight warm down insulation."),
        ("Wool Trench Coat", 169.99, "photo-1515886657613-9f3515b0c78f", "Elegant double-breasted wool blend trench coat with removable waist belt."),
        ("Bomber Flight Jacket", 69.99, "photo-1591047139829-d91aecb6caea", "Classic military-style nylon bomber jacket with ribbed collar and utility arm pocket."),
        ("Sherpa Lined Fleece Jacket", 54.99, "photo-1591047139829-d91aecb6caea", "Ultra-cozy sherpa fleece jacket with full front zipper and zippered hand pockets."),
        ("Lightweight Anorak", 49.99, "photo-1578587018452-892bacefd3f2", "Casual pullover anorak jacket with front pouch pocket and adjustable drawstring hem."),
        ("Tailored Suit Blazer", 119.99, "photo-1507679799987-c73779587ccf", "Slim-fit structured suit blazer jacket with notch lapel and inner pocket details."),
        ("Corduroy Trucker Jacket", 64.99, "photo-1512436991641-6745cdb1723f", "Soft ribbed corduroy jacket with warm fleece collar lining."),
        ("Oversized Cardigan Coat", 59.99, "photo-1434389677669-e08b4cac3105", "Chic open-front knit cardigan with relaxed dropped shoulders."),
        ("Quilted Vest Bodywarmer", 44.99, "photo-1521572267360-ee0c2909d518", "Sleeveless insulated vest perfect for seasonal layering over hoodies."),
        ("Suede Biker Jacket", 139.99, "photo-1520975954732-35dd22299614", "Soft brushed suede leather jacket with silver metal hardware."),
        ("Wool Peacoat", 149.99, "photo-1539533018447-63fcce2678e3", "Classic nautical double-breasted navy blue wool peacoat."),
        ("Waterproof Running Jacket", 49.99, "photo-1542291026-7eec264c27ff", "Reflective ultra-light running jacket for night workouts."),
        ("Fleece Zip Hoodie Jacket", 39.99, "photo-1556905055-8f358a7a47b2", "Heavyweight fleece hoodie with full zip and split kangaroo pocket."),
        ("Denim Shearling Jacket", 89.99, "photo-1576995853123-5a10305d93c0", "Heavy denim jacket lined with thick plush shearling fleece."),
        ("Casual Linen Blazer", 79.99, "photo-1507679799987-c73779587ccf", "Breathable summer linen blazer ideal for smart-casual outings."),
        ("Tracksuit Top Jacket", 34.99, "photo-1515886657613-9f3515b0c78f", "Retro athletic track jacket with contrast side sleeve stripes."),

        # Hoodies & Sweaters (20 items)
        ("Premium Pullover Hoodie", 44.99, "photo-1556905055-8f358a7a47b2", "Plush cotton-blend hoodie with double-lined hood and spacious front pouch."),
        ("Oversized Crewneck Sweatshirt", 39.99, "photo-1578632767115-351597cf2477", "Relaxed fit fleece crewneck sweatshirt with ribbed cuffs and hem."),
        ("Cable Knit Wool Sweater", 54.99, "photo-1620799140408-edc6dcb6d633", "Cozy chunky cable-knit wool sweater with classic crew neckline."),
        ("Graphic Print Streetwear Hoodie", 49.99, "photo-1509967419530-da38b4704bc6", "Streetwear cotton hoodie featuring custom screen-printed back graphics."),
        ("Turtleneck Ribbed Sweater", 49.99, "photo-1434389677669-e08b4cac3105", "Fitted rib-knit turtleneck sweater crafted from soft breathable yarn."),
        ("Half-Zip Fleece Pullover", 42.99, "photo-1556821840-3a63f15732ce", "Thermal polar fleece pullover with stand collar and 1/2 zip neck."),
        ("Vintage Wash Sweatshirt", 44.99, "photo-1578632767115-351597cf2477", "Pigment-dyed vintage aesthetic fleece sweatshirt with worn-in feel."),
        ("Cashmere Crew Sweater", 89.99, "photo-1620799140408-edc6dcb6d633", "100% pure cashmere luxury sweater offering unparalleled softness."),
        ("Cropped Fleece Hoodie", 34.99, "photo-1556905055-8f358a7a47b2", "Trendy cropped hoodie with raw-edge hem and drawstring hood."),
        ("V-Neck Pullover Sweater", 39.99, "photo-1434389677669-e08b4cac3105", "Classic V-neck pullover sweater made from lightweight cotton-acrylic yarn."),
        ("Heavyweight Thermal Henley", 32.99, "photo-1521572267360-ee0c2909d518", "Waffle-weave thermal henley shirt with 3-button placket."),
        ("Zip-Up Knit Cardigan", 49.99, "photo-1434389677669-e08b4cac3105", "Full-zip knit cardigan with stand collar and ribbed trim."),
        ("Tie-Dye Pullover Hoodie", 42.99, "photo-1509967419530-da38b4704bc6", "Vibrant hand-dyed tie-dye hoodie made with ultra-soft fleece."),
        ("Fleece Quarter-Snap Pullover", 38.99, "photo-1618354691373-d851c5c3a990", "Retro fleece pullover with snap-button placket and chest pocket."),
        ("Oversized Knit Jumper", 47.99, "photo-1620799140408-edc6dcb6d633", "Slouchy oversized knit jumper sweater in neutral earth tones."),
        ("Tech Fleece Zip Jacket", 59.99, "photo-1556905055-8f358a7a47b2", "Sleek tech fleece zip jacket with zippered sleeve pocket."),
        ("Knit Sweater Vest", 34.99, "photo-1434389677669-e08b4cac3105", "Preppy V-neck sweater vest crafted with soft cotton knit."),
        ("Striped Crew Sweatshirt", 36.99, "photo-1578632767115-351597cf2477", "Classic nautical Breton striped crewneck sweatshirt."),
        ("Fleece Sherpa Hoodie", 49.99, "photo-1556905055-8f358a7a47b2", "Double-sided sherpa fleece hoodie for cold winter days."),
        ("Lightweight Knit Pullover", 29.99, "photo-1434389677669-e08b4cac3105", "Fine gauge knit pullover shirt for mild spring layering."),

        # T-Shirts & Tops (20 items)
        ("Heavyweight Cotton T-Shirt", 24.99, "photo-1521572267360-ee0c2909d518", "100% combed cotton heavy tee with reinforced collar stitching."),
        ("Slim Fit Graphic Tee", 22.99, "photo-1503342217505-b0a15ec3261c", "Soft cotton jersey t-shirt with minimal modern chest graphic print."),
        ("Performance Athletic Shirt", 19.99, "photo-1518611012118-696072aa579a", "Moisture-wicking quick-dry workout t-shirt with 4-way stretch."),
        ("Vintage Rock Band Tee", 27.99, "photo-1503342217505-b0a15ec3261c", "Distressed retro graphic tee with vintage stonewashed treatment."),
        ("Organic Cotton V-Neck Tee", 19.99, "photo-1521572267360-ee0c2909d518", "Ultra-soft 100% organic cotton V-neck t-shirt."),
        ("Long Sleeve Pocket Tee", 26.99, "photo-1503342217505-b0a15ec3261c", "Durable long sleeve t-shirt featuring single chest pocket."),
        ("Oversized Streetwear Tee", 28.99, "photo-1521572267360-ee0c2909d518", "Boxy fit heavy cotton t-shirt with dropped shoulder silhouette."),
        ("Linen Button-Down Shirt", 49.99, "photo-1596755094514-f87e34085b2c", "Breathable 100% natural linen short-sleeve button-up shirt."),
        ("Classic Oxford Cotton Shirt", 44.99, "photo-1598033129183-c4f50c736f10", "Timeless button-down Oxford shirt with chest pocket and curved hem."),
        ("Casual Flannel Plaid Shirt", 39.99, "photo-1602810318383-e386cc2a3ccf", "Soft brushed cotton flannel shirt in classic buffalo check plaid."),
        ("Ribbed Cotton Crop Top", 17.99, "photo-1503342217505-b0a15ec3261c", "Stretchy ribbed cotton crop top with crew neckline."),
        ("Silk Button-Front Blouse", 59.99, "photo-1596755094514-f87e34085b2c", "Elegant Mulberry silk button-front blouse with button cuffs."),
        ("Striped Mariner Long Sleeve", 29.99, "photo-1503342217505-b0a15ec3261c", "Classic navy and white nautical striped long sleeve shirt."),
        ("Seamless Athletic Tank Top", 18.99, "photo-1518611012118-696072aa579a", "Breathable athletic tank top with racerback design."),
        ("Chambray Denim Button Shirt", 42.99, "photo-1576995853123-5a10305d93c0", "Mid-weight chambray denim shirt with pearl snap buttons."),
        ("Floral Print Hawaiian Shirt", 32.99, "photo-1596755094514-f87e34085b2c", "Tropical floral short-sleeve resort shirt made from silky rayon."),
        ("Thermal Waffle Long Sleeve", 28.99, "photo-1521572267360-ee0c2909d518", "Insulating waffle knit long-sleeve tee for cold weather layering."),
        ("Cotton Piqué Polo Shirt", 34.99, "photo-1586363104862-3a5e2ab60d99", "Cotton piqué polo shirt with ribbed collar and 2-button placket."),
        ("Relaxed Summer Linen Tank", 21.99, "photo-1596755094514-f87e34085b2c", "Lightweight summer linen tank top with scooped neckline."),
        ("Compression Workout Shirt", 24.99, "photo-1518611012118-696072aa579a", "Ergonomic compression shirt boosting blood flow during workouts."),

        # Pants & Bottoms (20 items)
        ("Slim Fit Stretch Jeans", 59.99, "photo-1541099649105-f69ad21f3246", "Dark wash denim jeans featuring 5-pocket styling and stretch comfort."),
        ("Straight Leg Vintage Jeans", 64.99, "photo-1560243563-062bfc001d68", "100% rigid cotton classic 90s straight leg blue denim jeans."),
        ("Relaxed Fit Cargo Pants", 49.99, "photo-1624378439575-d8705ad7ae80", "Durable cotton twill cargo pants with multiple utility pockets."),
        ("Tailored Stretch Chino Pants", 44.99, "photo-1473966968600-fa801b869a1a", "Versatile flat-front stretch chino pants suitable for work and weekend."),
        ("Fleece Jogger Sweatpants", 34.99, "photo-1552902865-b72c031ac5ea", "Soft fleece joggers with elastic drawstring waist and cuffed ankles."),
        ("Athletic Workout Leggings", 32.99, "photo-1506629082955-511b1aa562c8", "High-waisted squat-proof leggings with side phone pockets."),
        ("Ripped Black Skinny Jeans", 54.99, "photo-1541099649105-f69ad21f3246", "Black stretch denim jeans with distressed knee blowouts."),
        ("Wide Leg Linen Trousers", 46.99, "photo-1473966968600-fa801b869a1a", "Flowy wide-leg linen pants with elastic waist and side pockets."),
        ("Pleated Dress Trousers", 69.99, "photo-1507679799987-c73779587ccf", "Formal double-pleated suit trousers with creased legs."),
        ("Corduroy Straight Trousers", 48.99, "photo-1541099649105-f69ad21f3246", "Fine-wale corduroy trousers in warm chestnut brown."),
        ("High-Waist Mom Jeans", 58.99, "photo-1541099649105-f69ad21f3246", "High-rise tapered leg vintage wash denim jeans."),
        ("Athletic Tracksuit Pants", 32.99, "photo-1552902865-b72c031ac5ea", "Retro nylon track pants with zip ankles and mesh lining."),
        ("Tactile Cargo Joggers", 42.99, "photo-1624378439575-d8705ad7ae80", "Streetwear tactical cargo joggers with strap details."),
        ("Faux Leather Biker Pants", 129.99, "photo-1541099649105-f69ad21f3246", "Faux leather fitted biker pants with knee panel details."),
        ("Casual Twill Shorts", 24.99, "photo-1591195853828-11db59a44f6b", "Lightweight cotton twill casual shorts with elastic waistband."),
        ("Athletic Running Shorts", 22.99, "photo-1591195853828-11db59a44f6b", "Quick-dry workout shorts with built-in compression liner."),
        ("Distressed Denim Shorts", 29.99, "photo-1591195853828-11db59a44f6b", "High-waisted distressed denim shorts with frayed hems."),
        ("Smart Bermuda Shorts", 34.99, "photo-1591195853828-11db59a44f6b", "Knee-length smart Bermuda shorts in stretch cotton twill."),
        ("Seamless Yoga Leggings", 28.99, "photo-1506629082955-511b1aa562c8", "Ultra-soft contouring seamless leggings for yoga and gym."),
        ("Plaid Flannel Lounge Pants", 26.99, "photo-1552902865-b72c031ac5ea", "Warm plaid cotton flannel lounge pants with drawstring waist."),

        # Dresses, Skirts & Accessories (20 items)
        ("Floral Print Midi Dress", 54.99, "photo-1572804013309-59a88b7e92f1", "Chiffon floral midi dress with A-line skirt and ruffle sleeves."),
        ("Satin Evening Gown", 99.99, "photo-1566174053879-31528523f8ae", "Floor-length cowl neck satin dress in emerald green."),
        ("Casual T-Shirt Dress", 32.99, "photo-1515886657613-9f3515b0c78f", "Relaxed fit jersey t-shirt dress with side slit."),
        ("Denim Button Mini Skirt", 39.99, "photo-1583496661160-fb5886a0aaaa", "Classic high-waisted denim mini skirt with front button closure."),
        ("Pleated Tennis Skirt", 29.99, "photo-1583496661160-fb5886a0aaaa", "Preppy high-waisted pleated skirt with built-in shorts."),
        ("Satin Wrap Midi Skirt", 42.99, "photo-1583496661160-fb5886a0aaaa", "Silky wrap skirt with side tie waist in champagne gold."),
        ("White Leather Sneakers", 79.99, "photo-1549298916-b41d501d3772", "Clean minimalist low-top leather sneakers with cushioned footbed."),
        ("Mesh Athletic Running Shoes", 89.99, "photo-1542291026-7eec264c27ff", "Lightweight mesh running sneakers with responsive foam sole."),
        ("Chelsea Leather Boots", 119.99, "photo-1608256246200-53e635b5b65f", "Genuine leather Chelsea boots with elastic side gores and pull tab."),
        ("High Top Canvas Sneakers", 59.99, "photo-1525966222134-fcfa99b8ae77", "Classic high-top canvas sneakers with rubber toe cap."),
        ("Heeled Ankle Strap Sandals", 49.99, "photo-1543163521-1bf539c55dd2", "Elegant block heel sandals with adjustable ankle buckle."),
        ("Heavy-Duty Canvas Tote Bag", 24.99, "photo-1553062407-98eeb64c6a62", "Heavy-duty canvas shopping tote bag with inner zipper pocket."),
        ("Leather Crossbody Bag", 69.99, "photo-1548036328-c9fa89d128fa", "Compact leather shoulder bag with adjustable strap and magnetic flap."),
        ("Wool Felt Fedora Hat", 34.99, "photo-1534215754734-18e55d13e346", "Stylish wide-brim wool felt fedora with leather band."),
        ("Ribbed Cuff Knit Beanie", 19.99, "photo-1576871337632-b9aef4c17ab9", "Warm ribbed cuff beanie hat made with soft acrylic knit."),
        ("Genuine Leather Dress Belt", 29.99, "photo-1553062407-98eeb64c6a62", "Full-grain genuine leather belt with polished silver buckle."),
        ("Warm Wool Fringe Scarf", 27.99, "photo-1520903920243-00d872a2d1c9", "Soft warm winter scarf with tassel fringe edges."),
        ("Wayfarer Polarized Sunglasses", 39.99, "photo-1572635196237-14b3f281503f", "Classic wayfarer polarized sunglasses with UV400 lenses."),
        ("Knee-High Leather Riding Boots", 149.99, "photo-1608256246200-53e635b5b65f", "Knee-high genuine leather riding boots with side zipper."),
        ("Comfort Slide Sandals", 29.99, "photo-1543163521-1bf539c55dd2", "Comfortable molded footbed slide sandals for pool and beach.")
    ]

    for c_idx, (name, price, photo_id, desc) in enumerate(custom_clothing, start=61):
        image_url = f"https://images.unsplash.com/{photo_id}?auto=format&fit=crop&w=400&h=400&q=80"
        rating_val = round(random.uniform(4.2, 4.9), 1)
        c.execute(
            "INSERT INTO products (name, category, price, description, rating, image_url) VALUES (?, ?, ?, ?, ?, ?)",
            (name, "Clothing", price, desc, rating_val, image_url)
        )

    # Additional Mobile Phones (40 items -> 50 total Mobile Phones)
    more_mobiles = [
        ("Samsung Galaxy S23 Ultra", 999.99, "photo-1610945265064-0e34e5519bbf", "Flagship Samsung smartphone with 200MP camera and Snapdragon 8 Gen 2."),
        ("iPhone 14 Pro Max", 899.99, "photo-1695048133142-1a20484d2569", "Apple smartphone with Dynamic Island, A16 Bionic chip, and Pro camera system."),
        ("Google Pixel 8", 699.00, "photo-1598327105666-5b89351aff97", "Google AI-powered smartphone with Tensor G3 chip and Best Take photo tools."),
        ("OnePlus 11 5G", 699.99, "photo-1565630916779-e303be97b6f5", "High-speed smartphone with 100W charging and Hasselblad color calibration."),
        ("Nothing Phone (2)", 599.99, "photo-1511707171634-5f897ff02aa9", "Unique smartphone featuring transparent back with Glyph LED lighting interface."),
        ("Motorola Edge 40 Pro", 649.99, "photo-1510557880182-3d4d3cba35a5", "Curved 165Hz display smartphone with 125W TurboPower superfast charging."),
        ("Sony Xperia 1 V", 1199.99, "photo-1511707171634-5f897ff02aa9", "4K OLED smartphone tailored for creators with Exmor T mobile sensor."),
        ("Asus ROG Phone 7 Ultimate", 1299.99, "photo-1565630916779-e303be97b6f5", "Ultimate gaming smartphone with AirTrigger ultrasonic controls and active cooling."),
        ("iPhone 15 Plus", 899.99, "photo-1695048133142-1a20484d2569", "Large 6.7-inch display Apple smartphone with all-day battery life."),
        ("Samsung Galaxy Z Flip 5", 999.99, "photo-1610945265064-0e34e5519bbf", "Compact foldable smartphone featuring large Flex Window cover screen."),
        ("Xiaomi 13 Ultra", 949.99, "photo-1511707171634-5f897ff02aa9", "Quad-camera Leica smartphone with 1-inch variable aperture main sensor."),
        ("Realme GT 5 Pro", 599.99, "photo-1510557880182-3d4d3cba35a5", "Flagship killer phone with 4500 nits bright AMOLED screen."),
        ("Honor Magic 5 Pro", 849.99, "photo-1565630916779-e303be97b6f5", "Falcon Capture camera smartphone with LTPO curved display."),
        ("Vivo X90 Pro+", 999.99, "photo-1511707171634-5f897ff02aa9", "Zeiss optics smartphone with V2 ISP image processing chip."),
        ("Poco F5 Pro", 499.99, "photo-1598327105666-5b89351aff97", "WQHD+ 120Hz AMOLED smartphone with Snapdragon 8+ Gen 1."),
        ("Motorola Razr 40 Ultra", 899.99, "photo-1510557880182-3d4d3cba35a5", "Iconic flip phone with full outer interactive display."),
        ("iPhone 13 Mini", 549.99, "photo-1695048133142-1a20484d2569", "Pocket-sized 5.4-inch Super Retina XDR Apple smartphone."),
        ("Samsung Galaxy S23 FE", 599.99, "photo-1610945265064-0e34e5519bbf", "Fan Edition smartphone with pro-grade camera and long battery life."),
        ("Google Pixel 7 Pro", 649.00, "photo-1598327105666-5b89351aff97", "Telephoto 5x optical zoom smartphone with Real Tone video features."),
        ("OnePlus Nord 3", 449.99, "photo-1565630916779-e303be97b6f5", "Fluid 120Hz display smartphone with Sony IMX890 OIS camera."),
        ("ZTE Nubia Z60 Ultra", 749.99, "photo-1511707171634-5f897ff02aa9", "Under-display selfie camera smartphone with 6000mAh battery."),
        ("Xiaomi Redmi Note 13 Pro+", 399.99, "photo-1510557880182-3d4d3cba35a5", "200MP camera smartphone with 120W HyperCharge fast battery filler."),
        ("Samsung Galaxy A34 5G", 349.99, "photo-1610945265064-0e34e5519bbf", "Vibrant 120Hz AMOLED smartphone with IP67 water resistance."),
        ("Motorola Moto G84", 299.99, "photo-1598327105666-5b89351aff97", "Vegan leather finish smartphone with 50MP OIS camera."),
        ("iPhone 14", 699.99, "photo-1695048133142-1a20484d2569", "Dual-camera Apple smartphone with Crash Detection safety feature."),
        ("OnePlus 12R", 499.99, "photo-1565630916779-e303be97b6f5", "Performance-focused smartphone with LTPO4 120Hz display."),
        ("Google Pixel 6a", 329.00, "photo-1598327105666-5b89351aff97", "Compact Google Tensor smartphone with night sight camera."),
        ("Samsung Galaxy M54", 379.99, "photo-1610945265064-0e34e5519bbf", "Powerhouse smartphone featuring massive 6000mAh battery capacity."),
        ("Poco X6 Pro", 319.99, "photo-1511707171634-5f897ff02aa9", "Dimensity 8300-Ultra gaming smartphone with WildBoost optimization."),
        ("Honor 90 5G", 429.99, "photo-1510557880182-3d4d3cba35a5", "200MP eye-risk free PWM dimming display smartphone."),
        ("Sony Xperia 10 V", 399.99, "photo-1565630916779-e303be97b6f5", "Ultra-lightweight 159g 5G smartphone with front stereo speakers."),
        ("Asus Zenfone 10", 699.99, "photo-1511707171634-5f897ff02aa9", "Compact 5.9-inch one-handed flagship smartphone with 6-Axis Gimbal."),
        ("Oppo Find N3 Flip", 999.99, "photo-1598327105666-5b89351aff97", "Triple-camera Hasselblad foldable smartphone."),
        ("Fairphone 5", 649.99, "photo-1510557880182-3d4d3cba35a5", "Sustainable modular smartphone with 10-year software support."),
        ("Nokia X30 5G", 349.99, "photo-1565630916779-e303be97b6f5", "100% recycled aluminum frame eco-friendly smartphone."),
        ("Realme 11 Pro+", 369.99, "photo-1511707171634-5f897ff02aa9", "Curved 120Hz OLED smartphone with Gucci-designer leather back."),
        ("Infinix Zero 30 5G", 299.99, "photo-1598327105666-5b89351aff97", "Vlogging smartphone with 4K 60fps front camera recording."),
        ("TCL 40 NxtPaper", 229.99, "photo-1510557880182-3d4d3cba35a5", "Paper-like anti-glare display smartphone for eye protection."),
        ("Sharp Aquos R8 Pro", 899.99, "photo-1565630916779-e303be97b6f5", "1-inch image sensor smartphone with IGZO OLED 240Hz screen."),
        ("Xiaomi 13T Pro", 649.99, "photo-1511707171634-5f897ff02aa9", "Leica Summicron lens smartphone with 120W fast charging.")
    ]

    # Additional Electronics (35 items -> 50+ total Electronics)
    more_electronics = [
        ("Sony WH-1000XM5 Headphones", 398.00, "photo-1505740420928-5e560c06d30e", "Industry-leading noise canceling wireless headphones with Auto NC Optimizer."),
        ("Bose QuietComfort Ultra Headphones", 429.00, "photo-1546435770-a3e426bf472b", "Immersive audio Spatial sound wireless headphones."),
        ("Apple AirPods Pro (2nd Gen)", 249.00, "photo-1600294037681-c80b4cb5b434", "Active Noise Cancellation earbuds with Adaptive Audio and MagSafe Case."),
        ("Apple MacBook Pro 16 M3 Max", 3499.00, "photo-1517336714731-489689fd1ca8", "Ultimate developer laptop with 16-core CPU and 40-core GPU."),
        ("Dell XPS 15 Laptop", 1899.00, "photo-1593642632823-8f785ba67e45", "OLED touch display laptop with 13th Gen Intel i9 processor."),
        ("ASUS ROG Zephyrus G14 Laptop", 1599.99, "photo-1603302576837-37561b2e2302", "Ultra-thin gaming laptop with RTX 4070 graphics and AniMe Matrix lid."),
        ("LG C3 65 OLED 4K Smart TV", 1699.99, "photo-1593359677879-a4bb92f829d1", "Self-lit OLED 4K TV with α9 AI Processor Gen6 and 120Hz gaming mode."),
        ("Samsung Odyssey OLED G9 Monitor", 1299.99, "photo-1527443224154-c4a3942d3acf", "49-inch dual QHD curved OLED 240Hz gaming monitor."),
        ("Apple Watch Ultra 2", 799.00, "photo-1510017803434-a899398421b3", "Rugged titanium smartwatch with precision dual-frequency GPS."),
        ("Samsung Galaxy Watch 6 Classic", 399.99, "photo-1508685096489-7aacd43bd3b1", "Rotating bezel smartwatch with bioelectrical impedance analysis sensor."),
        ("Garmin Fenix 7X Pro Solar", 899.99, "photo-1523275335684-37898b6baf30", "Multisport GPS smartwatch with solar charging lens and LED flashlight."),
        ("Logitech MX Master 3S Mouse", 999.99, "photo-1615663245857-ac93bb7c39e7", "Quiet clicks ergonomic wireless mouse with 8K DPI sensor."),
        ("Keychron Q1 Pro Keyboard", 199.99, "photo-1587829741301-dc798b83add3", "Full aluminum QMK/VIA wireless custom mechanical keyboard."),
        ("JBL Charge 5 Bluetooth Speaker", 179.95, "photo-1545454675-3531b543be5d", "IP67 waterproof speaker with built-in powerbank."),
        ("Sonos Move 2 Smart Speaker", 449.00, "photo-1545454675-3531b543be5d", "Stereo sound weather-resistant portable smart speaker."),
        ("GoPro HERO12 Black Action Camera", 399.99, "photo-1526170375885-4d8ecf77b99f", "5.3K video action camera with HyperSmooth 6.0 stabilization."),
        ("DJI Mini 4 Pro Drone", 759.00, "photo-1527977966376-1c8408f9f108", "Sub-249g drone with omnidirectional obstacle sensing and 4K HDR video."),
        ("Canon EOS R6 Mark II Camera", 2499.00, "photo-1516035069371-29a1b244cc32", "Full-frame mirrorless camera shooting 40 fps continuous RAW."),
        ("Sony Alpha A7 IV Camera", 2498.00, "photo-1516035069371-29a1b244cc32", "33MP BSI full-frame camera with real-time eye autofocus."),
        ("iPad Pro 12.9 M2 Tablet", 1099.00, "photo-1544244015-0df4b3ffc6b0", "Liquid Retina XDR mini-LED display tablet powered by M2 chip."),
        ("Samsung Galaxy Tab S9 Ultra", 1199.99, "photo-1544244015-0df4b3ffc6b0", "Massive 14.6-inch Dynamic AMOLED 2X tablet with S Pen included."),
        ("Anker 737 Power Bank 24000mAh", 149.99, "photo-1609091839311-d5365f9ff1c5", "140W bi-directional fast charging portable battery pack."),
        ("Blue Yeti USB Microphone", 129.99, "photo-1590658268037-6bf12165a8df", "Multi-pattern condenser microphone for streaming and podcasting."),
        ("Shure SM7B Vocal Microphone", 399.00, "photo-1590658268037-6bf12165a8df", "Broadcast studio dynamic microphone with smooth warm response."),
        ("Elgato Stream Deck MK.2", 149.99, "photo-1615663245857-ac93bb7c39e7", "15 customizable macro keys studio controller for live streamers."),
        ("Razer BlackShark V2 Pro Headset", 199.99, "photo-1505740420928-5e560c06d30e", "HyperSpeed 2.4GHz wireless esports gaming headset."),
        ("Meta Quest 3 VR Headset", 499.99, "photo-1592478411213-6153e4ebc07d", "Breakthrough mixed reality VR headset with pancake optics."),
        ("Nintendo Switch OLED Console", 349.99, "photo-1578303512597-81e6cc155b3e", "Handheld gaming console with 7-inch vivid OLED screen."),
        ("PlayStation 5 Console", 499.99, "photo-1606813907291-d86efa9b94db", "Next-gen console with DualSense haptic triggers and ultra-fast SSD."),
        ("Xbox Series X Console", 499.99, "photo-1606813907291-d86efa9b94db", "12 teraflops 4K 120fps gaming console with Velocity Architecture."),
        ("Seagate Expansion 5TB HDD", 119.99, "photo-1544244015-0df4b3ffc6b0", "High capacity USB 3.0 external portable hard drive."),
        ("Samsung T7 Shield 2TB SSD", 159.99, "photo-1544244015-0df4b3ffc6b0", "IP65 rubberized rugged portable SSD with up to 1050MB/s transfers."),
        ("TP-Link WiFi 6 Mesh Router", 199.99, "photo-1544197150-b99a580bb7a8", "Deco AX3000 whole home mesh WiFi 6 system covering 5000 sq ft."),
        ("BenQ 4K Laser Projector", 1499.00, "photo-1517694712202-14dd9538aa97", "Home theater 3200 ANSI lumen 4K projector with Android TV."),
        ("Anker Soundcore Motion X600", 199.99, "photo-1545454675-3531b543be5d", "Hi-Res spatial audio portable bluetooth speaker with 5 drivers.")
    ]

    # Additional Home & Kitchen (40 items -> 50+ total Home & Kitchen)
    more_home = [
        ("Breville Barista Touch Espresso", 999.95, "photo-1517668808822-9ebb02f2a0e6", "Automated touch screen espresso machine with integrated grinder."),
        ("Nespresso VertuoPlus Coffee Maker", 169.00, "photo-1517668808822-9ebb02f2a0e6", "Single-serve coffee and espresso machine using Centrifusion technology."),
        ("Ninja Foodi 10-in-1 Pressure Cooker", 199.99, "photo-1585515320310-259814833e62", "Multi-cooker that pressure cooks and air fries with TenderCrisp Tech."),
        ("Cosori Dual Blaze Air Fryer", 149.99, "photo-1585515320310-259814833e62", "6.8-Quart smart air fryer with dual heating elements."),
        ("Vitamix A3500 Ascent Blender", 649.95, "photo-1585515320310-259814833e62", "Professional-grade high performance blender with wireless connectivity."),
        ("KitchenAid Artisan 5-Qt Mixer", 449.99, "photo-1594385208974-2e75f8d7bb48", "Iconic tilt-head stand mixer with 10 speed settings."),
        ("Dyson V15 Detect Cordless Vacuum", 749.99, "photo-1558317374-067fb5f30001", "Intelligent cordless vacuum with laser illumination for microscopic dust."),
        ("iRobot Roomba j7+ Robot Vacuum", 799.00, "photo-1558317374-067fb5f30001", "Self-emptying robot vacuum with PrecisionVision obstacle avoidance."),
        ("Le Creuset Enameled Dutch Oven", 419.95, "photo-1584992236310-6edddc08acff", "5.5-Qt French enameled cast iron round Dutch oven in Cerise Red."),
        ("All-Clad D3 Stainless Cookware", 699.99, "photo-1584992236310-6edddc08acff", "10-piece tri-ply bonded stainless steel pots and pans set."),
        ("Instant Pot Duo 7-in-1 Cooker", 89.99, "photo-1585515320310-259814833e62", "Versatile 6-Quart electric pressure cooker and slow cooker."),
        ("Cuisinart 14-Cup Food Processor", 249.95, "photo-1594385208974-2e75f8d7bb48", "Heavy-duty food processor with stainless steel chopping blade."),
        ("Fellow Stagg EKG Electric Kettle", 165.00, "photo-1517668808822-9ebb02f2a0e6", "Gooseneck pour-over electric kettle with variable temperature control."),
        ("Balmuda The Toaster", 299.00, "photo-1585515320310-259814833e62", "Steam technology toaster oven restoring freshly baked bread texture."),
        ("SodaStream Art Sparkling Maker", 129.99, "photo-1517668808822-9ebb02f2a0e6", "Retro lever sparkling water maker with dishwasher safe bottle."),
        ("Philips Sonicare 9900 Toothbrush", 379.96, "photo-1558317374-067fb5f30001", "SenseIQ AI electric toothbrush with dynamic pressure feedback."),
        ("Dyson Purifier Hot+Cool Fan", 749.99, "photo-1558317374-067fb5f30001", "HEPA air purifier, space heater, and cooling fan in one."),
        ("Leviathan Ergonomic Desk Lamp", 79.99, "photo-1507473885765-e6ed057f782c", "Dimmable LED architect desk lamp with wireless phone charger."),
        ("Artificial Monstera Plant", 49.99, "photo-1485955900006-10f4d324d411", "Realistic 4-foot indoor artificial Swiss cheese plant in pot."),
        ("Memory Foam Contour Pillow", 39.99, "photo-1631048835583-48b573498e8d", "Ergonomic cervical orthopedic neck support bed pillow."),
        ("Luxury Egyptian Cotton Sheets", 129.99, "photo-1617050318658-a9a3175474d8", "1000 thread count deep pocket sateen bed sheet set."),
        ("Weighted Blanket 15lbs", 69.99, "photo-1580552025938-a7f00e1bcd87", "Glass bead heavy soothing pressure blanket with washable cover."),
        ("Bamboo Knife Block Set", 99.99, "photo-1584992236310-6edddc08acff", "15-piece German stainless steel kitchen knife set."),
        ("Non-Stick Ceramic Frying Pans", 79.99, "photo-1584992236310-6edddc08acff", "Toxin-free nonstick ceramic skillet 2-piece set."),
        ("Digital Kitchen Food Scale", 19.99, "photo-1585515320310-259814833e62", "High precision 11lb electronic cooking measure scale."),
        ("Automatic Milk Frother", 39.99, "photo-1517668808822-9ebb02f2a0e6", "Electric hot and cold foam maker for lattes and cappuccinos."),
        ("Electric Wine Opener Set", 29.99, "photo-1517668808822-9ebb02f2a0e6", "Rechargeable automatic corkscrew with foil cutter and aerator."),
        ("Stainless Steel Trash Can 50L", 89.99, "photo-1558317374-067fb5f30001", "Fingerprint-proof step kitchen garbage bin with soft close lid."),
        ("Microfiber Cleaning Cloths", 14.99, "photo-1558317374-067fb5f30001", "Ultra-absorbent lint-free microfiber towels 24-pack."),
        ("Silicone Cooking Utensil Set", 29.99, "photo-1584992236310-6edddc08acff", "Heat resistant non-stick kitchen spatula and turner set."),
        ("Glass Food Storage Containers", 34.99, "photo-1584992236310-6edddc08acff", "Leakproof glass meal prep containers with locking lids 18-pack."),
        ("Dish Drying Rack Stainless", 42.99, "photo-1584992236310-6edddc08acff", "2-tier rustproof dish drainer with utensil holder."),
        ("Handheld Garment Steamer", 39.99, "photo-1558317374-067fb5f30001", "Fast heat-up portable clothing fabric steam remover."),
        ("Ultrasonic Oil Diffuser", 27.99, "photo-1507473885765-e6ed057f782c", "Aromatherapy cool mist humidifier with 7 color LED lights."),
        ("Scented Soy Candle Gift Set", 24.99, "photo-1507473885765-e6ed057f782c", "Natural aromatherapy soy candles in decorative tins 4-pack."),
        ("Velvet Accent Armchair", 199.99, "photo-1586023492125-27b2c045efd7", "Mid-century modern soft velvet club chair with gold legs."),
        ("Mid-Century Coffee Table", 149.99, "photo-1555041469-a586c61ea9bc", "Solid wood oval living room cocktail table."),
        ("Full Length Floor Mirror", 119.99, "photo-1618220252344-8ec99ec624b1", "Arched aluminum alloy frame standing dressing mirror."),
        ("Woven Storage Baskets", 32.99, "photo-1485955900006-10f4d324d411", "Natural cotton rope laundry and toy organizer baskets 3-pack."),
        ("Blackout Window Curtains", 39.99, "photo-1558618666-fcd25c85cd64", "Thermal insulated noise reducing grommet curtain drapes.")
    ]

    # Additional Sports & Outdoors (42 items -> 50+ total Sports & Outdoors)
    more_sports = [
        ("Bowflex SelectTech 552 Dumbbells", 429.00, "photo-1584735935682-2f2b69dff9d2", "Adjustable dumbbells changing weight from 5 to 52.5 lbs."),
        ("Lululemon Align Yoga Pants", 118.00, "photo-1506629082955-511b1aa562c8", "Buttery soft Nulu fabric high-rise athletic leggings."),
        ("Manduka PRO Yoga Mat 6mm", 138.00, "photo-1601925260368-ae2f83cf8b7f", "High-density cushioned non-slip joint protection workout mat."),
        ("Hydro Flask 32 oz Bottle", 44.95, "photo-1602143407151-7111542de6e8", "TempShield vacuum insulated stainless steel water bottle."),
        ("YETI Tundra 45 Cooler", 325.00, "photo-1527016021513-b09758b777bd", "Rotomolded ice chest with PermaFrost insulation."),
        ("Coleman Sundome 4-Person Tent", 89.99, "photo-1504280390367-361c6d9f38f4", "WeatherTec system waterproof dome camping tent."),
        ("Osprey Atmos AG 65 Backpack", 340.00, "photo-1553062407-98eeb64c6a62", "Anti-Gravity mesh suspension expedition hiking backpack."),
        ("Garmin Edge 540 Bike Computer", 349.99, "photo-1485965120184-e220f721d03e", "Solar charging GPS cycling computer with stamina insights."),
        ("Trek FX 3 Disc Fitness Bike", 1049.99, "photo-1485965120184-e220f721d03e", "Performance hybrid aluminum bicycle with hydraulic disc brakes."),
        ("NordicTrack 2450 Treadmill", 2499.00, "photo-1590487988256-9ed24133863e", "22-inch HD tilt touchscreen foldable running treadmill."),
        ("Concept2 Model D Rowing Machine", 990.00, "photo-1534258936925-c58bed479fcb", "Indoor air resistance rower with PM5 performance monitor."),
        ("TRX PRO4 Suspension Trainer", 249.95, "photo-1584735935682-2f2b69dff9d2", "Bodyweight workout straps with adjustable foot cradles."),
        ("Theragun PRO Massage Gun", 599.00, "photo-1584735935682-2f2b69dff9d2", "Deep tissue percussive therapy device with OLED screen."),
        ("Fitbit Charge 6 Fitness Tracker", 159.95, "photo-1510017803434-a899398421b3", "Heart rate and ECG fitness tracker with built-in GPS."),
        ("Wilson NBA Game Basketball", 199.99, "photo-1546519638-68e109498ffc", "Official NBA full-grain genuine leather game ball."),
        ("adidas Tango Soccer Ball", 39.99, "photo-1546519638-68e109498ffc", "Iconic hand-stitched FIFA quality training soccer ball."),
        ("Babolat Pure Drive Racket", 249.00, "photo-1546519638-68e109498ffc", "Explosive power high performance tennis racket."),
        ("Titleist Pro V1 Golf Balls", 54.99, "photo-1535131749006-b7f58c99034b", "Premium distance and spin control golf balls 12-pack."),
        ("Callaway Strata Golf Club Set", 599.99, "photo-1535131749006-b7f58c99034b", "Complete 12-piece driver, fairway wood, irons, and putter set."),
        ("Intex Explorer K2 Kayak", 169.99, "photo-1504280390367-361c6d9f38f4", "2-person inflatable kayak with aluminum oars and pump."),
        ("Black Diamond Trekking Poles", 139.95, "photo-1504280390367-361c6d9f38f4", "Natural cork grip adjustable aluminum hiking poles."),
        ("Petzl Actik Core Headlamp", 79.95, "photo-1504280390367-361c6d9f38f4", "600 lumen rechargeable outdoor headlamp with red lighting."),
        ("Therm-a-Rest NeoAir Pad", 239.95, "photo-1504280390367-361c6d9f38f4", "Ultra-light insulating inflatable camping mattress."),
        ("Marmot 0-Degree Sleeping Bag", 349.00, "photo-1504280390367-361c6d9f38f4", "650-fill power down cold weather mummy sleeping bag."),
        ("Resistance Loop Bands 5-Set", 19.99, "photo-1584735935682-2f2b69dff9d2", "Latex resistance training bands for physical therapy and fitness."),
        ("Heavy Duty Kettlebell 24kg", 69.99, "photo-1584735935682-2f2b69dff9d2", "Cast iron kettlebell with textured grip handle."),
        ("Foam Roller for Recovery", 24.99, "photo-1584735935682-2f2b69dff9d2", "High density EVA foam roller for deep muscle tissue massage."),
        ("Speed Jump Rope Steel", 14.99, "photo-1584735935682-2f2b69dff9d2", "Tangle-free ball bearing speed jump rope for cardio."),
        ("Pull-Up Bar Doorway Trainer", 34.99, "photo-1584735935682-2f2b69dff9d2", "Multi-grip upper body strength training doorway bar."),
        ("Workout Gym Gloves", 17.99, "photo-1584735935682-2f2b69dff9d2", "Padded weightlifting gloves with wrist wrap support."),
        ("CamelBak HydroBak Pack", 55.00, "photo-1602143407151-7111542de6e8", "1.5L Crux reservoir lightweight cycling hydration backpack."),
        ("Nalgene Tritan 32oz Bottle", 15.99, "photo-1602143407151-7111542de6e8", "BPA-free indestructible wide mouth water bottle."),
        ("Stanley Travel Tumbler 40oz", 45.00, "photo-1602143407151-7111542de6e8", "Vacuum insulated stainless steel straw tumbler."),
        ("Camping Hammock with Net", 39.99, "photo-1504280390367-361c6d9f38f4", "Portable parachute nylon double hammock with tree straps."),
        ("Portable Camping Stove", 29.99, "photo-1504280390367-361c6d9f38f4", "Single burner butane backpacking backpacking stove."),
        ("Cast Iron Skillet 12-Inch", 34.99, "photo-1504280390367-361c6d9f38f4", "Pre-seasoned heavy duty cast iron campfire pan."),
        ("Waterproof Dry Bag 20L", 22.99, "photo-1553062407-98eeb64c6a62", "Roll-top floating dry sack for kayaking and rafting."),
        ("Tactile Pocket Folding Knife", 27.99, "photo-1504280390367-361c6d9f38f4", "Stainless steel assisted opening outdoor survival knife."),
        ("Emergency Survival Kit", 39.99, "photo-1504280390367-361c6d9f38f4", "250-piece professional medical first aid supplies bag."),
        ("Binoculars 10x42 Waterproof", 89.99, "photo-1504280390367-361c6d9f38f4", "High power BAK4 prism bird watching hunting optics."),
        ("Snorkel Set Mask & Fins", 44.99, "photo-1504280390367-361c6d9f38f4", "Anti-fog panoramic tempered glass diving mask set."),
        ("Inflatable Paddle Board Set", 349.99, "photo-1504280390367-361c6d9f38f4", "10'6 SUP paddle board with pump, paddle, and backpack.")
    ]

    # Additional Toys & Games (44 items -> 50+ total Toys & Games)
    more_toys = [
        ("LEGO Millennium Falcon", 849.99, "photo-1587654780291-39c9404d746b", "Ultimate Collector Series 7541 piece LEGO Star Wars set."),
        ("LEGO Technic Porsche 911", 379.99, "photo-1587654780291-39c9404d746b", "Authentic 1:8 scale supercar building model with gearbox."),
        ("Catan Board Game", 55.00, "photo-1610890716171-6b1bb98ffd09", "Classic island trading and resource gathering strategy game."),
        ("Ticket to Ride Game", 59.99, "photo-1610890716171-6b1bb98ffd09", "Cross-country train adventure board game."),
        ("Wingspan Strategy Game", 60.00, "photo-1610890716171-6b1bb98ffd09", "Award-winning engine-building bird collection card game."),
        ("Exploding Kittens Card Game", 19.99, "photo-1610890716171-6b1bb98ffd09", "Hilarious Russian Roulette card game with laser beams."),
        ("Codenames Party Game", 19.95, "photo-1610890716171-6b1bb98ffd09", "Social deduction word guessing secret agent game."),
        ("Monopoly Classic Edition", 21.99, "photo-1610890716171-6b1bb98ffd09", "Fast-dealing property trading classic family board game."),
        ("Scrabble Deluxe Edition", 39.99, "photo-1610890716171-6b1bb98ffd09", "Rotating wooden game board crossword puzzle game."),
        ("Jenga Classic Hardwood Game", 15.99, "photo-1610890716171-6b1bb98ffd09", "Stacking wooden block balancing game."),
        ("Rubik's Speed Cube 3x3", 14.99, "photo-1563089145-599997674d42", "Fast turning stickerless original 3D puzzle cube."),
        ("Hot Wheels 20-Car Pack", 24.99, "photo-1594787318286-3d835c1d207f", "1:64 scale die-cast toy vehicle collection."),
        ("RC Monster Truck 4WD", 79.99, "photo-1594787318286-3d835c1d207f", "High speed 30mph off-road remote control car."),
        ("Syma Mini RC Helicopter", 24.99, "photo-1527977966376-1c8408f9f108", "Indoor 3-channel gyroscope remote control flyer."),
        ("Barbie Dreamhouse Playset", 199.99, "photo-1566576912321-d58ddd7a6088", "3-story dollhouse with pool, slide, lights, and sounds."),
        ("Nerf Commander Blaster", 14.99, "photo-1566576912321-d58ddd7a6088", "Rotating 6-dart drum toy blaster with tactical rails."),
        ("Play-Doh 20-Pack", 16.99, "photo-1566576912321-d58ddd7a6088", "Colorful non-toxic modeling clay tub set."),
        ("Crayola 152 Crayon Set", 17.99, "photo-1566576912321-d58ddd7a6088", "Ultimate drawing and coloring crayon tub with sharpener."),
        ("Wooden Building Blocks Set", 27.99, "photo-1587654780291-39c9404d746b", "100-piece solid wood architectural building block shapes."),
        ("Ravensburger 1000-Piece Puzzle", 19.99, "photo-1563089145-599997674d42", "Softclick technology high precision jigsaw puzzle."),
        ("Magic: The Gathering Deck", 14.99, "photo-1610890716171-6b1bb98ffd09", "2-player trading card game ready-to-play battle deck."),
        ("Pokémon TCG Trainer Box", 49.99, "photo-1610890716171-6b1bb98ffd09", "8 booster packs, sleeves, energy cards, and dice set."),
        ("Dungeons & Dragons Set", 19.99, "photo-1610890716171-6b1bb98ffd09", "Fifth edition tabletop roleplaying starter box with rulebook."),
        ("Spider-Man Action Figure", 24.99, "photo-1566576912321-d58ddd7a6088", "6-inch poseable superhero figure with web accessories."),
        ("Transformers Optimus Prime", 44.99, "photo-1566576912321-d58ddd7a6088", "Converting robot toy transforming into semi-truck."),
        ("Darth Vader Black Series", 29.99, "photo-1566576912321-d58ddd7a6088", "Collectible 6-inch detailed Star Wars action figure."),
        ("Funko Pop! Iron Man", 12.99, "photo-1566576912321-d58ddd7a6088", "Vinyl bobblehead figure display collectible."),
        ("Tamagotchi Pix Pet", 59.99, "photo-1566576912321-d58ddd7a6088", "Virtual electronic pet with camera, touch buttons, and games."),
        ("Squishmallows 16-Inch Plush", 24.99, "photo-1566576912321-d58ddd7a6088", "Super soft marshmallow-like stuffed animal pillow."),
        ("Gund Teddy Bear Plush", 29.99, "photo-1566576912321-d58ddd7a6088", "Classic 15-inch brown plush teddy bear."),
        ("Radio Flyer Red Wagon", 119.99, "photo-1594787318286-3d835c1d207f", "All-steel seamless body classic pull cart."),
        ("Razor A Kick Scooter", 39.99, "photo-1594787318286-3d835c1d207f", "Folding aircraft-grade aluminum scooter for kids."),
        ("Strider Balance Bike 12-Inch", 109.99, "photo-1594787318286-3d835c1d207f", "Pedal-free toddler learning bicycle with puncture-proof tires."),
        ("Little Tikes Cozy Coupe", 64.99, "photo-1594787318286-3d835c1d207f", "Iconic red and yellow foot-to-floor ride-on car."),
        ("Intex Metal Frame Pool", 149.99, "photo-1566576912321-d58ddd7a6088", "10ft x 30in outdoor backyard swimming pool with filter pump."),
        ("Slip N Slide Wave Rider", 19.99, "photo-1566576912321-d58ddd7a6088", "18ft backyard water slide with hydro-glide technology."),
        ("Bunch O Balloons 100-Pack", 11.99, "photo-1566576912321-d58ddd7a6088", "Self-sealing rapid filling water balloons."),
        ("Spikeball 3 Ball Kit", 69.99, "photo-1546519638-68e109498ffc", "Outdoor lawn and beach roundnet sport game."),
        ("Kan Jam Disc Game", 39.99, "photo-1546519638-68e109498ffc", "Frisbee target toss backyard tailgating game."),
        ("Cornhole Wooden Game Set", 99.99, "photo-1610890716171-6b1bb98ffd09", "Regulation size wooden bean bag toss boards set."),
        ("Giant Wooden Jenga Tower", 79.99, "photo-1610890716171-6b1bb98ffd09", "Outdoor yard wooden block stacking game up to 5ft."),
        ("Bocce Ball Game Set", 39.99, "photo-1546519638-68e109498ffc", "Poly-resin lawn ball game with measuring tape and bag."),
        ("Badminton Set with Net", 49.99, "photo-1546519638-68e109498ffc", "Portable backyard badminton court setup with 4 racquets."),
        ("Portable Ping Pong Set", 29.99, "photo-1546519638-68e109498ffc", "Retractable table tennis net with 2 paddles and balls.")
    ]

    # Additional Books (45 items -> 50+ total Books)
    more_books = [
        ("Atomic Habits by James Clear", 17.99, "photo-1544716278-ca5e3f4abd8c", "An easy & proven way to build good habits and break bad ones."),
        ("The Psychology of Money", 16.99, "photo-1544716278-ca5e3f4abd8c", "Timeless lessons on wealth, greed, and happiness by Morgan Housel."),
        ("Deep Work by Cal Newport", 18.00, "photo-1544716278-ca5e3f4abd8c", "Rules for focused success in a distracted world."),
        ("Thinking, Fast and Slow", 19.99, "photo-1544716278-ca5e3f4abd8c", "Nobel Prize winner Daniel Kahneman's tour of the mind."),
        ("Sapiens: History of Humankind", 22.99, "photo-1544716278-ca5e3f4abd8c", "Yuval Noah Harari's groundbreaking narrative of humanity."),
        ("The 48 Laws of Power", 21.00, "photo-1544716278-ca5e3f4abd8c", "Amoral, cunning, ruthless, and instructive handbook on power."),
        ("Can't Hurt Me by David Goggins", 19.95, "photo-1544716278-ca5e3f4abd8c", "Master Your Mind and Defy the Odds memoir."),
        ("Rich Dad Poor Dad", 16.60, "photo-1544716278-ca5e3f4abd8c", "What the rich teach their kids about money that the poor do not."),
        ("Man's Search for Meaning", 14.00, "photo-1544716278-ca5e3f4abd8c", "Viktor E. Frankl's classic memoir of survival in concentration camps."),
        ("The Subtle Art of Not Giving a F*ck", 16.99, "photo-1544716278-ca5e3f4abd8c", "Mark Manson's counterintuitive approach to living a good life."),
        ("Outlive: Science of Longevity", 24.99, "photo-1544716278-ca5e3f4abd8c", "Peter Attia's manifesto on living better and longer."),
        ("Essentialism: Pursuit of Less", 17.99, "photo-1544716278-ca5e3f4abd8c", "Greg McKeown's disciplined method for doing only what matters."),
        ("Designing Data-Intensive Applications", 49.99, "photo-1544716278-ca5e3f4abd8c", "Martin Kleppmann's guide to reliable, scalable system architectures."),
        ("Clean Code by Robert C. Martin", 44.99, "photo-1544716278-ca5e3f4abd8c", "A handbook of agile software craftsmanship."),
        ("Python Crash Course 3rd Ed", 34.95, "photo-1544716278-ca5e3f4abd8c", "Eric Matthes' hands-on, project-based introduction to programming."),
        ("Artificial Intelligence: A Modern Approach", 129.99, "photo-1544716278-ca5e3f4abd8c", "Stuart Russell and Peter Norvig's definitive AI textbook."),
        ("The Pragmatic Programmer", 49.99, "photo-1544716278-ca5e3f4abd8c", "David Thomas and Andrew Hunt's guide from journeyman to master."),
        ("Introduction to Algorithms CLRS", 99.99, "photo-1544716278-ca5e3f4abd8c", "Comprehensive computer science algorithms reference textbook."),
        ("System Design Interview Alex Xu", 36.99, "photo-1544716278-ca5e3f4abd8c", "An insider's guide to passing software engineering system design tests."),
        ("Head First Design Patterns", 54.99, "photo-1544716278-ca5e3f4abd8c", "Brain-friendly guide to object-oriented software design."),
        ("Dune by Frank Herbert", 18.00, "photo-1544716278-ca5e3f4abd8c", "Epic science fiction masterpiece set on the desert planet Arrakis."),
        ("Project Hail Mary Andy Weir", 20.00, "photo-1544716278-ca5e3f4abd8c", "A lone astronaut must save the Earth from an extinction-level threat."),
        ("The Hobbit J.R.R. Tolkien", 16.99, "photo-1544716278-ca5e3f4abd8c", "Enchanting prelude to The Lord of the Rings trilogy."),
        ("The Lord of the Rings Box Set", 39.99, "photo-1544716278-ca5e3f4abd8c", "The Fellowship, The Two Towers, and The Return of the King."),
        ("1984 by George Orwell", 15.00, "photo-1544716278-ca5e3f4abd8c", "Classic dystopian novel of totalitarian surveillance."),
        ("To Kill a Mockingbird", 16.00, "photo-1544716278-ca5e3f4abd8c", "Pulitzer Prize-winning novel of racial injustice and innocence."),
        ("The Great Gatsby F. Scott Fitzgerald", 14.99, "photo-1544716278-ca5e3f4abd8c", "The classic Jazz Age tragedy of Jay Gatsby."),
        ("Foundation by Isaac Asimov", 17.00, "photo-1544716278-ca5e3f4abd8c", "Sci-fi saga of Hari Seldon and psychohistory."),
        ("Neuromancer William Gibson", 16.00, "photo-1544716278-ca5e3f4abd8c", "Groundbreaking cyberpunk novel introducing the Matrix."),
        ("Three-Body Problem Cixin Liu", 18.99, "photo-1544716278-ca5e3f4abd8c", "Hugo Award-winning hard sci-fi first contact novel."),
        ("The Alchemist Paulo Coelho", 16.99, "photo-1544716278-ca5e3f4abd8c", "Fable about following your dream and listening to your heart."),
        ("Steve Jobs Walter Isaacson", 22.00, "photo-1544716278-ca5e3f4abd8c", "Exclusive biography of the Apple creative entrepreneur."),
        ("Shoe Dog by Phil Knight", 19.00, "photo-1544716278-ca5e3f4abd8c", "Memoir by the creator of Nike."),
        ("Elon Musk Walter Isaacson", 24.99, "photo-1544716278-ca5e3f4abd8c", "Intimate story of the innovator behind SpaceX and Tesla."),
        ("Becoming by Michelle Obama", 20.00, "photo-1544716278-ca5e3f4abd8c", "Deeply personal memoir of the former First Lady."),
        ("Principles by Ray Dalio", 22.00, "photo-1544716278-ca5e3f4abd8c", "Life and work guidelines from Bridgewater founder."),
        ("Zero to One Peter Thiel", 17.99, "photo-1544716278-ca5e3f4abd8c", "Notes on startups and how to build the future."),
        ("Good to Great Jim Collins", 21.99, "photo-1544716278-ca5e3f4abd8c", "Why some companies make the leap and others don't."),
        ("The Lean Startup Eric Ries", 19.99, "photo-1544716278-ca5e3f4abd8c", "Continuous innovation to create radically successful businesses."),
        ("Company of One Paul Jarvis", 17.00, "photo-1544716278-ca5e3f4abd8c", "Why staying small is the next big thing for business."),
        ("Never Split Difference Chris Voss", 18.99, "photo-1544716278-ca5e3f4abd8c", "FBI negotiator's field guide to persuasive communication."),
        ("Influence Robert Cialdini", 20.00, "photo-1544716278-ca5e3f4abd8c", "The psychology of persuasion and compliance."),
        ("Start with Why Simon Sinek", 17.00, "photo-1544716278-ca5e3f4abd8c", "How great leaders inspire everyone to take action."),
        ("Crucial Conversations", 19.99, "photo-1544716278-ca5e3f4abd8c", "Tools for talking when stakes are high."),
        ("Extreme Ownership Jocko Willink", 20.00, "photo-1544716278-ca5e3f4abd8c", "How Navy SEALs lead and win."),
        ("The Lean Startup 2nd Edition", 19.99, "photo-1544716278-ca5e3f4abd8c", "Continuous innovation for radical business success."),
        ("Zero to One Expanded", 17.99, "photo-1544716278-ca5e3f4abd8c", "Notes on startups and how to build the future."),
        ("Good to Great Leadership Edition", 21.99, "photo-1544716278-ca5e3f4abd8c", "Why some companies make the leap and others don't.")
    ]

    # Add extra items to hit 50+ in every category
    more_home.append(("Instant Pot Duo Plus 9-in-1", 129.99, "photo-1585515320310-259814833e62", "9-in-1 electric pressure cooker and slow cooker."))
    
    more_toys.extend([
        ("LEGO Harry Potter Hogwarts Castle", 469.99, "photo-1587654780291-39c9404d746b", "Iconic 6020 piece Hogwarts microscale model."),
        ("Settlers of Catan Cities & Knights", 49.99, "photo-1610890716171-6b1bb98ffd09", "Popular Catan strategy board game expansion pack."),
        ("Hasbro Connect 4 Game", 12.99, "photo-1610890716171-6b1bb98ffd09", "Classic 4-in-a-row grid drop disc game.")
    ])

    more_sports.extend([
        ("Wilson Evolution Game Basketball", 79.99, "photo-1546519638-68e109498ffc", "Preferred indoor high school and college basketball."),
        ("Coleman Triton 2-Burner Camping Stove", 89.99, "photo-1504280390367-361c6d9f38f4", "22,000 total BTU heavy duty propane camping stove."),
        ("Garmin Forerunner 265 Watch", 449.99, "photo-1510017803434-a899398421b3", "AMOLED touchscreen GPS running smartwatch."),
        ("YETI Rambler 30 oz Tumbler", 38.00, "photo-1602143407151-7111542de6e8", "Double-wall vacuum insulated travel coffee mug."),
        ("Intex Explorer 300 Boat Set", 39.99, "photo-1504280390367-361c6d9f38f4", "Inflatable 3-person pool and lake boat set with oars."),
        ("TRX GO Suspension Trainer Kit", 129.95, "photo-1584735935682-2f2b69dff9d2", "Lightweight travel suspension trainer kit.")
    ])

    all_custom_batches = [
        ("Mobile Phone", 161, more_mobiles),
        ("Electronics", 201, more_electronics),
        ("Home & Kitchen", 236, more_home),
        ("Sports & Outdoors", 276, more_sports),
        ("Toys & Games", 318, more_toys),
        ("Books", 362, more_books)
    ]

    for cat_name, start_id, batch in all_custom_batches:
        for idx, (name, price, photo_id, desc) in enumerate(batch, start=start_id):
            image_url = f"https://images.unsplash.com/{photo_id}?auto=format&fit=crop&w=400&h=400&q=80"
            rating_val = round(random.uniform(4.2, 4.9), 1)
            c.execute(
                "INSERT INTO products (name, category, price, description, rating, image_url) VALUES (?, ?, ?, ?, ?, ?)",
                (name, cat_name, price, desc, rating_val, image_url)
            )

    conn.commit()
    print("Inserted 407 products across all categories into database!")

    # 2. Extract customers
    print("Processing users...")
    raw_users = df[['CustomerID', 'CustomerName']].drop_duplicates()
    
    user_id_map = {}  # maps CustomerID string -> integer SQLite ID
    inserted_usernames = set()
    inserted_emails = set()
    
    sqlite_user_idx = 1
    for row in raw_users.itertuples():
        cust_id = row.CustomerID
        name = row.CustomerName
        
        # Parse first name and last name
        name_parts = name.split(maxsplit=1)
        first_name = name_parts[0] if len(name_parts) > 0 else name
        last_name = name_parts[1] if len(name_parts) > 1 else ""
        
        # Resolve username duplicate conflict
        base_name = name
        counter = 1
        while name in inserted_usernames:
            name = f"{base_name} ({counter})"
            counter += 1
        inserted_usernames.add(name)
        
        # Generate email
        clean_first = "".join(filter(str.isalnum, first_name.lower()))
        clean_last = "".join(filter(str.isalnum, last_name.lower()))
        email = f"{clean_first}.{clean_last}@example.com" if clean_last else f"{clean_first}@example.com"
        
        # Resolve email duplicate conflict
        base_email = email.split('@')[0]
        counter = 1
        while email in inserted_emails:
            email = f"{base_email}{counter}@example.com"
            counter += 1
        inserted_emails.add(email)
        
        # Default password
        password = "password123"
        
        # Generate random date of birth
        year = random.randint(1980, 2003)
        month = random.randint(1, 12)
        day = random.randint(1, 28)
        dob = f"{year:04d}-{month:02d}-{day:02d}"
        
        c.execute(
            "INSERT INTO users (username, email, password, first_name, last_name, dob) VALUES (?, ?, ?, ?, ?, ?)",
            (name, email, password, first_name, last_name, dob)
        )
        user_id_map[cust_id] = sqlite_user_idx
        sqlite_user_idx += 1
        
    conn.commit()
    print(f"Inserted {len(user_id_map)} users.")

    # 3. Process transactions (purchases) from Excel rows
    print("Processing transactions...")
    interactions = []
    
    # Track which users bought what to avoid exact duplicate purchase lines in database
    user_purchased = {} # user_id -> set of product_ids
    
    for row in df.itertuples():
        cust_id = row.CustomerID
        pid_str = row.ProductID
        
        user_sqlite_id = user_id_map[cust_id]
        prod_sqlite_id = product_id_map[pid_str]
        
        if user_sqlite_id not in user_purchased:
            user_purchased[user_sqlite_id] = set()
            
        # Avoid exact duplicate purchases to keep clean dataset
        if prod_sqlite_id not in user_purchased[user_sqlite_id]:
            user_purchased[user_sqlite_id].add(prod_sqlite_id)
            # Add purchase interaction
            interactions.append((user_sqlite_id, prod_sqlite_id, "purchase", None))

    c.executemany(
        "INSERT INTO interactions (user_id, product_id, interaction_type, rating) VALUES (?, ?, ?, ?)",
        interactions
    )
    conn.commit()
    print(f"Inserted {len(interactions)} real purchase interactions.")

    # 4. Enrich top 20 users with additional views and ratings for SVD models
    print("Enriching first 20 users for Collaborative Filtering taste profiles...")
    enriched_interactions = []
    
    # First 20 users will be our active demo users
    for user_sqlite_id in range(1, 21):
        # Find what they already purchased
        already_purchased = user_purchased.get(user_sqlite_id, set())
        
        # Pick 8-15 random additional products to view and rate
        additional_views = random.randint(8, 15)
        # Extend range to 407 to cover all products across all 7 categories (IDs 1 to 406)
        candidates = [pid for pid in range(1, 407) if pid not in already_purchased]
        viewed_products = random.sample(candidates, min(additional_views, len(candidates)))
        
        for p_id in viewed_products:
            # Add view
            enriched_interactions.append((user_sqlite_id, p_id, "view", None))
            
            # Make some of them rated (70% chance)
            if random.random() < 0.7:
                rating_val = random.randint(3, 5)
                enriched_interactions.append((user_sqlite_id, p_id, "rate", rating_val))
                
        # Also let's assign ratings (4-5 stars) to their actual purchased items
        for p_id in already_purchased:
            rating_val = random.randint(4, 5)
            enriched_interactions.append((user_sqlite_id, p_id, "rate", rating_val))

    c.executemany(
        "INSERT INTO interactions (user_id, product_id, interaction_type, rating) VALUES (?, ?, ?, ?)",
        enriched_interactions
    )
    conn.commit()

    # 5. Populate customer reviews with review photos
    print("Populating customer reviews...")
    reviews = []
    
    # Category-specific template statements to construct highly realistic reviews
    review_statements = {
        "Mobile Phone": [
            "Absolutely love this {p_name}! The screen is gorgeous, battery easily lasts two days, and the camera quality is professional. 10/10!",
            "Great performance on this {p_name}. Operating system is smooth and applications open instantly. Recommend a good case.",
            "The {p_name} is okay, but charging feels a bit slow and it gets slightly warm during heavy gaming.",
            "Incredible device! Upgraded to this {p_name} and the difference is day and night. Photos are super sharp.",
            "Solid smartphone. Good value, screen is bright even in sunlight. Very satisfied.",
            "Decent value, but the voice quality during calls could be slightly better.",
            "Best phone I have ever owned. The camera features are outstanding and it looks very premium."
        ],
        "Electronics": [
            "Absolutely thrilled with my {p_name}! The build quality is exceptional and it works flawlessly. Highly recommend!",
            "The {p_name} is really good value for money. Setup was quick and it performs well. Minor shipping delay.",
            "The {p_name} does the job, but the plastic casing feels a bit lightweight for the price.",
            "Amazing features on this {p_name}. Battery life exceeded my expectations and sound/display quality is top-notch.",
            "Decent {p_name}. Had a small issue with the bluetooth pairing initially, but a reboot resolved it.",
            "Average performance. It works, but there are better alternatives for this price point.",
            "Extremely satisfied! I use this {p_name} every single day and it hasn't let me down once."
        ],
        "Home & Kitchen": [
            "Highly recommend this {p_name}! It has quickly become an essential part of my kitchen. Very durable and efficient.",
            "The {p_name} works perfectly as advertised. Clean design and easy to wash. Good purchase.",
            "The {p_name} is decent, but it takes up a bit more counter space than I expected.",
            "An absolute game-changer in the household. It makes cooking and cleaning so much faster.",
            "Satisfactory build quality, although the instructions could have been a bit clearer.",
            "Okay product. It is a bit loud during operation, but it gets the job done.",
            "I am so glad I bought this {p_name}. It fits perfectly in my kitchen and looks beautiful."
        ],
        "Clothing": [
            "The {p_name} is super comfortable! The fabric feels premium, soft, and it fits perfectly true to size.",
            "Very happy with this {p_name}. The color matches the picture and the fit is comfortable.",
            "The {p_name} is okay, but the material is a bit thinner than I hoped for.",
            "Exceeded my expectations! Wore it all day and it feels very breathable and stylish.",
            "Good value for money. Stitching is solid. Might want to size up if you prefer a loose fit.",
            "A bit disappointed in the sizing, it runs slightly small, but the exchange process was easy.",
            "Absolutely gorgeous {p_name}. Got so many compliments on it already!"
        ],
        "Sports & Outdoors": [
            "Outstanding quality! This {p_name} is perfect for daily training and outdoor use. Extremely lightweight.",
            "The {p_name} works great, feels comfortable, and is built to last. Happy with the purchase.",
            "Good {p_name}, but the straps/adjustments take some getting used to.",
            "Excellent gear for my weekend trips. Stood up well to the weather conditions.",
            "Solid product. Good grip and support. Highly recommend for active users.",
            "A bit stiff at first, but after a few uses it broke in nicely and works well.",
            "Super durable and reliable. Will definitely be purchasing more gear from this brand."
        ],
        "Toys & Games": [
            "This {p_name} is a huge hit! Highly engaging, safe for the kids, and kept them entertained for hours.",
            "Very fun and well-designed {p_name}. Excellent quality pieces and great for family time.",
            "The {p_name} is interesting, but the rules are slightly complicated for younger players.",
            "Bought this as a gift and they absolutely loved it. Highly interactive and creative.",
            "Decent entertainment value. Some of the card/board parts could be sturdier.",
            "Fun game, but runs a bit long. Great for weekend nights though.",
            "Outstanding! Perfect combination of learning and fun."
        ],
        "Books": [
            "An absolute masterpiece! The {p_name} is incredibly written and highly thought-provoking. Couldn't put it down.",
            "Really enjoyed the {p_name}. It offers great insights, though it drags a bit in the middle chapters.",
            "The {p_name} has an interesting concept, but the pacing felt a bit dry for my taste.",
            "A beautifully written copy. The page quality is great and the content is life-changing.",
            "Decent read. Some takeaways, although it repeats itself in a few sections.",
            "Not quite my style, but I can see why it's a bestseller. Good character/ideas development.",
            "Highly recommend this {p_name} to anyone looking for inspiration and solid research."
        ]
    }
    
    # Fetch products to retrieve name, category, and ID
    c.execute("SELECT id, name, category FROM products")
    all_products = c.fetchall()
    
    # Track reviews counts
    total_reviews = 0
    
    for p_id, p_name, p_cat in all_products:
        statements = review_statements.get(p_cat, review_statements["Electronics"])
        
        # Add between 5 and 15 reviews per product
        n_reviews = random.randint(5, 15)
        
        # Pick random unique users from database to leave reviews (excluding demo users 1-20)
        reviewers = random.sample(range(21, 2000), n_reviews)
        
        # Map product name to a search keyword for Lorem Flickr
        keyword = get_product_keyword(p_name)
        
        for r_idx, u_id in enumerate(reviewers):
            # Select review statement
            statement_tpl = statements[r_idx % len(statements)]
            review_text = statement_tpl.format(p_name=p_name)
            
            # Select rating based on review stance
            # First statement is 5, second is 4, third is 3, others are random 4-5
            if r_idx % len(statements) == 0:
                rating_val = 5
            elif r_idx % len(statements) == 1:
                rating_val = 4
            elif r_idx % len(statements) == 2:
                rating_val = 3
            else:
                rating_val = random.randint(4, 5)
            
            # 50% chance to include a review photo
            image_url = None
            if random.random() < 0.5:
                # Use the product's own image with slight crop variation so
                # the review photo always matches the product
                crop_variants = [
                    "?auto=format&fit=crop&w=400&h=300&q=80",
                    "?auto=format&fit=crop&w=400&h=300&q=75&crop=center",
                    "?auto=format&fit=crop&w=400&h=300&q=80&crop=top",
                    "?auto=format&fit=crop&w=400&h=300&q=80&crop=bottom",
                    "?auto=format&fit=crop&w=360&h=280&q=80",
                ]
                # Get the product's image_url base
                prod_row = conn.execute("SELECT image_url FROM products WHERE id=?", (p_id,)).fetchone()
                if prod_row and prod_row[0]:
                    base = prod_row[0].split('?')[0]
                    image_url = base + random.choice(crop_variants)
                
            reviews.append((u_id, p_id, rating_val, review_text, image_url))
            total_reviews += 1
            
    c.executemany(
        "INSERT INTO reviews (user_id, product_id, rating, review_text, review_image_url) VALUES (?, ?, ?, ?, ?)",
        reviews
    )
    conn.commit()
    conn.close()
    
    print(f"Enrichment complete! Added {len(enriched_interactions)} views/ratings for collaborative filtering.")
    print(f"Database populate complete! Populated {total_reviews} reviews across all 60 products.")
    print("Running Flask app will now train on real Amazon Sales dataset.")

if __name__ == "__main__":
    populate_from_excel()
