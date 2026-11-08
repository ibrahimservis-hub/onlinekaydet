# -*- coding: utf-8 -*-
"""Canli destek (site sohbeti).
Ziyaretci sitedeki 'Canli Destek' penceresine ad, telefon ve mesaj yazar -> sohbet acilir, otomatik karsilama mesaji gider.
Yoneticiler panelde 'Canli Sohbet' ekraninda konusur; yeni ziyaretci mesajinda admin bildirimi (push) gider.
Ziyaretci sohbeti bir gizli 'token' ile okur/yazar (sadece kendi tarayicisinda saklanir)."""
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, Request

WELCOME = "Merhaba {ad}, ServisPlus'a hoş geldiniz. Müsait olan temsilci en kısa sürede size yardımcı olacaktır."
AUTO_REPLY = WELCOME  # yonetici "Otomatik cevap" butonu ayni karsilamayi gonderir

# Yonetici "Otomatik cevap gonder"e basinca secilen hazir mesajlar. {ad} musterinin adiyla degisir.
DEFAULT_QUICK = [
    ("Karşılama", WELCOME),
    ("Cihaz bilgisi iste", "Merhaba {ad}, size daha iyi yardımcı olabilmemiz için cihazınızın markasını, modelini ve yaşadığınız arızayı yazar mısınız?"),
    ("Adres / bölge iste", "Merhaba {ad}, servis planlayabilmemiz için ilçe ve mahalle bilginizi paylaşır mısınız?"),
    ("Randevu saati sor", "Merhaba {ad}, size uygun bir servis randevusu ayarlayalım. Hangi gün ve saat aralığı sizin için uygun?"),
    ("Sizi arıyoruz", "Merhaba {ad}, sizi birazdan telefonla arayacağız. Telefonunuzun yakınında olabilir misiniz?"),
    ("Mesai dışı", "Merhaba {ad}, şu an mesai saatlerimiz dışındayız. Mesajınızı aldık, ilk fırsatta size dönüş yapacağız."),
    ("Teşekkür / kapanış", "Bizi tercih ettiğiniz için teşekkür ederiz {ad}. Başka bir sorunuz olursa buradan yazabilirsiniz."),
]


def _now():
    return datetime.now(timezone.utc).isoformat()


def _recent(ts, secs):
    """ISO zaman damgasi son `secs` saniye icinde mi? (yazıyor / çevrimiçi göstergeleri için)"""
    try:
        return bool(ts) and (datetime.now(timezone.utc) - datetime.fromisoformat(ts)).total_seconds() <= secs
    except Exception:
        return False


def _first(name: str) -> str:
    return (name or "").strip().split(" ")[0] if name else ""


