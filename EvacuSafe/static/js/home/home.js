document.addEventListener('DOMContentLoaded', function () {
    const badge = document.getElementById('system-status-badge');
    if (badge) {
        function tick() {
            const now = new Date();
            badge.title = 'Last checked: ' + now.toLocaleTimeString();
        }
        tick();
        setInterval(tick, 30000);
    }

    const mapElement = document.getElementById('evacuation-map');
    if (!mapElement) return;

    const statusElement = document.getElementById('map-status');
    const dataElement = document.getElementById('evacuation-centers-data');
    if (!dataElement || !statusElement) return;

    if (!window.L) {
        statusElement.textContent = 'The map library could not be loaded. Check your internet connection and reload the page.';
        return;
    }

    const centers = JSON.parse(dataElement.textContent);
    const defaultCenter = [10.3157, 123.8854];
    const map = L.map(mapElement).setView(defaultCenter, 12);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19
    }).addTo(map);

    const markers = [];
    centers.forEach(function (center) {
        const utilization = center.capacity > 0
            ? Math.min(center.occupants / center.capacity, 1)
            : 0;
        const marker = L.circleMarker([center.latitude, center.longitude], {
            radius: 7 + Math.round(utilization * 5),
            color: '#fff',
            weight: 2,
            fillColor: statusColor(center.status_key),
            fillOpacity: 0.95,
            className: 'center-marker ' + center.status_key
        }).addTo(map);

        marker.bindPopup(createCenterPopup(center));
        markers.push(marker);
    });

    if (markers.length > 1) {
        map.fitBounds(L.featureGroup(markers).getBounds().pad(0.2));
    } else if (markers.length === 1) {
        map.setView(markers[0].getLatLng(), 14);
    }

    const unmappedCount = Number(mapElement.dataset.unmappedCount);
    if (markers.length === 0) {
        statusElement.textContent = unmappedCount
            ? 'No centers have coordinates yet. Add latitude and longitude in the evacuation center admin to show map markers.'
            : 'No evacuation centers are available to display.';
    } else if (unmappedCount > 0) {
        statusElement.textContent = markers.length + ' mapped center' + (markers.length === 1 ? '' : 's') +
            '; ' + unmappedCount + ' center' + (unmappedCount === 1 ? ' has' : 's have') +
            ' no coordinates and will not appear on the map. Marker color shows status; size reflects capacity use.';
    } else {
        statusElement.textContent = markers.length + ' evacuation center' + (markers.length === 1 ? '' : 's') +
            ' on the map. Marker color shows status; size reflects capacity use.';
    }

    function statusColor(status) {
        if (status === 'active') return '#16a34a';
        if (status === 'standby') return '#d97706';
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
