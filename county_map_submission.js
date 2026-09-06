let newLocationPlacementMode = false;

function initializeCountySubmission(map, { loadAddresses, nearestAddress, closeExisting }) {
  const menu = document.getElementById('countyMenu');
  const panel = document.getElementById('newLocationPanel');
  const address = document.getElementById('newLocationAddress');
  const status = document.getElementById('newLocationStatus');
  const coordinates = document.getElementById('newLocationCoordinates');
  const proceed = document.getElementById('newLocationContinue');
  let marker = null;
  let selected = null;
  let request = 0;

  function cancel() {
    ++request;
    newLocationPlacementMode = false;
    if (marker) marker.remove();
    marker = null;
    selected = null;
    panel.hidden = true;
    document.body.classList.remove('placing-new-location');
    map.getCanvas().style.cursor = '';
  }

  async function updateLocation(point) {
    const currentRequest = ++request;
    selected = { lng: point.lng, lat: point.lat };
    coordinates.textContent = `Latitude: ${point.lat.toFixed(6)}, Longitude: ${point.lng.toFixed(6)}`;
    address.value = '';
    address.disabled = true;
    proceed.disabled = true;
    status.textContent = 'Looking up a nearby parcel address...';
    try {
      const records = await loadAddresses(point.lng, point.lat);
      if (currentRequest !== request) return;
      address.value = nearestAddress(records, point.lng, point.lat) || '';
      status.textContent = address.value
        ? 'Check the suggested nearby address. Drag the pin or click the map to adjust the location.'
        : 'No parcel address found. Enter the address, or complete it in the form. Drag the pin to adjust.';
    } catch (error) {
      if (currentRequest !== request) return;
      status.textContent = 'Address lookup is unavailable. Enter the address, or complete it in the form.';
    } finally {
      if (currentRequest === request) {
        address.disabled = false;
        proceed.disabled = false;
      }
    }
  }

  document.getElementById('newLocationButton').addEventListener('click', () => {
    cancel();
    closeExisting();
    menu.open = false;
    newLocationPlacementMode = true;
    document.body.classList.add('placing-new-location');
    panel.hidden = false;
    address.value = '';
    address.disabled = true;
    proceed.disabled = true;
    coordinates.textContent = '';
    status.textContent = 'Click or tap the map to drop a pin, then drag it to adjust the location.';
  });
  document.getElementById('newLocationCancel').addEventListener('click', cancel);
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape') { menu.open = false; cancel(); }
  });
  document.addEventListener('click', event => {
    if (!menu.contains(event.target)) menu.open = false;
  });
  map.on('click', event => {
    if (!newLocationPlacementMode) return;
    if (!marker) {
      marker = new maplibregl.Marker({ color: '#dc2626', draggable: true }).setLngLat(event.lngLat).addTo(map);
      marker.on('dragstart', () => { ++request; proceed.disabled = true; });
      marker.on('dragend', () => updateLocation(marker.getLngLat()));
    } else {
      marker.setLngLat(event.lngLat);
    }
    updateLocation(event.lngLat);
  });
  proceed.addEventListener('click', () => {
    if (!selected || proceed.disabled) return;
    const url = new URL('https://docs.google.com/forms/d/e/1FAIpQLScaqUry-XEwx7kwZZbV34AxRJzbwJRWg3iM8OxpyzQ-U2lK0Q/viewform');
    url.searchParams.set('usp', 'pp_url');
    url.searchParams.set('entry.1078575168', address.value.trim());
    url.searchParams.set('entry.1115932317', selected.lng.toFixed(6));
    url.searchParams.set('entry.498343151', selected.lat.toFixed(6));
    window.open(url.href, '_blank', 'noopener');
  });
}
