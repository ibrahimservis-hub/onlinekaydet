# -*- coding: utf-8 -*-
"""Firma (ayrı veri) altyapısı.

Her firma kendi MongoDB veritabanını kullanır. Girişte firma belirlenir ve JWT'ye `firm` bilgisi yazılır;
sonraki her istekte `db` nesnesi (TenantDB) o istek için firmanın veritabanına yönlenir. Böylece mevcut tüm
ekranlar ve uçlar kod değişmeden firmanın KENDİ verisiyle çalışır; ServisPlus verisine hiç dokunmaz.

Güvenlik: `firm` bilgisi yalnız imzalı JWT'den ve giriş sırasında ana veritabanındaki `firms` kaydından gelir.
Firma belirlenemezse (bağlam yoksa) ana veritabanı kullanılır; firma jetonu ana veritabanında kullanıcı bulamaz.
"""
import contextvars
import re

_FIRM = contextvars.ContextVar("spx_firm_db", default=None)
_OK = re.compile(r"^[A-Za-z0-9_]{3,80}$")


def current():
    return _FIRM.get()


def set_firm(db_name):
    if db_name and not _OK.match(str(db_name)):
        raise ValueError("geçersiz firma veritabanı adı")
    return _FIRM.set(db_name or None)


def reset(token):
    try:
        _FIRM.reset(token)
    except Exception:                                     # noqa: BLE001
        pass


class TenantDB:
    """Motor veritabanı gibi davranır; hangi veritabanına gideceğini istek bağlamından seçer."""

    def __init__(self, client, main_name):
        object.__setattr__(self, "_client", client)
        object.__setattr__(self, "_main", main_name)

    def _cur(self):
        n = _FIRM.get()
        return self._client[n] if n else self._client[self._main]

    def __getattr__(self, name):
        if name.startswith("__"):
            raise AttributeError(name)
        return getattr(self._cur(), name)

    def __getitem__(self, name):
        return self._cur()[name]

    def main(self):
        """Her zaman ana (ServisPlus) veritabanı."""
        return self._client[self._main]

    def firm(self, db_name):
        if not _OK.match(str(db_name)):
            raise ValueError("geçersiz firma veritabanı adı")
        return self._client[db_name]

    def firm_db_name(self, firm_id):
        return "%s_f_%s" % (self._main, firm_id)
