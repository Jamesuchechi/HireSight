// Company Profile Locations Map Picker
// Handles structured locations with address autocomplete and map selection

class CompanyLocationsManager {
    constructor() {
        this.locations = [];
        this.map = null;
        this.marker = null;
        this.autocomplete = null;
        this.geocoder = null;
        this.init();
    }

    init() {
        // Initialize the locations manager
        this.setupEventListeners();
        this.loadExistingLocations();
        this.initializeMap();
        this.initializeAutocomplete();
    }

    setupEventListeners() {
        // Add new location button
        document.getElementById('add-location-btn').addEventListener('click', () => this.addNewLocation());

        // Save locations button
        document.getElementById('save-locations-btn').addEventListener('click', () => this.saveLocations());

        // Form submission
        const form = document.querySelector('form');
        if (form) {
            form.addEventListener('submit', (e) => {
                this.saveLocationsToForm();
            });
        }
    }

    loadExistingLocations() {
        // Load existing locations from the template
        const locationsJson = document.getElementById('existing-locations-data').value;
        if (locationsJson) {
            try {
                this.locations = JSON.parse(locationsJson);
                this.renderLocations();
            } catch (e) {
                console.error('Error parsing existing locations:', e);
            }
        }
    }

    initializeMap() {
        // Initialize Google Map
        const mapElement = document.getElementById('location-map');
        if (!mapElement) return;

        // Default to San Francisco
        const defaultLocation = { lat: 37.7749, lng: -122.4194 };

        this.map = new google.maps.Map(mapElement, {
            center: defaultLocation,
            zoom: 12,
            mapTypeControl: true,
            streetViewControl: false,
            fullscreenControl: false,
            styles: [
                {
                    featureType: 'all',
                    elementType: 'labels.text.fill',
                    stylers: [{ color: '#444444' }]
                },
                {
                    featureType: 'administrative.locality',
                    elementType: 'labels.text.fill',
                    stylers: [{ color: '#2C5F8D' }]
                },
                {
                    featureType: 'poi',
                    elementType: 'labels.text.fill',
                    stylers: [{ color: '#6B9A76' }]
                },
                {
                    featureType: 'poi.park',
                    elementType: 'geometry',
                    stylers: [{ color: '#E5E5E5' }]
                },
                {
                    featureType: 'poi.park',
                    elementType: 'labels.text.fill',
                    stylers: [{ color: '#9E9E9E' }]
                },
                {
                    featureType: 'road',
                    elementType: 'geometry',
                    stylers: [{ color: '#FFFFFF' }]
                },
                {
                    featureType: 'road',
                    elementType: 'geometry.stroke',
                    stylers: [{ color: '#D4AF37' }]
                },
                {
                    featureType: 'road',
                    elementType: 'labels.text.fill',
                    stylers: [{ color: '#6B9A76' }]
                },
                {
                    featureType: 'road.highway',
                    elementType: 'geometry',
                    stylers: [{ color: '#D4AF37' }]
                },
                {
                    featureType: 'road.highway',
                    elementType: 'geometry.stroke',
                    stylers: [{ color: '#D4AF37' }]
                },
                {
                    featureType: 'road.highway',
                    elementType: 'labels.text.fill',
                    stylers: [{ color: '#2C5F8D' }]
                },
                {
                    featureType: 'transit',
                    elementType: 'geometry',
                    stylers: [{ color: '#2C5F8D' }]
                },
                {
                    featureType: 'water',
                    elementType: 'geometry',
                    stylers: [{ color: '#4285F4' }]
                },
                {
                    featureType: 'water',
                    elementType: 'labels.text.fill',
                    stylers: [{ color: '#0D2250' }]
                }
            ]
        });

        this.geocoder = new google.maps.Geocoder();

        // Add click listener to set marker
        this.map.addListener('click', (event) => {
            this.placeMarker(event.latLng);
            this.reverseGeocode(event.latLng);
        });
    }

    initializeAutocomplete() {
        // Initialize address autocomplete
        const addressInput = document.getElementById('location-address-input');
        if (!addressInput) return;

        this.autocomplete = new google.maps.places.Autocomplete(addressInput, {
            types: ['geocode'],
            componentRestrictions: { country: 'us' } // Default to US, can be changed
        });

        this.autocomplete.addListener('place_changed', () => {
            const place = this.autocomplete.getPlace();
            if (!place.geometry) return;

            // Center map on selected location
            if (place.geometry.viewport) {
                this.map.fitBounds(place.geometry.viewport);
            } else {
                this.map.setCenter(place.geometry.location);
                this.map.setZoom(17);
            }

            // Place marker
            this.placeMarker(place.geometry.location);

            // Fill in address components
            this.fillAddressComponents(place);
        });
    }

