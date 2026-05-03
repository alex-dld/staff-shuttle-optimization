
# Çalışan Yönetim Paneli Proje Planı

**Proje Hedefi:** Kayıtlı çalışanların listelenebildiği, adres ve koordinatlarının (elle, haritadan veya metin olarak) güncellenebildiği ve Excel'den yeni kullanıcı eklenebilen bir yönetim paneli oluşturmak.

Dosya haritasına göre, bu çalışan yönetim panelini oluşturmak için ihtiyaç duyulan altyapının (API'ler, servisler) neredeyse tamamı zaten hazır durumdadır. Mevcut sistemde çalışan konumlarını güncellemek için üç farklı yöntemi destekleyen `update-location` ve `geocode` uç noktaları (endpoints) bulunmaktadır. Yeni paneli bu altyapı üzerine inşa etmek için aşağıdaki yol haritası izlenebilir:

## Aşama 1: Backend Hazırlıkları (Eksikleri Tamamlama)

API tablosuna göre adres ve koordinat güncellemeleri için gerekli uç noktalar mevcuttur ancak Excel yükleme işlemi için sisteme ekleme yapılması gerekmektedir.

* **Excel Import API'si:** Şu anda Excel'den çalışan verisi aktarımı `employees/management/commands/import_employees.py` komutu ile terminal üzerinden yapılmaktadır.
* **Yeni Uç Nokta:** Frontend'den dosya yükleyebilmek için `EmployeeViewSet` içerisine `@action(detail=False, methods=['post'])` dekoratörü ile yeni bir `import_excel` fonksiyonu yazılmalıdır.
* **İşlev:** Bu uç nokta, yüklenen dosyayı alıp mevcut komuttaki okuma ve Yandex ile geocoding yapma mantığını çalıştırarak veritabanına kaydetmelidir.

---

## Aşama 2: Yeni Şablon ve Yönlendirme (Routing)

* **Yeni Sayfa (View & Template):** Çalışan yönetim paneli için `templates/employees/manage.html` adında yeni bir şablon oluşturulmalıdır.
* **URL Tanımı:** `core/urls.py` veya `employees/urls.py` içerisine bu şablonu render edecek (Örn: `/workspaces/<uuid>/employees/`) yeni bir yol eklenmelidir.

---

## Aşama 3: Frontend ve Kullanıcı Arayüzü (UI)

Arayüz temel olarak bir tablo ve işlem modallarından oluşacaktır. Projede Vanilla JS kullanıldığı için bu işlemler API istekleriyle (fetch) yönetilmelidir.

* **Çalışan Tablosu (Data Table):** Sayfa yüklendiğinde, `GET /api/employees/?workspace={uuid}` uç noktasına istek atılarak ilgili çalışma alanındaki personeller çekilmelidir.
* **Tablo Yapısı:** İsim, Sicil No (personnel_code), Adres ve Geocode Durumu kolonlarından oluşan bir tablo kurulmalı ve her satırın sonuna "Düzenle" butonu eklenmelidir.
* **Excel Yükleme Modalı:** İçerisinde dosya seçimi barındıran basit bir modal hazırlanmalı ve kullanıcı "Yükle" dediğinde `FormData` oluşturularak `import_excel` uç noktasına POST isteği atılmalıdır.
* **Konum Düzenleme Modalı:** `map.html` dosyasında kullanılan ve `saveEmployeeLocation()` fonksiyonuna bağlanan üç sekmeli mantık burada da kullanılmalıdır.
* **Adres Metni Girerek (Sekme 1):** Kullanıcının girdiği adres metni için `POST /api/employees/geocode/` uç noktasına istek atılarak Yandex üzerinden koordinatlar alınmalı ve `PATCH /api/employees/{id}/update-location/` ile kaydedilmelidir.
* **Manuel Koordinat Girerek (Sekme 2):** Kullanıcının direkt olarak girdiği Enlem (Lat) ve Boylam (Lng) verileri ile doğrudan `update-location` uç noktasına PATCH isteği atılmalıdır.
* **Haritadan Sürükle-Bırak (Sekme 3):** Modal içerisine entegre edilecek küçük Leaflet.js haritasında çalışanın mevcut koordinatlarına işaretçi (marker) konulmalı ve `draggable: true` özelliği açılmalıdır. Sürükleme işlemi sonrasında (dragend) yeni koordinatlar alınıp `update-location` uç noktasına PATCH isteği atılmalıdır.

---

## Aşama 4: Entegrasyon ve Test

* **UI Güncellemesi:** Adres değişikliklerinden sonra `geocode_status` verisi değişen personellerin tabloda dinamik olarak güncellendiği (başarılı olanlara yeşil tik eklenmesi vb.) doğrulanmalıdır.
* **Sistem Testi:** Yapılan adres değişikliklerinin `map.html` tarafındaki rotaları ve durak hesaplamalarını (ORS Matrix vb.) doğrudan etkileyeceği göz önünde bulundurularak gerekli testler yapılmalıdır.