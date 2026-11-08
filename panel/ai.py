"""Yapay zekâ adaptörü (OpenAI uyumlu uç nokta): müşteri yanıt önerisi, not düzeltme, parça fotoğrafı tanıma,
arama kaydı çözümleme (ses→metin→özet). Anahtar panelden girilir; anahtar yoksa hiçbir şey gönderilmez.

GİZLİLİK: Metne gömülü telefon numaraları, e-posta ve uzun rakam dizileri sağlayıcıya gitmeden önce maskelenir.
NOT: Canlı bir sağlayıcıyla denenmedi; testler sahte yanıtla yapıldı. Ses/fotoğraf özellikleri sağlayıcının modeline bağlıdır.
"""
import asyncio
import base64
import json
import re
from datetime import datetime, timezone

import requests
from fastapi import Depends, HTTPException, UploadFile, File

MASK = "********"
DEFAULTS = {"enabled": False, "base_url": "https://api.openai.com/v1", "api_key": "", "chat_model": "gpt-4o-mini", "vision_model": "gpt-4o-mini",
            "transcribe_model": "whisper-1", "daily_limit": 200,
            "system_prompt": "Sen Türkiye'de kombi, klima ve beyaz eşya servisi yapan bir firmanın asistanısın. Kısa, nazik ve net Türkçe yaz. Fiyat veya garanti sözü verme."}


def redact(t: str) -> str:
    t = re.sub(r"[\w.+-]+@[\w-]+\.[\w.]+", "[eposta]", t or "")
    t = re.sub(r"(?:\+?90|0)?[\s-]?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}", "[tel]", t)
    return re.sub(r"\d{8,}", "[no]", t)


def _post(url, headers, json_body=None, files=None, data=None, timeout=60):
    r = requests.post(url, headers=headers, json=json_body, files=files, data=data, timeout=timeout)
    if r.status_code >= 400:
        raise RuntimeError(f"AI sağlayıcı hatası {r.status_code}: {r.text[:200]}")
    return r.json()


