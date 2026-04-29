# Proje Durum Dosyası

## Genel Yapı

Django projesi. Supabase (PostgreSQL) veritabanı, OpenRouteService API ile rota çizimi, Leaflet.js ile harita gösterimi.

```
core/           → Django ayarları, URL yapılandırması
employees/      → Çalışan modeli (henüz geliştirilmedi)
vehicles/       → Araç modeli (henüz geliştirilmedi)
workspaces/     → Operasyon/workspace yönetimi
routes/         → Rota yönetimi, ORS entegrasyonu
templates/      → HTML şablonları
```

---

## Yapılan Değişiklikler

### 1. Ortam Kurulumu

- `.gitignore` oluşturuldu: `venv/`, `.env`, `__pycache__/`, `*.pyc`, `db.sqlite3`, `*.log`
- `.env` oluşturuldu: Supabase bağlantı bilgileri ve ORS API anahtarı

---

### 2. Renk Seçici Yeniden Tasarlandı — `templates/routes/map.html`

**Eski yapı:** 24 renkten oluşan 8 kolonlu grid, sadece hazır renkler.

**Yeni yapı:**
- 10 hazır renk dairesi (28×28 px, 5×2 grid): `#E74C3C`, `#E67E22`, `#F1C40F`, `#2ECC71`, `#1ABC9C`, `#3498DB`, `#9B59B6`, `#34495E`, `#FF61A6`, `#00C9A7`
- Seçili daireye beyaz `outline` ring
- `+` butonu (dashed border, aynı boyut) — tıklayınca özel renk popup'ı açılır
- Popup içeriği: canlı önizleme dairesi, hex kodu (tıklanınca panoya kopyalanır), R/G/B slider + sayısal input ikilisi, "Seç" butonu
- "Seç" tıklayınca popup kapanır, `+` butonunun arka planı seçilen renge döner
- Seçilen renk `<input type="hidden" class="cp-value">` alanına yazılır
- Popup dışına tıklayınca kapanır
- `initColorPicker(wrapEl, onChange)` factory fonksiyonu ile hem "Yeni Rota" formu hem "Düzenle" modalı aynı kodla yönetiliyor
- Vanilla JS, harici kütüphane yok

---

### 3. Rota API'si Workspace'e Göre Filtrelendi — `routes/views.py`

**Eski davranış:** `GET /api/routes/` tüm rotaları döndürüyordu, workspace ayrımı yoktu.

**Yeni davranış:**
- `GET /api/routes/?workspace=<uuid>` → sadece o workspace'e ait rotaları döndürür
- `PATCH/DELETE /api/routes/<id>/` → session'daki workspace_id üzerinden filtreler (güvenlik)
- Parametre verilmezse ve session yoksa boş liste döner

```python
def get_queryset(self):
    workspace_id = (
        self.request.query_params.get('workspace')
        or self.request.session.get('workspace_id')
    )
    if workspace_id:
        return Route.objects.filter(workspace_id=workspace_id)
    return Route.objects.none()
```

---

### 4. Rotalar Template'e Gömme Kaldırıldı — `routes/views.py` + `templates/routes/map.html`

**Eski davranış:** `map_view` rotaları `routes_json` olarak Django template'e gömüyor, sayfa her açılışta tüm rota verisini HTML içinde taşıyordu.

**Yeni davranış:**
- `map_view` sadece `workspace` nesnesini geçiyor
- Sayfa yüklenince JS tarafında `loadRoutes()` fonksiyonu çalışır
- `GET /api/routes/?workspace=<id>` çağrısı yapılır, dönen veri listeye render edilir
- Session sıfırlansa bile rotalar API'den taze çekilir

---

### 5. Edit Modal Django Blok Dışında Kalma Hatası Düzeltildi — `templates/routes/map.html`

**Sorun:** Edit modal HTML `{% endblock %}` kapandıktan sonra, herhangi bir Django template bloğu dışında kalıyordu. Django extends modunda blok dışı içerik render edilmez. Bu yüzden `getElementById('edit-modal')` null dönüyor, ilk `addEventListener` çağrısında script tamamen çöküyordu. `loadRoutes()` hiç çalışmıyordu.

**Çözüm:** Edit modal `{% block scripts %}` içine, `<script>` tagından önce taşındı.

---

### 6. Harita Üzerinde Marker İkonları Değiştirildi — `templates/routes/map.html`

