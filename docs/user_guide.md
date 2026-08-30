# Libya B2B Platform — User Guide

**Version:** v3.1 | **Last Updated:** 24 August 2026

---

## Table of Contents

1. [Getting Started](#1-getting-started)
2. [Registration](#2-registration)
3. [Login](#3-login)
4. [Browse Products](#4-browse-products)
5. [Shopping Cart & Checkout](#5-shopping-cart--checkout)
6. [Order Tracking](#6-order-tracking)
7. [Seller Features](#7-seller-features)
8. [Buyer Features](#8-buyer-features)
9. [B2B Features](#9-b2b-features)
10. [Offline Mode](#10-offline-mode)
11. [Arabic Chatbot](#11-arabic-chatbot)
12. [Troubleshooting](#12-troubleshooting)

---

## 1. Getting Started

### System Requirements
- **Browser:** Chrome, Firefox, Safari, or Edge (latest version)
- **Internet:** Required for first load, then works offline
- **Mobile:** Responsive design works on phones and tablets

### Accessing the Platform
- **Frontend:** http://localhost:3000 (or your domain)
- **API Docs:** http://localhost:8000/docs (Swagger UI)
- **Health Check:** http://localhost:8000/health

### First Visit
1. Open the platform URL in your browser
2. You'll see the landing page with product categories
3. Click **Register** to create an account or **Login** if you already have one

---

## 2. Registration

The registration is a **3-step process**:

### Step 1: Account Details
1. Click **Register** on the landing page
2. Enter your **email address**
3. Create a **password** (strength meter shows security level)
4. **Confirm your password**
5. Click **Next**

### Step 2: Email Verification
1. Check your email inbox for a **6-digit verification code**
2. Enter the code in the verification form
3. Click **Verify**
4. If you didn't receive the code, click **Resend Code** (60-second cooldown)

> **Note:** The verification code expires after **10 minutes**. Request a new one if expired.

### Step 3: Profile Setup
1. Select your **role**: Buyer or Seller
2. Enter your **Company Name** (English)
3. Enter your **Company Name** (Arabic) — optional
4. Enter your **Phone Number**
5. Select your **Country**
6. **Accept the Terms & Conditions** (required)
7. Click **Create Account**

### After Registration
- **Buyers** are redirected to `/buyer` (Buyer Dashboard)
- **Sellers** are redirected to `/seller` (Seller Dashboard)

---

## 3. Login

1. Click **Login** on the landing page
2. Enter your **username** (email)
3. Enter your **password**
4. Check **Remember Me** for 30-day session (optional)
5. Click **Login**

### Two-Factor Authentication (2FA)
If you've enabled 2FA:
1. After entering username/password, you'll be prompted for a **6-digit code**
2. Open your authenticator app (Google Authenticator, Authy, etc.)
3. Enter the code from the app
4. Click **Verify**

### Password Reset
1. Click **Forgot Password** on the login page
2. Enter your email address
3. Check your inbox for the reset link
4. Click the link and create a new password

---

## 4. Browse Products

### Product Catalog
1. Click **Products** in the navigation
2. Browse by **category** (21 categories available)
3. Use the **search bar** for fuzzy text search
4. **Filter** by price range, MOQ, or category
5. **Sort** by name, price (ascending/descending)

### Product Details
Click any product to see:
- **Product name** (English + Arabic)
- **Price** in LYD (Libyan Dinar)
- **Description**
- **Stock quantity**
- **MOQ** (Minimum Order Quantity)
- **Supplier information**
- **Reviews and ratings** (1-5 stars)
- **Bulk pricing** (10+, 50+, 100+ units)

### Search
The search supports:
- **Exact matches** (highest priority)
- **Contains** matches
- **Fuzzy matching** (handles typos)
- **Arabic text** search
- Search across products AND suppliers

---

## 5. Shopping Cart & Checkout

### Adding to Cart
1. On a product page, select **quantity**
2. Click **Add to Cart**
3. The cart icon updates with item count

### Managing Cart
1. Click **Cart** in the navigation
2. View all items with prices and subtotals
3. **Update quantity** for any item
4. **Remove items** you don't want
5. View **total amount** in LYD

### Checkout (COD)
1. Click **Proceed to Checkout**
2. Enter your **delivery address**
3. Review your order summary
4. Select **Cash on Delivery (COD)** as payment method
5. Click **Place Order**
6. You'll receive an **order number** (format: `LYB-YYYYMMDD-XXXXXX`)

> **Note:** Payment is made in cash when the order is delivered. No online payment required.

---

## 6. Order Tracking

### Track by Order Number
1. Go to **Tracking** page
2. Enter your **order number** (e.g., `LYB-20260824-123456`)
3. View current **status**: Pending → Processing → Shipped → Delivered
4. See **delivery details** (photo, GPS coordinates when delivered)

### QR Code Tracking
1. Each order has a unique **QR code**
2. Scan the QR code with your phone camera
3. View order details and status instantly

### Order Statuses
- **pending** — Order placed, awaiting processing
- **processing** — Order is being prepared
- **shipped** — Order is on the way
- **delivered** — Order has been delivered (confirmed with photo + GPS)

---

## 7. Seller Features

### Seller Dashboard
Access at `/seller` after login as a seller:
- **Total products** listed
- **Active products** count
- **Total orders** received
- **Total revenue** in LYD
- **Recent orders** list

### Add Products
1. Go to **Seller Dashboard**
2. Click **Add Product**
3. Fill in:
   - Product name (English + Arabic)
   - Description (English + Arabic)
   - Price in LYD
   - Category (select from 21 categories)
   - Stock quantity
   - MOQ (Minimum Order Quantity)
4. Upload **product images**
5. Click **Save**

### Manage Orders
1. View **incoming orders** in the dashboard
2. Update order **status** (processing, shipped)
3. Confirm **delivery** with photo + GPS coordinates

### Supplier Profile
Create a supplier profile to appear in the supplier directory:
1. Go to **Suppliers** → **Create Profile**
2. Enter company name, description, location
3. Your profile appears in the supplier directory with ratings

---

## 8. Buyer Features

### Buyer Dashboard
Access at `/buyer` after login as a buyer:
- **Total orders** placed
- **Total spent** in LYD
- **Pending orders** count
- **Delivered orders** count
- **Recent orders** list

### Request for Quotation (RFQ)
1. Go to **RFQ** → **New RFQ**
2. Enter:
   - Product name (English + Arabic)
   - Quantity needed
   - Delivery address
   - Additional message
3. Submit the RFQ
4. Suppliers will respond with quotes

### Reviews & Ratings
After receiving an order:
1. Go to the product page
2. Click **Write a Review**
3. Select **1-5 stars**
4. Add a **comment** (optional)
5. Submit your review

---

## 9. B2B Features

### Supplier Directory
- Browse **verified suppliers** at `/suppliers`
- Sort by **rating**, **product count**, or **name**
- View supplier **profiles** with products and reviews

### Messaging
1. Go to **Messages** in the navigation
2. Start a **conversation** with a supplier
3. Send and receive messages in real-time
4. View **unread message counts**

### Bulk Pricing
- View **bulk pricing tiers** for products
- **10+ units:** 5% discount
- **50+ units:** 10% discount
- **100+ units:** 15% discount

### Inventory Management
- View **stock levels** for all products
- Identify **low stock** items (< 10 units)
- Track **inventory value** in LYD

---

## 10. Offline Mode

The platform is designed for areas with limited internet connectivity.

### What Works Offline
- ✅ **Browse products** (cached from last sync)
- ✅ **View product details**
- ✅ **Add to cart** (queued for sync)
- ✅ **View order history** (cached)
- ✅ **View chat history** (cached)

### What Requires Internet
- ❌ **Place order** (syncs when online)
- ❌ **Search products** (live search)
- ❌ **Send messages** (queued for sync)
- ❌ **Upload images**
- ❌ **Email verification**

### How Sync Works
1. When you perform an action offline, it's saved locally
2. When internet returns, the **Delta Sync** engine sends only changes
3. **Conflict resolution:** Last write wins (most recent change saved)
4. **Retry:** Failed syncs are retried up to 3 times

### Sync Status
- ⏳ **Pending** — Waiting to sync
- 🔄 **In Progress** — Currently syncing
- ✅ **Completed** — Successfully synced
- ❌ **Failed** — Sync failed (will retry)

---

## 11. Arabic Chatbot

The platform includes an AI-powered Arabic chatbot.

### How to Use
1. Click the **chat icon** on any page
2. Type your message in **Arabic** or **English**
3. The chatbot responds with relevant information

### Supported Intents
- **Greetings** — مرحبا، السلام عليكم
- **Product inquiries** — عرض المنتجات، الأسعار
- **Order status** — حالة الطلب، التتبع
- **Delivery information** — التوصيل، العنوان
- **Pricing** — الأسعار، الخصومات
- **Categories** — فئات المنتجات
- **Help** — مساعدة، دعم

### Chat Features
- **Session-based** — Your conversation is saved
- **Language detection** — Automatically detects Arabic/English
- **Suggestions** — Get relevant follow-up questions
- **Clear history** — Delete your chat history

---

## 12. Troubleshooting

### Common Issues

#### "Not authenticated" error
- Your session may have expired
- **Solution:** Log in again

#### "Username already taken"
- The username is already registered
- **Solution:** Use a different username or reset password

#### "Verification code expired"
- The 6-digit code is valid for 10 minutes
- **Solution:** Click "Resend Code" to get a new one

#### "Rate limit" error on verification
- You requested too many codes too quickly
- **Solution:** Wait 60 seconds before requesting again

#### Cart items not syncing
- You may be offline
- **Solution:** Items are queued and will sync when online

#### QR code not scanning
- Ensure good lighting
- Hold the camera steady
- Try zooming in on the QR code

### Getting Help
- **FAQ:** Visit `/faq` for frequently asked questions
- **Contact:** Use the messaging system to contact suppliers
- **Support:** Email support@libya-b2b.com (placeholder)

---

## Quick Reference

### Keyboard Shortcuts
| Shortcut | Action |
|----------|--------|
| `Ctrl + K` | Search |
| `Ctrl + /` | Toggle chat |
| `Esc` | Close modals |

### Navigation
| Page | URL | Description |
|------|-----|-------------|
| Home | `/landing` | Landing page |
| Products | `/products` | Product catalog |
| Cart | `/cart` | Shopping cart |
| Checkout | `/checkout` | Order checkout |
| Tracking | `/tracking` | Order tracking |
| Seller | `/seller` | Seller dashboard |
| Buyer | `/buyer` | Buyer dashboard |
| Register | `/register` | New account |
| Login | `/login` | Sign in |
| Suppliers | `/suppliers` | Supplier directory |
| RFQ | `/rfq` | Request for Quotation |
| Messages | `/messages` | Messaging inbox |

### Arabic Routes
All pages are available in Arabic by adding `/ar/` prefix:
- `/ar/landing` — Arabic homepage
- `/ar/products` — Arabic product catalog
- `/ar/cart` — Arabic cart
- `/ar/register` — Arabic registration
