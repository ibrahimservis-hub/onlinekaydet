"""Ekip & ortak modülü: teknisyen destek sohbeti, eğitim/sertifika (süre uyarılı), bayi portalı (bölge kilidi + komisyon).
"""
import re
import secrets
import uuid
from collections import defaultdict
from datetime import datetime, timezone, timedelta

from fastapi import Depends, HTTPException, Request

import fieldops
import tenant
import governance
import notify

try:
    from zoneinfo import ZoneInfo
    TR = ZoneInfo("Europe/Istanbul")
except Exception:                                     # pragma: no cover
    TR = timezone(timedelta(hours=3))

DONE = ("tamamlandi", "faturalandi")


def _id():
    return str(uuid.uuid4())


def _now():
    return datetime.now(timezone.utc).isoformat()


def _f(x, d=0.0):
    try:
        return float(x or 0)
    except (TypeError, ValueError):
        return d


def _p10(p):
    return re.sub(r"\D", "", p or "")[-10:]


def _mask_name(n):
    n = (n or "").strip()
    parts = n.split()
    return " ".join([parts[0]] + [p[0] + "." for p in parts[1:]]) if parts else ""


async def cert_payload(db, rec, base=""):
    """Belge verisi (panel + herkese açık doğrulama sayfası ortak)."""
    import atolye
    uid = rec["user_id"]
    u = await db.users.find_one({"id": uid}, {"_id": 0, "name": 1, "created_at": 1, "id": 1, "is_active": 1, "role": 1}) or {}
    rows = await db.service_jobs.find({"assigned_technician_id": uid, "survey.rating": {"$gt": 0}}, {"_id": 0, "survey": 1}).to_list(5000)
    rs = [r["survey"]["rating"] for r in rows]
    sc = await fieldops.tech_score(db, uid)
    done = await db.service_jobs.count_documents({"assigned_technician_id": uid, "status": {"$in": ["tamamlandi", "faturalandi"]}})
    iss = rec.get("issued_at", "")
    try:
        dt = datetime.fromisoformat(iss).strftime("%d.%m.%Y")
    except Exception:  # noqa: BLE001
        dt = ""
    url = atolye._pub_base(base) + "/belge/" + rec["code"]
    return {"name": u.get("name", ""), "year": rec.get("year"), "date": dt, "since": (u.get("created_at") or "")[:10],
            "no": "SP-" + str(rec.get("year")) + "-" + str(uid)[:6].upper(), "count": len(rs), "avg": sc["score"] if sc["has"] else 0, "score_has": sc["has"], "score_parts": sc["parts"],
            "done": done, "code": rec["code"], "url": url, "qr": atolye._qr_svg(url, 4),
            "valid": bool(u) and u.get("role") == "technician" and u.get("is_active", True) is not False}


