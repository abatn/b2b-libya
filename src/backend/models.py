"""
Libya B2B Platform - SQLAlchemy & Pydantic Models
All database models and API schemas in one place.
"""

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, ConfigDict
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text

from config import Base

# ============================================================
# HELPER
# ============================================================


def _utcnow():
    return datetime.now(timezone.utc)


# ============================================================
# SQLAlchemy ORM Models
# ============================================================


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="buyer")  # buyer | seller | admin
    business_name = Column(String(255), nullable=True)
    business_name_arabic = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)
    email_verified = Column(Boolean, default=False)
    email_verification_code = Column(String(10), nullable=True)
    email_verification_code_expires_at = Column(DateTime, nullable=True)
    two_factor_secret = Column(String(64), nullable=True)
    two_factor_enabled = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_utcnow)


class UserSession(Base):
    __tablename__ = "user_sessions"
    id = Column(Integer, primary_key=True, index=True)
    session_token = Column(String(128), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=_utcnow)
    expires_at = Column(DateTime, nullable=False)


class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    name_arabic = Column(String(255), nullable=True)
    description = Column(String(1000), nullable=True)
    description_arabic = Column(String(1000), nullable=True)
    price = Column(Float, nullable=False)
    currency = Column(String(3), default="LYD")
    category = Column(String(100), nullable=True)
    stock_quantity = Column(Integer, default=0)
    moq = Column(Integer, default=1)
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    image_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)


class ProductImage(Base):
    __tablename__ = "product_images"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    image_url = Column(String(500), nullable=False)
    is_primary = Column(Boolean, default=False)
    sort_order = Column(Integer, default=0)


class ProductVariant(Base):
    """Product variations: size, color, material, etc. (Alibaba-style)"""

    __tablename__ = "product_variants"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    name = Column(String(255), nullable=False)  # e.g. "Red / XL"
    sku = Column(String(100), nullable=True)
    price = Column(Float, nullable=False)  # variant-specific price
    stock_quantity = Column(Integer, default=0)
    moq = Column(Integer, default=1)
    image_url = Column(String(500), nullable=True)
    attributes = Column(
        Text, nullable=True
    )  # JSON: {"color": "red", "size": "XL", "material": "cotton"}
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)


class Review(Base):
    __tablename__ = "reviews"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)


class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String(50), unique=True, nullable=False)
    buyer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    total_amount = Column(Float, nullable=False)
    currency = Column(String(3), default="LYD")
    payment_method = Column(String(50), default="COD")
    status = Column(String(50), default="pending")
    delivery_address = Column(String(500), nullable=True)
    delivery_photo = Column(String(500), nullable=True)
    delivery_gps_lat = Column(Float, nullable=True)
    delivery_gps_lon = Column(Float, nullable=True)
    delivery_timestamp = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)


class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    supplier_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    product_name = Column(String(255), nullable=True)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    moq = Column(Integer, default=1)
    moq_met = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)


class Shipment(Base):
    """Shipment tracking with carrier integration (Alibaba-style)."""

    __tablename__ = "shipments"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    carrier = Column(String(50), nullable=False)  # DHL, FedEx, Aramex, local
    tracking_number = Column(String(100), nullable=True)
    status = Column(String(50), default="pending")  # pending/shipped/in_transit/delivered/returned
    weight_kg = Column(Float, nullable=True)
    shipping_cost = Column(Float, nullable=True)
    currency = Column(String(3), default="LYD")
    origin_city = Column(String(100), nullable=True)
    destination_city = Column(String(100), nullable=True)
    estimated_days = Column(Integer, nullable=True)
    shipped_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow)


class ShipmentEvent(Base):
    """Individual tracking events for a shipment."""

    __tablename__ = "shipment_events"
    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id"), nullable=False)
    status = Column(String(50), nullable=False)
    location = Column(String(255), nullable=True)
    description = Column(String(500), nullable=True)
    event_time = Column(DateTime, default=_utcnow)


class ShippingRate(Base):
    """Carrier shipping rates (weight-based)."""

    __tablename__ = "shipping_rates"
    id = Column(Integer, primary_key=True, index=True)
    carrier = Column(String(50), nullable=False)
    origin_city = Column(String(100), nullable=False)
    destination_city = Column(String(100), nullable=False)
    base_cost = Column(Float, nullable=False)
    cost_per_kg = Column(Float, nullable=False)
    min_cost = Column(Float, nullable=False)
    estimated_days = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), nullable=False)
    user_message = Column(String(2000), nullable=False)
    bot_response = Column(String(2000), nullable=False)
    is_arabic = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)


