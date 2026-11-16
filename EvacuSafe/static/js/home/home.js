document.addEventListener('DOMContentLoaded', function () {
    const badge = document.getElementById('system-status-badge');
    if (badge) {
        function tick() {
            badge.title = 'Last checked: ' + new Date().toLocaleTimeString();
        }
        tick();
        setInterval(tick, 30000);
    }

    const mapElement = document.getElementById('evacuation-map');
    if (!mapElement) return;

    const statusElement = document.getElementById('map-status');
    const dataElement = document.getElementById('evacuation-centers-data');
    const searchInput = document.getElementById('center-search');
    const tableBody = document.getElementById('centers-table-body');
    const emptyState = document.getElementById('center-empty-state');
    const filterButtons = Array.from(document.querySelectorAll('[data-status-filter]'));
    if (!dataElement || !statusElement || !searchInput || !tableBody || !emptyState) return;

    if (!window.L) {
        statusElement.textContent = 'The map library could not be loaded. Check your internet connection and reload the page.';
        return;
    }

    const centers = JSON.parse(dataElement.textContent);
    const map = L.map(mapElement).setView([10.3157, 123.8854], 12);
    L.tileLayer(mapElement.dataset.tileUrl, {
        attribution: mapElement.dataset.tileAttribution,
        maxZoom: 19
    }).addTo(map);

    const markerById = new Map();
    centers.forEach(function (center) {
        if (center.latitude === null || center.longitude === null) return;
        const marker = L.circleMarker([center.latitude, center.longitude], {
            radius: markerRadius(center),
            color: '#f8fafc',
            weight: 2,
            fillColor: statusColor(center.status_key),
            fillOpacity: 0.95,
            className: 'center-marker ' + center.status_key
        }).addTo(map);
        marker.bindPopup(createCenterPopup(center));
        markerById.set(String(center.id), marker);
    });

    const mappedMarkers = Array.from(markerById.values());
    if (mappedMarkers.length > 1) {
        map.fitBounds(L.featureGroup(mappedMarkers).getBounds().pad(0.2));
    } else if (mappedMarkers.length === 1) {
        map.setView(mappedMarkers[0].getLatLng(), 14);
    }

    let selectedStatus = 'all';
    function applyFilters() {
        const query = searchInput.value.trim().toLocaleLowerCase();
        let visibleCount = 0;

        Array.from(tableBody.rows).forEach(function (row) {
            const matchesStatus = selectedStatus === 'all' || row.dataset.status === selectedStatus;
            const matchesQuery = !query ||
                row.dataset.name.includes(query) ||
                row.dataset.location.includes(query);
            const visible = matchesStatus && matchesQuery;
            row.hidden = !visible;
            if (visible) visibleCount += 1;

            const marker = markerById.get(row.dataset.centerId);
            if (!marker) return;
            if (visible && !map.hasLayer(marker)) marker.addTo(map);
            if (!visible && map.hasLayer(marker)) map.removeLayer(marker);
        });

        emptyState.hidden = visibleCount > 0;
        statusElement.textContent = visibleCount + ' of ' + centers.length +
            ' evacuation center' + (centers.length === 1 ? '' : 's') + ' shown. ' +
            markerById.size + ' center' + (markerById.size === 1 ? ' marker' : ' markers') +
            ' available on the map.';
        if (Number(mapElement.dataset.unmappedCount) > 0) {
            statusElement.textContent += ' Some centers have no coordinates.';
        }
        if (Number(mapElement.dataset.approximateCount) > 0) {
            statusElement.textContent += ' ' + mapElement.dataset.approximateCount +
                ' marker' + (Number(mapElement.dataset.approximateCount) === 1 ? ' is' : 's are') +
                ' approximate area locations.';
        }
    }

    searchInput.addEventListener('input', applyFilters);
    filterButtons.forEach(function (button) {
        button.addEventListener('click', function () {
            selectedStatus = button.dataset.statusFilter;
            filterButtons.forEach(function (item) {
                const active = item === button;
                item.classList.toggle('active', active);
                item.setAttribute('aria-pressed', String(active));
            });
            applyFilters();
        });
    });
    applyFilters();

    function markerRadius(center) {
        const utilization = center.capacity > 0
            ? Math.min(center.occupants / center.capacity, 1)
            : 0;
        return 7 + Math.round(utilization * 5);
    }

    function statusColor(status) {
        if (status === 'active') return '#10b981';
        if (status === 'standby') return '#f59e0b';
        return '#64748b';
    }

    function createCenterPopup(center) {
        const popup = document.createElement('div');
        popup.className = 'center-popup';

        const name = document.createElement('strong');
        name.textContent = center.name;
        popup.appendChild(name);

        if (center.location) {
            const location = document.createElement('p');
            location.textContent = center.location;
            popup.appendChild(location);
        }

        if (center.coordinates_are_approximate) {
            const approximate = document.createElement('p');
            approximate.textContent = 'Approximate area marker — verify exact facility location before operational use.';
            popup.appendChild(approximate);
        }

        const status = document.createElement('p');
        status.textContent = 'Status: ' + center.status;
        popup.appendChild(status);

        const capacity = document.createElement('p');
        const utilization = center.capacity > 0
            ? Math.round(center.occupants / center.capacity * 100)
            : 0;
        capacity.textContent = 'Occupancy: ' + center.occupants + ' / ' + center.capacity +
            ' (' + utilization + '% capacity)';
        popup.appendChild(capacity);
        return popup;
    }
});
