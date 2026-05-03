# Proje Mimarisi — Staff Shuttle Optimization

**Backend:** Django 6 + DRF · **DB:** PostgreSQL (Supabase) · **Frontend:** Vanilla JS + Leaflet.js  
**Dış API'ler:** Yandex Geocoding · Mapbox Directions · OpenRouteService (ORS)

---

## Dosya Haritası

| Dosya | Sorumluluk |
|-------|------------|
| `core/settings.py` | Django ayarları; DB, env değişkenleri (ORS_API_KEY, YANDEX_API_KEY, MAPBOX_API_KEY) |
| `core/urls.py` | Root URL router — `/`, `/map/<uuid>/`, `/api/` |
| **workspaces/models.py** | `Workspace` modeli (UUID PK, name, is_active, M2M → Employee) |
| `workspaces/views.py` | `workspace_select()` (template view) + `WorkspaceViewSet` (CRUD API) |
| `workspaces/serializers.py` | `WorkspaceSerializer` |
| **employees/models.py** | `Employee` modeli (personnel_code, address, lat/lng, geocode_status) |
| `employees/views.py` | `EmployeeViewSet` + custom actions: `update_location`, `geocode`, `assign`, `import_row`, `parse_excel` |
| `employees/serializers.py` | `EmployeeSerializer` (read, `address_score` hesaplanır) · `EmployeeCreateSerializer` (write) |
| **`employees/utils.py`** | `geocode_address()` — Yandex API çağrısı · `address_match_score()` — token + string benzerlik skoru |
| `templates/employees/manage.html` | Çalışan yönetim UI — tablo, Excel import (async per-row), konum düzenleme, tümünü sil |
| `employees/management/commands/import_employees.py` | Excel'den toplu import + Yandex geocoding → `Docs/geocode_results.xlsx` |
| **routes/models.py** | `RouteGroup` (workspace FK) · `Route` (route_group FK, geojson, waypoints) · `Stop` (route FK, isochrone cache) |
| `routes/views.py` | `RouteGroupViewSet` · `RouteViewSet` · `StopViewSet` + custom actions |
| `routes/serializers.py` | `StopSerializer` · `RouteSerializer` (nested stops) · `RouteGroupSerializer` (nested routes) |
| **`routes/services.py`** | Tüm dış API çağrıları (Mapbox, ORS isochrone, ORS matrix, Google Maps parse) |
| `templates/workspaces/select.html` | Workspace seçim/oluşturma sayfası |
| **`templates/routes/map.html`** | Ana UI (2400+ satır) — sidebar, harita, tüm modaller, JS iş mantığı |

---

## Model İlişkileri

```
Workspace
├── employees (M2M) ──────────────── Employee
│                                    (personnel_code, lat, lng, geocode_status)
│
└── RouteGroup (FK: workspace)
    └── Route (FK: route_group)
        ├── waypoints (JSON: [{lat, lng}])
        ├── geojson (Mapbox'tan gelen GeoJSON)
        └── Stop (FK: route)
            └── isochrone (ORS'tan gelen GeoJSON polygon, DB'de cache'li)
```

**Önemli:** `Route` modelinde `workspace` FK **yoktur**. Workspace filtresi `RouteGroup.workspace` üzerinden gelir.  
→ Route sorgularında `?workspace={uuid}` → view içinde `RouteGroup.objects.filter(workspace=...)` ile çözülür.

---

## API Endpoint Tablosu

### Workspace
| Method | URL | View | Not |
|--------|-----|------|-----|
| GET/POST | `/api/workspaces/` | `WorkspaceViewSet` | Liste + oluştur |
| GET/PATCH/DELETE | `/api/workspaces/{id}/` | `WorkspaceViewSet` | Tek kayıt |

### RouteGroup
| Method | URL | View | Not |
|--------|-----|------|-----|
| GET | `/api/route-groups/?workspace={uuid}` | `RouteGroupViewSet.list` | Nested routes ile |
| POST | `/api/route-groups/` | `RouteGroupViewSet.create` | — |
| PATCH/DELETE | `/api/route-groups/{id}/` | `RouteGroupViewSet` | — |
| **POST** | `/api/route-groups/assign-all/` | `RouteGroupViewSet.assign_all` | 3-aşamalı employee atama |

