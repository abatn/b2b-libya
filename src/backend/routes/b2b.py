"""
Libya B2B Platform - B2B Routes
Dashboard, analytics, inventory, bulk pricing, product feed.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from config import get_db
from models import Order, Product, User
from routes.auth_routes import get_current_user

router = APIRouter(prefix="/api/b2b", tags=["b2b"])


# ============================================================
# DASHBOARD
# ============================================================


@router.get("/dashboard")
def get_b2b_dashboard(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    recent_orders = db.query(Order).filter(Order.created_at >= thirty_days_ago).all()
    total_revenue = sum(o.total_amount for o in recent_orders)
    pending = len([o for o in recent_orders if o.status == "pending"])
    delivered = len([o for o in recent_orders if o.status == "delivered"])
    avg_order = total_revenue / len(recent_orders) if recent_orders else 0

    return {
        "period": "last_30_days",
        "total_orders": len(recent_orders),
        "total_revenue": round(total_revenue, 2),
        "avg_order_value": round(avg_order, 2),
        "pending_orders": pending,
        "delivered_orders": delivered,
        "currency": "LYD",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/seller/{seller_id}")
def get_seller_dashboard(
    seller_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    products = db.query(Product).filter(Product.seller_id == seller_id).all()
    orders = db.query(Order).filter(Order.seller_id == seller_id).all()
    total_revenue = sum(o.total_amount for o in orders)
    active_products = len([p for p in products if p.is_active])
    return {
        "seller_id": seller_id,
        "total_products": len(products),
        "active_products": active_products,
        "total_orders": len(orders),
        "total_revenue": round(total_revenue, 2),
        "currency": "LYD",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/buyer/{buyer_id}")
def get_buyer_dashboard(
    buyer_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    orders = db.query(Order).filter(Order.buyer_id == buyer_id).all()
    total_spent = sum(o.total_amount for o in orders)
    pending = [o for o in orders if o.status == "pending"]
    delivered = [o for o in orders if o.status == "delivered"]
    return {
        "buyer_id": buyer_id,
        "total_orders": len(orders),
        "total_spent": round(total_spent, 2),
        "pending_orders": len(pending),
        "delivered_orders": len(delivered),
        "currency": "LYD",
        "recent_orders": [
            {
                "order_number": o.order_number,
                "total_amount": o.total_amount,
                "status": o.status,
                "seller_id": o.seller_id,
                "created_at": o.created_at.isoformat() if o.created_at else None,
            }
            for o in orders[-10:]
        ],
    }


# ============================================================
# ANALYTICS
# ============================================================


@router.get("/analytics")
def get_b2b_analytics(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    categories = db.query(Product.category, func.count(Product.id)).group_by(Product.category).all()
    top_products = db.query(Product).order_by(Product.stock_quantity.desc()).limit(10).all()
    return {
        "categories": [{"category": c[0] or "Other", "count": c[1]} for c in categories],
        "top_products": [
            {
                "id": p.id,
                "name": p.name,
                "name_arabic": p.name_arabic,
                "price": p.price,
                "stock": p.stock_quantity,
            }
            for p in top_products
        ],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ============================================================
# INVENTORY
# ============================================================


@router.get("/inventory")
def get_inventory(db: Session = Depends(get_db)):
    products = db.query(Product).filter(Product.is_active).all()
    return {
        "products": [
            {
                "id": p.id,
                "name": p.name,
                "name_arabic": p.name_arabic,
                "category": p.category,
                "stock": p.stock_quantity,
                "price": p.price,
                "currency": p.currency,
            }
            for p in products
        ],
        "total_products": len(products),
        "low_stock": len([p for p in products if p.stock_quantity < 10]),
    }


# ============================================================
# BULK PRICING
# ============================================================


@router.get("/bulk-pricing")
def get_bulk_pricing(db: Session = Depends(get_db)):
    products = db.query(Product).filter(Product.is_active).all()
    return {
        "products": [
            {
                "id": p.id,
                "name": p.name,
                "name_arabic": p.name_arabic,
                "base_price": p.price,
                "bulk_prices": {
                    "10+": round(p.price * 0.95, 2),
                    "50+": round(p.price * 0.90, 2),
                    "100+": round(p.price * 0.85, 2),
                },
            }
            for p in products
        ]
    }


# ============================================================
# PRODUCT FEED (with filters)
# ============================================================


@router.get("/products")
def list_b2b_products(
    search: Optional[str] = None,
    category: Optional[str] = None,
    min_moq: Optional[int] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    sort_by: Optional[str] = "name",
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    query = db.query(Product).filter(Product.is_active)

    if search:
        query = query.filter(
            (Product.name.ilike(f"%{search}%"))
            | (Product.name_arabic.ilike(f"%{search}%"))
            | (Product.description.ilike(f"%{search}%"))
        )
    if category and category != "all":
        # Map slug → DB name via CATEGORY_META (handles "food_beverage" → "Food & Beverage")
        slug_to_name = {c["id"]: c["name_en"] for c in CATEGORY_META}
        category_name = slug_to_name.get(category, category.replace("_", " ").title())
        query = query.filter(Product.category.ilike(category_name))
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)

    if sort_by == "price_asc":
        query = query.order_by(Product.price.asc())
    elif sort_by == "price_desc":
        query = query.order_by(Product.price.desc())
    else:
        query = query.order_by(Product.name.asc())

    products = query.offset(skip).limit(limit).all()
    total = query.count()

    return {
        "products": [
            {
                "id": p.id,
                "name": p.name,
                "name_arabic": p.name_arabic,
                "price": p.price,
                "currency": p.currency,
                "category": p.category,
                "stock_quantity": p.stock_quantity,
                "moq": p.moq
                if p.moq
                else max(1, p.stock_quantity // 100)
                if p.stock_quantity > 0
                else 1,
                "image_url": p.image_url,
                "seller_name": "Libya Supplier " + str(p.seller_id or 1),
                "is_active": p.is_active,
            }
            for p in products
        ],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


# ============================================================
# CATEGORIES (dynamic with counters)
# ============================================================

CATEGORY_META = [
    {
        "id": "building_materials",
        "name_en": "Building Materials",
        "name_ar": "مواد بناء",
        "icon": " ",
        "subcategories": [
            {
                "id": "cement",
                "name_en": "Cement",
                "name_ar": "اسمنت",
                "icon": " ",
                "sub_subcategories": [
                    {
                        "id": "portland_cement",
                        "name_en": "Portland Cement",
                        "name_ar": "اسمنت بورتلاند",
                        "sub_sub_subcategories": [
                            {"id": "opc_42_5", "name_en": "OPC 42.5", "name_ar": "اسمنت عادي 42.5"},
                            {
                                "id": "ppc_42_5",
                                "name_en": "PPC 42.5",
                                "name_ar": "اسمنت بوزولاني 42.5",
                            },
                            {"id": "cement_52_5", "name_en": "52.5 Grade", "name_ar": "درجة 52.5"},
                        ],
                    },
                    {"id": "white_cement", "name_en": "White Cement", "name_ar": "اسمنت ابيض"},
                    {"id": "ready_mix", "name_en": "Ready Mix Concrete", "name_ar": "خرسانة جاهزة"},
                ],
            },
            {
                "id": "steel",
                "name_en": "Steel & Rebar",
                "name_ar": "حديد",
                "icon": " ️",
                "sub_subcategories": [
                    {"id": "rebar_12", "name_en": "Rebar 12mm", "name_ar": "حديد تسليح 12"},
                    {"id": "rebar_16", "name_en": "Rebar 16mm", "name_ar": "حديد تسليح 16"},
                    {"id": "steel_sheet", "name_en": "Steel Sheets", "name_ar": "صفائح حديد"},
                ],
            },
            {
                "id": "tiles",
                "name_en": "Tiles & Ceramics",
                "name_ar": "بلاط",
                "icon": " ️",
                "sub_subcategories": [
                    {"id": "floor_tiles", "name_en": "Floor Tiles", "name_ar": "بلاط ارضية"},
                    {"id": "wall_tiles", "name_en": "Wall Tiles", "name_ar": "بلاط حائط"},
                    {"id": "porcelain", "name_en": "Porcelain Tiles", "name_ar": "سيراميك"},
                ],
            },
            {"id": "wood", "name_en": "Wood & Timber", "name_ar": "خشب", "icon": " "},
            {"id": "sand", "name_en": "Sand & Aggregate", "name_ar": "رمل", "icon": " ️"},
        ],
    },
    {
        "id": "electrical",
        "name_en": "Electrical",
        "name_ar": "كهرباء",
        "icon": "⚡",
        "subcategories": [
            {
                "id": "wires",
                "name_en": "Wires & Cables",
                "name_ar": "اسلاك",
                "icon": "⚡",
                "sub_subcategories": [
                    {
                        "id": "copper_wire",
                        "name_en": "Copper Wires",
                        "name_ar": "اسلاك نحاس",
                        "sub_sub_subcategories": [
                            {
                                "id": "copper_1_5mm",
                                "name_en": "1.5mm Single Core",
                                "name_ar": "نحاس 1.5 ملم لبنة واحدة",
                            },
                            {
                                "id": "copper_2_5mm",
                                "name_en": "2.5mm Single Core",
                                "name_ar": "نحاس 2.5 ملم لبنة واحدة",
                            },
                            {
                                "id": "copper_4mm",
                                "name_en": "4mm Single Core",
                                "name_ar": "نحاس 4 ملم لبنة واحدة",
                            },
                        ],
                    },
                    {
                        "id": "fiber_optic",
                        "name_en": "Fiber Optic Cables",
                        "name_ar": "كابلات ضوئية",
                    },
                    {"id": "power_cable", "name_en": "Power Cables", "name_ar": "كابلات طاقة"},
                ],
            },
            {
                "id": "switches",
                "name_en": "Switches & Sockets",
                "name_ar": "مفاتيح",
                "icon": " ",
                "sub_subcategories": [
                    {
                        "id": "wall_switch",
                        "name_en": "Wall Switches",
                        "name_ar": "مفاتيح حائط",
                        "sub_sub_subcategories": [
                            {
                                "id": "single_switch",
                                "name_en": "Single Gang",
                                "name_ar": "alyze واحدة",
                            },
                            {
                                "id": "double_switch",
                                "name_en": "Double Gang",
                                "name_ar": "alyze اثنتين",
                            },
                            {
                                "id": "dimmer_switch",
                                "name_en": "Dimmer Switches",
                                "name_ar": "مفاتيح تعتيم",
                            },
                        ],
                    },
                    {"id": "smart_switch", "name_en": "Smart Switches", "name_ar": "مفاتيح ذكية"},
                    {
                        "id": "industrial_socket",
                        "name_en": "Industrial Sockets",
                        "name_ar": "مقابس صناعية",
                    },
                ],
            },
            {
                "id": "panels",
                "name_en": "Distribution Panels",
                "name_ar": "لوحات",
                "icon": " ",
                "sub_subcategories": [
                    {"id": "main_panel", "name_en": "Main Panels", "name_ar": "لوحة رئيسية"},
                    {"id": "sub_panel", "name_en": "Sub Panels", "name_ar": "لوحة فرعية"},
                    {
                        "id": "circuit_breaker",
                        "name_en": "Circuit Breakers",
                        "name_ar": "قواطع الدارة",
                    },
                ],
            },
            {
                "id": "generators",
                "name_en": "Generators",
                "name_ar": "مولادات",
                "icon": "🔌",
                "sub_subcategories": [
                    {"id": "diesel_gen", "name_en": "Diesel Generators", "name_ar": "مولادات ديزل"},
                    {"id": "gas_gen", "name_en": "Gas Generators", "name_ar": "مولادات غاز"},
                    {
                        "id": "portable_gen",
                        "name_en": "Portable Generators",
                        "name_ar": "مولادات محمولة",
                    },
                ],
            },
            {"id": "solar", "name_en": "Solar Panels", "name_ar": "طاقة شمسية", "icon": "☀️"},
        ],
    },
    {
        "id": "hardware",
        "name_en": "Hardware",
        "name_ar": "ادوات",
        "icon": " ",
        "subcategories": [
            {
                "id": "tools",
                "name_en": "Hand Tools",
                "name_ar": "ادوات يدوية",
                "icon": " ",
                "sub_subcategories": [
                    {
                        "id": "wrenches",
                        "name_en": "Wrenches",
                        "name_ar": "مفاتيح ربط",
                        "sub_sub_subcategories": [
                            {
                                "id": "spanner_set",
                                "name_en": "Spanner Sets",
                                "name_ar": "طقم مفاتيح",
                            },
                            {
                                "id": "adjustable",
                                "name_en": "Adjustable Wrenches",
                                "name_ar": "مفاتيح قابلة للتعديل",
                            },
                        ],
                    },
                    {"id": "drills", "name_en": "Drills & Drivers", "name_ar": "ثفانات"},
                    {"id": "grinders", "name_en": "Grinders & Saws", "name_ar": "كشطات"},
                ],
            },
            {
                "id": "fasteners",
                "name_en": "Fasteners & Screws",
                "name_ar": "براغي",
                "icon": " ️",
                "sub_subcategories": [
                    {"id": "bolts", "name_en": "Bolts & Nuts", "name_ar": "براغي وصواميل"},
                    {"id": "screws", "name_en": "Wood Screws", "name_ar": "براغي خشب"},
                    {"id": "anchors", "name_en": "Wall Anchors", "name_ar": "توتير جدران"},
                ],
            },
            {"id": "locks", "name_en": "Locks & Keys", "name_ar": "اقفال", "icon": " "},
            {"id": "adhesives", "name_en": "Adhesives & Sealants", "name_ar": "غراء", "icon": " ️"},
        ],
    },
    {
        "id": "office_supplies",
        "name_en": "Office Supplies",
        "name_ar": "مستلزمات مكتبية",
        "icon": " ",
        "subcategories": [
            {"id": "paper", "name_en": "Paper & Notebooks", "name_ar": "ورق", "icon": " "},
            {"id": "printers", "name_en": "Printers & Ink", "name_ar": "طابعات", "icon": " ️"},
            {
                "id": "furniture_office",
                "name_en": "Office Furniture",
                "name_ar": "اثاث مكتبي",
                "icon": " ",
            },
            {"id": "stationery", "name_en": "Pens & Stationery", "name_ar": "اقلام", "icon": "✏️"},
        ],
    },
    {
        "id": "machinery",
        "name_en": "Machinery",
        "name_ar": "آلات",
        "icon": "⚙️",
        "subcategories": [
            {
                "id": "construction_machinery",
                "name_en": "Construction Machinery",
                "name_ar": "آلات بناء",
                "icon": " ",
                "sub_subcategories": [
                    {
                        "id": "excavators",
                        "name_en": "Excavators",
                        "name_ar": "حفارات",
                        "sub_sub_subcategories": [
                            {
                                "id": "mini_excavator",
                                "name_en": "Mini Excavators",
                                "name_ar": "حفارات صغيرة",
                            },
                            {
                                "id": "track_excavator",
                                "name_en": "Track Excavators",
                                "name_ar": "حفارات على سكك",
                            },
                        ],
                    },
                    {"id": "cranes", "name_en": "Cranes", "name_ar": "رافعات"},
                    {"id": "bulldozers", "name_en": "Bulldozers", "name_ar": "جرافات"},
                ],
            },
            {
                "id": "industrial",
                "name_en": "Industrial Machines",
                "name_ar": "آلات صناعية",
                "icon": "⚙️",
            },
            {
                "id": "pumps",
                "name_en": "Pumps & Compressors",
                "name_ar": "مضخات",
                "icon": " ",
                "sub_subcategories": [
                    {"id": "water_pump", "name_en": "Water Pumps", "name_ar": "مضخات مياه"},
                    {
                        "id": "air_compressor",
                        "name_en": "Air Compressors",
                        "name_ar": " compressors الهواء",
                    },
                    {"id": "centrifugal", "name_en": "Centrifugal Pumps", "name_ar": "مضحات أقطاب"},
                ],
            },
            {"id": "welding", "name_en": "Welding Equipment", "name_ar": "لحام", "icon": " "},
        ],
    },
    {
        "id": "textiles",
        "name_en": "Textiles",
        "name_ar": "منسوجات",
        "icon": " ️",
        "subcategories": [
            {"id": "fabric", "name_en": "Raw Fabric", "name_ar": "قماش", "icon": " ️"},
            {"id": "garments", "name_en": "Garments", "name_ar": "ملابس", "icon": " "},
            {
                "id": "industrial_textile",
                "name_en": "Industrial Textiles",
                "name_ar": "منسوجات صناعية",
                "icon": " ️",
            },
        ],
    },
    {
        "id": "packaging",
        "name_en": "Packaging",
        "name_ar": "تغليف",
        "icon": " ",
        "subcategories": [
            {"id": "boxes", "name_en": "Carton Boxes", "name_ar": "كراتين", "icon": " "},
            {"id": "labels", "name_en": "Labels & Stickers", "name_ar": "ملصقات", "icon": " ️"},
            {"id": "plastic_wrap", "name_en": "Plastic Wrap", "name_ar": "فيلم", "icon": " ️"},
        ],
    },
    {
        "id": "chemicals",
        "name_en": "Chemicals",
        "name_ar": "كيميائيات",
        "icon": " ",
        "subcategories": [
            {
                "id": "industrial_chem",
                "name_en": "Industrial Chemicals",
                "name_ar": "كيميائيات صناعية",
                "icon": " ",
            },
            {
                "id": "cleaning_chem",
                "name_en": "Cleaning Chemicals",
                "name_ar": "مواد تنظيف",
                "icon": " ️",
            },
        ],
    },
    {
        "id": "automotive",
        "name_en": "Automotive",
        "name_ar": "سيارات",
        "icon": " ",
        "subcategories": [
            {"id": "parts", "name_en": "Spare Parts", "name_ar": "قطع غيار", "icon": " "},
            {"id": "tires", "name_en": "Tires & Wheels", "name_ar": "اطارات", "icon": " ️"},
            {"id": "oils", "name_en": "Oils & Lubricants", "name_ar": "زيوت", "icon": " ️"},
        ],
    },
    {
        "id": "agriculture",
        "name_en": "Agriculture",
        "name_ar": "زراعة",
        "icon": " ",
        "subcategories": [
            {"id": "irrigation", "name_en": "Irrigation Systems", "name_ar": "ري", "icon": " ️"},
            {"id": "fertilizers", "name_en": "Fertilizers", "name_ar": "سماد", "icon": " "},
            {"id": "seeds", "name_en": "Seeds & Plants", "name_ar": "بذور", "icon": " "},
        ],
    },
    {
        "id": "food_beverage",
        "name_en": "Food & Beverage",
        "name_ar": "اطعمة ومشروبات",
        "icon": " ",
        "subcategories": [
            {
                "id": "dry_food",
                "name_en": "Dry Goods",
                "name_ar": "مواد جافة",
                "icon": " ",
                "sub_subcategories": [
                    {
                        "id": "grains",
                        "name_en": "Grains & Rice",
                        "name_ar": "حبوب",
                        "sub_sub_subcategories": [
                            {
                                "id": "basmati_rice",
                                "name_en": "Basmati Rice",
                                "name_ar": "ارز بسمتي",
                            },
                            {"id": "wheat_flour", "name_en": "Wheat Flour", "name_ar": "دقيق قمح"},
                            {"id": "sugar", "name_en": "Sugar", "name_ar": "سكر"},
                        ],
                    },
                    {"id": "spices", "name_en": "Spices & Seasonings", "name_ar": "بهارات"},
                    {"id": "canned_food", "name_en": "Canned Food", "name_ar": "معلبات"},
                ],
            },
            {"id": "beverages", "name_en": "Beverages", "name_ar": "مشروبات", "icon": " "},
            {"id": "dairy", "name_en": "Dairy Products", "name_ar": "ألبان", "icon": " "},
        ],
    },
    {
        "id": "furniture",
        "name_en": "Furniture",
        "name_ar": "اثاث",
        "icon": " ",
        "subcategories": [
            {
                "id": "office_furn",
                "name_en": "Office Furniture",
                "name_ar": "اثاث مكتبي",
                "icon": " ",
            },
            {"id": "home_furn", "name_en": "Home Furniture", "name_ar": "اثاث منزلي", "icon": " "},
            {"id": "outdoor", "name_en": "Outdoor Furniture", "name_ar": "اثاث خارجي", "icon": " "},
        ],
    },
    {
        "id": "safety",
        "name_en": "Safety Equipment",
        "name_ar": "معدات السلامة",
        "icon": " ",
        "subcategories": [
            {
                "id": "ppe",
                "name_en": "PPE (Helmets, Gloves)",
                "name_ar": "معدات حماية",
                "icon": " ",
            },
            {"id": "fire_ext", "name_en": "Fire Extinguishers", "name_ar": "طفايات", "icon": " "},
            {"id": "signs", "name_en": "Safety Signs", "name_ar": "لافتات", "icon": " "},
        ],
    },
    {
        "id": "plumbing",
        "name_en": "Plumbing",
        "name_ar": "سباكة",
        "icon": " ",
        "subcategories": [
            {"id": "pipes", "name_en": "Pipes & Fittings", "name_ar": "انابيب", "icon": " "},
            {"id": "valves", "name_en": "Valves & Taps", "name_ar": "صمامات", "icon": " ️"},
            {"id": "water_tanks", "name_en": "Water Tanks", "name_ar": "خزانات", "icon": " "},
        ],
    },
    {
        "id": "painting",
        "name_en": "Painting",
        "name_ar": "طلاء",
        "icon": " ",
        "subcategories": [
            {"id": "paint_cans", "name_en": "Paint Cans", "name_ar": "علب طلاء", "icon": " ️"},
            {"id": "brushes", "name_en": "Brushes & Rollers", "name_ar": "فرش", "icon": " "},
            {"id": "primers", "name_en": "Primers & Thinners", "name_ar": "مخفف طلاء", "icon": " ️"},
        ],
    },
    {
        "id": "cleaning",
        "name_en": "Cleaning",
        "name_ar": "تنظيف",
        "icon": " ",
        "subcategories": [
            {"id": "detergents", "name_en": "Detergents", "name_ar": "صابون", "icon": " ️"},
            {
                "id": "equipment",
                "name_en": "Cleaning Equipment",
                "name_ar": "معدات تنظيف",
                "icon": " ",
            },
        ],
    },
    {
        "id": "medical",
        "name_en": "Medical Supplies",
        "name_ar": "مستلزمات طبية",
        "icon": " ",
        "subcategories": [
            {"id": "first_aid", "name_en": "First Aid Kits", "name_ar": "احزان اولية", "icon": " "},
            {"id": "masks", "name_en": "Masks & Gloves", "name_ar": "كمامات", "icon": " ️"},
            {"id": "disinfectant", "name_en": "Disinfectants", "name_ar": "معقمات", "icon": " ️"},
        ],
    },
    {
        "id": "lighting",
        "name_en": "Lighting",
        "name_ar": "انارة",
        "icon": " ",
        "subcategories": [
            {"id": "led", "name_en": "LED Lights", "name_ar": "انارة LED", "icon": "💡"},
            {"id": "street", "name_en": "Street Lights", "name_ar": "انارة شوارع", "icon": " ️"},
            {
                "id": "industrial_light",
                "name_en": "Industrial Lighting",
                "name_ar": "انارة صناعية",
                "icon": " ️",
            },
        ],
    },
    {
        "id": "it_equipment",
        "name_en": "IT Equipment",
        "name_ar": "معدات تقنية",
        "icon": " ",
        "subcategories": [
            {"id": "computers", "name_en": "Computers & Laptops", "name_ar": "حواسيب", "icon": " ️"},
            {"id": "networking", "name_en": "Networking", "name_ar": "شبكات", "icon": " ️"},
            {"id": "printers_it", "name_en": "Printers", "name_ar": "طابعات", "icon": " ️"},
        ],
    },
    {
        "id": "security",
        "name_en": "Security",
        "name_ar": "امان",
        "icon": " ",
        "subcategories": [
            {"id": "cameras", "name_en": "CCTV Cameras", "name_ar": "كاميرات", "icon": " ️"},
            {"id": "alarms", "name_en": "Alarm Systems", "name_ar": "انذار", "icon": " ️"},
            {"id": "gates", "name_en": "Gates & Fences", "name_ar": "ابواب", "icon": " ️"},
        ],
    },
    {"id": "others", "name_en": "Others", "name_ar": "اخرى", "icon": " ", "subcategories": []},
    # ── NEW CATEGORIES (from Libya YP mapping) ──
    {
        "id": "energy",
        "name_en": "Energy",
        "name_ar": "طاقة",
        "icon": " ",
        "subcategories": [
            {
                "id": "solar_systems",
                "name_en": "Solar Systems",
                "name_ar": "أنظمة طاقة شمسية",
                "icon": "☀️",
            },
            {
                "id": "generators_energy",
                "name_en": "Generators & Turbines",
                "name_ar": "مولادات",
                "icon": "🔌",
            },
            {"id": "fuel", "name_en": "Fuel & Petroleum", "name_ar": "وقود وبترول", "icon": "⛽"},
        ],
    },
    {
        "id": "engineering",
        "name_en": "Engineering Products",
        "name_ar": "منتجات هندسية",
        "icon": " ",
        "subcategories": [
            {
                "id": "precision_tools",
                "name_en": "Precision Tools",
                "name_ar": "ادوات دقيقة",
                "icon": " ",
            },
            {
                "id": "measurement",
                "name_en": "Measurement Instruments",
                "name_ar": "أجهزة قياس",
                "icon": " ",
            },
            {
                "id": "compressors",
                "name_en": "Compressors & Pumps",
                "name_ar": "ضاغطات",
                "icon": " ",
            },
        ],
    },
    {
        "id": "glass",
        "name_en": "Glass & Mirrors",
        "name_ar": "زجاج",
        "icon": " ",
        "subcategories": [
            {"id": "flat_glass", "name_en": "Flat Glass", "name_ar": "زجاج مسطح", "icon": " "},
            {"id": "safety_glass", "name_en": "Safety Glass", "name_ar": "زجاج امني", "icon": " ️"},
            {"id": "mirror", "name_en": "Mirrors & Decorative", "name_ar": "مرايا", "icon": " ️"},
        ],
    },
    {
        "id": "home_appliances",
        "name_en": "Home Appliances",
        "name_ar": "ادوات منزلية",
        "icon": " ",
        "subcategories": [
            {
                "id": "kitchen",
                "name_en": "Kitchen Appliances",
                "name_ar": "ادوات مطبخ",
                "icon": " ",
            },
            {"id": "laundry", "name_en": "Laundry & Washing", "name_ar": "غسيل", "icon": " "},
            {"id": "cooling", "name_en": "Cooling & HVAC", "name_ar": "تبريد", "icon": "❄️"},
        ],
    },
    {
        "id": "metals",
        "name_en": "Metals & Minerals",
        "name_ar": "معادن",
        "icon": "⛏️",
        "subcategories": [
            {
                "id": "steel_products",
                "name_en": "Steel Products",
                "name_ar": "منتجات فولاذ",
                "icon": " ️",
            },
            {
                "id": "aluminum",
                "name_en": "Aluminum Products",
                "name_ar": "منتجات الومينيوم",
                "icon": " ",
            },
            {"id": "copper", "name_en": "Copper & Brass", "name_ar": "نحاس", "icon": " ️"},
        ],
    },
    {
        "id": "plastics",
        "name_en": "Plastics & Rubber",
        "name_ar": "بلاستيك",
        "icon": " ",
        "subcategories": [
            {
                "id": "packaging_plastic",
                "name_en": "Packaging Plastics",
                "name_ar": "بلاستيك تغليف",
                "icon": " ️",
            },
            {
                "id": "industrial_plastic",
                "name_en": "Industrial Plastics",
                "name_ar": "بلاستيك صناعي",
                "icon": " ",
            },
            {
                "id": "pipes_plastic",
                "name_en": "Plastic Pipes",
                "name_ar": "انابيب بلاستيك",
                "icon": " ",
            },
        ],
    },
    {
        "id": "transportation",
        "name_en": "Transportation & Logistics",
        "name_ar": "نقل",
        "icon": " ",
        "subcategories": [
            {
                "id": "logistics",
                "name_en": "Logistics Services",
                "name_ar": "خدمات لوجستية",
                "icon": " ",
            },
            {"id": "shipping", "name_en": "Shipping & Freight", "name_ar": "شحن", "icon": " "},
            {"id": "fleet", "name_en": "Fleet & Vehicles", "name_ar": "اساطيل", "icon": " "},
        ],
    },
]


@router.get("/categories")
def list_b2b_categories(db: Session = Depends(get_db)):
    """Return categories with live product counts from the database."""
    # Get counts per category
    rows = (
        db.query(Product.category, func.count(Product.id))
        .filter(Product.is_active)
        .group_by(Product.category)
        .all()
    )
    # Build count map keyed by lowercase name ("Building Materials" → "building materials")
    count_map = {r[0].lower(): r[1] for r in rows}

    return {
        "categories": [
            {**cat, "count": count_map.get(cat["name_en"].lower(), 0)} for cat in CATEGORY_META
        ]
    }


# ============================================================
# PLATFORM STATS (for landing page)
# ============================================================


@router.get("/stats")
def get_platform_stats(db: Session = Depends(get_db)):
    """Platform-wide statistics for the landing page."""
    from models import Supplier

    total_products = db.query(func.count(Product.id)).filter(Product.is_active).scalar() or 0
    total_suppliers = db.query(func.count(Supplier.id)).scalar() or 0
    total_categories = (
        db.query(func.count(func.distinct(Product.category))).filter(Product.is_active).scalar()
        or 0
    )
    total_orders = db.query(func.count(Order.id)).scalar() or 0

    return {
        "total_products": total_products,
        "total_suppliers": total_suppliers,
        "total_categories": total_categories,
        "total_orders": total_orders,
    }
