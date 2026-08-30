"""
Libya B2B Platform - Arabic Chatbot Module
Sprint 3: KI-Chatbot mit Intent-Recognition (Offline-first)
Projektversion: v1.3

CPU-basiert, Open-Source (Apache 2.0 / MIT)
"""

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# ============================================================
# INTENT DEFINITIONS
# ============================================================


@dataclass
class Intent:
    """Intent fuer Chatbot"""

    name: str
    keywords_ar: List[str]
    keywords_en: List[str]
    response_ar: str
    response_en: str
    follow_up: Optional[str] = None


# ============================================================
# INTENT DATABASE (Offline-kompatibel)
# ============================================================

INTENTS: List[Intent] = [
    # Begruessung
    Intent(
        name="greeting",
        keywords_ar=["مرحبا", "السلام", "اهلا", "صباح", "مساء", "اهلا وسهلا"],
        keywords_en=["hello", "hi", "hey", "good morning", "good evening"],
        response_ar="مرحباً بك في منصة B2B ليبيا! 👋 كيف يمكنني مساعدتك اليوم؟\n\nيمكنني مساعدتك في:\n• البحث عن منتجات\n• معرفة الاسعار\n• معلومات عن التوصيل\n• طرق الدفع\n• انشاء حساب",  # noqa: E501
        response_en="Welcome to Libya B2B Platform! 👋 How can I help you today?\n\nI can help you with:\n• Product search\n• Price information\n• Delivery info\n• Payment methods\n• Account creation",  # noqa: E501
    ),
    # Fragen zu Preisen
    Intent(
        name="price_inquiry",
        keywords_ar=["سعر", "ثمن", "كم", "تكلف", "قيمة", "مبلغ", "price", "cost"],
        keywords_en=["price", "cost", "how much", "rate"],
        response_ar="يمكنك الاطلاع على الاسعار في صفحة المنتجات. 💰\n\nهل تريد:\n• تصفح جميع المنتجات؟\n• البحث عن منتج معين؟\n• معرفة خصومات_bulk؟",  # noqa: E501
        response_en="You can check prices on the products page. 💰\n\nDo you want to:\n• Browse all products?\n• Search for a specific product?\n• Learn about bulk discounts?",  # noqa: E501
    ),
    # Fragen zu Tischlfern
    Intent(
        name="delivery_inquiry",
        keywords_ar=["توصيل", "شحن", "توصيل", "وصل", "توصيل", "دليفري"],
        keywords_en=["delivery", "shipping", "ship", "deliver"],
        response_ar="التوصيل متاح في جميع مناطق ليبيا! 🚚\n\n• الدفع عند الاستلام (COD)\n• تتبع عبر QR-Code\n• تأكيد بالصورة وال GPS\n• مدة التوصيل: 1-3 ايام عمل\n\nهل تريد معرفة المزيد؟",  # noqa: E501
        response_en="Delivery is available across Libya! 🚚\n\n• Cash on Delivery (COD)\n• QR-Code tracking\n• Photo + GPS confirmation\n• Delivery time: 1-3 business days\n\nWant to know more?",  # noqa: E501
    ),
    # Fragen zu Zalungen
    Intent(
        name="payment_inquiry",
        keywords_ar=["دفع", "فواتير", " paying", "فلوس", "حساب", "محفظة"],
        keywords_en=["payment", "pay", "bill", "wallet", "cash"],
        response_ar="طرق الدفع المتاحة: 💳\n\n• الدفع عند الاستلام (COD) - الطريقة الاساسية\n• محفظة إلكترونية (قريب)\n• خدمة Escrow للواردات\n\nهل تريد معرفة المزيد عن طريقة معينة؟",  # noqa: E501
        response_en="Available payment methods: 💳\n\n• Cash on Delivery (COD) - Primary method\n• Digital wallet (coming soon)\n• Escrow service for imports\n\nWant to know more about a specific method?",  # noqa: E501
    ),
    # Fragen zu Produkten
    Intent(
        name="product_inquiry",
        keywords_ar=["منتج", "بضاعة", "سلعة", "موجود", "متوفر", "product", "item"],
        keywords_en=["product", "item", "goods", "available", "stock"],
        response_ar="يمكنك تصفح جميع المنتجات في المتجر! 🛒\n\nالفئات المتاحة:\n• مواد بناء\n• ادوات كهربائية\n• اجهزة مكتبية\n• مواد تنظيف\n\nهل تبحث عن منتج معين؟",  # noqa: E501
        response_en="Browse all products in the store! 🛒\n\nAvailable categories:\n• Building materials\n• Electrical tools\n• Office supplies\n• Cleaning products\n\nLooking for something specific?",  # noqa: E501
    ),
    # الحساب (Account)
    Intent(
        name="account_inquiry",
        keywords_ar=["حساب", "تسجيل", "دخول", "عضو", "account", "register", "login"],
        keywords_en=["account", "register", "login", "signup", "member"],
        response_ar="لإنشاء حساب جديد: 📝\n\n1. حمّل التطبيق\n2. اضغط على 'تسجيل'\n3. ادخل بياناتك\n4. اختر نوع الحساب (مشتري/بائع)\n5. اكمل التسجيل\n\nهل تحتاج مساعدة في خطوة معينة؟",  # noqa: E501
        response_en="To create a new account: 📝\n\n1. Download the app\n2. Click 'Register'\n3. Enter your details\n4. Choose account type (Buyer/Seller)\n5. Complete registration\n\nNeed help with a specific step?",  # noqa: E501
    ),
    # الدعم الفني
    Intent(
        name="support_inquiry",
        keywords_ar=["دعم", "مساعدة", "شكاوى", "تذكرة", "support", "help"],
        keywords_en=["support", "help", "complaint", "ticket", "issue"],
        response_ar="فريق الدعم الفني جاهز لمساعدتك! 🎧\n\n• واتساب: +218-XX-XXX-XXXX\n• البريد: support@libya-b2b.ly\n• ساعات العمل: 9 صباحاً - 6 مساءً\n\nاوصف مشكلتك وسنساعدك فوراً!",  # noqa: E501
        response_en="Our support team is ready to help! 🎧\n\n• WhatsApp: +218-XX-XXX-XXXX\n• Email: support@libya-b2b.ly\n• Working hours: 9 AM - 6 PM\n\nDescribe your issue and we'll help immediately!",  # noqa: E501
    ),
    # سؤال عام
    Intent(
        name="general_inquiry",
        keywords_ar=["عام", "معلومات", "عن المنصة", "general", "about"],
        keywords_en=["general", "information", "about", "platform"],
        response_ar="منصة B2B ليبيا هي اول منصة تجارة إلكترونية B2B في ليبيا! 🇱🇾\n\n• 100% دفع عند الاستلام\n• تتبع عبر QR-Code\n• تأكيد بالصورة\n• دعم فني على مدار الساعة\n\nكيف يمكنني مساعدتك؟",  # noqa: E501
        response_en="Libya B2B Platform is the first B2B e-commerce platform in Libya! 🇱🇾\n\n• 100% Cash on Delivery\n• QR-Code tracking\n• Photo confirmation\n• 24/7 support\n\nHow can I help you?",  # noqa: E501
    ),
    # شكراً
    Intent(
        name="thanks",
        keywords_ar=["شكراً", "شكر", "ممتاز", "thanks", "thank"],
        keywords_en=["thanks", "thank you", "great", "excellent"],
        response_ar="العفو! 😊 يسعدني ان اكون قد ساعدتك.\n\nهل لديك اي اسئلة اخرى؟\n\nنتمنى لك تجربة ممتعة مع منصة B2B ليبيا!",  # noqa: E501
        response_en="You're welcome! 😊 Glad I could help.\n\nDo you have any other questions?\n\nWe wish you a great experience with Libya B2B Platform!",  # noqa: E501
    ),
    # وداعاً
    Intent(
        name="goodbye",
        keywords_ar=["وداعاً", "مع السلامة", "باي", "goodbye", "bye"],
        keywords_en=["goodbye", "bye", "see you", "farewell"],
        response_ar="وداعاً! 👋 نتمنى لك يوماً سعيداً.\n\nلا تتردد في التواصل معنا في اي وقت.\n\nمع السلامة!",  # noqa: E501
        response_en="Goodbye! 👋 Have a great day.\n\nDon't hesitate to contact us anytime.\n\nTake care!",  # noqa: E501
    ),
    # === NEUE INTENTS (Sprint 6/7) ===
    # حالة الطلب
    Intent(
        name="order_status",
        keywords_ar=["حالة الطلب", "تتبع الطلب", "اين الطلب", "متى يصل", "order status", "track"],
        keywords_en=["order status", "track order", "where is my order", "when will it arrive"],
        response_ar="لتتبع طلبك: 📦\n\n1. ادخل رقم الطلب في صفحة التتبع\n2. امسح رمز QR عند التوصيل\n3. ستتلقى تأكيداً بالصورة\n\nهل تريد مساعدة في تتبع طلب معين؟",  # noqa: E501
        response_en="To track your order: 📦\n\n1. Enter order number on tracking page\n2. Scan QR code on delivery\n3. You'll receive photo confirmation\n\nNeed help tracking a specific order?",  # noqa: E501
    ),
    # طلب جماعي
    Intent(
        name="bulk_order",
        keywords_ar=["طلب جماعي", "كمية كبيرة", "جملة", "wholesale", "bulk", "large order"],
        keywords_en=["bulk order", "wholesale", "large order", "quantity"],
        response_ar="للطلبات الجماعية: 📦\n\n• خصومات خاصة للكميات الكبيرة\n• توصيل مباشر للمستودع\n• دفع عند الاستلام حتى للمبالغ الكبيرة\n• اتصل بفريق المبيعات: +218-XX-XXX-XXXX\n\nكم الكمية المطلوبة؟",  # noqa: E501
        response_en="For bulk orders: 📦\n\n• Special discounts for large quantities\n• Direct warehouse delivery\n• COD available for large amounts\n• Contact sales: +218-XX-XXX-XXXX\n\nWhat quantity do you need?",  # noqa: E501
    ),
    # سياسة الارجاع
    Intent(
        name="return_policy",
        keywords_ar=["ارجاع", "استرجاع", "استبدال", "return", "refund", "exchange"],
        keywords_en=["return", "refund", "exchange", "policy"],
        response_ar="سياسة الارجاع: 🔄\n\n• ارجاع خلال 7 ايام من التوصيل\n• المنتج يجب ان يكون في حالته الاصلية\n• الدفع المسترد خلال 3-5 ايام عمل\n• للمنتجات التالفة: استبدال مجاني\n\nهل تريد بدء عملية ارجاع؟",  # noqa: E501
        response_en="Return Policy: 🔄\n\n• Return within 7 days of delivery\n• Product must be in original condition\n• Refund within 3-5 business days\n• For damaged products: free replacement\n\nWant to start a return?",  # noqa: E501
    ),
    # ضمان
    Intent(
        name="warranty",
        keywords_ar=[
            "ضمان",
            "كفالة",
            "warranty",
            "guarantee",
            " bảo hành",
            "الضمان",
            " فترة الضمان",
        ],
        keywords_en=["warranty", "guarantee", "coverage"],
        response_ar="معلومات الضمان: 🛡️\n\n• ضمان 12 شهر على جميع المنتجات\n• ضمان استبدال للمنتجات التالفة\n• التغطية تشمل عيوب التصنيع\n• لا تشمل الأضرار الناتجة عن سوء الاستخدام\n\nهل لديك مشكلة في منتج تحت الضمان؟",  # noqa: E501
        response_en="Warranty Information: 🛡️\n\n• 12-month warranty on all products\n• Replacement warranty for defective items\n• Coverage includes manufacturing defects\n• Does not cover damage from misuse\n\nHave an issue with a product under warranty?",  # noqa: E501
    ),
    # شكوى
    Intent(
        name="complaint",
        keywords_ar=["شكوى", "مشكلة", "سيء", "disappointed", "complaint", "bad"],
        keywords_en=["complaint", "problem", "issue", "bad", "disappointed"],
        response_ar="نعتذر عن اي إزعاج! 🙏\n\nيرجى تزويدنا بالتفاصيل:\n• رقم الطلب\n• وصف المشكلة\n• صور اذا امكن\n\nسنعمل على حل المشكلة في اسرع وقت\n\n• واتساب: +218-XX-XXX-XXXX\n• البريد: complaints@libya-b2b.ly",  # noqa: E501
        response_en="We apologize for any inconvenience! 🙏\n\nPlease provide details:\n• Order number\n• Problem description\n• Photos if possible\n\nWe'll resolve it ASAP\n\n• WhatsApp: +218-XX-XXX-XXXX\n• Email: complaints@libya-b2b.ly",  # noqa: E501
    ),
    # اقتراح
    Intent(
        name="suggestion",
        keywords_ar=["اقتراح", "فكرة", "تحسين", "suggestion", "idea", "improve"],
        keywords_en=["suggestion", "idea", "improve", "feedback"],
        response_ar="نقدر اقتراحاتك! 💡\n\nيمكنك ارسال اقتراحاتك عبر:\n• البريد: suggestions@libya-b2b.ly\n• استبيان الرضا في التطبيق\n• مراجعة على Google Play\n\nكل اقتراح يساعدنا في التحسين!",  # noqa: E501
        response_en="We appreciate your suggestions! 💡\n\nSend your suggestions via:\n• Email: suggestions@libya-b2b.ly\n• In-app satisfaction survey\n• Google Play review\n\nEvery suggestion helps us improve!",  # noqa: E501
    ),
    # شراكة
    Intent(
        name="partnership",
        keywords_ar=["شراكة", "تعاون", "اتفاقية", "partnership", "collaborate"],
        keywords_en=["partnership", "collaborate", "agreement"],
        response_ar="للتواصل حول فرص الشراكة: 🤝\n\n• البريد: partnerships@libya-b2b.ly\n• الهاتف: +218-XX-XXX-XXXX\n\nنبحث عن شركاء في:\n• التوزيع واللوجستيات\n• الخدمات المالية\n• التقنية والتطوير\n\nكيف يمكننا التعاون؟",  # noqa: E501
        response_en="For partnership opportunities: 🤝\n\n• Email: partnerships@libya-b2b.ly\n• Phone: +218-XX-XXX-XXXX\n\nWe're looking for partners in:\n• Distribution & logistics\n• Financial services\n• Technology & development\n\nHow can we collaborate?",  # noqa: E501
    ),
    # جملة (Wholesale)
    Intent(
        name="wholesale",
        keywords_ar=["جملة", "تاجر جملة", "wholesale", "bulk pricing"],
        keywords_en=["wholesale", "bulk pricing", "reseller"],
        response_ar="أسعار الجملة: 💼\n\n• خصومات تبدأ من 10 قطع\n• أسعار خاصة للموزعين المعتمدين\n• شروط دفع مرنة\n• دعم تقني للموزعين\n\nللحصول على كتالوج الجملة تواصل معنا!",  # noqa: E501
        response_en="Wholesale pricing: 💼\n\n• Discounts starting from 10 units\n• Special prices for authorized distributors\n• Flexible payment terms\n• Technical support for distributors\n\nContact us for wholesale catalog!",  # noqa: E501
    ),
    # شهادة
    Intent(
        name="certification",
        keywords_ar=["شهادة", "شهادات", "جودة", "certification", "quality"],
        keywords_en=["certification", "quality", "certificate"],
        response_ar="شهادات الجودة: 📜\n\n• جميع المنتجات معتمدة\n• شهادة ISO 9001\n• معايير الجودة الليبية\n• فحص قبل الشحن\n\nهل تريد الاطلاع على شهادة منتج معين؟",  # noqa: E501
        response_en="Quality Certifications: 📜\n\n• All products certified\n• ISO 9001 certification\n• Libyan quality standards\n• Pre-shipment inspection\n\nWant to see a specific product's certificate?",  # noqa: E501
    ),
    # لوجستيات
    Intent(
        name="logistics",
        keywords_ar=["لوجستيات", "نقل", "شحن", "logistics", "transport", "shipping"],
        keywords_en=["logistics", "transport", "shipping", "freight"],
        response_ar="خدمات اللوجستيات: 🚛\n\n• توصيل لجميع المناطق الليبية\n• شحن بحري وجوي\n• تأمين الشحنات\n• تتبع مباشر\n• مخازن فيTripolis وبنغازي\n\nهل تحتاج معلومات عن شحن معين؟",  # noqa: E501
        response_en="Logistics Services: 🚛\n\n• Delivery across all Libyan regions\n• Sea and air freight\n• Shipment insurance\n• Real-time tracking\n• Warehouses in Tripoli and Benghazi\n\nNeed info on specific shipment?",  # noqa: E501
    ),
]

