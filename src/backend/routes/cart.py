"""
Libya B2B Platform - Cart Routes
Server-side cart management.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from config import get_db
from models import Cart, CartItem, CartItemCreate, CartItemResponse, CartResponse, Product, User
from routes.auth_routes import get_current_user

router = APIRouter(prefix="/api/cart", tags=["cart"])


def _get_or_create_cart(user_id: int, db: Session) -> Cart:
    """Get existing cart or create new one."""
    cart = db.query(Cart).filter(Cart.user_id == user_id).first()
    if not cart:
        cart = Cart(user_id=user_id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    return cart


@router.get("", response_model=CartResponse)
def get_cart(user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Get current user's cart with items and total."""
    cart = _get_or_create_cart(user.id, db)
    items = db.query(CartItem).filter(CartItem.cart_id == cart.id).all()

    cart_items = []
    total = 0.0
    for item in items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if product:
            item_total = product.price * item.quantity
            total += item_total
            # Get supplier name
            supplier_name = None
            supplier_id = getattr(item, "supplier_id", None)
            if supplier_id:
                supplier = db.query(User).filter(User.id == supplier_id).first()
                if supplier:
                    supplier_name = supplier.business_name or supplier.username
            moq = product.moq or 1
            cart_items.append(
                CartItemResponse(
                    id=item.id,
                    product_id=item.product_id,
                    quantity=item.quantity,
                    product_name=product.name,
                    product_price=product.price,
                    product_image=product.image_url,
                    supplier_id=supplier_id,
                    supplier_name=supplier_name,
                    moq=moq,
                    moq_met=item.quantity >= moq,
                    added_at=item.added_at,
                )
            )

    return CartResponse(
        id=cart.id,
        user_id=cart.user_id,
        items=cart_items,
        total=total,
        item_count=len(cart_items),
        created_at=cart.created_at,
    )


@router.post("/items", response_model=CartItemResponse)
def add_to_cart(
    item_data: CartItemCreate, user=Depends(get_current_user), db: Session = Depends(get_db)
):
    """Add item to cart or update quantity if already exists."""
    product = (
        db.query(Product).filter(Product.id == item_data.product_id, Product.is_active).first()
    )
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # MOQ validation
    moq = product.moq or 1
    if item_data.quantity < moq:
        raise HTTPException(
            status_code=400,
            detail=f"Minimum order quantity is {moq}. You ordered {item_data.quantity}.",
        )

    # Determine supplier_id: use provided or fall back to product seller_id
    supplier_id = item_data.supplier_id or product.seller_id

    cart = _get_or_create_cart(user.id, db)
    existing_item = (
        db.query(CartItem)
        .filter(
            CartItem.cart_id == cart.id,
            CartItem.product_id == item_data.product_id,
        )
        .first()
    )

    if existing_item:
        new_qty = existing_item.quantity + item_data.quantity
        if new_qty < moq:
            raise HTTPException(
                status_code=400,
                detail=f"Minimum order quantity is {moq}. Combined quantity would be {new_qty}.",
            )
        existing_item.quantity = new_qty
        db.commit()
        db.refresh(existing_item)
        item = existing_item
    else:
        item = CartItem(
            cart_id=cart.id,
            product_id=item_data.product_id,
            quantity=item_data.quantity,
        )
        # Store supplier_id if column exists
        if hasattr(item, "supplier_id"):
            item.supplier_id = supplier_id
        db.add(item)
        db.commit()
        db.refresh(item)

    supplier_name = None
    if supplier_id:
        supplier = db.query(User).filter(User.id == supplier_id).first()
        if supplier:
            supplier_name = supplier.business_name or supplier.username

    return CartItemResponse(
        id=item.id,
        product_id=item.product_id,
        quantity=item.quantity,
        product_name=product.name,
        product_price=product.price,
        product_image=product.image_url,
        supplier_id=supplier_id,
        supplier_name=supplier_name,
        moq=moq,
        moq_met=item.quantity >= moq,
        added_at=item.added_at,
    )


@router.put("/items/{item_id}")
def update_cart_item(
    item_id: int, quantity: int, user=Depends(get_current_user), db: Session = Depends(get_db)
):
    """Update cart item quantity."""
    cart = _get_or_create_cart(user.id, db)
    item = db.query(CartItem).filter(CartItem.id == item_id, CartItem.cart_id == cart.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found")

    if quantity <= 0:
        db.delete(item)
    else:
        item.quantity = quantity

    db.commit()
    return {"message": "Cart updated"}


@router.delete("/items/{item_id}")
def remove_from_cart(item_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Remove item from cart."""
    cart = _get_or_create_cart(user.id, db)
    item = db.query(CartItem).filter(CartItem.id == item_id, CartItem.cart_id == cart.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found")

    db.delete(item)
    db.commit()
    return {"message": "Item removed from cart"}


@router.delete("")
def clear_cart(user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Clear all items from cart."""
    cart = _get_or_create_cart(user.id, db)
    db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()
    db.commit()
    return {"message": "Cart cleared"}