def register(api_router, db, deps):
    get_current_user = deps["get_current_user"]

    async def _admin(user):
        if user.get("role") != "admin":
            raise HTTPException(403, "Yetkisiz")

    async def _notify(title, body):
        try:
            import notify as _n
            await _n.push_admins_t(db, title, body, "/admin?ek=sohbet")
        except Exception:
            pass

    async def _add(chat_id, sender, text):
        doc = {"id": str(uuid.uuid4()), "chat_id": chat_id, "from": sender, "text": text[:1000], "at": _now()}
        await db.live_messages.insert_one(doc)
        return doc

    async def _chat_for_visitor(cid, token):
        c = await db.live_chats.find_one({"id": cid}, {"_id": 0})
        if not c or not token or not secrets.compare_digest(str(c.get("token", "")), str(token)):
            raise HTTPException(404, "Sohbet bulunamadı")
        return c

    # ---------- ziyaretci (site) ----------
    @api_router.post("/public/chat/start")
    async def chat_start(payload: dict):
        name = str(payload.get("name") or "").strip()[:80]
        phone = "".join(ch for ch in str(payload.get("phone") or "") if ch.isdigit())[:15]
        page = str(payload.get("page") or "")[:200]
        brand = str(payload.get("brand") or "")[:60]
        first_msg = str(payload.get("message") or "").strip()[:1000]
        if len(name) < 3 or len(phone) < 10:
            raise HTTPException(422, "Ad soyad ve telefon gerekli")
        cid = str(uuid.uuid4())
        token = secrets.token_urlsafe(24)
        now = _now()
        await db.live_chats.insert_one({
            "id": cid, "token": token, "name": name, "phone": phone, "page": page, "brand": brand,
            "status": "acik", "created_at": now, "updated_at": now, "unread_admin": 1, "last_text": first_msg or WELCOME.format(ad=_first(name)),
        })
        # otomatik karsilama (sistem mesaji)
        await _add(cid, "bot", WELCOME.format(ad=_first(name)))
        if first_msg:
            await _add(cid, "visitor", first_msg)
        await _notify("Yeni canlı sohbet", f"{name} · {phone}" + (f" · {brand}" if brand else ""))
        return {"ok": True, "chat_id": cid, "token": token}

    @api_router.get("/public/chat/{cid}/messages")
    async def chat_messages(cid: str, token: str = "", after: str = ""):
        await _chat_for_visitor(cid, token)
        q = {"chat_id": cid}
        if after:
            q["at"] = {"$gt": after}
        rows = [r async for r in db.live_messages.find(q, {"_id": 0}).sort("at", 1).limit(200)]
        now = _now()
        await db.live_chats.update_one({"id": cid}, {"$set": {"visitor_seen_at": now, "visitor_last_seen": now}})
        c = await db.live_chats.find_one({"id": cid}, {"_id": 0, "typing_admin_at": 1, "admin_seen_at": 1, "status": 1}) or {}
        return {"ok": True, "messages": [{"from": r["from"], "text": r["text"], "at": r["at"]} for r in rows],
                "agent_typing": _recent(c.get("typing_admin_at"), 6), "admin_seen_at": c.get("admin_seen_at") or "", "status": c.get("status", "acik")}

    @api_router.post("/public/chat/{cid}/typing")
    async def chat_visitor_typing(cid: str, payload: dict):
        await _chat_for_visitor(cid, str(payload.get("token") or ""))
        await db.live_chats.update_one({"id": cid}, {"$set": {"typing_visitor_at": _now(), "visitor_last_seen": _now()}})
        return {"ok": True}

    @api_router.post("/public/chat/{cid}/message")
    async def chat_visitor_msg(cid: str, payload: dict):
        token = str(payload.get("token") or "")
        c = await _chat_for_visitor(cid, token)
        text = str(payload.get("text") or "").strip()[:1000]
        if not text:
            raise HTTPException(422, "Mesaj boş")
        cutoff = (datetime.now(timezone.utc) - timedelta(seconds=60)).isoformat()
        if await db.live_messages.count_documents({"chat_id": cid, "from": "visitor", "at": {"$gt": cutoff}}) >= 15:
            raise HTTPException(429, "Çok hızlı yazıyorsunuz, lütfen biraz bekleyin")
        await _add(cid, "visitor", text)
        await db.live_chats.update_one({"id": cid}, {"$set": {"updated_at": _now(), "last_text": text, "status": "acik"}, "$unset": {"deleted_at": ""}, "$inc": {"unread_admin": 1}})
        await _notify(f"Canlı sohbet: {c.get('name', '')}", text[:120])
        return {"ok": True}

    # ---------- yonetici (panel) ----------
    @api_router.get("/admin/chat/list")
    async def admin_chat_list(user: dict = Depends(get_current_user)):
        await _admin(user)
        rows = [r async for r in db.live_chats.find({"deleted_at": {"$exists": False}}, {"_id": 0, "token": 0}).sort("updated_at", -1).limit(200)]
        for r in rows:
            r["online"] = _recent(r.get("visitor_last_seen"), 15)
        return {"ok": True, "items": rows}

    # --- hazir (otomatik) mesajlar: liste / ekle / duzenle / sil. {cid} yollarindan once tanimli olmali ---
    async def _seed_quick():
        if await db.live_chat_settings.find_one({"id": "quick_seeded"}, {"_id": 1}):
            return
        if await db.live_quick_replies.count_documents({}) == 0:
            for i, (title, text) in enumerate(DEFAULT_QUICK):
                await db.live_quick_replies.insert_one({"id": str(uuid.uuid4()), "title": title, "text": text, "order": i, "at": _now()})
        await db.live_chat_settings.insert_one({"id": "quick_seeded", "at": _now()})

    def _quick_fields(payload):
        title = str(payload.get("title") or "").strip()[:60]
        text = str(payload.get("text") or "").strip()[:1000]
        if not title or not text:
            raise HTTPException(422, "Başlık ve mesaj gerekli")
        return title, text

    @api_router.get("/admin/chat/quick-replies")
    async def quick_list(user: dict = Depends(get_current_user)):
        await _admin(user)
        await _seed_quick()
        rows = [r async for r in db.live_quick_replies.find({}, {"_id": 0}).sort([("order", 1), ("at", 1)]).limit(60)]
        return {"ok": True, "items": rows}

    @api_router.post("/admin/chat/quick-replies")
    async def quick_add(payload: dict, user: dict = Depends(get_current_user)):
        await _admin(user)
        await _seed_quick()
        title, text = _quick_fields(payload)
        if await db.live_quick_replies.count_documents({}) >= 40:
            raise HTTPException(422, "En fazla 40 hazır mesaj eklenebilir")
        last = [r async for r in db.live_quick_replies.find({}, {"_id": 0, "order": 1}).sort("order", -1).limit(1)]
        doc = {"id": str(uuid.uuid4()), "title": title, "text": text, "order": (last[0].get("order", 0) + 1) if last else 0, "at": _now()}
        await db.live_quick_replies.insert_one(dict(doc))
        return {"ok": True, "item": doc}

    @api_router.put("/admin/chat/quick-replies/{qid}")
    async def quick_edit(qid: str, payload: dict, user: dict = Depends(get_current_user)):
        await _admin(user)
        title, text = _quick_fields(payload)
        r = await db.live_quick_replies.update_one({"id": qid}, {"$set": {"title": title, "text": text}})
        if not r.matched_count:
            raise HTTPException(404, "Hazır mesaj bulunamadı")
        return {"ok": True}

    @api_router.delete("/admin/chat/quick-replies/{qid}")
    async def quick_delete(qid: str, user: dict = Depends(get_current_user)):
        # DELETE yalnizca Sahip hesabina acik (governance ara katmani)
        await _admin(user)
        await db.live_quick_replies.delete_one({"id": qid})
        return {"ok": True}

    @api_router.get("/admin/chat/{cid}")
    async def admin_chat_get(cid: str, user: dict = Depends(get_current_user)):
        await _admin(user)
        c = await db.live_chats.find_one({"id": cid}, {"_id": 0, "token": 0})
        if not c:
            raise HTTPException(404, "Sohbet bulunamadı")
        await db.live_chats.update_one({"id": cid}, {"$set": {"unread_admin": 0, "admin_seen_at": _now()}})
        msgs = [r async for r in db.live_messages.find({"chat_id": cid}, {"_id": 0}).sort("at", 1).limit(500)]
        c["online"] = _recent(c.get("visitor_last_seen"), 15)
        c["visitor_typing"] = _recent(c.get("typing_visitor_at"), 6)
        return {"ok": True, "chat": c, "messages": msgs}

    @api_router.post("/admin/chat/{cid}/typing")
    async def admin_chat_typing(cid: str, user: dict = Depends(get_current_user)):
        await _admin(user)
        await db.live_chats.update_one({"id": cid}, {"$set": {"typing_admin_at": _now()}})
        return {"ok": True}

    @api_router.post("/admin/chat/{cid}/reply")
    async def admin_chat_reply(cid: str, payload: dict, user: dict = Depends(get_current_user)):
        await _admin(user)
        text = str(payload.get("text") or "").strip()[:1000]
        if not text:
            raise HTTPException(422, "Mesaj boş")
        if not await db.live_chats.find_one({"id": cid}, {"_id": 1}):
            raise HTTPException(404, "Sohbet bulunamadı")
        await _add(cid, "admin", text)
        await db.live_chats.update_one({"id": cid}, {"$set": {"updated_at": _now(), "last_text": text}})
        return {"ok": True}

    @api_router.post("/admin/chat/{cid}/auto")
    async def admin_chat_auto(cid: str, user: dict = Depends(get_current_user)):
        await _admin(user)
        c = await db.live_chats.find_one({"id": cid}, {"_id": 0, "name": 1})
        if not c:
            raise HTTPException(404, "Sohbet bulunamadı")
        text = AUTO_REPLY.format(ad=_first(c.get("name", "")))
        await _add(cid, "admin", text)
        await db.live_chats.update_one({"id": cid}, {"$set": {"updated_at": _now(), "last_text": text}})
        return {"ok": True}

    @api_router.post("/admin/chat/{cid}/close")
    async def admin_chat_close(cid: str, user: dict = Depends(get_current_user)):
        await _admin(user)
        await db.live_chats.update_one({"id": cid}, {"$set": {"status": "kapali", "updated_at": _now()}})
        return {"ok": True}

    @api_router.delete("/admin/chat/{cid}")
    async def admin_chat_delete(cid: str, user: dict = Depends(get_current_user)):
        # Panelden gizler; mesajlar veritabaninda kalir (sikayet/kayit icin). DELETE yalnizca Sahip hesabina acik.
        await _admin(user)
        r = await db.live_chats.update_one({"id": cid}, {"$set": {"deleted_at": _now(), "status": "kapali"}})
        if not r.matched_count:
            raise HTTPException(404, "Sohbet bulunamadı")
        return {"ok": True}