def register(api_router, db, deps):
    require_admin = deps["require_admin"]
    get_current_user = deps["get_current_user"]

    def need_tech(user):
        if user.get("role") != "technician":
            raise HTTPException(403, "Yalnızca teknisyen")

    # =================================================================== DESTEK SOHBETİ
    def clean_text(t):
        t = str(t or "").strip()
        if not t:
            raise HTTPException(422, "Mesaj boş")
        return t[:2000]

    @api_router.get("/chat/my")
    async def chat_my(user: dict = Depends(get_current_user)):
        need_tech(user)
        rows = await db.chat_messages.find({"thread_id": user["id"]}, {"_id": 0}).sort("created_at", 1).to_list(500)
        await db.chat_messages.update_many({"thread_id": user["id"], "sender_role": "admin", "read": False}, {"$set": {"read": True}})
        return rows[-200:]

    @api_router.post("/chat/my")
    async def chat_send(payload: dict, user: dict = Depends(get_current_user)):
        need_tech(user)
        doc = {"id": _id(), "thread_id": user["id"], "sender_id": user["id"], "sender_name": user.get("name", ""), "sender_role": "technician",
               "text": clean_text(payload.get("text")), "job_id": str(payload.get("job_id", ""))[:64], "read": False, "created_at": _now()}
        await db.chat_messages.insert_one(dict(doc))
        return doc

    @api_router.get("/chat/unread")
    async def chat_unread(user: dict = Depends(get_current_user)):
        if user["role"] == "technician":
            return {"unread": await db.chat_messages.count_documents({"thread_id": user["id"], "sender_role": "admin", "read": False})}
        return {"unread": await db.chat_messages.count_documents({"sender_role": "technician", "read": False})} if user["role"] == "admin" else {"unread": 0}

    @api_router.get("/chat/threads")
    async def chat_threads(_: dict = Depends(require_admin)):
        techs = await db.users.find({"role": "technician"}, {"_id": 0, "id": 1, "name": 1}).to_list(500)
        out = []
        for t in techs:
            last = await db.chat_messages.find({"thread_id": t["id"]}, {"_id": 0}).sort("created_at", -1).to_list(1)
            out.append({"technician_id": t["id"], "name": t["name"], "last": (last[0] if last else None),
                        "unread": await db.chat_messages.count_documents({"thread_id": t["id"], "sender_role": "technician", "read": False})})
        return sorted(out, key=lambda r: (r["last"] or {}).get("created_at", ""), reverse=True)

    @api_router.get("/chat/threads/{tid}")
    async def chat_thread(tid: str, _: dict = Depends(require_admin)):
        rows = await db.chat_messages.find({"thread_id": tid}, {"_id": 0}).sort("created_at", 1).to_list(500)
        await db.chat_messages.update_many({"thread_id": tid, "sender_role": "technician", "read": False}, {"$set": {"read": True}})
        return rows[-200:]

    @api_router.post("/chat/threads/{tid}")
    async def chat_reply(tid: str, payload: dict, user: dict = Depends(require_admin)):
        if not await db.users.find_one({"id": tid, "role": "technician"}, {"_id": 1}):
            raise HTTPException(404, "Teknisyen yok")
        doc = {"id": _id(), "thread_id": tid, "sender_id": user["id"], "sender_name": user.get("name", "Merkez"), "sender_role": "admin",
               "text": clean_text(payload.get("text")), "job_id": str(payload.get("job_id", ""))[:64], "read": False, "created_at": _now()}
        await db.chat_messages.insert_one(dict(doc))
        await fieldops.push_to(db, [tid], "Merkezden mesaj", doc["text"][:120], "/tech/chat")
        return doc

    @api_router.delete("/chat/threads/{tid}")
    async def chat_thread_delete(tid: str, user: dict = Depends(require_admin)):
        """Bir ustayla olan tüm konuşmayı siler (iki tarafta da kaybolur)."""
        r = await db.chat_messages.delete_many({"thread_id": tid})
        return {"ok": True, "deleted": r.deleted_count}

    @api_router.delete("/chat/messages/{mid}")
    async def chat_message_delete(mid: str, user: dict = Depends(require_admin)):
        r = await db.chat_messages.delete_one({"id": mid})
        if not r.deleted_count:
            raise HTTPException(404, "Mesaj bulunamadı")
        return {"ok": True}


    # =================================================================== USTA: KVKK AYDINLATMA + İLETİŞİM İZNİ (ilk girişte)
    CONSENT_VER = "5"

    async def consent_texts():
        g = await db.app_settings.find_one({"_id": "global"}, {"_id": 0}) or {}
        firma = (g.get("company_name") or "").strip() or "ServisPlus Teknik Servis Hizmetleri"
        kvkk = (
            "KİŞİSEL VERİLERİN KORUNMASI AYDINLATMA METNİ — İŞ ORTAĞI / USTA\n\n"
            "1) Veri sorumlusu: MODA EKRU E-TİCARET HİZMETLERİ TEKSTİL SANAYİ VE TİCARET LİMİTED ŞİRKETİ (ServisPlus), Kazım Karabekir Mah. Şehit Hasan Öztürk Cad. No: 8 İç Kapı No: 5 Etimesgut / Ankara — info@servisplus.net.tr. "
            "(Panelde tanımlı firma adı: " + firma + ").\n\n"
            "2) İşlenen verileriniz: ad-soyad, telefon, e-posta, çalışma bölgesi ve uzmanlık alanları, araç bilgisi; IBAN, hakediş ve borç/alacak kayıtları; vergi/fatura bilgileri; "
            "iş kayıtlarınız (atanan ve tamamlanan işler, kullanılan parça, işçilik, fotoğraf, imza), müşteri puan ve yorumları, performans verileri; "
            "uygulama giriş kayıtlarınız (tarih, IP adresi, cihaz/tarayıcı bilgisi), müşteriyi arama/mesaj kayıtlarınız (arama başlatma zamanı, numara görüntüleme sayısı) ve — “Yoldayım” özelliğini kullanırsanız — iş süresince anlık konumunuz; ayrıca isteğe bağlı olarak yüklediğiniz profil fotoğrafınız.\n\n"
            "3) Amaçlar: size iş atanması ve servis hizmetinin yürütülmesi; müşteriyle iletişimin sağlanması ve müşteriye “usta yolda”, randevu ve iş tamamlama bilgilendirmesi ve müşterinin ustayı tanıyabilmesi (profil fotoğrafı); hakediş, ödeme ve muhasebe işlemleri; hizmet kalitesi, 15 dakikalık müşteri arama süresi gibi iş kurallarının takibi ve performans değerlendirmesi; "
            "müşteri verilerinin kötüye kullanımının önlenmesi, hesap ve uygulama güvenliği; yasal yükümlülükler ve uyuşmazlıklarda hakkın korunması.\n\n"
            "4) Hukuki sebepler (KVKK m.5/2): sözleşmenin kurulması veya ifası (c), hukuki yükümlülük (ç), bir hakkın tesisi/kullanılması/korunması (e), meşru menfaat (f). Ticari ileti ve Türkiye dışına aktarım gibi açık rıza gerektiren işlemler yalnızca onayınızla yapılır.\n\n"
            "5) Aktarım: iş kapsamında müşterilere (ad ve iletişim bilgileriniz, konumunuz; profil fotoğrafı yüklediyseniz atandığınız işin takip sayfasında ve müşteri hesabında fotoğrafınız), SMS/WhatsApp/e-posta ve bildirim hizmet sağlayıcılarına, bilişim/barındırma/yedekleme hizmet sağlayıcılarına, mali müşavir ve hukuk danışmanlarına, "
            "mevzuatın gerektirdiği hâllerde yetkili kamu kurum ve mahkemelere aktarılabilir. Bazı hizmet sağlayıcıların (ör. Google, Cloudflare) sunucuları yurt dışında olabilir; aktarım KVKK m.9’a uygun yapılır.\n\n"
            "Profil fotoğrafı: Fotoğraf yüklemek tamamen isteğe bağlıdır; yüklediğinizde yönetim panelinde ve — atandığınız işlerde — müşteriye gönderilen takip bağlantısında ve müşterinin hesabında görünür. Dilediğiniz zaman Profil sayfasından kaldırabilirsiniz; kaldırdığınızda görünmez olur. Profil fotoğrafınız yönetim onayından sonra müşteriye görünür. İş sırasında çektiğiniz önce/sonra fotoğrafları, iş tamamlandıktan sonra yönetimin inceleme süresi geçince veya yönetim onaylayınca müşterinin takip sayfasında ve servis fişinde (küçük görsel olarak) yer alır; yönetim uygunsuz gördüğü fotoğrafı gizleyebilir. Müşterilerin evini, kişisel eşyasını veya yüzünü gereksiz yere göstermeyecek şekilde çekim yapmalısınız. Müşteriler de isteğe bağlı olarak fotoğraf yükleyebilir; müşteri fotoğrafı yalnızca yönetimde ve size atanmış işte görünür, kaydedilemez veya paylaşılamaz.\n\n"
            "6) Müşteri verileriyle ilgili yükümlülüğünüz: panelde gördüğünüz müşteri adı, telefon, adres, cihaz ve fotoğraflar yalnızca ilgili işin yürütülmesi içindir; kopyalanamaz, kaydedilemez, üçüncü kişilerle paylaşılamaz, müşteriye ServisPlus dışı doğrudan satış/pazarlama için kullanılamaz. "
            "Numara görüntüleme ve arama işlemleri denetim amacıyla kaydedilir. İhlal hâlinde hesap kapatılabilir ve hukuki yollara başvurulabilir.\n\n"
            "7) Saklama: iş, hakediş ve muhasebe kayıtları yasal saklama süresi (genel olarak 10 yıl), erişim/işlem kayıtları ilgili mevzuattaki süre boyunca saklanır; süre sonunda silinir, yok edilir veya anonim hâle getirilir.\n\n"
            "8) Veri güvenliği: şifreli bağlantı, rol bazlı yetkilendirme, bot doğrulaması, iki adımlı doğrulama (yöneticilerde), erişim kaydı ve yedekleme uygulanır. Şifrenizi kimseyle paylaşmayınız.\n\n"
            "9) Haklarınız (KVKK m.11): verilerinizin işlenip işlenmediğini öğrenme; bilgi talep etme; amacını ve amaca uygun kullanılıp kullanılmadığını öğrenme; aktarıldığı kişileri bilme; eksik/yanlış işlenmişse düzeltilmesini isteme; şartları oluştuysa silinmesini/yok edilmesini isteme ve bunun üçüncü kişilere bildirilmesini isteme; "
            "otomatik analiz sonucu aleyhinize bir sonuca itiraz etme; kanuna aykırı işleme nedeniyle zararın giderilmesini isteme.\n\n"
            "10) Başvuru: taleplerinizi info@servisplus.net.tr adresine veya yukarıdaki adrese yazılı iletebilirsiniz; en geç 30 gün içinde yanıtlanır. Yanıtı yetersiz bulursanız 30 gün içinde Kişisel Verileri Koruma Kurulu’na şikâyet hakkınız saklıdır. "
            "Güncel ve tam metin: servisplus.net.tr/kvkk/"
        )

        kurallar = (
            "USTA KURALLARI VE HİZMET PUANI (İş Ortağı Sözleşmesi’nin özetidir; tam metin: servisplus.net.tr/is-ortagi-sozlesmesi/)\n\n"
            "1) Statü: Bağımsız iş ortağısınız; ServisPlus’ın çalışanı, bayisi veya temsilcisi değilsiniz. Kabul ettiğiniz işi özenle ve mevzuata uygun tamamlarsınız. Vergi, SGK/Bağ-Kur, meslek belgesi ve sigorta yükümlülükleri size aittir; belgesiz/yetkisiz iş (ör. gaz cihazı) yapılmaz.\n\n"
            "2) Müşteri iletişimi: Yeni atanan işte müşteriyi 15 dakika içinde panelden aramanız gerekir; arama başlatma zamanı kaydedilir, süresinde aranmayan iş yönetime bildirilir ve başka iş ortağına yönlendirilebilir.\n\n"
            "3) Randevu ve davranış: Randevuya uyun, gecikmeyi müşteriye önceden bildirin; müşteriye ve evine saygılı olun. Hakaret, taciz, baskı ve ayrımcılık yasaktır.\n\n"
            "4) Fiyat ve kayıt: İş yapılmadan önce ücret müşteriye bildirilip onay alınır; onaysız ek ücret, panel dışı bahşiş/ek bedel istenemez. Yapılan iş, parça, ücret, fotoğraf ve imza panelde doğru ve eksiksiz kaydedilir; sahte kayıt ve fiyat şişirme ciddi ihlaldir.\n\n"
            "5) Müşteri verisi ve yönlendirme yasağı: Müşteri bilgileri yalnızca ilgili iş içindir; kopyalanamaz, paylaşılamaz. Müşteriyi ServisPlus dışında iş yapmak üzere yönlendirmek, ServisPlus’ı “yetkili servis” gibi tanıtmak yasaktır; ihlalde sözleşmedeki cezai şart uygulanır.\n\n"
            "6) HİZMET PUANI (5 üzerinden): Puanınız, son 180 günde tamamladığınız işlerden dört ölçütün ağırlıklı ortalamasıdır:\n"
            "• Müşteri yorumları (%35): müşterinin verdiği 1–5 puan.\n"
            "• İşe gitme hızı (%25): randevu saatinden (randevu yoksa atamadan) itibaren yola çıkma/işe başlama süresi — 60 dk içinde 5, 120 dk 4, 240 dk 3, 480 dk 2, daha geç 1.\n"
            "• Müşteriyi arama hızı (%20): atamadan ilk aramaya — 15 dk içinde 5, 30 dk 4, 60 dk 3, 120 dk 2, daha geç veya aranmadıysa 1.\n"
            "• İşi bitirme hızı (%20): işe başlamadan tamamlamaya — 2 saat içinde 5, 4 saat 4, 8 saat 3, 24 saat 2, daha uzun 1 (atölyeye alınan işler hariç).\n"
            "Verisi olmayan ölçüt hesaba katılmaz; en az 3 tamamlanmış işten sonra puan görünür. Puanınız profilinizde ve sertifikanızda yer alır. Puan 3,5’in altına inerse yönetim sizinle görüşür; 3,0’ın altında iş yönlendirmesi azaltılabilir; 2,5’in altında iş ataması geçici durdurulabilir. "
            "Puanlamaya itirazınızı yönetime 7 gün içinde yazılı bildirebilirsiniz. Müşteriye yorum/puan yazdırmak, baskı yapmak veya puanı yapay yükseltmek yasaktır.\n\n"
            "7) Sorumluluk: Yaptığınız işten ve hata/ihmalinizden doğan müşteri ve üçüncü kişi zararlarından siz sorumlusunuz; ServisPlus’ın bu nedenle ödemek zorunda kaldığı bedeller ve masraflar size rücu edilebilir, ServisPlus’a yönelik üçüncü kişi taleplerinde ServisPlus’ı korumayı kabul edersiniz. Mesleki sorumluluk sigortası önerilir.\n\n"
            "8) Yaptırım: Kuralların ihlalinde uyarı, iş atamasının durdurulması, hesabın kapatılması ve sözleşmedeki hükümler uygulanır. Bu metin İş Ortağı Sözleşmesi’nin ayrılmaz parçasıdır."
        )
        iletisim = (
            "Servis iş atamaları, randevu hatırlatmaları, duyurular, bakiye/ödeme bilgilendirmeleri ve hesap bildirimlerinin; kayıtlı telefon numaranıza SMS veya WhatsApp ile, "
            "uygulama bildirimi ve e-posta yoluyla tarafıma iletilmesine izin veriyorum. Bunların iş ilişkisinin yürütülmesine yönelik bilgilendirme olduğunu, kampanya/tanıtım içerikli ticari iletilerin ancak ayrıca vereceğim onayla gönderilebileceğini ve "
            "bu izni dilediğim zaman yönetime bildirerek geri alabileceğimi biliyorum."
        )
        return {"firma": firma, "kvkk": kvkk, "iletisim": iletisim, "kurallar": kurallar}

    @api_router.get("/tech/consent")
    async def tech_consent_get(user: dict = Depends(get_current_user)):
        need_tech(user)
        if tenant.current():                                   # firma hesabı: ServisPlus usta onay ekranı gösterilmez
            return {"accepted": True, "version": CONSENT_VER, "at": "", "current_version": CONSENT_VER, "texts": {}}
        u = await db.users.find_one({"id": user["id"]}, {"_id": 0, "consent": 1}) or {}
        c = u.get("consent") or {}
        return {"accepted": bool(c.get("kvkk_at") and c.get("contact_at") and c.get("version") == CONSENT_VER), "version": c.get("version", ""), "at": c.get("kvkk_at", ""),
                "current_version": CONSENT_VER, "texts": await consent_texts()}

    @api_router.post("/tech/consent")
    async def tech_consent_post(payload: dict, request: Request, user: dict = Depends(get_current_user)):
        need_tech(user)
        if not (payload.get("kvkk") is True and payload.get("contact") is True and payload.get("rules") is True):
            raise HTTPException(422, "Devam etmek için aydınlatma metnini, iletişim iznini ve usta kurallarını onaylamanız gerekir")
        xf = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        ip = xf or (request.client.host if request.client else "")
        now = _now()
        c = {"version": CONSENT_VER, "kvkk_at": now, "contact_at": now, "rules_at": now, "ip": ip[:64], "ua": request.headers.get("user-agent", "")[:200]}
        await db.users.update_one({"id": user["id"]}, {"$set": {"consent": c}})
        await governance.audit(db, user, "tech_consent", "KVKK aydınlatma + iletişim izni + usta kuralları/hizmet puanı onaylandı (v" + CONSENT_VER + ")", ip=ip)
        return {"ok": True, "at": now}

    @api_router.post("/tech/photo")
    async def tech_photo_set(payload: dict, user: dict = Depends(get_current_user)):
        """Usta kendi profil fotoğrafını belirler. 'path' yalnızca kendi /upload klasöründen gelebilir."""
        need_tech(user)
        path = str(payload.get("path") or "")
        if not path or ".." in path or f"/uploads/{user['id']}/" not in path or not path.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
            raise HTTPException(422, "Geçersiz fotoğraf")
        await db.users.update_one({"id": user["id"]}, {"$set": {"photo_path": path, "photo_at": _now(), "photo_status": "pending"}})
        return {"ok": True, "photo_path": path, "photo_status": "pending"}

    @api_router.delete("/tech/photo")
    async def tech_photo_del(user: dict = Depends(get_current_user)):
        need_tech(user)
        await db.users.update_one({"id": user["id"]}, {"$unset": {"photo_path": "", "photo_at": "", "photo_status": ""}})
        return {"ok": True}

    # ---- GUNCELLEME 118: usta kendi iletisim + konum bilgisi, musteri yorumlari
    def _tr_ph(v):
        d = re.sub(r"\D", "", str(v or ""))
        if d.startswith("00"):
            d = d[2:]
        if d.startswith("90") and len(d) == 12:
            d = d[2:]
        elif d.startswith("0") and len(d) == 11:
            d = d[1:]
        if len(d) != 10 or d[0] not in "2345" or len(set(d)) < 3:
            raise HTTPException(422, "Telefon numarası eksik veya hatalı. Örnek: +90 532 123 45 67")
        return "+90" + d

    @api_router.get("/tech/contact")
    async def tech_contact_get(user: dict = Depends(get_current_user)):
        need_tech(user)
        u = await db.users.find_one({"id": user["id"]}, {"_id": 0, "email": 1, "phone": 1, "profile": 1}) or {}
        p = u.get("profile") or {}
        return {"email": u.get("email", ""), "phone": u.get("phone", ""), "city": p.get("city", ""),
                "districts": ", ".join(p.get("districts") or []), "address": p.get("address", "")}

    @api_router.put("/tech/contact")
    async def tech_contact_put(payload: dict, user: dict = Depends(get_current_user)):
        need_tech(user)
        email = str(payload.get("email") or "").strip().lower()
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]{2,}$", email) or len(email) > 120:
            raise HTTPException(422, "E-posta adresi geçersiz")
        phone = _tr_ph(payload.get("phone"))
        if await db.users.find_one({"email": email, "id": {"$ne": user["id"]}}, {"_id": 0, "id": 1}):
            raise HTTPException(409, "Bu e-posta başka bir hesapta kayıtlı")
        cur = await db.users.find_one({"id": user["id"]}, {"_id": 0, "profile": 1}) or {}
        prof = dict(cur.get("profile") or {})
        prof["city"] = str(payload.get("city") or "").strip()[:40]
        prof["districts"] = [x.strip()[:40] for x in str(payload.get("districts") or "").replace("\n", ",").split(",") if x.strip()][:40]
        prof["address"] = str(payload.get("address") or "").strip()[:300]
        prof["updated_at"] = _now()
        await db.users.update_one({"id": user["id"]}, {"$set": {"email": email, "phone": phone, "profile": prof}})
        await governance.audit(db, user, "tech_contact", "Usta iletişim/konum bilgisini güncelledi")
        try:
            await notify.notify_owner(db, f'ℹ {user.get("name", "Usta")} iletişim/konum bilgisini güncelledi ({phone}, {email}{", " + prof["city"] if prof.get("city") else ""})', "tech_contact")
        except Exception:  # noqa: BLE001
            pass
        return {"ok": True, "email": email, "phone": phone}

    @api_router.get("/tech/reviews")
    async def tech_reviews(user: dict = Depends(get_current_user)):
        need_tech(user)
        rows = await db.service_jobs.find({"assigned_technician_id": user["id"], "survey.rating": {"$gt": 0}},
                                          {"_id": 0, "job_number": 1, "customer_name": 1, "device_type": 1, "device_brand_name": 1, "survey": 1, "completed_at": 1}).to_list(2000)
        rows.sort(key=lambda j: (j.get("survey") or {}).get("at", ""), reverse=True)
        rs = [(j["survey"]["rating"]) for j in rows]
        dist = {str(i): sum(1 for r in rs if r == i) for i in range(1, 6)}
        _ok = {r["job_number"] async for r in db.reviews.find({"status": "yayinda", "job_number": {"$in": [j.get("job_number", "") for j in rows[:100]]}}, {"_id": 0, "job_number": 1})}
        out = [{"job_number": j.get("job_number", ""), "name": _mask_name(j.get("customer_name")) or "Müşteri", "rating": j["survey"]["rating"],
                "comment": j["survey"].get("comment", "") if j.get("job_number", "") in _ok else "", "comment_pending": bool(j["survey"].get("comment")) and j.get("job_number", "") not in _ok,
                "at": j["survey"].get("at", ""),
                "device": " ".join([x for x in [j.get("device_brand_name", ""), j.get("device_type", "")] if x])} for j in rows[:100]]
        return {"count": len(rs), "avg": round(sum(rs) / len(rs), 2) if rs else 0, "dist": dist, "items": out}

    @api_router.get("/tech/certificate")
    async def tech_certificate(base: str = "", user: dict = Depends(get_current_user)):
        """Usta belgeleri için veri: gerçek müşteri puanı (yoksa puan gösterilmez) + doğrulama kodu/QR."""
        need_tech(user)
        year = datetime.now(timezone.utc).year
        rec = await db.certificates.find_one({"user_id": user["id"], "year": year}, {"_id": 0})
        if not rec:
            rec = {"code": secrets.token_urlsafe(9).replace("-", "x").replace("_", "y"), "user_id": user["id"], "year": year, "issued_at": _now()}
            await db.certificates.insert_one(dict(rec))
        d = await cert_payload(db, rec, base)
        return d

    @api_router.get("/tech-consents")
    async def tech_consents(_: dict = Depends(require_admin)):
        rows = await db.users.find({"role": "technician"}, {"_id": 0, "id": 1, "name": 1, "phone": 1, "consent": 1}).to_list(2000)
        return [{"id": r["id"], "name": r.get("name", ""), "phone": r.get("phone", ""), "accepted": bool((r.get("consent") or {}).get("kvkk_at")),
                 "at": (r.get("consent") or {}).get("kvkk_at", ""), "version": (r.get("consent") or {}).get("version", "")} for r in rows]

    # =================================================================== EĞİTİM + SERTİFİKA
    @api_router.get("/training/modules")
    async def modules(user: dict = Depends(get_current_user)):
        q = {} if user["role"] == "admin" else {"active": {"$ne": False}}
        rows = await db.training_modules.find(q, {"_id": 0}).sort("created_at", 1).to_list(500)
        if user["role"] == "technician":
            done = {d["module_id"]: d["at"] for d in await db.training_done.find({"user_id": user["id"]}, {"_id": 0}).to_list(1000)}
            for r in rows:
                r["done_at"] = done.get(r["id"], "")
        return rows

    @api_router.post("/training/modules")
    async def module_create(payload: dict, _: dict = Depends(require_admin)):
        title = str(payload.get("title", "")).strip()[:120]
        if not title:
            raise HTTPException(422, "Başlık gerekli")
        doc = {"id": _id(), "title": title, "content": str(payload.get("content", ""))[:8000], "url": str(payload.get("url", ""))[:300],
               "required": bool(payload.get("required", False)), "active": True, "created_at": _now()}
        await db.training_modules.insert_one(dict(doc))
        return doc

    @api_router.put("/training/modules/{mid}")
    async def module_update(mid: str, payload: dict, _: dict = Depends(require_admin)):
        upd = {}
        for k, n in (("title", 120), ("content", 8000), ("url", 300)):
            if k in payload:
                upd[k] = str(payload[k])[:n]
        for k in ("required", "active"):
            if k in payload:
                upd[k] = bool(payload[k])
        await db.training_modules.update_one({"id": mid}, {"$set": upd})
        return await db.training_modules.find_one({"id": mid}, {"_id": 0})

    @api_router.delete("/training/modules/{mid}")
    async def module_delete(mid: str, _: dict = Depends(require_admin)):
        await db.training_modules.delete_one({"id": mid})
        await db.training_done.delete_many({"module_id": mid})
        return {"ok": True}

    @api_router.post("/training/modules/{mid}/complete")
    async def module_complete(mid: str, user: dict = Depends(get_current_user)):
        need_tech(user)
        if not await db.training_modules.find_one({"id": mid, "active": {"$ne": False}}):
            raise HTTPException(404, "Eğitim yok")
        if not await db.training_done.find_one({"user_id": user["id"], "module_id": mid}):
            await db.training_done.insert_one({"id": _id(), "user_id": user["id"], "module_id": mid, "at": _now()})
        return {"ok": True}

    def cert_status(exp):
        if not exp:
            return "suresiz", None
        left = (datetime.fromisoformat(exp).date() - datetime.now(TR).date()).days
        return ("suresi_doldu" if left < 0 else "yaklasiyor" if left <= 30 else "gecerli"), left

    @api_router.get("/training/certificates")
    async def certs(technician_id: str = "", user: dict = Depends(get_current_user)):
        q = {}
        if user["role"] == "technician":
            q["technician_id"] = user["id"]
        elif technician_id:
            q["technician_id"] = technician_id
        rows = await db.certificates.find(q, {"_id": 0}).sort("expires_at", 1).to_list(2000)
        names = {t["id"]: t["name"] for t in await db.users.find({"role": "technician"}, {"_id": 0, "id": 1, "name": 1}).to_list(500)}
        for r in rows:
            r["technician_name"] = names.get(r["technician_id"], "?")
            r["status"], r["days_left"] = cert_status(r.get("expires_at"))
        return rows

    @api_router.post("/training/certificates")
    async def cert_create(payload: dict, _: dict = Depends(require_admin)):
        if not await db.users.find_one({"id": payload.get("technician_id"), "role": "technician"}, {"_id": 1}):
            raise HTTPException(404, "Teknisyen yok")
        title = str(payload.get("title", "")).strip()[:120]
        if not title:
            raise HTTPException(422, "Sertifika adı gerekli")
        for k in ("issued_at", "expires_at"):
            v = str(payload.get(k, ""))[:10]
            if v:
                try:
                    datetime.fromisoformat(v)
                except ValueError:
                    raise HTTPException(422, "Tarih biçimi YYYY-AA-GG olmalı")
        doc = {"id": _id(), "technician_id": payload["technician_id"], "title": title, "issuer": str(payload.get("issuer", ""))[:120],
               "issued_at": str(payload.get("issued_at", ""))[:10], "expires_at": str(payload.get("expires_at", ""))[:10],
               "file_url": str(payload.get("file_url", ""))[:400], "created_at": _now()}
        await db.certificates.insert_one(dict(doc))
        return doc

    @api_router.delete("/training/certificates/{cid}")
    async def cert_delete(cid: str, _: dict = Depends(require_admin)):
        await db.certificates.delete_one({"id": cid})
        return {"ok": True}

    @api_router.get("/training/overview")
    async def training_overview(_: dict = Depends(require_admin)):
        mods = await db.training_modules.find({"active": {"$ne": False}, "required": True}, {"_id": 0, "id": 1}).to_list(500)
        mids = {m["id"] for m in mods}
        out = []
        for t in await db.users.find({"role": "technician"}, {"_id": 0, "id": 1, "name": 1}).to_list(500):
            done = {d["module_id"] for d in await db.training_done.find({"user_id": t["id"]}, {"_id": 0}).to_list(1000)}
            cs = [cert_status(c.get("expires_at"))[0] for c in await db.certificates.find({"technician_id": t["id"]}, {"_id": 0}).to_list(500)]
            out.append({"technician_id": t["id"], "name": t["name"], "required_total": len(mids), "required_done": len(mids & done),
                        "certs": len(cs), "expiring": cs.count("yaklasiyor"), "expired": cs.count("suresi_doldu")})
        return out

    async def cert_hook(_db):
        today = datetime.now(TR).date()
        for c in await db.certificates.find({"expires_at": {"$nin": ["", None]}}, {"_id": 0}).to_list(5000):
            try:
                left = (datetime.fromisoformat(c["expires_at"]).date() - today).days
            except ValueError:
                continue
            hit = [th for th in (30, 7, 0) if left <= th]
            if not hit or left < -3:
                continue
            th = min(hit)
            if await db.outbox.find_one({"kind": "cert_expiry", "ref": f"{c['id']}:{th}"}):
                continue
            t = await db.users.find_one({"id": c["technician_id"]}, {"_id": 0, "name": 1})
            msg = f"Sertifika uyarısı: {(t or {}).get('name', '')} — {c['title']} {('bitti' if left < 0 else 'bitiyor')} ({c['expires_at']})"
            await notify.notify_owner(db, msg, kind="cert_expiry_msg")
            await fieldops.push_to(db, [c["technician_id"]], ("Sertifika süresi doldu" if left < 0 else "Sertifika süresi yaklaşıyor"), f"{c['title']} · son tarih {c['expires_at']}", "/tech/training")
            await db.outbox.insert_one({"id": _id(), "channel": "marker", "to": "", "text": msg, "kind": "cert_expiry", "ref": f"{c['id']}:{th}",
                                        "status": "marker", "error": "", "created_at": _now()})

    governance.HOOKS.append(cert_hook)

    # =================================================================== BAYİ PORTALI
    def clean_dealer(p, cur=None):
        name = str(p.get("name", (cur or {}).get("name", ""))).strip()[:100]
        if not name:
            raise HTTPException(422, "Bayi adı gerekli")
        ds = p.get("districts", (cur or {}).get("districts", []))
        if isinstance(ds, str):
            ds = [x for x in re.split(r"[,\n]", ds)]
        return {"name": name, "phone": str(p.get("phone", (cur or {}).get("phone", "")))[:30], "districts": [x.strip().lower() for x in ds if x.strip()][:100],
                "commission_pct": min(100.0, max(0.0, _f(p.get("commission_pct", (cur or {}).get("commission_pct", 0))))),
                "active": bool(p.get("active", (cur or {}).get("active", True))), "notes": str(p.get("notes", (cur or {}).get("notes", "")))[:500]}

    @api_router.get("/partners")
    async def dealers_list(_: dict = Depends(require_admin)):
        return await db.dealers.find({}, {"_id": 0}).sort("name", 1).to_list(1000)

    @api_router.post("/partners")
    async def dealer_create(payload: dict, _: dict = Depends(require_admin)):
        doc = {**clean_dealer(payload), "id": _id(), "token": secrets.token_urlsafe(24), "created_at": _now()}
        await db.dealers.insert_one(dict(doc))
        return doc

    @api_router.put("/partners/{did}")
    async def dealer_update(did: str, payload: dict, _: dict = Depends(require_admin)):
        cur = await db.dealers.find_one({"id": did}, {"_id": 0})
        if not cur:
            raise HTTPException(404, "Bayi yok")
        upd = clean_dealer(payload, cur)
        await db.dealers.update_one({"id": did}, {"$set": upd})
        return {**cur, **upd}

    @api_router.post("/partners/{did}/rotate-token")
    async def dealer_rotate(did: str, _: dict = Depends(require_admin)):
        tok = secrets.token_urlsafe(24)
        await db.dealers.update_one({"id": did}, {"$set": {"token": tok}})
        return {"token": tok}

    @api_router.delete("/partners/{did}")
    async def dealer_delete(did: str, _: dict = Depends(require_admin)):
        await db.dealers.delete_one({"id": did})
        return {"ok": True}

    @api_router.put("/partners/job/{job_id}")
    async def dealer_job(job_id: str, payload: dict, _: dict = Depends(require_admin)):
        did = payload.get("dealer_id", "")
        if did and not await db.dealers.find_one({"id": did}):
            raise HTTPException(404, "Bayi yok")
        await db.service_jobs.update_one({"id": job_id}, {"$set": {"dealer_id": did}})
        return {"ok": True}

    async def dealer_book(d, month=None):
        leads = await db.contact_messages.find({"dealer_id": d["id"]}, {"_id": 0}).sort("created_at", -1).to_list(2000)
        phones = {_p10(l["phone"]) for l in leads}
        jobs = await db.service_jobs.find({}, {"_id": 0, "workshop.photos": 0, "workshop.signature": 0, "workshop.tech_signature": 0, "workshop.delivery_signature": 0}).to_list(200000)
        mine = [j for j in jobs if j.get("dealer_id") == d["id"] or _p10(j.get("customer_phone")) in phones]
        rows, tot_rev, tot_com = [], 0.0, 0.0
        for j in sorted(mine, key=lambda j: j.get("created_at", ""), reverse=True):
            done = j.get("status") in DONE
            ref = (j.get("completed_at") or "")[:7]
            if month and done and ref != month:
                continue
            com = round(_f(j.get("total_amount")) * d["commission_pct"] / 100.0, 2) if done else 0.0
            rows.append({"job_number": j.get("job_number"), "date": (j.get("created_at") or "")[:10], "customer": _mask_name(j.get("customer_name")),
                         "device": " ".join(x for x in [j.get("device_brand_name"), j.get("device_type")] if x), "status": j.get("status"),
                         "total": _f(j.get("total_amount")) if done else None, "commission": com if done else None})
            if done:
                tot_rev += _f(j.get("total_amount"))
                tot_com += com
        paid = await db.dealer_payouts.find({"dealer_id": d["id"]}, {"_id": 0}).sort("at", -1).to_list(200)
        paid_total = sum(p["amount"] for p in paid)
        all_com = 0.0
        if month:
            for j in mine:
                if j.get("status") in DONE:
                    all_com += round(_f(j.get("total_amount")) * d["commission_pct"] / 100.0, 2)
        else:
            all_com = tot_com
        return {"leads": [{"name": _mask_name(l["name"]), "district": l.get("district", ""), "status": l.get("status"), "date": l["created_at"][:10]} for l in leads[:100]],
                "jobs": rows[:300], "revenue": round(tot_rev, 2), "commission": round(tot_com, 2), "commission_all_time": round(all_com, 2), "paid": round(paid_total, 2),
                "payouts": paid[:50]}

    @api_router.get("/partners/{did}/statement")
    async def dealer_statement(did: str, month: str = "", _: dict = Depends(require_admin)):
        d = await db.dealers.find_one({"id": did}, {"_id": 0})
        if not d:
            raise HTTPException(404, "Bayi yok")
        b = await dealer_book(d, month or None)
        # tüm zamanların komisyonu - ödenen = bakiye
        full = await dealer_book(d, None)
        return {"dealer": d, **b, "balance": round(full["commission"] - full["paid"], 2)}

    @api_router.post("/partners/{did}/pay")
    async def dealer_pay(did: str, payload: dict, user: dict = Depends(require_admin)):
        d = await db.dealers.find_one({"id": did}, {"_id": 0})
        amt = round(_f(payload.get("amount")), 2)
        if not d or amt <= 0:
            raise HTTPException(422, "Bayi ve tutar gerekli")
        await db.cash_transactions.insert_one({"id": _id(), "type": "gider", "amount": amt, "date": _now(), "created_by": user["id"], "technician_id": "", "job_id": "",
                                               "category": "Bayi Komisyonu", "description": f"Bayi komisyon ödemesi - {d['name']}"})
        await db.dealer_payouts.insert_one({"id": _id(), "dealer_id": did, "amount": amt, "note": str(payload.get("note", ""))[:200], "at": _now()})
        return {"ok": True}

    async def dealer_by_token(token):
        d = await db.dealers.find_one({"token": token, "active": True}, {"_id": 0})
        if not d or len(token) < 20:
            raise HTTPException(404, "Bağlantı geçersiz")
        return d

    _hits = defaultdict(list)

    def rate(request, key, n, win):
        import time
        ip = (request.headers.get("x-forwarded-for", "").split(",")[0].strip() or (request.client.host if request.client else ""))
        now = time.time()
        k = (key, ip)
        _hits[k] = [t for t in _hits[k] if now - t < win]
        if len(_hits[k]) >= n:
            raise HTTPException(429, "Çok fazla deneme")
        _hits[k].append(now)

    @api_router.get("/public/dealer/{token}")
    async def dealer_portal(token: str, request: Request):
        rate(request, "dealer", 60, 600)
        d = await dealer_by_token(token)
        b = await dealer_book(d, None)
        s = await db.app_settings.find_one({"_id": "global"}, {"_id": 0}) or {}
        return {"dealer": {"name": d["name"], "districts": d["districts"], "commission_pct": d["commission_pct"]},
                "company": {"name": s.get("company_name", ""), "phone": s.get("company_phone", "")}, **{k: b[k] for k in ("leads", "jobs", "revenue", "commission", "paid")},
                "balance": round(b["commission"] - b["paid"], 2)}

    @api_router.post("/public/dealer/{token}/lead")
    async def dealer_lead(token: str, payload: dict, request: Request):
        rate(request, "dealer-lead", 20, 3600)
        d = await dealer_by_token(token)
        name = str(payload.get("name", "")).strip()[:80]
        phone = _p10(str(payload.get("phone", "")))
        dist = str(payload.get("district", "")).strip()[:60]
        if len(name) < 2 or not re.match(r"^[2-5]\d{9}$", phone):
            raise HTTPException(422, "Ad ve geçerli telefon gerekli")
        if d["districts"] and dist.lower() not in d["districts"]:
            raise HTTPException(403, "Bu ilçe bayi bölgenizde değil: " + ", ".join(x.title() for x in d["districts"]))
        since = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        if await db.contact_messages.find_one({"dealer_id": d["id"], "phone": {"$regex": phone + "$"}, "created_at": {"$gte": since}}):
            raise HTTPException(409, "Bu müşteri zaten yönlendirilmiş")
        doc = {"id": _id(), "type": "servis_talebi", "name": name, "phone": "0" + phone, "email": "", "city": str(payload.get("city", ""))[:60], "district": dist,
               "device_type": str(payload.get("device_type", ""))[:40], "brand": "", "message": str(payload.get("fault", ""))[:600], "status": "yeni", "note": f"Bayi: {d['name']}",
               "job_id": "", "job_number": "", "source": {"channel": "bayi"}, "channel": "bayi", "dealer_id": d["id"], "page": "", "sid": "", "ip": "", "ua": "",
               "created_at": _now(), "updated_at": _now()}
        await db.contact_messages.insert_one(doc)
        try:
            await notify.notify_owner_t(db, f"Bayi yönlendirmesi ({d['name']}): {name} — {dist}", kind="dealer_lead")
        except Exception:                               # noqa: BLE001
            pass
        return {"ok": True}


