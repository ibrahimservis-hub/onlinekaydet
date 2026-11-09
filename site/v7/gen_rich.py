import pages_cozum,pages_hub,pages_tema,pages_misc,pages_blog
n=pages_cozum.build_all()
pages_hub.hub_ozellikler();pages_hub.usta();pages_hub.hub_ent();pages_hub.sub_ent()
pages_tema.temalar();t=pages_tema.detail()
for f in ['guvenlik','sikayet','senaryo','baslangic','karsilastirma','sss','neden','destek','araclar','garanti','fis']: getattr(pages_misc,f)()
b=pages_blog.build_all()
leg=[('blog-servis-takip-programi-nedir.html','Servis takip programı nedir?',('Temel','Servis takip programı ne işe yarar, kimler için gerekli ve neleri çözer.')),
('blog-servis-kaydi-bilgileri.html','Servis kaydında hangi bilgiler tutulur?',('Rehber','Servis kaydında olması gereken bilgiler ve neden önemli olduğu.')),
('blog-servis-fisi-nasil-hazirlanir.html','Servis fişi nasıl hazırlanır?',('Rehber','Servis fişinde bulunması gereken alanlar ve düzenleme ipuçları.'))]
pages_misc.bilgi_bankasi(leg+pages_blog.HUB)
print(n,'çözüm',t,'tema',b,'blog')
