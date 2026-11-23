document.addEventListener('DOMContentLoaded', function () {
    const badge = document.getElementById('system-status-badge');
    const liveSyncText = document.getElementById('live-sync-text');
    const mapSyncTime = document.getElementById('map-last-sync');

    function updateLiveBadge(timeStr) {
        if (badge) {
            badge.title = 'Live Sync Active. Last synced at ' + (timeStr || new Date().toLocaleTimeString());
        }
        if (mapSyncTime) {
            mapSyncTime.textContent = 'Synced at ' + (timeStr || new Date().toLocaleTimeString());
        }
    }
    updateLiveBadge();

    const mapElement = document.getElementById('evacuation-map');
    if (!mapElement) return;

    const statusElement = document.getElementById('map-status');
    const dataElement = document.getElementById('evacuation-centers-data');
    const searchInput = document.getElementById('center-search');
    const tableBody = document.getElementById('centers-table-body');
    const emptyState = document.getElementById('center-empty-state');
    const filterButtons = Array.from(document.querySelectorAll('[data-status-filter]'));
    if (!dataElement || !statusElement || !searchInput || !tableBody || !emptyState) return;

    function getCsrfToken() {
        const input = document.querySelector('[name=csrfmiddlewaretoken]') || document.getElementById('dashboard-csrf');
        return input ? input.value : '';
    }

    if (!window.L) {
        statusElement.textContent = 'The map library could not be loaded. Check your internet connection and reload the page.';
        return;
    }

    let centers = JSON.parse(dataElement.textContent);
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
        let visibleMarkerCount = 0;

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
            if (visible && map.hasLayer(marker)) visibleMarkerCount += 1;
        });

        filterButtons.forEach(function (button) {
            const active = button.dataset.statusFilter === selectedStatus;
            button.classList.toggle('active', active);
            button.setAttribute('aria-pressed', String(active));
        });
        emptyState.hidden = visibleCount > 0;
        statusElement.textContent = visibleCount + ' of ' + centers.length +
            ' evacuation center' + (centers.length === 1 ? '' : 's') + ' shown. ' +
            visibleMarkerCount + ' center' + (visibleMarkerCount === 1 ? ' marker' : ' markers') +
            ' shown on the map.';
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
            applyFilters();
        });
    });
    applyFilters();

    // -------------------------------------------------------------------------
    // Create Center Dialog Handling
    // -------------------------------------------------------------------------
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

    // -------------------------------------------------------------------------
    // Inline Update Form Handling
    // -------------------------------------------------------------------------
    tableBody.addEventListener('submit', async function (event) {
        const updateForm = event.target.closest('.inline-update-form');
        if (!updateForm) return;
        event.preventDefault();

        const inlineSave = updateForm.querySelector('.inline-save-btn');
        const updateFeedback = updateForm.querySelector('.inline-feedback');
        updateFeedback.hidden = true;
        updateFeedback.textContent = '';
        inlineSave.disabled = true;
        inlineSave.textContent = 'Saving';

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
            const centerIndex = centers.findIndex(function (c) {
                return String(c.id) === String(updatedCenter.id);
            });
            if (centerIndex !== -1) centers[centerIndex] = updatedCenter;

            const row = Array.from(tableBody.rows).find(function (item) {
                return item.dataset.centerId === String(updatedCenter.id);
            });
            if (row) {
                row.dataset.status = updatedCenter.status_key;
            }
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
            inlineSave.disabled = false;
            inlineSave.textContent = 'Save';
        }
    });

    // -------------------------------------------------------------------------
    // Row Actions: Archive & Delete Workflow
    // -------------------------------------------------------------------------
    const deleteModal = document.getElementById('delete-confirm-dialog');
    const deleteNameText = document.getElementById('delete-center-name-text');
    const confirmDeleteBtn = document.getElementById('confirm-delete-btn');
    const cancelDeleteBtn = document.getElementById('cancel-delete-btn');
    let centerPendingDeleteId = null;

    if (cancelDeleteBtn && deleteModal) {
        cancelDeleteBtn.addEventListener('click', function () {
            deleteModal.close();
            centerPendingDeleteId = null;
        });
    }

    if (confirmDeleteBtn && deleteModal) {
        confirmDeleteBtn.addEventListener('click', async function () {
            if (!centerPendingDeleteId) return;
            confirmDeleteBtn.disabled = true;
            confirmDeleteBtn.textContent = 'Deleting…';

            try {
                const response = await fetch('/centers/' + centerPendingDeleteId + '/delete/', {
                    method: 'POST',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'X-CSRFToken': getCsrfToken()
                    },
                    credentials: 'same-origin'
                });
                const result = await response.json();
                if (!response.ok) {
                    throw new Error(result.error || 'Could not permanently delete center.');
                }

                removeCenterFromUI(centerPendingDeleteId);
                updateSummary(result.summary);
                mapElement.dataset.unmappedCount = String(result.unmapped_center_count);
                mapElement.dataset.approximateCount = String(result.approximate_center_count);
                applyFilters();
                deleteModal.close();
                statusElement.textContent = result.message;
            } catch (err) {
                alert(err.message);
            } finally {
                confirmDeleteBtn.disabled = false;
                confirmDeleteBtn.textContent = 'Permanently Delete';
                centerPendingDeleteId = null;
            }
        });
    }

    tableBody.addEventListener('click', async function (event) {
        const actionBtn = event.target.closest('.btn-row-action');
        if (!actionBtn) return;

        const action = actionBtn.dataset.action;
        const centerId = actionBtn.dataset.centerId;
        const centerName = actionBtn.dataset.centerName || 'this center';

        if (action === 'archive') {
            if (!confirm('Are you sure you want to archive ' + centerName + '? It will be marked closed and soft-deleted from active view.')) {
                return;
            }
            try {
                actionBtn.disabled = true;
                actionBtn.textContent = 'Archiving…';
                const response = await fetch('/centers/' + centerId + '/archive/', {
                    method: 'POST',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'X-CSRFToken': getCsrfToken()
                    },
                    credentials: 'same-origin'
                });
                const result = await response.json();
                if (!response.ok) {
                    throw new Error(result.error || 'Failed to archive center.');
                }
                removeCenterFromUI(centerId);
                updateSummary(result.summary);
                mapElement.dataset.unmappedCount = String(result.unmapped_center_count);
                mapElement.dataset.approximateCount = String(result.approximate_center_count);
                applyFilters();
                statusElement.textContent = result.message;
            } catch (err) {
                alert(err.message);
                actionBtn.disabled = false;
                actionBtn.textContent = 'Archive';
            }
        } else if (action === 'delete') {
            if (deleteModal) {
                centerPendingDeleteId = centerId;
                deleteNameText.textContent = 'Permanently delete facility: "' + centerName + '"?';
                deleteModal.showModal();
            }
        }
    });

    function removeCenterFromUI(centerId) {
        const idStr = String(centerId);
        centers = centers.filter(function (c) { return String(c.id) !== idStr; });
        const marker = markerById.get(idStr);
        if (marker) {
            map.removeLayer(marker);
            markerById.delete(idStr);
        }
        const row = Array.from(tableBody.rows).find(function (r) {
            return r.dataset.centerId === idStr;
        });
        if (row) {
            row.remove();
        }
    }

    // -------------------------------------------------------------------------
    // Resource Inventory Dialog Handling
    // -------------------------------------------------------------------------
    const resourceDialog = document.getElementById('resource-dialog');
    const resourceForm = document.getElementById('resource-form');
    const resourceSubtitle = document.getElementById('resource-dialog-subtitle');
    const closeResourceBtn = document.getElementById('close-resource-dialog');
    const cancelResourceBtn = document.getElementById('cancel-resource-dialog');
    let currentResourceCenterId = null;

    if (closeResourceBtn) closeResourceBtn.addEventListener('click', function () { resourceDialog.close(); });
    if (cancelResourceBtn) cancelResourceBtn.addEventListener('click', function () { resourceDialog.close(); });

    tableBody.addEventListener('click', function (event) {
        const resBtn = event.target.closest('.btn-resource-view');
        if (!resBtn || !resourceDialog) return;

        currentResourceCenterId = resBtn.dataset.centerId;
        resourceSubtitle.textContent = 'Relief supplies inventory for ' + (resBtn.dataset.centerName || 'center') + ':';
        document.getElementById('res-food').value = resBtn.dataset.food || 0;
        document.getElementById('res-water').value = resBtn.dataset.water || 0;
        document.getElementById('res-meds').value = resBtn.dataset.meds || 0;
        document.getElementById('res-blankets').value = resBtn.dataset.blankets || 0;
        resourceForm.action = '/centers/' + currentResourceCenterId + '/resources/';
        resourceDialog.showModal();
    });

    if (resourceForm) {
        resourceForm.addEventListener('submit', async function (event) {
            event.preventDefault();
            const saveResBtn = document.getElementById('save-resource-button');
            const resFeedback = document.getElementById('resource-form-feedback');
            if (saveResBtn) { saveResBtn.disabled = true; saveResBtn.textContent = 'Updating…'; }
            if (resFeedback) { resFeedback.hidden = true; }

            try {
                const response = await fetch(resourceForm.action, {
                    method: 'POST',
                    body: new FormData(resourceForm),
                    headers: {'X-Requested-With': 'XMLHttpRequest'},
                    credentials: 'same-origin'
                });
                const result = await response.json();
                if (!response.ok) {
                    throw new Error(result.error || 'Failed to update resource supplies.');
                }
                // Update table button text
                const rowBtn = tableBody.querySelector('.btn-resource-view[data-center-id="' + currentResourceCenterId + '"]');
                if (rowBtn) {
                    rowBtn.dataset.food = result.resources.food_packs;
                    rowBtn.dataset.water = result.resources.water_liters;
                    rowBtn.dataset.meds = result.resources.medical_kits;
                    rowBtn.dataset.blankets = result.resources.blankets;
                    rowBtn.textContent = '📦 Food: ' + result.resources.food_packs + ' | Water: ' + result.resources.water_liters + 'L';
                }
                resourceDialog.close();
                statusElement.textContent = result.message;
            } catch (err) {
                if (resFeedback) {
                    resFeedback.textContent = err.message;
                    resFeedback.hidden = false;
                }
            } finally {
                if (saveResBtn) { saveResBtn.disabled = false; saveResBtn.textContent = 'Update Supplies'; }
            }
        });
    }

    // -------------------------------------------------------------------------
    // Active Incidents Modal Handling
    // -------------------------------------------------------------------------
    const incidentDialog = document.getElementById('incident-dialog');
    const incidentForm = document.getElementById('incident-form');
    const openIncidentBtn = document.getElementById('open-incident-dialog');
    const openIncidentQuickBtn = document.getElementById('add-incident-quick-btn');
    const closeIncidentBtn = document.getElementById('close-incident-dialog');
    const cancelIncidentBtn = document.getElementById('cancel-incident-dialog');

    function showIncidentModal() {
        if (!incidentDialog) return;
        incidentForm.reset();
        document.getElementById('incident-form-feedback').hidden = true;
        incidentDialog.showModal();
    }

    if (openIncidentBtn) openIncidentBtn.addEventListener('click', showIncidentModal);
    if (openIncidentQuickBtn) openIncidentQuickBtn.addEventListener('click', showIncidentModal);
    if (closeIncidentBtn) closeIncidentBtn.addEventListener('click', function () { incidentDialog.close(); });
    if (cancelIncidentBtn) cancelIncidentBtn.addEventListener('click', function () { incidentDialog.close(); });

    if (incidentForm) {
        incidentForm.addEventListener('submit', async function (event) {
            event.preventDefault();
            const saveIncBtn = document.getElementById('save-incident-button');
            const incFeedback = document.getElementById('incident-form-feedback');
            saveIncBtn.disabled = true;
            saveIncBtn.textContent = 'Broadcasting…';
            incFeedback.hidden = true;

            try {
                const response = await fetch(incidentForm.action, {
                    method: 'POST',
                    body: new FormData(incidentForm),
                    headers: {'X-Requested-With': 'XMLHttpRequest'},
                    credentials: 'same-origin'
                });
                const result = await response.json();
                if (!response.ok) {
                    throw new Error(result.error || 'Failed to broadcast incident.');
                }
                incidentDialog.close();
                alert(result.message);
                window.location.reload();
            } catch (err) {
                incFeedback.textContent = err.message;
                incFeedback.hidden = false;
            } finally {
                saveIncBtn.disabled = false;
                saveIncBtn.textContent = 'Broadcast Incident';
            }
        });
    }

    // Resolve incident click handler
    document.addEventListener('click', async function (event) {
        const resolveBtn = event.target.closest('.btn-resolve-incident');
        if (!resolveBtn) return;
        const incId = resolveBtn.dataset.incidentId;
        if (!confirm('Mark this disaster incident as resolved?')) return;

        try {
            resolveBtn.disabled = true;
            resolveBtn.textContent = 'Resolving…';
            const response = await fetch('/incidents/' + incId + '/resolve/', {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': getCsrfToken()
                },
                credentials: 'same-origin'
            });
            const result = await response.json();
            if (!response.ok) throw new Error(result.error || 'Failed to resolve incident.');
            const incCard = document.querySelector('.incident-card[data-incident-id="' + incId + '"]');
            if (incCard) incCard.remove();
        } catch (err) {
            alert(err.message);
            resolveBtn.disabled = false;
            resolveBtn.textContent = 'Mark Resolved';
        }
    });

    // -------------------------------------------------------------------------
    // Real-Time Background Auto-Sync (12-15s Polling)
    // -------------------------------------------------------------------------
    const liveUrl = mapElement.dataset.liveUrl;
    if (liveUrl) {
        async function pollLiveStatus() {
            try {
                const response = await fetch(liveUrl, {
                    headers: {'X-Requested-With': 'XMLHttpRequest'},
                    credentials: 'same-origin'
                });
                if (!response.ok) return;
                const data = await response.json();
                if (data.status !== 'ok') return;

                updateLiveBadge(data.timestamp);
                updateSummary(data.summary);

                // Sync center markers on map
                if (Array.isArray(data.centers)) {
                    data.centers.forEach(function (center) {
                        const marker = markerById.get(String(center.id));
                        if (marker) {
                            marker.setStyle({fillColor: statusColor(center.status_key)});
                            marker.setRadius(markerRadius(center));
                            marker.setPopupContent(createCenterPopup(center));
                        }
                    });
                }

                // Update recent audit feed dynamically
                const auditContainer = document.getElementById('audit-log-list');
                if (auditContainer && Array.isArray(data.audit_logs) && data.audit_logs.length > 0) {
                    auditContainer.innerHTML = '';
                    data.audit_logs.forEach(function (log) {
                        const item = document.createElement('div');
                        item.className = 'audit-item action-' + (log.action_key || 'update');
                        item.innerHTML = '<div class="audit-item-header">' +
                            '<span class="audit-action-chip ' + (log.action_key || 'update') + '">' + log.action + '</span>' +
                            '<strong class="audit-center">' + log.center_name + '</strong>' +
                            '<span class="audit-time">' + log.timestamp + '</span>' +
                            '</div>' +
                            '<p class="audit-detail">' + (log.details || 'Operation recorded.') + '</p>' +
                            '<div class="audit-user">Operated by: ' + log.user + '</div>';
                        auditContainer.appendChild(item);
                    });
                }
            } catch (e) {
                // Ignore transient network errors during background poll
            }
        }
        setInterval(pollLiveStatus, 12000);
    }

    // -------------------------------------------------------------------------
    // Map Marker & Summary Utility Functions
    // -------------------------------------------------------------------------
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
        row.dataset.location = center.location ? center.location.toLocaleLowerCase() : '';

        const name = document.createElement('td');
        name.innerHTML = '<strong>' + center.name + '</strong>';
        if (center.is_full) {
            name.innerHTML += ' <span class="capacity-warning full">FULL</span>';
        }
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
            ['closed', 'Closed'],
            ['full', 'Full']
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

        const suppliesCell = document.createElement('td');
        suppliesCell.innerHTML = '<button type="button" class="btn-resource-view" data-center-id="' + center.id + '" data-center-name="' + center.name + '" data-food="0" data-water="0" data-meds="0" data-blankets="0">📦 Food: 0 | Water: 0L</button>';
        row.appendChild(suppliesCell);

        const actions = document.createElement('td');
        const updateForm = document.createElement('form');
        updateForm.id = updateFormId;
        updateForm.className = 'inline-update-form';
        updateForm.method = 'post';
        updateForm.action = mapElement.dataset.centersUrl + center.id + '/';

        const token = getCsrfToken();
        if (token) {
            const tokenInput = document.createElement('input');
            tokenInput.type = 'hidden';
            tokenInput.name = 'csrfmiddlewaretoken';
            tokenInput.value = token;
            updateForm.appendChild(tokenInput);
        }
        const saveBtn = document.createElement('button');
        saveBtn.className = 'btn inline-save-btn';
        saveBtn.type = 'submit';
        saveBtn.textContent = 'Save';
        updateForm.appendChild(saveBtn);
        const updateFeedback = document.createElement('span');
        updateFeedback.className = 'inline-feedback';
        updateFeedback.setAttribute('role', 'status');
        updateFeedback.hidden = true;
        updateForm.appendChild(updateFeedback);

        const actionsDiv = document.createElement('div');
        actionsDiv.className = 'row-actions';
        actionsDiv.appendChild(updateForm);

        const archiveBtn = document.createElement('button');
        archiveBtn.type = 'button';
        archiveBtn.className = 'btn-row-action archive';
        archiveBtn.dataset.action = 'archive';
        archiveBtn.dataset.centerId = String(center.id);
        archiveBtn.dataset.centerName = center.name;
        archiveBtn.textContent = 'Archive';
        actionsDiv.appendChild(archiveBtn);

        actions.appendChild(actionsDiv);
        row.appendChild(actions);

        tableBody.appendChild(row);
    }

    function updateSummary(summary) {
        if (!summary) return;
        const activeElem = document.getElementById('active-center-count');
        const occElem = document.getElementById('total-occupants');
        const capElem = document.getElementById('capacity-used');

        if (activeElem) activeElem.textContent = summary.active_count + ' / ' + summary.total_count;
        if (occElem) occElem.textContent = summary.total_occupants;
        if (capElem) capElem.textContent = summary.total_occupants + ' / ' + summary.total_capacity;

        filterButtons.forEach(function (button) {
            const count = button.querySelector('span');
            if (!count) return;
            const counts = {
                all: summary.total_count,
                active: summary.active_count,
                standby: summary.standby_count,
                closed: summary.closed_count
            };
            if (counts[button.dataset.statusFilter] !== undefined) {
                count.textContent = counts[button.dataset.statusFilter];
            }
        });
    }

    function markerRadius(center) {
        const utilization = center.capacity > 0
            ? Math.min(center.occupants / center.capacity, 1)
            : 0;
        return 7 + Math.round(utilization * 5);
    }

    function statusColor(status) {
        if (status === 'full') return '#ef4444';
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
        if (utilization >= 100) {
            capacity.style.color = '#ef4444';
            capacity.style.fontWeight = 'bold';
        }
        popup.appendChild(capacity);
        return popup;
    }
});
