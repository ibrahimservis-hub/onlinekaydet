# cPanel kurulumu (onlinekaydet.com)

1. **Alan adı → hosting:** Atak Domain panelinde DNS'i hosting'e yönlendirin (ad sunucuları ya da A kaydı; hosting'in hoşgeldin e-postasındaki değerler).
2. **cPanel › Domains › Create A New Domain:** `onlinekaydet.com`, "Share document root" kapalı; kök klasör `onlinekaydet.com`.
3. **cPanel › Git™ Version Control › Create:** Clone URL `https://github.com/ibrahimservis-hub/onlinekaydet.git` (özel depo: erişim anahtarı/şifre ister), depo yolu `repositories/onlinekaydet`.
4. **MongoDB Atlas:** ücretsiz küme açın, veritabanı kullanıcısı oluşturun, Network Access'e hosting sunucusunun IP'sini (veya 0.0.0.0/0) ekleyin; bağlantı dizesini `MONGO_URL` yapın.
5. **cPanel › Setup Python App:** Python 3.11+, Application root `onlinekaydet_app`, Application URL `onlinekaydet.com`, startup file `passenger_wsgi.py`, entry point `application`.
6. Deploy HEAD Commit (`.cpanel.yml`) ile dosyalar kopyalanır. Python uygulamasında "Run Pip Install" ile `requirements.txt` kurulur.
7. Uygulama klasöründe `.env.example` dosyasını `.env` olarak kopyalayıp doldurun (**JWT_SECRET ve ADMIN_PASSWORD'ü mutlaka değiştirin**). Uygulamayı Restart edin.
8. **SSL:** cPanel › SSL/TLS Status › Run AutoSSL (onlinekaydet.com ve www).
9. Test: `https://onlinekaydet.com/` (satış sitesi), `/giris` (panel), `/api/public/lead` (form).
