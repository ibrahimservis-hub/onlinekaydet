"""Test yardımcısı: demo ile gelen örnek randevu ve müşterileri siler (eski testler boş firma varsayar)."""
import asyncio


def bos(c, s, demo_json, koleksiyonlar=("bookings", "yp_customers")):
    A = {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": "admin@servis.com", "password": "admin123"}).json()["token"]}
    firms = c.get("/api/admin/firms", headers=A).json()["firms"]
    f = [x for x in firms if x.get("demo")][-1]
    dbname = s.db.firm_db_name(f["id"])
    async def run():
        fdb = s.db.firm(dbname) if hasattr(s.db, "firm") else None
        for col in koleksiyonlar:
            await getattr(fdb, col).delete_many({})
    c.portal.call(run)