async def ensure_indexes(db):
    await db.chat_messages.create_index([("thread_id", 1), ("created_at", 1)])
    await db.dealers.create_index("token", unique=True)
    await db.certificates.create_index("technician_id")
    await db.training_done.create_index([("user_id", 1), ("module_id", 1)])

_USTA_KILAVUZ = [
 [
  "Usta ekranına giriş ve ana ekran",
  "Alt menü: Görevler, Sohbet, Teklif, Duyuru, Bakiyem, Daha.\n• Kırmızı rakamlar: Görevler'de yeni atanan iş, Teklif'te bekleyen teklif, Duyuru'da okunmamış duyuru. Bakiyem üzerindeki \"!\" borcunuz olduğunu gösterir.\n• Ana ekran (Görevler): üstte Puanım kartı, hoş geldin alanı, Açık ve Bugün iş sayıları, Arıza Asistanı düğmesi. Altında Aktif Görevler, Tamamlanan (son 7 gün) ve Atölye sekmeleri bulunur.\n• Ekran birkaç saniyede bir kendini yeniler; yeni iş atanınca bildirim gelir.\n• Bir göreve dokunarak iş detayını açarsınız: cihaz, arıza, adres ve müşteri telefonu.\n• Daha sayfasında: bugünkü rota, bu ayki karnem, eğitimler, sık sorulan sorular, arıza rehberi ve profilim yer alır."
 ],
 [
  "İş akışı: Yoldayım → Servise Başla → Tamamla",
  "1) Yeni iş atanınca bildirim gelir. Görevler'den işi açın; adresi, cihazı ve arızayı kontrol edin.\n2) Yola çıkarken \"Yoldayım\"a basın. Tahmini varış süresini seçersiniz; müşteriye \"usta yolda\" mesajı ve canlı takip linki gönderilir. Özel bir not için \"Müşteriye mesaj\"ı kullanın.\n3) \"Yola Çık\" düğmesi durumu Yolda yapar. Müşteriye vardığınızda \"Servise Başla\" ile durum Başladı olur.\n4) Başladı durumunda iş formu açılır: Yapılan İş, Yedek Parçalar, İşçilik, Fotoğraflar. Doldurup \"Kaydet\"e basın.\n5) İş bitince \"Tamamla\"ya basın. Eksik zorunlu bilgi varsa ekran neyin eksik olduğunu söyler (örneğin işaretlenmemiş zorunlu kontrol listesi maddesi; kurulum işlerinde \"Sonra\" fotoğrafı).\n6) Tamamlanan iş sizin tarafınızdan düzenlenemez. Düzeltme gerekiyorsa Sohbet'ten yönetime yazın."
 ],
 [
  "Yedek parça, işçilik ve fotoğraf",
  "• Yedek Parçalar → \"Ekle\": stoktaki parçayı seçin. Stokta kayıtlı olmayan parça için \"Manuel\" seçip adını ve fiyatını yazın.\n• İşçilik (₺): aldığınız işçilik ücretini yazın. Toplam, parça ve işçilikten otomatik hesaplanır.\n• Fotoğraflar: \"Önce\" (işe başlamadan), \"Sonra\" (iş bittikten sonra). Telefon fotoğrafları sistem tarafından otomatik küçültülür, ayrıca bir şey yapmanız gerekmez. Kurulum işlerinde en az bir \"Sonra\" fotoğrafı gerekir.\n• Yapılan İş alanında \"Sesle yaz\" ile konuşarak yazabilir, \"AI ile düzelt\" ile metni düzelttirebilirsiniz. Yapay zekâ yönetim tarafından açıksa çalışır.\n• Her değişiklikten sonra \"Kaydet\"e basmayı unutmayın."
 ],
 [
  "Atölyeye alma, müşteri vazgeçti, QR etiket",
  "• Atölyeye Al: cihaz yerinde onarılamıyor ve atölyeye götürülecekse kullanılır. Düğme yalnızca iş \"Başladı\" durumundayken görünür. Neden, cihaz durumu, aksesuarlar, tahmini teslim tarihi/ücret ve müşteri imzası alınır; Teslim alma formu oluşur.\n• Atölyedeki cihazlar ana ekranda Atölye sekmesinde listelenir: formu yazdırabilir, kaydı açabilir, \"Hazır\" ve \"Teslim edildi\" işaretleyebilirsiniz.\n• Müşteri Vazgeçti: müşteri işlemi istemezse işi bu düğmeyle kapatın.\n• QR Etiket: cihaza yapıştırılacak QR etiketi yazdırır. Müşteri telefonuyla okutarak cihazın servis geçmişini ve garanti durumunu görebilir."
 ],
 [
  "Teklif, sohbet, duyuru ve arıza rehberi",
  "• Teklif: müşteriye fiyat teklifi hazırlayın. Teklif ve alt notu müşteriye gösterilen ekranda ve PDF'te görünür. Bekleyen teklif sayısı sekme üzerinde rakamla görünür.\n• Sohbet: merkezle yazışma alanı. Arıza kodu, parça veya fiyat konusunda merkeze buradan yazabilirsiniz.\n• Duyuru: yönetimin ustalara yazdığı duyurular. Okunmamışlar rozetle görünür.\n• Arıza Asistanı / Arıza Rehberi: arıza koduna veya belirtiye göre olası neden ve çözüm önerileri sunar. İş detayından da açılır."
 ],
 [
  "Bakiyem, ödeme ve profilim",
  "• Bakiyem: şirkete borcunuz, borç oranınız ve şirket IBAN bilgileri görünür. IBAN'ı kopyala düğmesiyle kopyalayabilirsiniz.\n• Ödeme yaptıktan sonra \"Ödeme yaptım\" ile yönetime bildirim gönderin. Ödeme yönetimde tahsilat olarak işlenince bakiyeniz düşer. Borcunuz yoksa ₺0 görünür.\n• Profilim: kendi bilgilerinizi ve IBAN'ınızı girersiniz (şirketin size ödeme yapabilmesi için).\n• Eğitimler: her modülü okuyunca \"Okudum\"a basın. Zorunlu işaretli olanları mutlaka tamamlayın. Aldığınız sertifikalar Sertifikalarım bölümünde görünür."
 ],
 [
  "Bildirimler, internet kesintisi ve ekran ayarları",
  "• Bildirim: üstteki zil (🔔) düğmesine bir kez dokunup izin verin. Yeni iş atanınca ses, titreşim ve bildirim gelir. İzin vermezseniz yeni işleri ancak uygulamayı açınca görürsünüz.\n• Uygulamayı açınca \"N yeni işiniz var\" şeridi çıkar.\n• İnternet kesilirse üstte \"Çevrimdışı\" şeridi çıkar. İş formundaki kayıtlar cihazda bekletilir ve bağlantı gelince otomatik gönderilir. Çok büyük fotoğraflar bekletilmez; internet gelince yeniden yükleyin. Bu özellik, sayfa açıkken bağlantı kopması için geçerlidir.\n• Daha sayfasının altında A− / A+ ile yazı boyutunu değiştirebilirsiniz. Üstteki ay/güneş düğmesi koyu-açık temayı, dil düğmesi dili değiştirir.\n• Müşteri telefonu yönetim ayarına göre maskeli (örnek: 0544 *** ** 04) görünebilir. Arama anında numara açılır ve her açış kaydedilir."
 ]
]

async def seed_training(db):
    """Usta ekranı kullanım kılavuzu eğitim modüllerini BİR KEZ ekler (sonradan silinse/düzenlense geri eklenmez)."""
    if await db.app_settings.find_one({"_id": "seed_training_usta_v1"}):
        return
    now = _now()
    for i, (title, content) in enumerate(_USTA_KILAVUZ):
        mid = "seed-usta-%d" % (i + 1)
        if not await db.training_modules.find_one({"id": mid}):
            await db.training_modules.insert_one({"id": mid, "title": "%d) %s" % (i + 1, title), "content": content, "url": "",
                                                  "required": False, "active": True, "created_at": (datetime.now(timezone.utc) + timedelta(seconds=i)).isoformat()})
    await db.app_settings.update_one({"_id": "seed_training_usta_v1"}, {"$set": {"at": now}}, upsert=True)
