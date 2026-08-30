# منصة B2B ليبيا - KI-gestützte B2B-Plattform

**إصدار المشروع:** v1.6  
**التاريخ:** 15 أغسطس 2026  
**الميزانية:** 20 يورو شهرياً استضافة  
**التقنية:** 100% مفتوح المصدر، يعمل على المعالج فقط

---

## الميزات

- **100% الدفع عند الاستلام (COD)** - لا حاجة لحساب بنكي
- **تتبع عبر QR-Code** - كل طلب له رمز فريد
- **روبوت محادثة بالعربية** - 20 نية بالعربية
- **تعمل بدون انترنت** - SQLite + Delta-Sync
- **تحقق بالصورة** - صورة + GPS عند التوصيل
- **مفتوح المصدر** - MIT, Apache 2.0, BSD

---

## البدء السريع

### محلياً
```bash
./setup.sh
cd src/backend && uvicorn main:app --reload
```

### باستخدام Docker
```bash
./docker-setup.sh
```

### باستخدام Make
```bash
make setup
make dev
```

---

## روابط مهمة

| الرابط | الوصف |
|--------|-------|
| [/landing](/landing) | الصفحة الرئيسية (إنجليزي) |
| [/ar/landing](/ar/landing) | الصفحة الرئيسية (عربي) |
| [/docs](/docs) | توثيق API |
| [/health](/health) | فحص الحالة |
| [/ar/chat](/ar/chat) | روبوت المحادثة |

---

## نقاط الوصول API

| النقطة | الطريقة | الوصف |
|--------|---------|-------|
| `/api/products` | GET/POST | المنتجات |
| `/api/orders` | GET/POST | الطلبات (COD) |
| `/api/qrcode/generate` | POST | إنشاء رمز QR |
| `/api/chat` | POST | روبوت المحادثة |
| `/api/sync/delta` | POST | مزامنة Delta |
| `/ar/products` | GET | المنتجات (عربي) |
| `/ar/orders` | POST | الطلبات (عربي) |
| `/ar/chat` | POST | المحادثة (عربي) |
| `/ar/errors` | GET | رسائل الخطأ (عربي) |

---

## اختبارات

```bash
# تشغيل الاختبارات
make test

# اختبارات التكامل
pytest tests/test_integration.py -v
```

---

## الرخص

MIT License - انظر ملف LICENSE