### Route
| Method | URL | View | Servis Çağrısı |
|--------|-----|------|----------------|
| GET | `/api/routes/?workspace={uuid}` | `RouteViewSet.list` | — |
| POST | `/api/routes/` | `RouteViewSet.create` | — |
| PATCH/DELETE | `/api/routes/{id}/` | `RouteViewSet` | — |
| **POST** | `/api/routes/parse-google-maps/` | `RouteViewSet.parse_google_maps` | `parse_google_maps_url()` + `get_route_from_mapbox()` |
| **GET** | `/api/routes/{id}/assign-stops/` | `RouteViewSet.assign_stops` | `get_isochrone_from_ors()` + `get_walking_matrix_from_ors()` |

### Stop
| Method | URL | View | Servis Çağrısı |
|--------|-----|------|----------------|
| GET/POST | `/api/stops/` | `StopViewSet` | — |
| PATCH/DELETE | `/api/stops/{id}/` | `StopViewSet` | — |
| **GET** | `/api/stops/{id}/nearby-employees/` | `StopViewSet.nearby_employees` | Shapely point-in-polygon |

### Employee
| Method | URL | View | Servis Çağrısı |
|--------|-----|------|----------------|
| GET | `/api/employees/?all=1` | `EmployeeViewSet.list` | Tüm çalışanlar (`address_score` dahil) |
| GET | `/api/employees/?workspace={uuid}` | `EmployeeViewSet.list` | Workspace'e atanmış, sadece `geocode_status=ok` |
| POST | `/api/employees/` | `EmployeeViewSet.create` | — |
| PATCH | `/api/employees/{id}/` | `EmployeeViewSet` | — |
| DELETE | `/api/employees/{id}/` | `EmployeeViewSet` | — |
| **PATCH** | `/api/employees/{id}/update-location/` | `EmployeeViewSet.update_location` | Coords güncelle, API çağrısı yok |
| **POST** | `/api/employees/geocode/` | `EmployeeViewSet.geocode` | `geocode_address()` (Yandex), kaydetmez |
| **POST** | `/api/employees/assign/` | `EmployeeViewSet.assign` | Workspace M2M güncelle |
| **POST** | `/api/employees/parse-excel/` | `EmployeeViewSet.parse_excel` | Excel'i oku, çakışmaları tespit et |
| **POST** | `/api/employees/import-row/` | `EmployeeViewSet.import_row` | Tek satır geocode + kaydet; `{status, api_address}` döner |

### Template Views
| URL | View | Template |
|-----|------|----------|
| `/` | `workspace_select()` | `workspaces/select.html` |
| `/employees/` | `manage_view()` | `employees/manage.html` |
| `/map/{uuid}/` | `map_view()` | `routes/map.html` |

---

## Template → API Bağlantıları (employees/manage.html)

| JS Fonksiyonu | Çağırdığı Endpoint | Ne Zaman |
|---------------|--------------------|----------|
| `loadEmployees()` | GET `/api/employees/?all=1` | Sayfa yüklenince, her import adımından sonra |
| `import-start` → `parse_excel` | POST `/api/employees/parse-excel/` | Dosya seçilip "İçe Aktar" tıklanınca |
| `runImport(rows)` → her satır | POST `/api/employees/import-row/` | Async for-loop, 180ms aralıkla |
| `openEditModal` → adres tab | POST `/api/employees/geocode/` + PATCH `update-location` | Konum önizle + kaydet |
| `openEditModal` → coords/drag tab | PATCH `/api/employees/{id}/update-location/` | Koordinat/sürükle kaydet |
| `deleteAllEmployees()` | DELETE `/api/employees/{id}/` (her biri) | "Tümünü Sil" onaylanınca |

---

## Template → API Bağlantıları (map.html)

| JS Fonksiyonu | Çağırdığı Endpoint | Ne Zaman |
|---------------|--------------------|----------|
| `loadRoutes()` | GET `/api/route-groups/?workspace=` | Sayfa yüklenince |
| `loadEmployees()` | GET `/api/employees/?workspace=` | Sayfa yüklenince |
| `openLinkModal()` → save | POST `/api/routes/parse-google-maps/` sonra POST `/api/routes/` | Yeni route ekle |
| `openLinkModal(isEdit=true)` → save | PATCH `/api/routes/{id}/` | Route düzenle |
| `assignAll()` | POST `/api/route-groups/assign-all/` | "Hesapla Tümü" butonu |
| `assignStops(routeId)` | GET `/api/routes/{id}/assign-stops/` | "Hesapla" butonu (tek route) |
| `deleteResource(url)` | DELETE `{url}` | Route/Group/Stop sil |
| `saveEmployeeLocation()` tab1 | POST `/api/employees/geocode/` → PATCH `/api/employees/{id}/update-location/` | Adres tab |
| `saveEmployeeLocation()` tab2 | PATCH `/api/employees/{id}/update-location/` | Manuel coords tab |
| `saveEmployeeLocation()` tab3 | PATCH `/api/employees/{id}/update-location/` | Drag marker tab |
| Employee modal → assign | POST `/api/employees/assign/` | Workspace'e employee ata |
| Stop marker click → nearby | GET `/api/stops/{id}/nearby-employees/` | Stop'a tıkla |