    placeMarker(location) {
        // Remove existing marker
        if (this.marker) {
            this.marker.setMap(null);
        }

        // Create new marker
        this.marker = new google.maps.Marker({
            position: location,
            map: this.map,
            draggable: true,
            animation: google.maps.Animation.DROP,
            icon: {
                path: google.maps.SymbolPath.CIRCLE,
                scale: 10,
                fillColor: '#2C5F8D',
                fillOpacity: 1,
                strokeWeight: 2,
                strokeColor: '#ffffff'
            }
        });

        // Update position when marker is dragged
        this.marker.addListener('dragend', (event) => {
            this.reverseGeocode(event.latLng);
        });
    }

    fillAddressComponents(place) {
        // Fill address form fields from place details
        let address = '';
        let city = '';
        let state = '';
        let country = '';
        let postalCode = '';

        // Get address components
        if (place.address_components) {
            place.address_components.forEach(component => {
                const types = component.types;
                if (types.includes('street_number')) {
                    address = component.long_name + ' ' + address;
                }
                if (types.includes('route')) {
                    address += component.long_name;
                }
                if (types.includes('locality')) {
                    city = component.long_name;
                }
                if (types.includes('administrative_area_level_1')) {
                    state = component.short_name;
                }
                if (types.includes('country')) {
                    country = component.long_name;
                }
                if (types.includes('postal_code')) {
                    postalCode = component.long_name;
                }
            });
        }

        // Update form fields
        document.getElementById('location-address-input').value = place.formatted_address || address;
        document.getElementById('location-city-input').value = city;
        document.getElementById('location-state-input').value = state;
        document.getElementById('location-country-input').value = country;
        document.getElementById('location-postal-input').value = postalCode;
        document.getElementById('location-lat-input').value = place.geometry.location.lat();
        document.getElementById('location-lng-input').value = place.geometry.location.lng();
    }

    reverseGeocode(latLng) {
        // Convert lat/lng to address
        this.geocoder.geocode({ location: latLng }, (results, status) => {
            if (status === 'OK' && results[0]) {
                const place = results[0];
                this.fillAddressComponents(place);

                // Update marker position inputs
                document.getElementById('location-lat-input').value = latLng.lat();
                document.getElementById('location-lng-input').value = latLng.lng();
            }
        });
    }

    addNewLocation() {
        // Add a new location to the list
        const address = document.getElementById('location-address-input').value.trim();
        const city = document.getElementById('location-city-input').value.trim();
        const state = document.getElementById('location-state-input').value.trim();
        const country = document.getElementById('location-country-input').value.trim();
        const postalCode = document.getElementById('location-postal-input').value.trim();
        const lat = parseFloat(document.getElementById('location-lat-input').value);
        const lng = parseFloat(document.getElementById('location-lng-input').value);
        const isHQ = document.getElementById('location-is-hq-input').checked;

        if (!address || !city || !country || isNaN(lat) || isNaN(lng)) {
            alert('Please fill in all required location fields and select a valid location on the map.');
            return;
        }

        const newLocation = {
            address: address,
            city: city,
            state: state,
            country: country,
            postal_code: postalCode,
            lat: lat,
            lng: lng,
            is_hq: isHQ
        };

        // Check if this is replacing an existing HQ
        const existingHQIndex = this.locations.findIndex(loc => loc.is_hq);
        if (newLocation.is_hq && existingHQIndex !== -1 && existingHQIndex !== this.currentEditIndex) {
            // Ask user if they want to replace the existing HQ
            const confirmReplace = confirm('You already have a headquarters location. Do you want to replace it with this new location?');
            if (confirmReplace) {
                this.locations[existingHQIndex].is_hq = false;
            } else {
                newLocation.is_hq = false;
            }
        }

        // Add or update location
        if (this.currentEditIndex !== undefined && this.currentEditIndex !== null) {
            this.locations[this.currentEditIndex] = newLocation;
            this.currentEditIndex = null;
        } else {
            this.locations.push(newLocation);
        }

        // Reset form and render locations
        this.resetLocationForm();
        this.renderLocations();

        // Show success message
        const successMsg = document.getElementById('location-success-message');
        if (successMsg) {
            successMsg.textContent = 'Location added successfully!';
            successMsg.style.display = 'block';
            setTimeout(() => {
                successMsg.style.display = 'none';
            }, 3000);
        }
    }

