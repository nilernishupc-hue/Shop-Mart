"""
app.py
------
Main Flask application for the AI-Powered Personalised Recommendation System.
Run with: python app.py
"""

from flask import (
    Flask, render_template, request, session,
    redirect, url_for, g, jsonify,
)
import os
import time
import sqlite3
from werkzeug.utils import secure_filename
from models import DB_NAME, get_products_df, get_interactions_df
from recommendation_engine import (
    get_hybrid_recommendations,
    get_cb_recommendations,
    evaluate_models,
)
from whitenoise import WhiteNoise

app = Flask(__name__, static_folder="static")
app.secret_key = "ai_recommend_msc_2024_secret"
app.wsgi_app = WhiteNoise(app.wsgi_app, root="static/", prefix="static/")

# ──────────────────────────────────────────────────────────────────────────
# Database helpers
# ──────────────────────────────────────────────────────────────────────────

def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DB_NAME)
        db.row_factory = sqlite3.Row
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


# ──────────────────────────────────────────────────────────────────────────
# Context – inject current user into every template
# ──────────────────────────────────────────────────────────────────────────

@app.context_processor
def inject_user():
    user = None
    if "user_id" in session:
        user = query_db("SELECT * FROM users WHERE id = ?", [session["user_id"]], one=True)
    return dict(current_user=user)


# ──────────────────────────────────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    products = query_db("SELECT * FROM products ORDER BY rating DESC LIMIT 8")
    recommendations = []

    if "user_id" in session:
        recent = query_db(
            "SELECT product_id FROM interactions WHERE user_id = ? "
            "ORDER BY id DESC LIMIT 1",
            [session["user_id"]],
            one=True,
        )
        recent_id = recent["product_id"] if recent else None
        try:
            recommendations = get_hybrid_recommendations(
                session["user_id"], recent_id, top_n=4
            )
        except Exception:
            recommendations = []

    return render_template("index.html", products=products, recommendations=recommendations)


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        
        user = query_db(
            "SELECT * FROM users WHERE (username = ? OR email = ?) AND password = ?",
            [username, username, password],
            one=True
        )
        if user:
            session["user_id"] = user["id"]
            return redirect(url_for("index"))
        error = "Invalid username/email or password. For demo accounts, use password 'password123'."
    return render_template("login.html", error=error)


@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        last_name  = request.form.get("last_name", "").strip()
        email      = request.form.get("email", "").strip()
        username   = request.form.get("username", "").strip()
        password   = request.form.get("password", "").strip()
        dob        = request.form.get("dob", "").strip()
        
        if not username or not email or not password:
            error = "Username, email, and password are required."
        else:
            db = get_db()
            # Check username uniqueness
            exist_username = query_db("SELECT * FROM users WHERE username = ?", [username], one=True)
            # Check email uniqueness
            exist_email = query_db("SELECT * FROM users WHERE email = ?", [email], one=True)
            
            if exist_username:
                error = f"Username '{username}' is already taken."
            elif exist_email:
                error = f"Email '{email}' is already registered."
            else:
                try:
                    cur = db.execute(
                        "INSERT INTO users (username, email, password, first_name, last_name, dob) VALUES (?, ?, ?, ?, ?, ?)",
                        [username, email, password, first_name, last_name, dob]
                    )
                    db.commit()
                    session["user_id"] = cur.lastrowid
                    return redirect(url_for("index"))
                except sqlite3.IntegrityError:
                    error = "An error occurred during registration. Please try again."
    return render_template("register.html", error=error)


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect(url_for("index"))