---

## Dış API Referansı

| API | Anahtar | Nerede Çağrılır | Ne İçin |
|-----|---------|-----------------|---------|
| **Yandex Geocoding** | `YANDEX_API_KEY` | `employees/utils.py → geocode_address()` | Adres → koordinat |
| **Mapbox Directions** | `MAPBOX_API_KEY` | `routes/services.py → get_route_from_mapbox()` | Waypoints → route GeoJSON + mesafe/süre |
| **ORS Isochrones** | `ORS_API_KEY` | `routes/services.py → get_isochrone_from_ors()` | Stop → yürüme mesafesi polygon (15 dk) |
| **ORS Matrix** | `ORS_API_KEY` | `routes/services.py → get_walking_matrix_from_ors()` | Employee ↔ Stop yürüme süreleri matrisi |

---

## Temel Akışlar

### Route Ekle
1. User: Google Maps `/dir/` URL'ini modal'a yapıştırır
2. JS → POST `/api/routes/parse-google-maps/`
3. View → `parse_google_maps_url(url)` → waypoints listesi
4. View → `get_route_from_mapbox(waypoints)` → GeoJSON + distance + duration
5. Response: preview gösterilir
6. User "Kaydet" → POST `/api/routes/` → DB'ye yaz
7. JS → `drawRoute(r)` → Leaflet polyline + start/end marker + stop marker'lar

### Employee Workspace'e Atama
1. Employee modal açılır → GET `/api/employees/?workspace=` (mevcut)
2. User seçer → POST `/api/employees/assign/` → `{employee_ids: [...], workspace_id: ...}`
3. View → `workspace.employees.set(employees)` (M2M güncelle)

### Assign-All (3-Aşamalı Algoritma)
1. POST `/api/route-groups/assign-all/?workspace={uuid}`
2. **Aşama 1:** Her Stop için ORS isochrone çek (cache'de varsa kullan, `Stop.isochrone`)
3. **Aşama 2:** Shapely `point_in_polygon` → her employee hangi stop'lara düşüyor?
4. **Aşama 3:** Birden fazla stop'a düşen employee'ler için ORS Matrix API → en yakın stop seç (fallback: Haversine)
5. Response: `{routes: [{stops: [{employees: [...], count: N}]}]}`
6. JS → Stop kartlarına `👥 N` badge ekler + isochrone polygon'ları haritaya çizer

### Yeni Özellik Eklerken Kontrol Listesi
- **Yeni model alanı** → `routes/models.py` veya `employees/models.py` + migration
- **Yeni endpoint** → ilgili `views.py` + `urls.py`'de router'a ekle (varsa `routes.py`)
- **Yeni dış API çağrısı** → `routes/services.py` veya `employees/utils.py`
- **UI değişikliği** → `templates/routes/map.html` (sidebar, modal, JS fonksiyonu)
- **Serializer alanı** → `routes/serializers.py` veya `employees/serializers.py`

---

## Klasör Yapısı (Özet)

```
staff-shuttle-optimization/
├── core/               # Django proje ayarları (settings, urls)
├── workspaces/         # Workspace app
├── employees/          # Employee app + utils (geocode) + import komutları
├── routes/             # Route/Stop app + services.py (dış API'ler)
├── vehicles/           # Henüz boş
├── templates/
│   ├── base.html
│   ├── workspaces/select.html
│   ├── employees/manage.html   ← Çalışan yönetim UI
│   └── routes/map.html         ← Harita + rota UI
├── Docs/               # Excel çıktıları, geocode analiz
├── requirements.txt
├── STATUS.md           # Değişiklik günlüğü (Türkçe)
└── ARCHITECTURE.md     ← Bu dosya
```