class Supplier(Base):
    __tablename__ = "suppliers"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    name = Column(String(255), nullable=False)
    name_arabic = Column(String(255), nullable=True)
    description = Column(String(1000), nullable=True)
    location = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    website = Column(String(500), nullable=True)
    category = Column(String(100), nullable=True)
    categories = Column(Text, nullable=True)  # JSON array of category IDs
    logo_url = Column(String(500), nullable=True)
    cover_image_url = Column(String(500), nullable=True)
    gallery_images = Column(Text, nullable=True)  # JSON array of image URLs
    rating = Column(Float, default=0.0)
    rating_count = Column(Integer, default=0)
    is_verified = Column(Boolean, default=False)
    verification_level = Column(Integer, default=0)  # 0-4
    verification_documents = Column(Text, nullable=True)  # JSON
    verified_at = Column(DateTime, nullable=True)
    verified_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    years_on_platform = Column(Integer, default=1)
    product_count = Column(Integer, default=0)
    employee_count = Column(Integer, nullable=True)
    annual_revenue = Column(Float, nullable=True)
    year_established = Column(Integer, nullable=True)
    business_registration = Column(String(255), nullable=True)
    tax_id = Column(String(100), nullable=True)
    certifications = Column(Text, nullable=True)  # JSON
    response_time_hours = Column(Integer, nullable=True)
    on_time_delivery_rate = Column(Float, nullable=True)
    total_transactions = Column(Integer, default=0)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    created_at = Column(DateTime, default=_utcnow)


class RFQ(Base):
    __tablename__ = "rfqs"
    id = Column(Integer, primary_key=True, index=True)
    buyer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    product_name = Column(String(255), nullable=False)
    product_name_arabic = Column(String(255), nullable=True)
    quantity = Column(Integer, nullable=False)
    delivery_address = Column(String(500), nullable=True)
    message = Column(String(1000), nullable=True)
    status = Column(String(50), default="pending")
    created_at = Column(DateTime, default=_utcnow)


class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(Integer, primary_key=True, index=True)
    buyer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    supplier_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    last_message_at = Column(DateTime, default=_utcnow)
    last_message_text = Column(String, nullable=True)
    unread_count = Column(Integer, default=0)


class LoginHistory(Base):
    __tablename__ = "login_history"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    success = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)


class Cart(Base):
    __tablename__ = "carts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)


class CartItem(Base):
    __tablename__ = "cart_items"
    id = Column(Integer, primary_key=True, index=True)
    cart_id = Column(Integer, ForeignKey("carts.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    added_at = Column(DateTime, default=_utcnow)
    last_message_text = Column(String(500), nullable=True)
    unread_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=_utcnow)


class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    sender_type = Column(String(20), nullable=False)
    sender_id = Column(Integer, nullable=True)
    text = Column(String(2000), nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_utcnow)


class Escrow(Base):
    __tablename__ = "escrow_transactions"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    buyer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    supplier_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="LYD")
    status = Column(String(50), default="pending")  # pending|released|refunded|disputed
    note = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    released_at = Column(DateTime, nullable=True)
    refunded_at = Column(DateTime, nullable=True)
    disputed_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    resolution_reason = Column(String(500), nullable=True)
    # Dispute fields
    dispute_reason = Column(String(50), nullable=True)  # quality|damage|wrong_item|not_delivered
    dispute_description = Column(String(2000), nullable=True)
    dispute_evidence = Column(Text, nullable=True)  # JSON array of image URLs
    # Multi-level escalation
    escalation_level = Column(
        Integer, default=0
    )  # 0=none, 1=direct_negotiation, 2=mediation, 3=third_party_inspection, 4=arbitration
    escalation_deadline = Column(DateTime, nullable=True)  # 30-day window after delivery
    last_escalated_at = Column(DateTime, nullable=True)


class EscrowHistory(Base):
    """Audit trail for every escrow status change."""

    __tablename__ = "escrow_history"
    id = Column(Integer, primary_key=True, index=True)
    escrow_id = Column(Integer, ForeignKey("escrow_transactions.id"), nullable=False)
    action = Column(
        String(50), nullable=False
    )  # created|released|refunded|disputed|resolved|auto_expired
    old_status = Column(String(50), nullable=True)
    new_status = Column(String(50), nullable=False)
    performed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    note = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=_utcnow)