    editLocation(index) {
        // Edit an existing location
        const location = this.locations[index];

        // Set form values
        document.getElementById('location-address-input').value = location.address || '';
        document.getElementById('location-city-input').value = location.city || '';
        document.getElementById('location-state-input').value = location.state || '';
        document.getElementById('location-country-input').value = location.country || '';
        document.getElementById('location-postal-input').value = location.postal_code || '';
        document.getElementById('location-lat-input').value = location.lat || '';
        document.getElementById('location-lng-input').value = location.lng || '';
        document.getElementById('location-is-hq-input').checked = location.is_hq || false;

        // Center map on this location
        if (location.lat && location.lng) {
            const latLng = new google.maps.LatLng(location.lat, location.lng);
            this.map.setCenter(latLng);
            this.map.setZoom(15);
            this.placeMarker(latLng);
        }

        this.currentEditIndex = index;

        // Update button text
        const addBtn = document.getElementById('add-location-btn');
        if (addBtn) {
            addBtn.textContent = 'Update Location';
            addBtn.classList.add('updating');
        }
    }

    removeLocation(index) {
        // Remove a location
        if (confirm('Are you sure you want to remove this location?')) {
            this.locations.splice(index, 1);
            this.renderLocations();
            this.resetLocationForm();
        }
    }

    resetLocationForm() {
        // Reset the location form
        document.getElementById('location-address-input').value = '';
        document.getElementById('location-city-input').value = '';
        document.getElementById('location-state-input').value = '';
        document.getElementById('location-country-input').value = '';
        document.getElementById('location-postal-input').value = '';
        document.getElementById('location-lat-input').value = '';
        document.getElementById('location-lng-input').value = '';
        document.getElementById('location-is-hq-input').checked = false;

        // Reset button text
        const addBtn = document.getElementById('add-location-btn');
        if (addBtn) {
            addBtn.textContent = 'Add Location';
            addBtn.classList.remove('updating');
        }

        this.currentEditIndex = null;

        // Remove marker
        if (this.marker) {
            this.marker.setMap(null);
            this.marker = null;
        }
    }

    renderLocations() {
        // Render the list of locations
        const locationsContainer = document.getElementById('locations-list');
        if (!locationsContainer) return;

        if (this.locations.length === 0) {
            locationsContainer.innerHTML = '<div class="no-locations-message"><p>No locations added yet. Use the form above to add your company locations.</p></div>';
            return;
        }

        let html = '<div class="locations-grid">';

        this.locations.forEach((location, index) => {
            const hqBadge = location.is_hq ? '<span class="hq-badge">HQ</span>' : '';
            const addressParts = [];
            if (location.address) addressParts.push(location.address);
            if (location.city) addressParts.push(location.city);
            if (location.state) addressParts.push(location.state);
            if (location.country) addressParts.push(location.country);
            if (location.postal_code) addressParts.push(location.postal_code);

            html += `
                <div class="location-card">
                    <div class="location-header">
                        <h4>${addressParts.join(', ')}</h4>
                        ${hqBadge}
                    </div>
                    <div class="location-coords">
                        Lat: ${location.lat.toFixed(6)}, Lng: ${location.lng.toFixed(6)}
                    </div>
                    <div class="location-actions">
                        <button type="button" class="btn-edit" onclick="locationsManager.editLocation(${index})">Edit</button>
                        <button type="button" class="btn-remove" onclick="locationsManager.removeLocation(${index})">Remove</button>
                    </div>
                </div>
            `;
        });

        html += '</div>';
        locationsContainer.innerHTML = html;
    }

    saveLocations() {
        // Save locations to hidden form field
        this.saveLocationsToForm();
        alert('Locations saved! Don\'t forget to click "Save Changes" on the main form.');
    }

    saveLocationsToForm() {
        // Save locations to the hidden form field that gets submitted with the main form
        const locationsInput = document.getElementById('id_locations_json');
        if (locationsInput) {
            locationsInput.value = JSON.stringify(this.locations);
        }
    }

    loadGoogleMapsAPI() {
        // Load Google Maps API if not already loaded
        if (typeof google === 'undefined' || typeof google.maps === 'undefined') {
            const script = document.createElement('script');
            script.src = `https://maps.googleapis.com/maps/api/js?key=AIzaSyDqQX7pZ7J9V7X8X8X8X8X8X8X8X8X8X8X&libraries=places&callback=initLocationsManager`;
            script.async = true;
            script.defer = true;
            document.head.appendChild(script);
        } else {
            // Google Maps already loaded, initialize immediately
            window.initLocationsManager();
        }
    }
}

// Global instance
let locationsManager;

function initLocationsManager() {
    // Initialize the locations manager when Google Maps is ready
    if (!locationsManager) {
        locationsManager = new CompanyLocationsManager();
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Load Google Maps API
    if (document.getElementById('company-locations-section')) {
        if (typeof locationsManager === 'undefined') {
            locationsManager = new CompanyLocationsManager();
            locationsManager.loadGoogleMapsAPI();
        }
    }
});