# ============================================================
# INTENT RECOGNITION ENGINE
# ============================================================


class IntentRecognizer:
    """
    Intent-Recognition Engine (CPU-basiert, Open-Source)

    Erkennt Absichten basierend auf Keywords und Muster.
    Funktioniert vollstaendig offline.
    """

    def __init__(self):
        self.intents = INTENTS
        self.confidence_threshold = 0.3

    def recognize(self, message: str, is_arabic: bool = True) -> Tuple[Intent, float]:
        """
        Intent aus Nachricht erkennen.

        Prioritaeten:
        - warranty, complaint, partnership, logistics: Hoechste Prioritaet (spezifisch)
        - order_status, bulk_order, return_policy: Hohe Prioritaet
        - Alle anderen: Normale Prioritaet
        """
        message_lower = message.lower().strip()

        # Prioritaets-Reihenfolge (spezifischere Intents zuerst)
        priority_order = [
            "warranty",
            "complaint",
            "partnership",
            "logistics",
            "order_status",
            "bulk_order",
            "return_policy",
            "certification",
            "wholesale",
            "suggestion",
            "greeting",
            "goodbye",
            "thanks",
            "price_inquiry",
            "delivery_inquiry",
            "payment_inquiry",
            "product_inquiry",
            "account_inquiry",
            "support_inquiry",
            "general_inquiry",
        ]

        best_intent = None
        best_score = 0.0

        # Zuerst nach Prioritaet sortierte Intents durchsuchen
        sorted_intents = sorted(
            self.intents,
            key=lambda x: priority_order.index(x.name) if x.name in priority_order else 999,
        )

        for intent in sorted_intents:
            keywords = intent.keywords_ar if is_arabic else intent.keywords_en
            score = self._calculate_score(message_lower, keywords)

            if score > best_score:
                best_score = score
                best_intent = intent

        if best_score < self.confidence_threshold:
            for intent in self.intents:
                if intent.name == "general_inquiry":
                    return intent, 0.1

        return best_intent, best_score

    def _calculate_score(self, message: str, keywords: List[str]) -> float:
        """
        Uebereinstimmungs-Score berechnen.

        Algorithmus:
        - Exakter Keyword-Treffer (ganzes Wort): 1.0
        - Keyword als Teil eines Wortes: 0.3
        - Bonus fuer mehrere Treffer
        """
        score = 0.0
        matches = 0
        message_lower = message.lower()

        for keyword in keywords:
            keyword_lower = keyword.lower()

            # Exakter Wort-Treffer (mit Leerzeichen als Begrenzer)
            if (
                keyword_lower == message_lower
                or f" {keyword_lower} " in f" {message_lower} "
                or message_lower.startswith(keyword_lower + " ")
                or message_lower.endswith(" " + keyword_lower)
            ):
                score += 1.0
                matches += 1
            elif keyword_lower in message_lower:
                # Keyword ist Teil eines laengeren Wortes - geringerer Score
                score += 0.3

        # Bonus fuer mehrere Treffer
        if matches > 1:
            score *= 1.2

        return min(score, 3.0)


