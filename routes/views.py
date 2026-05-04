from django.conf import settings
from django.db import DatabaseError
from django.shortcuts import render, redirect
from uuid import UUID
from shapely.geometry import shape, Point
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from employees.models import Employee
from workspaces.models import Workspace
from .models import RouteGroup, Route, Stop
from .serializers import RouteGroupSerializer, RouteSerializer, StopSerializer
from .services import parse_google_maps_url, get_route_from_mapbox, get_isochrone_from_ors, get_walking_matrix_from_ors


def _valid_uuid(value):
    try:
        UUID(str(value))
        return True
    except (TypeError, ValueError):
        return False


def map_view(request, workspace_id):
    try:
        workspace = Workspace.objects.get(id=workspace_id)
    except Workspace.DoesNotExist:
        return redirect('/')

    return render(request, 'routes/map.html', {'workspace': workspace})


class RouteGroupViewSet(viewsets.ModelViewSet):
    queryset = RouteGroup.objects.all()
    serializer_class = RouteGroupSerializer

    def get_queryset(self):
        if self.action in ('retrieve', 'update', 'partial_update', 'destroy'):
            return RouteGroup.objects.all()
        workspace_id = self.request.query_params.get('workspace')
        if not workspace_id or not _valid_uuid(workspace_id):
            return RouteGroup.objects.none()
        return RouteGroup.objects.filter(workspace_id=workspace_id).prefetch_related('routes')

    def perform_create(self, serializer):
        workspace_id = self.request.data.get('workspace')
        if not workspace_id:
            raise ValidationError({'workspace': 'workspace is required'})
        try:
            workspace_uuid = UUID(str(workspace_id))
        except (TypeError, ValueError) as exc:
            raise ValidationError({'workspace': 'workspace must be a valid UUID'}) from exc
        try:
            workspace = Workspace.objects.get(id=workspace_uuid)
        except Workspace.DoesNotExist as exc:
            raise ValidationError({'workspace': 'workspace not found'}) from exc
        serializer.save(workspace=workspace)

    def list(self, request, *args, **kwargs):
        try:
            return super().list(request, *args, **kwargs)
        except DatabaseError as exc:
            return Response(
                {'error': f'route_groups query failed: {exc}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=['post'], url_path='assign-all')
    def assign_all(self, request):
        import time
        try:
            workspace_id = request.data.get('workspace')
            if not workspace_id or not _valid_uuid(workspace_id):
                return Response({'error': 'workspace gerekli'}, status=status.HTTP_400_BAD_REQUEST)
            try:
                workspace = Workspace.objects.get(id=workspace_id)
            except Workspace.DoesNotExist:
                return Response({'error': 'workspace bulunamadı'}, status=status.HTTP_400_BAD_REQUEST)

            all_stops = list(Stop.objects.filter(
                route__route_group__workspace=workspace
            ).select_related('route').order_by('route_id', 'sort_order'))
            if not all_stops:
                return Response({'error': 'Hiç durak yok.'}, status=status.HTTP_400_BAD_REQUEST)

            employees = list(workspace.employees.all())
            if not employees:
                return Response({'error': 'Çalışan yok.'}, status=status.HTTP_400_BAD_REQUEST)

            # Phase 1: tüm durakların izokronlarını önceden cache'le
            for stop in all_stops:
                if not stop.isochrone:
                    if not settings.ORS_API_KEY:
                        return Response({'error': 'ORS_API_KEY sunucuda tanımlı değil.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                    for attempt in range(5):
                        try:
                            stop.isochrone = get_isochrone_from_ors(stop.latitude, stop.longitude, 1200, settings.ORS_API_KEY)
                            stop.save(update_fields=['isochrone'])
                            time.sleep(2)
                            break
                        except Exception as exc:
                            if '429' in str(exc) and attempt < 4:
                                time.sleep(10 * (2 ** attempt))  # 10s, 20s, 40s, 80s
                            else:
                                return Response({'error': f'İzokron hatası ({stop.name}): {exc}'}, status=status.HTTP_502_BAD_GATEWAY)

            stop_polygons = []
            for stop in all_stops:
                try:
                    if not stop.isochrone or 'features' not in stop.isochrone:
                         raise ValueError("Geçersiz izokron verisi")
                    stop_polygons.append(shape(stop.isochrone['features'][0]['geometry']))
                except Exception as exc:
                    return Response({'error': f'İzokron geometri hatası ({stop.name}): {exc}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Phase 2: Shapely — tüm rotaların durakları aynı havuzda, her çalışan en yakın durağa
            assignments = {stop.id: [] for stop in all_stops}
            unreachable = []
            ambiguous = []
            shapely_zero = 0  # hiçbir izokrona giremeyen

            for emp in employees:
                if emp.lat is None or emp.lng is None:
                    shapely_zero += 1
                    unreachable.append(emp)
                    continue
                pt = Point(emp.lng, emp.lat)
                candidates = [i for i, poly in enumerate(stop_polygons) if poly.contains(pt)]
                if len(candidates) == 0:
                    shapely_zero += 1
                    unreachable.append(emp)
                elif len(candidates) == 1:
                    assignments[all_stops[candidates[0]].id].append(emp)
                else:
                    ambiguous.append((emp, candidates))

            # Phase 3: Haversine — birden fazla izokrona giren çalışanlar için en yakın durak
            if ambiguous:
                import math

                def _haversine(lat1, lng1, lat2, lng2):
                    R = 6371000
                    p1, p2 = math.radians(lat1), math.radians(lat2)
                    dp = math.radians(lat2 - lat1)
                    dl = math.radians(lng2 - lng1)
                    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
                    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

                for emp, candidates in ambiguous:
                    best_i = min(candidates, key=lambda i: _haversine(
                        emp.lat, emp.lng, all_stops[i].latitude, all_stops[i].longitude
                    ))
                    assignments[all_stops[best_i].id].append(emp)

            # Sonuçları rota bazında grupla
            route_results: dict = {}
            for stop in all_stops:
                rid = str(stop.route_id)
                if rid not in route_results:
                    route_results[rid] = {'stops': []}
                route_results[rid]['stops'].append({
                    'stop_id': str(stop.id), 'stop_name': stop.name, 'sort_order': stop.sort_order,
                    'employee_count': len(assignments[stop.id]), 'isochrone': stop.isochrone,
                    'employees': [{'personnel_code': e.personnel_code, 'lat': e.lat, 'lng': e.lng,
                                   'address': e.api_address or e.address}
                                  for e in assignments[stop.id]],
                })

            return Response({
                'routes': [{'route_id': rid, **d} for rid, d in route_results.items()],
                'unreachable': [{'personnel_code': e.personnel_code, 'lat': e.lat, 'lng': e.lng,
                                 'address': e.api_address or e.address} for e in unreachable],
                'total_assigned': len(employees) - len(unreachable),
                'total_unreachable': len(unreachable),
                'total_employees': len(employees),
                '_debug': {
                    'stop_count': len(all_stops),
                    'shapely_zero': shapely_zero,
                    'ambiguous': len(ambiguous),
                    'direct': len(employees) - shapely_zero - len(ambiguous),
                },
            })
        except Exception as e:
            return Response({'error': f'Sunucu hatası: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RouteViewSet(viewsets.ModelViewSet):
    queryset = Route.objects.all()
    serializer_class = RouteSerializer

    def get_queryset(self):
        if self.action in ('retrieve', 'update', 'partial_update', 'destroy', 'assign_stops'):
            return Route.objects.all()
        workspace_id = self.request.query_params.get('workspace')
        if workspace_id and _valid_uuid(workspace_id):
            return Route.objects.filter(route_group__workspace_id=workspace_id)
        return Route.objects.none()

    def perform_create(self, serializer):
        route_group = serializer.validated_data.get('route_group')
        if not route_group:
            raise ValidationError({'route_group_id': 'route_group_id is required'})
        workspace_id = self.request.data.get('workspace')
        if workspace_id and str(route_group.workspace_id) != str(workspace_id):
            raise ValidationError({'route_group_id': 'route_group does not belong to this workspace'})
        serializer.save()

    @action(detail=True, methods=['get'], url_path='assign-stops')
    def assign_stops(self, request, pk=None):  # noqa: ARG002
        route = self.get_object()
        stops = list(route.stops.all())
        if not stops:
            return Response({'error': 'Bu rotada durak yok.'}, status=status.HTTP_400_BAD_REQUEST)

        workspace = route.route_group.workspace
        employees = list(workspace.employees.all())
        if not employees:
            return Response({'error': 'Workspace\'te çalışan yok.'}, status=status.HTTP_400_BAD_REQUEST)

        # Phase 1: ensure all stops have an isochrone cached
        import time
        for stop in stops:
            if not stop.isochrone:
                for attempt in range(5):
                    try:
                        stop.isochrone = get_isochrone_from_ors(stop.latitude, stop.longitude, 1200, settings.ORS_API_KEY)
                        stop.save(update_fields=['isochrone'])
                        time.sleep(2)
                        break
                    except Exception as exc:
                        if '429' in str(exc) and attempt < 4:
                            time.sleep(10 * (2 ** attempt))  # 10s, 20s, 40s, 80s
                        else:
                            return Response({'error': f'İzokron hatası ({stop.name}): {exc}'}, status=status.HTTP_502_BAD_GATEWAY)

        stop_polygons = []
        for stop in stops:
            try:
                stop_polygons.append(shape(stop.isochrone['features'][0]['geometry']))
            except Exception as exc:
                return Response({'error': f'İzokron geometri hatası ({stop.name}): {exc}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Phase 2: Shapely filter — find candidate stops per employee
        assignments = {stop.id: [] for stop in stops}
        unreachable = []
        ambiguous = []  # (employee, [stop_indices])

        for emp in employees:
            if emp.lat is None or emp.lng is None:
                unreachable.append(emp)
                continue
            pt = Point(emp.lng, emp.lat)
            candidates = [i for i, poly in enumerate(stop_polygons) if poly.contains(pt)]
            if len(candidates) == 0:
                unreachable.append(emp)
            elif len(candidates) == 1:
                assignments[stops[candidates[0]].id].append(emp)
            else:
                ambiguous.append((emp, candidates))

        # Phase 3: ORS Matrix for ambiguous employees
        if ambiguous:
            # Collect unique stop indices involved
            involved_stop_indices = sorted({i for _, cands in ambiguous for i in cands})
            emp_list = [e for e, _ in ambiguous]

            # Build combined locations: employees first, then stops
            locations = [[e.lng, e.lat] for e in emp_list] + \
                        [[stops[i].longitude, stops[i].latitude] for i in involved_stop_indices]
            src_indices = list(range(len(emp_list)))
            dst_indices = list(range(len(emp_list), len(locations)))

            # Batch if > 50 locations (ORS free tier limit)
            BATCH = 50
            # duration_matrix[emp_idx][dst_idx] — accumulated across batches
            duration_matrix = [[None] * len(involved_stop_indices) for _ in emp_list]

            if len(locations) <= BATCH:
                try:
                    rows = get_walking_matrix_from_ors(locations, src_indices, dst_indices, settings.ORS_API_KEY)
                    for ei, row in enumerate(rows):
                        for di, dur in enumerate(row):
                            duration_matrix[ei][di] = dur
                except Exception as exc:
                    return Response({'error': f'ORS Matrix hatası: {exc}'}, status=status.HTTP_502_BAD_GATEWAY)
            else:
                # Batch employees to keep total locations ≤ BATCH
                max_emp_per_batch = BATCH - len(involved_stop_indices)
                for batch_start in range(0, len(emp_list), max_emp_per_batch):
                    batch_emps = emp_list[batch_start:batch_start + max_emp_per_batch]
                    batch_locs = [[e.lng, e.lat] for e in batch_emps] + \
                                 [[stops[i].longitude, stops[i].latitude] for i in involved_stop_indices]
                    batch_src = list(range(len(batch_emps)))
                    batch_dst = list(range(len(batch_emps), len(batch_locs)))
                    try:
                        rows = get_walking_matrix_from_ors(batch_locs, batch_src, batch_dst, settings.ORS_API_KEY)
                        for bi, row in enumerate(rows):
                            for di, dur in enumerate(row):
                                duration_matrix[batch_start + bi][di] = dur
                    except Exception as exc:
                        return Response({'error': f'ORS Matrix hatası: {exc}'}, status=status.HTTP_502_BAD_GATEWAY)

            # Assign each ambiguous employee to the nearest reachable stop
            for ei, (emp, candidates) in enumerate(ambiguous):
                best_stop_id = None
                best_dur = None
                for local_di, global_si in enumerate(involved_stop_indices):
                    if global_si not in candidates:
                        continue
                    dur = duration_matrix[ei][local_di]
                    if dur is None:
                        continue
                    if dur <= 900 and (best_dur is None or dur < best_dur):
                        best_dur = dur
                        best_stop_id = stops[global_si].id
                if best_stop_id:
                    assignments[best_stop_id].append(emp)
                else:
                    unreachable.append(emp)

        return Response({
            'route_id': str(route.id),
            'stops': [
                {
                    'stop_id': str(stop.id),
                    'stop_name': stop.name,
                    'sort_order': stop.sort_order,
                    'employee_count': len(assignments[stop.id]),
                    'isochrone': stop.isochrone,
                    'employees': [
                        {'personnel_code': e.personnel_code, 'lat': e.lat, 'lng': e.lng,
                         'address': e.api_address or e.address}
                        for e in assignments[stop.id]
                    ],
                }
                for stop in stops
            ],
            'unreachable_count': len(unreachable),
            'unreachable': [
                {'personnel_code': e.personnel_code, 'lat': e.lat, 'lng': e.lng,
                 'address': e.api_address or e.address}
                for e in unreachable
            ],
        })

    @action(detail=False, methods=['post'], url_path='parse-google-maps')
    def parse_google_maps(self, request):
        url = request.data.get('url')
        if not url:
            return Response({'error': 'url field is required'}, status=status.HTTP_400_BAD_REQUEST)

        waypoints = parse_google_maps_url(url)

        if not waypoints:
            return Response(
                {'error': 'URL içinde koordinat bulunamadı.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            geojson = get_route_from_mapbox(waypoints, settings.MAPBOX_API_KEY)
        except Exception as exc:
            return Response({'error': f'Mapbox API error: {exc}'}, status=status.HTTP_502_BAD_GATEWAY)

        return Response({'waypoints': waypoints, 'geojson': geojson})



class StopViewSet(viewsets.ModelViewSet):
    serializer_class = StopSerializer

    def get_queryset(self):
        if self.action in ('retrieve', 'update', 'partial_update', 'destroy', 'nearby_employees'):
            return Stop.objects.all()
        route_id = self.request.query_params.get('route')
        if route_id:
            return Stop.objects.filter(route_id=route_id)
        return Stop.objects.none()

    def perform_create(self, serializer):
        route = serializer.validated_data['route']
        next_order = Stop.objects.filter(route=route).count() + 1
        serializer.save(sort_order=next_order)

    @action(detail=True, methods=['get'], url_path='nearby-employees')
    def nearby_employees(self, request, pk=None):  # noqa: ARG002
        stop = self.get_object()

        # Fetch or refresh isochrone
        meters = int(request.query_params.get('meters', 1200))
        if not stop.isochrone:
            try:
                stop.isochrone = get_isochrone_from_ors(
                    stop.latitude, stop.longitude, meters, settings.ORS_API_KEY
                )
                stop.save(update_fields=['isochrone'])
            except Exception as exc:
                return Response({'error': f'ORS API error: {exc}'}, status=status.HTTP_502_BAD_GATEWAY)

        # Build shapely polygon from isochrone GeoJSON
        try:
            feature = stop.isochrone['features'][0]
            polygon = shape(feature['geometry'])
        except (KeyError, IndexError, Exception) as exc:
            return Response({'error': f'Invalid isochrone geometry: {exc}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Find employees whose coordinates fall within the polygon
        nearby = []
        for emp in Employee.objects.filter(geocode_status='ok'):
            if polygon.contains(Point(emp.lng, emp.lat)):
                nearby.append({
                    'personnel_code': emp.personnel_code,
                    'lat': emp.lat,
                    'lng': emp.lng,
                    'address': emp.api_address or emp.address,
                })

        return Response({
            'stop_id': str(stop.id),
            'stop_name': stop.name,
            'meters': meters,
            'employee_count': len(nearby),
            'employees': nearby,
            'isochrone': stop.isochrone,
        })