class DisputeMessage(Base):
    """Messages between buyer and supplier during a dispute."""

    __tablename__ = "dispute_messages"
    id = Column(Integer, primary_key=True, index=True)
    escrow_id = Column(Integer, ForeignKey("escrow_transactions.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    sender_type = Column(String(20), nullable=False)  # buyer|supplier|admin
    text = Column(String(2000), nullable=False)
    created_at = Column(DateTime, default=_utcnow)


class SupplierReview(Base):
    """Reviews for suppliers from buyers."""

    __tablename__ = "supplier_reviews"
    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5
    comment = Column(String(1000), nullable=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)


class DisputeEscalation(Base):
    """Tracks escalation steps in a dispute (Alibaba-style multi-level)."""

    __tablename__ = "dispute_escalations"
    id = Column(Integer, primary_key=True, index=True)
    escrow_id = Column(Integer, ForeignKey("escrow_transactions.id"), nullable=False)
    level = Column(Integer, nullable=False)  # 1=direct, 2=mediation, 3=inspection, 4=arbitration
    level_name = Column(
        String(50), nullable=False
    )  # direct_negotiation, mediation, third_party_inspection, arbitration
    initiated_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String(50), default="active")  # active|resolved|expired
    description = Column(String(2000), nullable=True)
    resolution = Column(String(2000), nullable=True)
    resolved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    deadline = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    resolved_at = Column(DateTime, nullable=True)


class PaymentTransaction(Base):
    """Payment transaction log for all payment methods."""

    __tablename__ = "payment_transactions"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    provider = Column(String(50), nullable=False)  # cod|sadad|fawry|moamalat|mock
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="LYD")
    status = Column(String(50), default="pending")  # pending|processing|completed|failed|refunded
    provider_reference = Column(String(255), nullable=True)
    provider_response = Column(Text, nullable=True)
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    completed_at = Column(DateTime, nullable=True)
    refunded_at = Column(DateTime, nullable=True)


# ============================================================
# Pydantic Schemas
# ============================================================


# --- Auth ---
class UserCreate(BaseModel):
    username: str
    email: Optional[str] = None
    password: str
    role: str = "buyer"
    business_name: Optional[str] = None
    business_name_arabic: Optional[str] = None
    phone: Optional[str] = None


class UserLogin(BaseModel):
    username: str
    password: str
    remember_me: bool = False


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    email: Optional[str] = None
    role: str
    business_name: Optional[str] = None
    is_active: bool
    created_at: datetime


class SessionResponse(BaseModel):
    session_token: str
    user: UserResponse


class EmailVerifyRequest(BaseModel):
    code: str


class ProfileUpdateRequest(BaseModel):
    role: Optional[str] = None
    business_name: Optional[str] = None
    business_name_arabic: Optional[str] = None
    phone: Optional[str] = None


class TwoFASetupResponse(BaseModel):
    secret: str
    qr_url: str


class TwoFAVerifyRequest(BaseModel):
    code: str


class LoginHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    success: bool
    created_at: datetime


# --- Product ---
class ProductCreate(BaseModel):
    name: str
    name_arabic: Optional[str] = None
    description: Optional[str] = None
    description_arabic: Optional[str] = None
    price: float
    currency: str = "LYD"
    category: Optional[str] = None
    stock_quantity: int = 0
    moq: int = 1
    seller_id: Optional[int] = None
    image_url: Optional[str] = None


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    name_arabic: Optional[str] = None
    description: Optional[str] = None
    price: float
    currency: str
    category: Optional[str] = None
    stock_quantity: int
    moq: int
    seller_id: Optional[int] = None
    image_url: Optional[str] = None
    is_active: bool
    created_at: datetime


# --- Product Variant ---
class ProductVariantCreate(BaseModel):
    name: str
    sku: Optional[str] = None
    price: float
    stock_quantity: int = 0
    moq: int = 1
    image_url: Optional[str] = None
    attributes: Optional[str] = None  # JSON string


class ProductVariantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    product_id: int
    name: str
    sku: Optional[str] = None
    price: float
    stock_quantity: int
    moq: int
    image_url: Optional[str] = None
    attributes: Optional[str] = None
    is_active: bool
    created_at: datetime


# --- Review ---
class ReviewCreate(BaseModel):
    product_id: int
    rating: int
    comment: Optional[str] = None


class ReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    product_id: int
    user_id: int
    rating: int
    comment: Optional[str] = None
    created_at: datetime