**Eski davranış:** Tüm waypoint'ler (başlangıç, ara duraklar, bitiş) daire marker ile gösteriliyordu.

**Yeni davranış:**
- Sadece başlangıç ve bitiş noktaları gösterilir, ara duraklar kaldırıldı
- **Başlangıç:** Rotanın rengiyle dolu yuvarlak içinde `▶` oku (`DivIcon`)
- **Bitiş:** Rotanın rengiyle klasik konum iğnesi (tepe noktasına sabitlenmiş, `DivIcon`)

---

### 7. Tümünü Göster / Gizle Butonu Eklendi — `templates/routes/map.html`

- Rota listesi başlığında "Tümünü Göster" butonu eklendi
- Tıklayınca tüm rotalar haritaya çizilir, buton "Tümünü Gizle" olur
- Bireysel Göster/Gizle butonlarıyla oynandığında `syncToggleAllBtn()` ile başlık butonu güncellenir

---

### 8. Rota Listesi Açılır/Kapanır Yapıya Geçirildi — `templates/routes/map.html`

- "Rotalar" başlığına tıklanınca liste kapanıp açılıyor
- Ok ikonu (`▼`) yön değiştiriyor
- "Tümünü Göster" butonu başlık satırında kalıyor, listeyi kapatmadan çalışmaya devam ediyor (`event.stopPropagation()`)

---

### 9. RouteGroup + Route Modeli Yapısına Geçiş

**Eski yapı:** `Route` modeli doğrudan `workspace` FK'sı taşıyordu. Yön (inbound/outbound) ayrımı yoktu.

**Yeni yapı:**
- `RouteGroup` modeli eklendi: her grup bir workspace'e bağlı, isim alanı var
- `Route` modeli `RouteGroup`'a FK ile bağlandı (`route_group`), `workspace` FK kaldırıldı
- `Route.direction` alanı eklendi: `inbound` (İş Yerine Geliş) / `outbound` (İş Yerinden Çıkış)
- Veri migrasyonu: mevcut 13 rota için birer RouteGroup oluşturuldu, yön `outbound` atandı
- API: `GET /api/route-groups/?workspace=<uuid>` → grup + rotaları iç içe döndürür

**Değişen dosyalar:** `routes/models.py`, `routes/migrations/0003_routegroup.py`, `routes/serializers.py`, `routes/views.py`, `routes/urls.py`

---

### 10. Harita Arayüzü Tam Yeniden Yazıldı — `templates/routes/map.html`

**Eski yapı:** Tek düzey rota listesi, her rota bir kart.

**Yeni yapı:**
- Sol panel: `RouteGroup` kartları, her kart iki satır içerir (İş Yerine Geliş / İş Yerinden Çıkış)
- Her direction satırı: rota varsa ad + düzenle/sil butonları; yoksa "Link Ekle" butonu
- "Link Ekle" → Google Maps URL'si girilerek ORS üzerinden rota çizilir ve kaydedilir
- Modal `openLinkModal(groupId, direction)` hem ekleme hem düzenleme için kullanılır
- Haritada marker: `wps[0]` → ▶ kalkış dairesi, `wps[last]` → 📍 varış iğnesi (URL sırası esas alınır)

---

### 11. Google Maps URL Parser Sıralama Hatası Düzeltildi — `routes/services.py`

**Sorun:** İsimli yer (named place) segmentleri için `data=` parametresindeki koordinatlar toplu olarak başa ekleniyordu. Bu nedenle URL'de sonda gelen iş yeri, `wps[0]`'a düşüyor ve haritada kalkış noktasında görünüyordu.

**Çözüm:** Path segmentleri sırayla geziIir; her isimli segmentle karşılaşılınca `data=` sırasındaki bir sonraki koordinat tüketilir. URL sırası korunur.

---

### 12. PATCH route_group_id Hatası Düzeltildi — `routes/serializers.py`

`route_group_id` alanındaki `required=True` kaldırılarak `required=False` yapıldı. Artık renk-sadece PATCH istekleri `route_group_id` göndermeden çalışır.

---

### 16. Çalışan Verisi İçe Aktarıldı — `Docs/Birey_Listesi.xlsx`

