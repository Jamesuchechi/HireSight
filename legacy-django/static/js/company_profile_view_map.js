// Company Profile View - Locations Map
// Renders company locations on a map in the profile view

class CompanyProfileViewMap {
    constructor() {
        this.map = null;
        this.markers = [];
        this.infoWindows = [];
        this.init();
    }

    init() {
        // Check if we have locations to display
        const locationsData = document.getElementById('company-locations-data');
        if (!locationsData) return;

        try {
            const locations = JSON.parse(locationsData.value);
            if (locations && locations.length > 0) {
                this.loadGoogleMapsAPI(locations);
            }
        } catch (e) {
            console.error('Error parsing company locations:', e);
        }
    }

    loadGoogleMapsAPI(locations) {
        // Load Google Maps API if not already loaded
        if (typeof google === 'undefined' || typeof google.maps === 'undefined') {
            const script = document.createElement('script');
            script.src = `https://maps.googleapis.com/maps/api/js?key=AIzaSyDqQX7pZ7J9V7X8X8X8X8X8X8X8X8X8X8X&libraries=places&callback=initCompanyViewMap`;
            script.async = true;
            script.defer = true;
            document.head.appendChild(script);
        } else {
            // Google Maps already loaded, initialize immediately
            this.initializeMap(locations);
        }
    }

    initializeMap(locations) {
        // Initialize the map
        const mapElement = document.getElementById('company-locations-map');
        if (!mapElement) return;

        // Calculate bounds to fit all locations
        const bounds = new google.maps.LatLngBounds();

        // Add all locations to bounds
        locations.forEach(location => {
            if (location.lat && location.lng) {
                const latLng = new google.maps.LatLng(location.lat, location.lng);
                bounds.extend(latLng);
            }
        });

        // Create map centered on first location or default
        const firstLocation = locations[0];
        const center = firstLocation.lat && firstLocation.lng
            ? new google.maps.LatLng(firstLocation.lat, firstLocation.lng)
            : new google.maps.LatLng(37.7749, -122.4194); // Default: San Francisco

        this.map = new google.maps.Map(mapElement, {
            center: center,
            zoom: bounds.getCenter() ? this.map.fitBounds(bounds) : 12,
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

        // Add markers for all locations
        this.addLocationMarkers(locations);
    }

    addLocationMarkers(locations) {
        // Add markers for each location
        locations.forEach((location, index) => {
            if (!location.lat || !location.lng) return;

            const latLng = new google.maps.LatLng(location.lat, location.lng);

            // Create marker with different icon for HQ
            const markerIcon = location.is_hq ? {
                path: google.maps.SymbolPath.CIRCLE,
                scale: 12,
                fillColor: '#D4AF37',
                fillOpacity: 1,
                strokeWeight: 2,
                strokeColor: '#ffffff'
            } : {
                path: google.maps.SymbolPath.CIRCLE,
                scale: 10,
                fillColor: '#2C5F8D',
                fillOpacity: 1,
                strokeWeight: 2,
                strokeColor: '#ffffff'
            };

            const marker = new google.maps.Marker({
                position: latLng,
                map: this.map,
                title: location.address || this.getLocationTitle(location),
                icon: markerIcon,
                animation: google.maps.Animation.DROP
            });

            this.markers.push(marker);

            // Create info window
            const infoWindow = new google.maps.InfoWindow({
                content: this.createInfoWindowContent(location)
            });

            this.infoWindows.push(infoWindow);

            // Add click listener
            marker.addListener('click', () => {
                // Close all other info windows
                this.infoWindows.forEach((window, idx) => {
                    if (idx !== index) {
                        window.close();
                    }
                });

                infoWindow.open(this.map, marker);
            });
        });

        // Fit map to show all markers
        if (this.markers.length > 1) {
            const bounds = new google.maps.LatLngBounds();
            this.markers.forEach(marker => {
                bounds.extend(marker.getPosition());
            });
            this.map.fitBounds(bounds);
        }
    }

    getLocationTitle(location) {
        // Create a title from location components
        const parts = [];
        if (location.address) parts.push(location.address);
        if (location.city) parts.push(location.city);
        if (location.state) parts.push(location.state);
        if (location.country) parts.push(location.country);
        return parts.join(', ');
    }

    createInfoWindowContent(location) {
        // Create HTML content for info window
        const title = location.address || this.getLocationTitle(location);
        const hqBadge = location.is_hq ? '<span class="hq-badge">HQ</span>' : '';

        return `
            <div class="map-info-window">
                <h4>${title}</h4>
                ${hqBadge}
                <div class="location-details">
                    ${location.address ? `<p><strong>Address:</strong> ${location.address}</p>` : ''}
                    ${location.city ? `<p><strong>City:</strong> ${location.city}</p>` : ''}
                    ${location.state ? `<p><strong>State:</strong> ${location.state}</p>` : ''}
                    ${location.country ? `<p><strong>Country:</strong> ${location.country}</p>` : ''}
                    ${location.postal_code ? `<p><strong>Postal Code:</strong> ${location.postal_code}</p>` : ''}
                </div>
                <div class="location-coords">
                    <p><strong>Coordinates:</strong> ${location.lat.toFixed(6)}, ${location.lng.toFixed(6)}</p>
                </div>
            </div>
        `;
    }
}

// Global instance
let companyProfileViewMap;

function initCompanyViewMap() {
    // Initialize the map when Google Maps is ready
    if (!companyProfileViewMap) {
        companyProfileViewMap = new CompanyProfileViewMap();
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('company-locations-map')) {
        if (typeof companyProfileViewMap === 'undefined') {
            companyProfileViewMap = new CompanyProfileViewMap();
        }
    }
});