# ============================================================
# CHATBOT ENGINE
# ============================================================


class ArabicChatbot:
    """
    Arabischer KI-Chatbot (CPU-basiert, Open-Source)

    Features:
    - Intent-Recognition (Offline)
    - Kontext-bezogene Antworten
    - Chat-Verlauf (Lokal gespeichert)
    - Mehrsprachig (Arabisch/Englisch)
    """

    def __init__(self):
        self.recognizer = IntentRecognizer()
        self.chat_history: Dict[str, List[Dict]] = {}

    def process_message(self, session_id: str, message: str, is_arabic: bool = True) -> Dict:
        """
        Nachricht verarbeiten und Antwort generieren.

        Args:
            session_id: Einzigartige Sitzungs-ID
            message: Eingabe-Nachricht
            is_arabic: True fuer Arabisch

        Returns:
            Dictionary mit Antwort und Metriken
        """

        # Intent erkennen
        intent, confidence = self.recognizer.recognize(message, is_arabic)

        # Antwort generieren
        if is_arabic:
            response = intent.response_ar
        else:
            response = intent.response_en

        # Chat-Verlauf aktualisieren
        if session_id not in self.chat_history:
            self.chat_history[session_id] = []

        self.chat_history[session_id].append(
            {
                "user_message": message,
                "bot_response": response,
                "intent": intent.name,
                "confidence": confidence,
                "is_arabic": is_arabic,
                "timestamp": datetime.now().isoformat(),
            }
        )

        return {
            "session_id": session_id,
            "response": response,
            "intent": intent.name,
            "confidence": confidence,
            "is_arabic": is_arabic,
            "timestamp": datetime.now().isoformat(),
        }

    def get_chat_history(self, session_id: str) -> List[Dict]:
        """Chat-Verlauf abrufen"""
        return self.chat_history.get(session_id, [])

    def clear_chat_history(self, session_id: str) -> bool:
        """Chat-Verlauf loeschen"""
        if session_id in self.chat_history:
            del self.chat_history[session_id]
            return True
        return False

    def get_suggestions(self, session_id: str) -> List[str]:
        """Naechste Handlungsempfehlungen basierend auf Verlauf"""
        history = self.chat_history.get(session_id, [])

        if not history:
            return ["تصفح المنتجات", "معرفة الاسعار", "التوصيل والشحن", "طرق الدفع"]

        last_intent = history[-1].get("intent", "")

        suggestions = {
            "greeting": ["البحث عن منتج", "معرفة الاسعار", "التوصيل"],
            "price_inquiry": ["تصفح المنتجات", "خصومات_bulk", "طرق الدفع"],
            "delivery_inquiry": ["تتبع الطلب", "مناطق التوصيل", "مدة التوصيل"],
            "payment_inquiry": ["الدفع عند الاستلام", "خدمة Escrow", "محفظة إلكترونية"],
            "product_inquiry": ["اضافة للسلة", "مقارنة المنتجات", "التقييمات"],
            "account_inquiry": ["تسجيل الدخول", "استعادة كلمة المرور", "تحديث البيانات"],
            "support_inquiry": ["التواصل مع الدعم", "شكوى", "اقتراح"],
        }

        return suggestions.get(last_intent, ["البحث عن منتج", "معرفة الاسعار"])


# ============================================================
# SINGLETON INSTANCE
# ============================================================

_chatbot_instance = None


def get_chatbot() -> ArabicChatbot:
    """Singleton-Instanz des Chatbots"""
    global _chatbot_instance
    if _chatbot_instance is None:
        _chatbot_instance = ArabicChatbot()
    return _chatbot_instance


# ============================================================
# HILFSFUNKTIONEN
# ============================================================


def detect_language(message: str) -> bool:
    """
    Sprache erkennen.

    Returns:
        True = Arabisch, False = Englisch
    """
    arabic_chars = re.findall(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]", message)
    return len(arabic_chars) > len(message) / 4


def format_response(response: str, user_name: Optional[str] = None) -> str:
    """Antwort formatieren"""
    if user_name:
        return f"مرحباً {user_name}!\n\n{response}"
    return response