- `Docs/Birey_Listesi.xlsx` dosyasındaki kişi kodu ve adres aynı hücrede birleşik geldi (`W2AM, Yenimahalle, ...` formatı)
- İlk virgüle göre ayrıştırılarak kişi kodu A sütununa, adres B sütununa yazıldı (596 satır)
- `python manage.py import_employees --file Docs/Birey_Listesi.xlsx` komutuyla Yandex API üzerinden geocode edildi
- **567 kayıt** `geocode_status=ok` (koordinatlı, haritada görünür)
- **29 kayıt** `geocode_status=failed` (koordinat alınamadı — adres hatalı/eksik olabilir)
- Sonuçlar `Docs/geocode_results.xlsx` dosyasına yazıldı
- **Not:** Adresler şimdilik doğru kabul ediliyor; hatalı adresler ilerleyen aşamada gözden geçirilecek

---

### 13. Marker Renk Güncelleme Hatası Düzeltildi — `templates/routes/map.html`

Renk düzenleme modalında sadece polyline güncelleniyordu, ▶ ve 📍 markerlar eski renkte kalıyordu. `polyline.setStyle()` yerine `hideRoute` + `drawRoute` çağrısı yapılarak tüm rota yeniden çizilir; marker renkleri de güncellenir.

---

### 14. Harita Açık/Koyu Mod Toggleı Eklendi — `templates/routes/map.html`

- Default: CartoDB Light (beyaz harita)
- Sağ alt köşede 🌙 butonu — tıklayınca CartoDB Dark'a geçer, buton ☀️ olur
- Tekrar tıklayınca açık moda döner
- Tile layer runtime'da swap edilir, sayfa yenilenmez

---

### 15. Kod Temizliği — `routes/views.py`, `routes/services.py`, `templates/routes/map.html`

- **`routes/services.py`** — `_COORD_RE` modül seviyesine taşındı, her çağrıda yeniden derlenmiyor
- **`routes/views.py`** — `_valid_uuid()` helper eklendi, iki ViewSet'teki tekrarlı UUID kodu kaldırıldı; `serializer.save()` gereksiz `route_group` argümanı silindi
- **`templates/routes/map.html`** — `makeCollapsible(toggleId, bodyId)` ile iki IIFE birleştirildi; `openLinkModal(groupId, direction, isEdit)` ile iki ayrı modal fonksiyonu tek oldu; `deleteResource(url, msg, onSuccess)` helper ile `deleteGroup`/`deleteRouteDir` ortak mantığı ayrıştırıldı

---

---

## Bekleyen Görevler

- [ ] **Hatalı adresleri düzelt:** 29 çalışanın geocode işlemi başarısız oldu (`geocode_status=failed`). `Docs/geocode_results.xlsx` dosyasında `STATUS=failed` olan satırları incele, adresleri düzelterek `import_employees` komutunu tekrar çalıştır. Başarısız olan kayıtlar: A44PM, E56PM, I62UB, Q87JM, M111VM, D159ZM, M164CM, L168MB, T180VB, P183CM, Z200QM, G333IM, J339OB, A340GM, O346KM, K359QB, E374EM, S453MB, J466NB, G478SM, F484GM, I269MM, Z305VM, T240BM, H568VM, S577ZM, X512HB, K508MB, U594UB

---

## Mevcut Durum

| Özellik | Durum |
|---|---|
| Workspace seçimi | ✅ Çalışıyor |
| RouteGroup listeleme | ✅ Çalışıyor |
| Rota ekleme (Google Maps URL + ORS) | ✅ Çalışıyor |
| Rota düzenleme (isim, renk) | ✅ Çalışıyor |
| Rota silme | ✅ Çalışıyor |
| Yön (inbound/outbound) ayrımı | ✅ Çalışıyor |
| Haritada kalkış/varış ikonları (URL sırası) | ✅ Çalışıyor |
| Marker renk güncellemesi | ✅ Çalışıyor |
| Harita açık/koyu mod | ✅ Çalışıyor |
| Özel renk seçici | ✅ Çalışıyor |
| Çalışan içe aktarma (Yandex geocode) | ✅ Çalışıyor (567/596 başarılı) |
| Çalışan haritada gösterme | ✅ Çalışıyor |
| Hatalı adres düzeltme (29 kayıt) | ⚠️ Bekliyor |
| Çalışan yönetimi (UI) | ⏳ Geliştirilmedi |
| Araç yönetimi | ⏳ Geliştirilmedi |
| Rota optimizasyonu | ⏳ Geliştirilmedi |