def register(api_router, db, deps):
    require_admin = deps["require_admin"]
    get_current_user = deps["get_current_user"]

    async def cfg():
        d = await db.app_settings.find_one({"_id": "ai"}, {"_id": 0}) or {}
        return {**DEFAULTS, **d}

    async def guard(user):
        c = await cfg()
        if not c["enabled"] or not c["api_key"]:
            raise HTTPException(400, "Yapay zekâ kapalı veya anahtar girilmemiş (Ayarlar → Yapay Zekâ)")
        day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        n = await db.ai_usage.count_documents({"day": day})
        if n >= int(c["daily_limit"]):
            raise HTTPException(429, "Günlük yapay zekâ limiti doldu")
        await db.ai_usage.insert_one({"day": day, "user_id": user["id"], "at": datetime.now(timezone.utc).isoformat()})
        return c

    async def chat(c, messages, model=None, max_tokens=500, json_mode=False):
        body = {"model": model or c["chat_model"], "messages": messages, "max_tokens": max_tokens, "temperature": 0.4}
        if json_mode:
            body["response_format"] = {"type": "json_object"}
        url = c["base_url"].rstrip("/") + "/chat/completions"
        hdr = {"Authorization": "Bearer " + c["api_key"]}
        models = [body["model"]]
        if "googleapis.com" in c["base_url"] and "gemini-flash-latest" not in models:
            models.append("gemini-flash-latest")          # yedek: model yoğunken/kapanınca Google'ın "güncel flash" takma adı
        last = None
        for m in models:
            for attempt in range(3):                      # geçici 429/503 (yoğunluk): 1 sn, 2 sn bekleyip tekrar dene
                try:
                    res = await asyncio.to_thread(_post, url, hdr, {**body, "model": m})
                    return res["choices"][0]["message"]["content"].strip()
                except Exception as e:                    # noqa: BLE001
                    last = e
                    if any(x in str(e) for x in ("429", "503", "UNAVAILABLE", "overloaded")) and attempt < 2:
                        await asyncio.sleep(1 + attempt)
                        continue
                    break
        raise HTTPException(502, str(last)[:250])

    @api_router.get("/ai/settings")
    async def get_ai(_: dict = Depends(require_admin)):
        c = await cfg()
        c["api_key"] = MASK if c["api_key"] else ""
        return c

    @api_router.put("/ai/settings")
    async def put_ai(payload: dict, _: dict = Depends(require_admin)):
        cur = await cfg()
        upd = {}
        for k in ("enabled",):
            if k in payload:
                upd[k] = bool(payload[k])
        for k in ("base_url", "chat_model", "vision_model", "transcribe_model", "system_prompt"):
            if k in payload:
                upd[k] = str(payload[k])[:600]
        if "daily_limit" in payload:
            upd["daily_limit"] = max(1, min(5000, int(payload["daily_limit"] or 200)))
        if "api_key" in payload and payload["api_key"] != MASK:
            upd["api_key"] = str(payload["api_key"]).strip()[:300]
        if upd.get("base_url") and not re.match(r"^https?://", upd["base_url"]):
            raise HTTPException(422, "Adres http(s):// ile başlamalı")
        await db.app_settings.update_one({"_id": "ai"}, {"$set": upd}, upsert=True)
        return await get_ai(_)

    @api_router.post("/ai/reply-suggest")
    async def reply_suggest(payload: dict, user: dict = Depends(require_admin)):
        c = await guard(user)
        msg = redact(str(payload.get("message", ""))[:1500])
        if not msg.strip():
            raise HTTPException(422, "Müşteri mesajı gerekli")
        ctx = redact(str(payload.get("context", ""))[:800])
        out = await chat(c, [{"role": "system", "content": c["system_prompt"] + " Müşteriye gönderilecek 3 farklı kısa yanıt önerisi yaz. Yalnızca JSON döndür: {\"replies\":[\"...\",\"...\",\"...\"]}"},
                             {"role": "user", "content": f"Bağlam: {ctx}\nMüşteri mesajı: {msg}"}], json_mode=True)
        try:
            reps = json.loads(out).get("replies", [])
        except ValueError:
            reps = [out]
        return {"replies": [str(r)[:600] for r in reps][:3]}

    @api_router.post("/ai/polish")
    async def polish(payload: dict, user: dict = Depends(get_current_user)):
        c = await guard(user)
        text = redact(str(payload.get("text", ""))[:3000])
        if not text.strip():
            raise HTTPException(422, "Metin gerekli")
        kind = payload.get("kind", "servis notu")
        out = await chat(c, [{"role": "system", "content": f"Aşağıdaki {kind} metnini anlamı değiştirmeden imla/noktalama düzelt, net ve profesyonel hâle getir. Yeni bilgi ekleme. Yalnızca düzeltilmiş metni döndür."},
                             {"role": "user", "content": text}], max_tokens=800)
        return {"text": out}

    @api_router.post("/ai/identify-part")
    async def identify_part(payload: dict, user: dict = Depends(get_current_user)):
        c = await guard(user)
        img = str(payload.get("image", ""))
        if not (img.startswith("data:image/") or img.startswith("https://")):
            raise HTTPException(422, "Fotoğraf (data URL veya https) gerekli")
        if len(img) > 6_000_000:
            raise HTTPException(413, "Fotoğraf çok büyük")
        hint = redact(str(payload.get("hint", ""))[:300])
        out = await chat(c, [{"role": "system", "content": c["system_prompt"] + " Fotoğraftaki yedek parçayı/etiketi tanımla: olası parça adı, marka/model/kod (okunabiliyorsa), emin değilsen belirt. Kısa madde işaretleri kullan."},
                             {"role": "user", "content": [{"type": "text", "text": f"Cihaz ipucu: {hint or '-'}"}, {"type": "image_url", "image_url": {"url": img}}]}],
                         model=c["vision_model"], max_tokens=500)
        return {"text": out, "warning": "Yapay zekâ tahmini — sipariş vermeden önce etiketle doğrulayın."}

    @api_router.post("/ai/transcribe")
    async def transcribe(file: UploadFile = File(...), summarize: bool = True, user: dict = Depends(require_admin)):
        c = await guard(user)
        data = await file.read()
        if not data or len(data) > 24 * 1024 * 1024:
            raise HTTPException(413, "Ses dosyası boş veya 24 MB'tan büyük")
        try:
            res = await asyncio.to_thread(_post, c["base_url"].rstrip("/") + "/audio/transcriptions", {"Authorization": "Bearer " + c["api_key"]},
                                          None, {"file": (file.filename or "kayit.mp3", data, file.content_type or "audio/mpeg")}, {"model": c["transcribe_model"], "language": "tr"}, 120)
        except Exception as e:                          # noqa: BLE001
            raise HTTPException(502, str(e)[:250])
        text = (res.get("text") or "").strip()
        out = {"transcript": text}
        if summarize and text:
            raw = await chat(c, [{"role": "system", "content": "Aşağıdaki müşteri görüşmesi dökümünden Türkçe JSON çıkar: {\"summary\":\"2 cümle\",\"fault\":\"arıza\",\"device\":\"cihaz\",\"urgency\":\"dusuk|normal|yuksek|acil\",\"next_step\":\"yapılacak\"}"},
                                {"role": "user", "content": redact(text)[:6000]}], json_mode=True, max_tokens=400)
            try:
                out["analysis"] = json.loads(raw)
            except ValueError:
                out["analysis"] = {"summary": raw}
        return out

    @api_router.get("/ai/usage")
    async def usage(_: dict = Depends(require_admin)):
        day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return {"today": await db.ai_usage.count_documents({"day": day}), "limit": (await cfg())["daily_limit"]}


async def ensure_indexes(db):
    await db.ai_usage.create_index("day")