@app.route("/products")
def products():
    search   = request.args.get("q", "")
    category = request.args.get("category", "")
    sort     = request.args.get("sort", "")
    page     = max(int(request.args.get("page", 1)), 1)
    per_page = 12

    sql  = "SELECT * FROM products WHERE 1=1"
    args = []

    if search:
        sql  += " AND (name LIKE ? OR description LIKE ?)"
        args += [f"%{search}%", f"%{search}%"]
    if category:
        sql  += " AND category = ?"
        args.append(category)

    if sort == "price_asc":
        sql += " ORDER BY price ASC"
    elif sort == "price_desc":
        sql += " ORDER BY price DESC"
    else:
        sql += " ORDER BY rating DESC"

    all_products = query_db(sql, args)
    total        = len(all_products)
    start        = (page - 1) * per_page
    paginated    = all_products[start : start + per_page]
    total_pages  = max((total + per_page - 1) // per_page, 1)

    # Max 5 visible page numbers window
    max_visible_pages = 5
    if total_pages <= max_visible_pages:
        start_page = 1
        end_page = total_pages
    else:
        if page <= 3:
            start_page = 1
            end_page = max_visible_pages
        elif page >= total_pages - 2:
            start_page = total_pages - max_visible_pages + 1
            end_page = total_pages
        else:
            start_page = page - 2
            end_page = page + 2

    categories = [r["category"] for r in query_db("SELECT DISTINCT category FROM products ORDER BY category")]

    return render_template(
        "products.html",
        products=paginated,
        search=search,
        current_category=category,
        sort=sort,
        page=page,
        total_pages=total_pages,
        start_page=start_page,
        end_page=end_page,
        categories=categories,
    )


@app.route("/product/<int:id>")
def product_detail(id):
    product = query_db("SELECT * FROM products WHERE id = ?", [id], one=True)
    if not product:
        return "Product not found", 404

    # Log view interaction
    if "user_id" in session:
        db = get_db()
        db.execute(
            "INSERT INTO interactions (user_id, product_id, interaction_type) VALUES (?, ?, ?)",
            [session["user_id"], id, "view"],
        )
        db.commit()

    # Fetch product reviews
    reviews = query_db(
        """
        SELECT r.*, u.username
        FROM reviews r
        JOIN users u ON r.user_id = u.id
        WHERE r.product_id = ?
        ORDER BY r.timestamp DESC
        """,
        [id],
    )

    # Content-based "You May Also Like"
    try:
        products_df = get_products_df()
        related = get_cb_recommendations(id, products_df, top_n=4)
    except Exception:
        related = []

    return render_template(
        "product_detail.html",
        product=product,
        related_products=related,
        reviews=reviews,
    )


@app.route("/submit_review/<int:product_id>", methods=["POST"])
def submit_review(product_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    rating = request.form.get("rating", "0")
    review_text = request.form.get("review_text", "").strip()
    review_image_url = request.form.get("review_image_url", "").strip()

    # Process uploaded customer photo file if provided
    if "review_image" in request.files:
        file = request.files["review_image"]
        if file and file.filename != "":
            filename = secure_filename(file.filename)
            unique_filename = f"rev_{session['user_id']}_{int(time.time())}_{filename}"
            upload_dir = os.path.join(app.root_path, "static", "uploads", "reviews")
            os.makedirs(upload_dir, exist_ok=True)
            file_path = os.path.join(upload_dir, unique_filename)
            file.save(file_path)
            review_image_url = url_for("static", filename=f"uploads/reviews/{unique_filename}")

    if rating.isdigit() and 1 <= int(rating) <= 5 and review_text:
        db = get_db()
        # Save to reviews table
        db.execute(
            "INSERT INTO reviews (user_id, product_id, rating, review_text, review_image_url) VALUES (?, ?, ?, ?, ?)",
            [session["user_id"], product_id, int(rating), review_text, review_image_url or None],
        )
        # Also log 'rate' interaction to update SVD collaborative filtering models
        db.execute(
            "INSERT INTO interactions (user_id, product_id, interaction_type, rating) VALUES (?, ?, ?, ?)",
            [session["user_id"], product_id, "rate", int(rating)],
        )
        db.commit()
    return redirect(url_for("product_detail", id=product_id))


@app.route("/profile")
def profile():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user = query_db("SELECT * FROM users WHERE id = ?", [session["user_id"]], one=True)
    history = query_db(
        """
        SELECT p.id, p.name, p.category, p.image_url, p.price,
               i.timestamp, i.interaction_type, i.rating
        FROM products p
        JOIN interactions i ON p.id = i.product_id
        WHERE i.user_id = ?
        ORDER BY i.id DESC
        LIMIT 30
        """,
        [session["user_id"]],
    )
    return render_template("profile.html", user=user, history=history)


@app.route("/dashboard")
def dashboard():
    try:
        metrics = evaluate_models()
    except Exception:
        metrics = {}
    return render_template("dashboard.html", metrics=metrics)


# ──────────────────────────────────────────────────────────────────────────
# Shopping Cart Endpoints & Helpers
# ──────────────────────────────────────────────────────────────────────────

@app.context_processor
def inject_cart_count():
    count = 0
    if "user_id" in session:
        res = query_db("SELECT SUM(quantity) as total FROM cart_items WHERE user_id = ?", [session["user_id"]], one=True)
        if res and res["total"]:
            count = res["total"]
    return dict(cart_count=count)


@app.route("/cart")
def cart():
    if "user_id" not in session:
        return redirect(url_for("login"))
        
    items = query_db(
        """
        SELECT c.quantity, p.id as product_id, p.name, p.category, p.price, p.image_url, p.rating
        FROM cart_items c
        JOIN products p ON c.product_id = p.id
        WHERE c.user_id = ?
        """,
        [session["user_id"]]
    )
    
    subtotal = sum(item["price"] * item["quantity"] for item in items)
    
    # Free shipping on orders over $99 (Temu/Shein style threshold)
    free_shipping_threshold = 99.0
    shipping_cost = 0.0 if (subtotal >= free_shipping_threshold or subtotal == 0) else 9.99
    tax = round(subtotal * 0.08, 2)
    
    shipping_progress = min(int((subtotal / free_shipping_threshold) * 100), 100) if subtotal > 0 else 0
    needed_for_free = max(free_shipping_threshold - subtotal, 0.0)
    
    return render_template(
        "cart.html",
        items=items,
        subtotal=subtotal,
        shipping_cost=shipping_cost,
        tax=tax,
        shipping_progress=shipping_progress,
        needed_for_free=needed_for_free,
        free_shipping_threshold=free_shipping_threshold
    )


@app.route("/cart/add", methods=["POST"])
def cart_add():
    if "user_id" not in session:
        return jsonify({"success": False, "error": "Login required"}), 401
        
    data = request.get_json() or {}
    product_id = data.get("product_id")
    quantity = int(data.get("quantity", 1))
    
    if not product_id:
        return jsonify({"success": False, "error": "Missing product ID"}), 400
        
    db = get_db()
    product = query_db("SELECT id FROM products WHERE id = ?", [product_id], one=True)
    if not product:
        return jsonify({"success": False, "error": "Product not found"}), 404
        
    db.execute(
        """
        INSERT INTO cart_items (user_id, product_id, quantity)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id, product_id)
        DO UPDATE SET quantity = quantity + excluded.quantity
        """,
        [session["user_id"], product_id, quantity]
    )
    db.commit()
    
    # Log 'view' (or implicit interest) in interactions for SVD models
    db.execute(
        "INSERT INTO interactions (user_id, product_id, interaction_type) VALUES (?, ?, ?)",
        [session["user_id"], product_id, "view"]
    )
    db.commit()
    
    res = query_db("SELECT SUM(quantity) as total FROM cart_items WHERE user_id = ?", [session["user_id"]], one=True)
    cart_count = res["total"] if (res and res["total"]) else 0
    
    return jsonify({"success": True, "cart_count": cart_count})


@app.route("/cart/update", methods=["POST"])
def cart_update():
    if "user_id" not in session:
        return jsonify({"success": False, "error": "Login required"}), 401
        
    data = request.get_json() or {}
    product_id = data.get("product_id")
    quantity = int(data.get("quantity", 1))
    
    if not product_id or quantity < 1:
        return jsonify({"success": False, "error": "Invalid arguments"}), 400
        
    db = get_db()
    db.execute(
        "UPDATE cart_items SET quantity = ? WHERE user_id = ? AND product_id = ?",
        [quantity, session["user_id"], product_id]
    )
    db.commit()
    
    items = query_db(
        "SELECT c.quantity, p.price FROM cart_items c JOIN products p ON c.product_id = p.id WHERE c.user_id = ?",
        [session["user_id"]]
    )
    subtotal = sum(item["price"] * item["quantity"] for item in items)
    cart_count = sum(item["quantity"] for item in items)
    
    free_shipping_threshold = 99.0
    shipping_cost = 0.0 if (subtotal >= free_shipping_threshold or subtotal == 0) else 9.99
    tax = round(subtotal * 0.08, 2)
    total = round(subtotal + shipping_cost + tax, 2)
    shipping_progress = min(int((subtotal / free_shipping_threshold) * 100), 100) if subtotal > 0 else 0
    needed_for_free = max(free_shipping_threshold - subtotal, 0.0)
    
    return jsonify({
        "success": True,
        "subtotal": subtotal,
        "shipping_cost": shipping_cost,
        "tax": tax,
        "total": total,
        "shipping_progress": shipping_progress,
        "needed_for_free": needed_for_free,
        "cart_count": cart_count
    })


@app.route("/cart/remove", methods=["POST"])
def cart_remove():
    if "user_id" not in session:
        return jsonify({"success": False, "error": "Login required"}), 401
        
    data = request.get_json() or {}
    product_id = data.get("product_id")
    
    if not product_id:
        return jsonify({"success": False, "error": "Invalid arguments"}), 400
        
    db = get_db()
    db.execute(
        "DELETE FROM cart_items WHERE user_id = ? AND product_id = ?",
        [session["user_id"], product_id]
    )
    db.commit()
    
    items = query_db(
        "SELECT c.quantity, p.price FROM cart_items c JOIN products p ON c.product_id = p.id WHERE c.user_id = ?",
        [session["user_id"]]
    )
    subtotal = sum(item["price"] * item["quantity"] for item in items)
    cart_count = sum(item["quantity"] for item in items)
    
    free_shipping_threshold = 99.0
    shipping_cost = 0.0 if (subtotal >= free_shipping_threshold or subtotal == 0) else 9.99
    tax = round(subtotal * 0.08, 2)
    total = round(subtotal + shipping_cost + tax, 2)
    shipping_progress = min(int((subtotal / free_shipping_threshold) * 100), 100) if subtotal > 0 else 0
    needed_for_free = max(free_shipping_threshold - subtotal, 0.0)
    
    return jsonify({
        "success": True,
        "subtotal": subtotal,
        "shipping_cost": shipping_cost,
        "tax": tax,
        "total": total,
        "shipping_progress": shipping_progress,
        "needed_for_free": needed_for_free,
        "cart_count": cart_count
    })


@app.route("/checkout")
def checkout():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user = query_db("SELECT * FROM users WHERE id = ?", [session["user_id"]], one=True)
    items = query_db(
        """
        SELECT c.quantity, p.id as product_id, p.name, p.category, p.price, p.image_url
        FROM cart_items c
        JOIN products p ON c.product_id = p.id
        WHERE c.user_id = ?
        """,
        [session["user_id"]]
    )

    if not items:
        return redirect(url_for("cart"))

    subtotal = sum(item["price"] * item["quantity"] for item in items)
    free_shipping_threshold = 99.0
    std_shipping = 0.0 if (subtotal >= free_shipping_threshold or subtotal == 0) else 9.99
    express_shipping = 14.99
    tax = round(subtotal * 0.08, 2)
    total = round(subtotal + std_shipping + tax, 2)

    # 4-installment calculation for Klarna / Afterpay
    klarna_installment = round(total / 4.0, 2)

    return render_template(
        "checkout.html",
        user=user,
        items=items,
        subtotal=subtotal,
        std_shipping=std_shipping,
        express_shipping=express_shipping,
        tax=tax,
        total=total,
        klarna_installment=klarna_installment
    )


@app.route("/checkout/process", methods=["POST"])
def checkout_process():
    if "user_id" not in session:
        return redirect(url_for("login"))

    db = get_db()
    items = query_db(
        """
        SELECT c.quantity, p.id as product_id, p.name, p.price
        FROM cart_items c
        JOIN products p ON c.product_id = p.id
        WHERE c.user_id = ?
        """,
        [session["user_id"]]
    )

    if not items:
        return redirect(url_for("cart"))

    # Form fields
    first_name = request.form.get("first_name", "").strip()
    last_name = request.form.get("last_name", "").strip()
    email = request.form.get("email", "").strip()
    address = request.form.get("address", "").strip()
    city = request.form.get("city", "").strip()
    state = request.form.get("state", "").strip()
    zip_code = request.form.get("zip", "").strip()
    phone = request.form.get("phone", "").strip()
    shipping_method = request.form.get("shipping_method", "standard")
    payment_method = request.form.get("payment_method", "card")
    card_number = request.form.get("card_number", "").strip()

    # Calculate pricing
    subtotal = sum(item["price"] * item["quantity"] for item in items)
    free_shipping_threshold = 99.0
    shipping_cost = 0.0 if (subtotal >= free_shipping_threshold or subtotal == 0) else 9.99
    if shipping_method == "express":
        shipping_cost = 14.99

    tax = round(subtotal * 0.08, 2)
    total = round(subtotal + shipping_cost + tax, 2)

    # Log purchase interactions for collaborative filtering model training
    for item in items:
        db.execute(
            "INSERT INTO interactions (user_id, product_id, interaction_type) VALUES (?, ?, ?)",
            [session["user_id"], item["product_id"], "purchase"]
        )

    # Clear user's cart
    db.execute("DELETE FROM cart_items WHERE user_id = ?", [session["user_id"]])
    db.commit()

    import random as py_random
    import datetime
    order_num = f"SM-{py_random.randint(100000, 999999)}"
    
    days_to_add = 3 if shipping_method == "express" else 6
    deliv_date = (datetime.date.today() + datetime.timedelta(days=days_to_add)).strftime("%A, %b %d")

    card_last4 = card_number[-4:] if len(card_number) >= 4 else "4242"

    session["order_receipt"] = {
        "order_num": order_num,
        "delivery_date": deliv_date,
        "shipping_method": shipping_method,
        "payment_method": payment_method,
        "card_last4": card_last4,
        "customer_name": f"{first_name} {last_name}".strip() or "Valued Customer",
        "shipping_address": f"{address}, {city}, {state} {zip_code}".strip(", "),
        "item_count": sum(item["quantity"] for item in items),
        "subtotal": subtotal,
        "shipping_cost": shipping_cost,
        "tax": tax,
        "total": total
    }

    return redirect(url_for("checkout_success"))


@app.route("/checkout-success")
def checkout_success():
    if "user_id" not in session:
        return redirect(url_for("login"))

    receipt = session.pop("order_receipt", None)
    if not receipt:
        return redirect(url_for("products"))

    return render_template("checkout_success.html", receipt=receipt)


# ──────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