class ProductRatingSummary(BaseModel):
    average: float
    count: int
    distribution: dict  # {1: n, 2: n, 3: n, 4: n, 5: n}


# --- Order ---
class OrderItemCreate(BaseModel):
    product_id: int
    supplier_id: Optional[int] = None
    quantity: int
    unit_price: float
    moq: int = 1


class OrderCreate(BaseModel):
    buyer_id: Optional[int] = None
    seller_id: Optional[int] = None
    total_amount: float
    currency: str = "LYD"
    payment_method: str = "COD"
    delivery_address: Optional[str] = None
    items: Optional[list[OrderItemCreate]] = None


class OrderItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    order_id: int
    product_id: int
    supplier_id: Optional[int] = None
    product_name: Optional[str] = None
    quantity: int
    unit_price: float
    moq: int
    moq_met: bool


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    order_number: str
    total_amount: float
    currency: str
    payment_method: str
    status: str
    buyer_id: Optional[int] = None
    seller_id: Optional[int] = None
    created_at: datetime


# --- Chat ---
class ChatRequest(BaseModel):
    session_id: str
    message: str
    is_arabic: bool = True


class ChatResponse(BaseModel):
    session_id: str
    response: str
    is_arabic: bool
    created_at: datetime


# --- Supplier ---
class SupplierCreate(BaseModel):
    name: str
    name_arabic: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    city: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    category: Optional[str] = None
    categories: Optional[list[str]] = None  # Multi-category support
    logo_url: Optional[str] = None
    cover_image_url: Optional[str] = None
    user_id: Optional[int] = None
    is_verified: bool = False
    verification_level: int = 0
    employee_count: Optional[int] = None
    annual_revenue: Optional[float] = None
    year_established: Optional[int] = None
    business_registration: Optional[str] = None
    tax_id: Optional[str] = None
    response_time_hours: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class SupplierImportItem(BaseModel):
    name: str
    name_arabic: Optional[str] = None
    description: Optional[str] = None
    city: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    category: Optional[str] = None
    location: Optional[str] = None


class SupplierResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    name_arabic: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    city: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    category: Optional[str] = None
    categories: Optional[list[str]] = None
    logo_url: Optional[str] = None
    cover_image_url: Optional[str] = None
    rating: float
    rating_count: int
    is_verified: bool
    verification_level: int
    years_on_platform: int
    product_count: int
    employee_count: Optional[int] = None
    annual_revenue: Optional[float] = None
    year_established: Optional[int] = None
    response_time_hours: Optional[int] = None
    on_time_delivery_rate: Optional[float] = None
    total_transactions: int
    created_at: datetime


# --- RFQ ---
class RFQCreate(BaseModel):
    buyer_id: Optional[int] = None
    product_name: str
    product_name_arabic: Optional[str] = None
    quantity: int
    delivery_address: Optional[str] = None
    message: Optional[str] = None


class RFQResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    buyer_id: Optional[int] = None
    product_name: str
    product_name_arabic: Optional[str] = None
    quantity: int
    delivery_address: Optional[str] = None
    message: Optional[str] = None
    status: str
    created_at: datetime


# --- Message ---
class MessageCreate(BaseModel):
    sender_type: str
    sender_id: Optional[int] = None
    text: str


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    conversation_id: int
    sender_type: str
    sender_id: Optional[int] = None
    text: str
    is_read: bool
    created_at: datetime


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    buyer_id: Optional[int] = None
    supplier_id: Optional[int] = None
    last_message_at: Optional[datetime] = None
    last_message_text: Optional[str] = None
    unread_count: int
    created_at: datetime


# --- Cart ---
class CartItemCreate(BaseModel):
    product_id: int
    quantity: int = 1
    supplier_id: Optional[int] = None


class CartItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    product_id: int
    quantity: int
    product_name: Optional[str] = None
    product_price: Optional[float] = None
    product_image: Optional[str] = None
    supplier_id: Optional[int] = None
    supplier_name: Optional[str] = None
    moq: int = 1
    moq_met: bool = True
    added_at: datetime


class CartResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    items: list[CartItemResponse]
    total: float
    item_count: int
    created_at: datetime


# --- Escrow ---
class EscrowCreate(BaseModel):
    order_id: int
    amount: float
    note: Optional[str] = None


class EscrowResolveRequest(BaseModel):
    resolution: str  # "release" | "refund"
    reason: str = ""
    amount: Optional[float] = None  # Partial refund amount (None = full)


class EscrowHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    escrow_id: int
    action: str
    old_status: Optional[str] = None
    new_status: str
    performed_by: Optional[int] = None
    note: Optional[str] = None
    created_at: datetime


class EscrowResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    order_id: int
    buyer_id: int
    supplier_id: int
    amount: float
    currency: str
    status: str
    note: Optional[str] = None
    created_at: datetime
    released_at: Optional[datetime] = None
    refunded_at: Optional[datetime] = None
    disputed_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[int] = None
    resolution_reason: Optional[str] = None


class DisputeMessageCreate(BaseModel):
    text: str


class DisputeMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    escrow_id: int
    sender_id: int
    sender_type: str
    text: str
    created_at: datetime


# --- Shipping / Logistics ---
class ShipmentCreate(BaseModel):
    order_id: int
    carrier: str
    tracking_number: Optional[str] = None
    weight_kg: Optional[float] = None
    shipping_cost: Optional[float] = None
    currency: str = "LYD"
    origin_city: Optional[str] = None
    destination_city: Optional[str] = None
    estimated_days: Optional[int] = None


class ShipmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    order_id: int
    carrier: str
    tracking_number: Optional[str] = None
    status: str
    weight_kg: Optional[float] = None
    shipping_cost: Optional[float] = None
    currency: str
    origin_city: Optional[str] = None
    destination_city: Optional[str] = None
    estimated_days: Optional[int] = None
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class ShipmentEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    shipment_id: int
    status: str
    location: Optional[str] = None
    description: Optional[str] = None
    event_time: datetime


class ShippingRateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    carrier: str
    origin_city: str
    destination_city: str
    base_cost: float
    cost_per_kg: float
    min_cost: float
    estimated_days: int


class SupplierReviewCreate(BaseModel):
    rating: int  # 1-5
    comment: Optional[str] = None
    order_id: Optional[int] = None


class SupplierReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    supplier_id: int
    user_id: int
    rating: int
    comment: Optional[str] = None
    order_id: Optional[int] = None
    created_at: datetime


# --- Dispute Escalation ---
class EscalationCreate(BaseModel):
    escrow_id: int
    level: int  # 1=direct, 2=mediation, 3=inspection, 4=arbitration
    description: Optional[str] = None


class EscalationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    escrow_id: int
    level: int
    level_name: str
    initiated_by: int
    status: str
    description: Optional[str] = None
    resolution: Optional[str] = None
    resolved_by: Optional[int] = None
    deadline: Optional[datetime] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None


# --- Payment ---
class PaymentTransactionCreate(BaseModel):
    order_id: int
    amount: float
    method: str = "cod"
    currency: str = "LYD"
    description: str = ""


class PaymentTransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    order_id: int
    user_id: int
    provider: str
    amount: float
    currency: str
    status: str
    provider_reference: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    refunded_at: Optional[datetime] = None


# ── Push Notifications ──────────────────────────────────────────────


class PushSubscription(Base):
    """Web Push subscription for a user (one per device)."""

    __tablename__ = "push_subscriptions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    endpoint = Column(String(500), nullable=False, unique=True)
    p256dh = Column(String(255), nullable=False)
    auth = Column(String(255), nullable=False)
    user_agent = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)
    last_used_at = Column(DateTime, nullable=True)


class Notification(Base):
    """Notification log for a user (in-app + push)."""

    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    type = Column(String(50), nullable=False)  # order_status|escrow|message|system
    title = Column(String(200), nullable=False)
    title_ar = Column(String(200), nullable=True)
    body = Column(String(500), nullable=False)
    body_ar = Column(String(500), nullable=True)
    url = Column(String(500), nullable=True)
    is_read = Column(Boolean, default=False)
    is_pushed = Column(Boolean, default=False)
    related_id = Column(Integer, nullable=True)  # order_id, escrow_id, etc.
    created_at = Column(DateTime, default=_utcnow)


# ── Pydantic Schemas: Notifications ─────────────────────────────────


class PushSubscriptionCreate(BaseModel):
    endpoint: str
    p256dh: str
    auth: str
    user_agent: Optional[str] = None


class PushSubscriptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    is_active: bool
    created_at: datetime


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    type: str
    title: str
    title_ar: Optional[str] = None
    body: str
    body_ar: Optional[str] = None
    url: Optional[str] = None
    is_read: bool
    is_pushed: bool
    related_id: Optional[int] = None
    created_at: datetime
