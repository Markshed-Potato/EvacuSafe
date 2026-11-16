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
    const form = document.getElementById('center-form');
    const dialog = document.getElementById('center-dialog');
    const feedback = document.getElementById('center-form-feedback');
    const saveButton = document.getElementById('save-center-button');
    const map = L.map(mapElement).setView([10.3157, 123.8854], 12);
    L.tileLayer(mapElement.dataset.tileUrl, {
        attribution: mapElement.dataset.tileAttribution,
        maxZoom: 19
    }).addTo(map);

    const markerById = new Map();
    centers.forEach(function (center) {
        addMarker(center);
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

    const openCreateButton = document.getElementById('open-create-center');
    const closeDialogButtons = [
        document.getElementById('close-center-dialog'),
        document.getElementById('cancel-center-dialog')
    ];
    if (openCreateButton && dialog && form && feedback) {
        openCreateButton.addEventListener('click', function () {
            feedback.hidden = true;
            feedback.textContent = '';
            form.reset();
            dialog.showModal();
            document.getElementById('center-name').focus();
        });

        closeDialogButtons.forEach(function (button) {
            if (button) button.addEventListener('click', function () {
                dialog.close();
            });
        });

        dialog.addEventListener('click', function (event) {
            if (event.target === dialog) dialog.close();
        });

        form.addEventListener('submit', async function (event) {
            event.preventDefault();
            feedback.hidden = true;
            feedback.textContent = '';
            saveButton.disabled = true;
            saveButton.textContent = 'Saving…';

            try {
                const response = await fetch(form.action, {
                    method: 'POST',
                    body: new FormData(form),
                    headers: {'X-Requested-With': 'XMLHttpRequest'},
                    credentials: 'same-origin'
                });
                if (response.redirected) {
                    throw new Error('Your session has expired. Sign in again before adding a center.');
                }
                const result = await response.json();
                if (!response.ok) {
                    const messages = Object.values(result.errors || {})
                        .flatMap(function (errors) { return errors.map(function (error) { return error.message; }); });
                    throw new Error(messages.join(' ') || result.error || 'Could not save the evacuation center.');
                }

                centers.push(result.center);
                appendCenterRow(result.center);
                addMarker(result.center);
                updateSummary(result.summary);
                mapElement.dataset.unmappedCount = String(result.unmapped_center_count);
                mapElement.dataset.approximateCount = String(result.approximate_center_count);
                applyFilters();
                if (result.center.latitude !== null && result.center.longitude !== null) {
                    map.setView([result.center.latitude, result.center.longitude], 14);
                }
                statusElement.textContent = result.message + ' ' + statusElement.textContent;
                dialog.close();
                form.reset();
            } catch (error) {
                feedback.textContent = error.message;
                feedback.hidden = false;
            } finally {
                saveButton.disabled = false;
                saveButton.textContent = 'Save center';
            }
        });
    }

    tableBody.addEventListener('submit', async function (event) {
        const updateForm = event.target.closest('.inline-update-form');
        if (!updateForm) return;
        event.preventDefault();

        const saveButton = updateForm.querySelector('.inline-save-btn');
        const updateFeedback = updateForm.querySelector('.inline-feedback');
        updateFeedback.hidden = true;
        updateFeedback.textContent = '';
        saveButton.disabled = true;
        saveButton.textContent = 'Saving';

        try {
            const response = await fetch(updateForm.action, {
                method: 'POST',
                body: new FormData(updateForm),
                headers: {'X-Requested-With': 'XMLHttpRequest'},
                credentials: 'same-origin'
            });
            if (response.redirected) {
                throw new Error('Your session has expired. Sign in again before updating a center.');
            }
            const result = await response.json();
            if (!response.ok) {
                const messages = Object.values(result.errors || {})
                    .flatMap(function (errors) { return errors.map(function (error) { return error.message; }); });
                throw new Error(messages.join(' ') || result.error || 'Could not update the evacuation center.');
            }

            const updatedCenter = result.center;
            const centerIndex = centers.findIndex(function (center) {
                return String(center.id) === String(updatedCenter.id);
            });
            if (centerIndex !== -1) centers[centerIndex] = updatedCenter;

            const row = Array.from(tableBody.rows).find(function (item) {
                return item.dataset.centerId === String(updatedCenter.id);
            });
            row.dataset.status = updatedCenter.status_key;
            const marker = markerById.get(String(updatedCenter.id));
            if (marker) {
                marker.setStyle({fillColor: statusColor(updatedCenter.status_key)});
                marker.setRadius(markerRadius(updatedCenter));
                marker.bindPopup(createCenterPopup(updatedCenter));
            }

            updateSummary(result.summary);
            mapElement.dataset.unmappedCount = String(result.unmapped_center_count);
            mapElement.dataset.approximateCount = String(result.approximate_center_count);
            applyFilters();
            statusElement.textContent = result.message + ' ' + statusElement.textContent;
            updateFeedback.textContent = 'Saved';
            updateFeedback.hidden = false;
        } catch (error) {
            updateFeedback.textContent = error.message;
            updateFeedback.hidden = false;
        } finally {
            saveButton.disabled = false;
            saveButton.textContent = 'Save';
        }
    });

    function addMarker(center) {
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
    }

    function appendCenterRow(center) {
        const row = document.createElement('tr');
        row.dataset.centerId = String(center.id);
        row.dataset.status = center.status_key;
        row.dataset.name = center.name.toLocaleLowerCase();
        row.dataset.location = center.location.toLocaleLowerCase();

        const name = document.createElement('td');
        name.textContent = center.name;
        row.appendChild(name);

        const location = document.createElement('td');
        location.textContent = center.location || '—';
        row.appendChild(location);

        const updateFormId = 'update-center-' + center.id;
        const statusCell = document.createElement('td');
        const statusSelect = document.createElement('select');
        statusSelect.className = 'inline-control';
        statusSelect.name = 'status';
        statusSelect.setAttribute('form', updateFormId);
        statusSelect.setAttribute('aria-label', 'Status for ' + center.name);
        [
            ['active', 'Active'],
            ['standby', 'Standby'],
            ['closed', 'Closed']
        ].forEach(function (choice) {
            const option = document.createElement('option');
            option.value = choice[0];
            option.textContent = choice[1];
            option.selected = center.status_key === choice[0];
            statusSelect.appendChild(option);
        });
        statusCell.appendChild(statusSelect);
        row.appendChild(statusCell);

        const occupants = document.createElement('td');
        const occupantInput = document.createElement('input');
        occupantInput.className = 'inline-control occupant-control';
        occupantInput.type = 'number';
        occupantInput.name = 'occupants';
        occupantInput.min = '0';
        occupantInput.step = '1';
        occupantInput.value = String(center.occupants);
        occupantInput.setAttribute('form', updateFormId);
        occupantInput.setAttribute('aria-label', 'Occupants at ' + center.name);
        occupants.appendChild(occupantInput);
        row.appendChild(occupants);

        const capacity = document.createElement('td');
        capacity.textContent = center.capacity;
        row.appendChild(capacity);

        const actions = document.createElement('td');
        const updateForm = document.createElement('form');
        updateForm.id = updateFormId;
        updateForm.className = 'inline-update-form';
        updateForm.method = 'post';
        updateForm.action = mapElement.dataset.centersUrl + center.id + '/';
        const csrfToken = document.querySelector('#center-form [name=csrfmiddlewaretoken]');
        if (csrfToken) {
            const tokenInput = document.createElement('input');
            tokenInput.type = 'hidden';
            tokenInput.name = 'csrfmiddlewaretoken';
            tokenInput.value = csrfToken.value;
            updateForm.appendChild(tokenInput);
        }
        const saveButton = document.createElement('button');
        saveButton.className = 'btn inline-save-btn';
        saveButton.type = 'submit';
        saveButton.textContent = 'Save';
        updateForm.appendChild(saveButton);
        const updateFeedback = document.createElement('span');
        updateFeedback.className = 'inline-feedback';
        updateFeedback.setAttribute('role', 'status');
        updateFeedback.hidden = true;
        updateForm.appendChild(updateFeedback);
        actions.appendChild(updateForm);
        row.appendChild(actions);

        tableBody.appendChild(row);
    }

    function updateSummary(summary) {
        document.getElementById('active-center-count').textContent =
            summary.active_count + ' / ' + summary.total_count;
        document.getElementById('total-occupants').textContent = summary.total_occupants;
        document.getElementById('capacity-used').textContent =
            summary.total_occupants + ' / ' + summary.total_capacity;
        filterButtons.forEach(function (button) {
            const count = button.querySelector('span');
            if (!count) return;
            const counts = {
                all: summary.total_count,
                active: summary.active_count,
                standby: summary.standby_count,
                closed: summary.closed_count
            };
            count.textContent = counts[button.dataset.statusFilter];
        });
    }

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
