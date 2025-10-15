// Car2X Dashboard JavaScript
class Car2XDashboard {
    constructor() {
        this.socket = io();
        this.map = null;
        this.vehicleMarkers = {};
        this.emergencyMarkers = {};
        this.infrastructureMarkers = {};
        
        this.init();
    }
    
    init() {
        this.setupSocketListeners();
        this.initMap();
        this.setupEventListeners();
        this.requestInitialData();
        this.startPolling();
    }
    
    startPolling() {
        // Poll for updates every 2 seconds as backup to WebSocket
        setInterval(() => {
            this.pollForUpdates();
        }, 2000);
    }
    
    pollForUpdates() {
        // Fetch vehicles
        fetch('/api/vehicles')
            .then(response => response.json())
            .then(vehicles => {
                Object.values(vehicles).forEach(vehicle => {
                    this.updateVehicle(vehicle);
                    this.updateVehicleMarker(vehicle);
                });
                this.updateStatistics();
            })
            .catch(error => console.error('Error fetching vehicles:', error));
        
        // Fetch infrastructure
        fetch('/api/infrastructure')
            .then(response => response.json())
            .then(infrastructure => {
                Object.values(infrastructure).forEach(infra => {
                    this.updateInfrastructureItem(infra);
                    this.updateInfrastructureMarker(infra);
                });
            })
            .catch(error => console.error('Error fetching infrastructure:', error));
        
        // Fetch emergencies
        fetch('/api/emergencies')
            .then(response => response.json())
            .then(emergencies => {
                // Only add new emergencies
                const existingCount = document.querySelectorAll('.alert-card').length;
                if (emergencies.length > existingCount) {
                    this.updateEmergencies(emergencies);
                }
            })
            .catch(error => console.error('Error fetching emergencies:', error));
    }
    
    setupSocketListeners() {
        this.socket.on('connect', () => {
            console.log('Connected to server');
            this.updateConnectionStatus(true);
        });
        
        this.socket.on('disconnect', () => {
            console.log('Disconnected from server');
            this.updateConnectionStatus(false);
        });
        
        this.socket.on('initial_data', (data) => {
            this.updateVehicles(data.vehicles);
            this.updateInfrastructure(data.infrastructure);
            this.updateEmergencies(data.emergencies);
            this.updateJobs(data.jobs);
            this.updateStatistics();
        });
        
        this.socket.on('vehicle_update', (vehicle) => {
            this.updateVehicle(vehicle);
            this.updateVehicleMarker(vehicle);
        });
        
        this.socket.on('vehicle_emergency', (data) => {
            this.addEmergencyAlert(data);
            this.updateVehicleMarker(data.message, true);
        });
        
        this.socket.on('infrastructure_update', (infra) => {
            this.updateInfrastructureItem(infra);
            this.updateInfrastructureMarker(infra);
        });
        
        this.socket.on('emergency_alert', (emergency) => {
            this.addEmergencyAlert(emergency);
            this.addEmergencyMarker(emergency);
        });
        
        this.socket.on('job_response', (data) => {
            this.updateJobResponse(data);
        });
    }
    
    initMap() {
        // Initialize Leaflet map centered on Munich
        this.map = L.map('map').setView([48.1351, 11.5820], 13);
        
        // Add OpenStreetMap tiles
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(this.map);
    }
    
    setupEventListeners() {
        // Job creation modal
        const createJobBtn = document.getElementById('create-job-btn');
        const jobModal = document.getElementById('job-modal');
        const closeBtn = document.querySelector('.close');
        const cancelBtn = document.getElementById('cancel-job');
        const jobForm = document.getElementById('job-form');
        
        createJobBtn.addEventListener('click', () => {
            this.showJobModal();
        });
        
        closeBtn.addEventListener('click', () => {
            this.hideJobModal();
        });
        
        cancelBtn.addEventListener('click', () => {
            this.hideJobModal();
        });
        
        jobForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.createJob();
        });
        
        // Close modal when clicking outside
        window.addEventListener('click', (e) => {
            if (e.target === jobModal) {
                this.hideJobModal();
            }
        });
    }
    
    requestInitialData() {
        this.socket.emit('request_data');
    }
    
    updateConnectionStatus(connected) {
        const statusElement = document.getElementById('connection-status');
        if (connected) {
            statusElement.textContent = 'Online';
            statusElement.className = 'status-indicator online';
        } else {
            statusElement.textContent = 'Offline';
            statusElement.className = 'status-indicator offline';
        }
    }
    
    updateVehicles(vehicles) {
        const vehiclesList = document.getElementById('vehicles-list');
        vehiclesList.innerHTML = '';
        
        Object.values(vehicles).forEach(vehicle => {
            this.addVehicleCard(vehicle);
            this.updateVehicleMarker(vehicle);
        });
    }
    
    updateVehicle(vehicle) {
        const existingCard = document.querySelector(`[data-vehicle-id="${vehicle.vehicle_id}"]`);
        if (existingCard) {
            this.updateVehicleCard(vehicle, existingCard);
        } else {
            this.addVehicleCard(vehicle);
        }
        this.updateVehicleMarker(vehicle);
    }
    
    addVehicleCard(vehicle) {
        const vehiclesList = document.getElementById('vehicles-list');
        const card = document.createElement('div');
        card.className = 'vehicle-card';
        card.setAttribute('data-vehicle-id', vehicle.vehicle_id);
        
        card.innerHTML = `
            <div class="vehicle-header">
                <span class="vehicle-id">${vehicle.vehicle_id}</span>
                <span class="vehicle-status ${vehicle.status}">${vehicle.status}</span>
            </div>
            <div class="vehicle-info">
                <div>Speed: ${Math.round(vehicle.speed)} km/h</div>
                <div>Heading: ${Math.round(vehicle.heading)}°</div>
                <div>Lat: ${vehicle.position.latitude.toFixed(6)}</div>
                <div>Lon: ${vehicle.position.longitude.toFixed(6)}</div>
            </div>
        `;
        
        vehiclesList.appendChild(card);
    }
    
    updateVehicleCard(vehicle, card) {
        const statusElement = card.querySelector('.vehicle-status');
        const infoElement = card.querySelector('.vehicle-info');
        
        statusElement.textContent = vehicle.status;
        statusElement.className = `vehicle-status ${vehicle.status}`;
        
        infoElement.innerHTML = `
            <div>Speed: ${Math.round(vehicle.speed)} km/h</div>
            <div>Heading: ${Math.round(vehicle.heading)}°</div>
            <div>Lat: ${vehicle.position.latitude.toFixed(6)}</div>
            <div>Lon: ${vehicle.position.longitude.toFixed(6)}</div>
        `;
        
        if (vehicle.status === 'emergency') {
            card.classList.add('emergency');
        } else {
            card.classList.remove('emergency');
        }
    }
    
    updateVehicleMarker(vehicle, isEmergency = false) {
        const lat = vehicle.position.latitude;
        const lon = vehicle.position.longitude;
        
        if (this.vehicleMarkers[vehicle.vehicle_id]) {
            this.map.removeLayer(this.vehicleMarkers[vehicle.vehicle_id]);
        }
        
        const icon = L.divIcon({
            className: 'vehicle-marker',
            html: `<div class="marker vehicle-marker-${isEmergency ? 'emergency' : 'normal'}">🚗</div>`,
            iconSize: [20, 20],
            iconAnchor: [10, 10]
        });
        
        const marker = L.marker([lat, lon], { icon }).addTo(this.map);
        marker.bindPopup(`
            <strong>${vehicle.vehicle_id}</strong><br>
            Speed: ${Math.round(vehicle.speed)} km/h<br>
            Status: ${vehicle.status}<br>
            Time: ${new Date(vehicle.timestamp).toLocaleTimeString()}
        `);
        
        this.vehicleMarkers[vehicle.vehicle_id] = marker;
    }
    
    updateInfrastructure(infrastructure) {
        const infraList = document.getElementById('infrastructure-list');
        infraList.innerHTML = '';
        
        Object.values(infrastructure).forEach(infra => {
            this.addInfrastructureCard(infra);
            this.updateInfrastructureMarker(infra);
        });
    }
    
    updateInfrastructureItem(infra) {
        const existingCard = document.querySelector(`[data-infra-id="${infra.infrastructure_id}"]`);
        if (existingCard) {
            this.updateInfrastructureCard(infra, existingCard);
        } else {
            this.addInfrastructureCard(infra);
        }
        this.updateInfrastructureMarker(infra);
    }
    
    addInfrastructureCard(infra) {
        const infraList = document.getElementById('infrastructure-list');
        const card = document.createElement('div');
        card.className = 'infra-card';
        card.setAttribute('data-infra-id', infra.infrastructure_id);
        
        const state = infra.data.traffic_light_state;
        const remainingTime = infra.data.remaining_time;
        
        card.innerHTML = `
            <div class="infra-id">${infra.infrastructure_id}</div>
            <div class="infra-status">
                <span class="traffic-light ${state}"></span>
                <span>${state.toUpperCase()} (${remainingTime}s)</span>
            </div>
        `;
        
        infraList.appendChild(card);
    }
    
    updateInfrastructureCard(infra, card) {
        const state = infra.data.traffic_light_state;
        const remainingTime = infra.data.remaining_time;
        
        const statusElement = card.querySelector('.infra-status');
        statusElement.innerHTML = `
            <span class="traffic-light ${state}"></span>
            <span>${state.toUpperCase()} (${remainingTime}s)</span>
        `;
    }
    
    updateInfrastructureMarker(infra) {
        const lat = infra.position.lat;
        const lon = infra.position.lon;
        
        if (this.infrastructureMarkers[infra.infrastructure_id]) {
            this.map.removeLayer(this.infrastructureMarkers[infra.infrastructure_id]);
        }
        
        const state = infra.data.traffic_light_state;
        const icon = L.divIcon({
            className: 'infra-marker',
            html: `<div class="marker infra-marker-${state}">🚦</div>`,
            iconSize: [20, 20],
            iconAnchor: [10, 10]
        });
        
        const marker = L.marker([lat, lon], { icon }).addTo(this.map);
        marker.bindPopup(`
            <strong>${infra.infrastructure_id}</strong><br>
            State: ${state.toUpperCase()}<br>
            Remaining: ${infra.data.remaining_time}s
        `);
        
        this.infrastructureMarkers[infra.infrastructure_id] = marker;
    }
    
    updateEmergencies(emergencies) {
        const alertsList = document.getElementById('alerts-list');
        alertsList.innerHTML = '';
        
        emergencies.forEach(emergency => {
            this.addEmergencyAlert(emergency);
        });
    }
    
    addEmergencyAlert(emergency) {
        const alertsList = document.getElementById('alerts-list');
        const alert = document.createElement('div');
        alert.className = 'alert-card emergency';
        
        const time = new Date(emergency.timestamp).toLocaleTimeString();
        
        alert.innerHTML = `
            <div class="alert-header">
                <span class="alert-type">${emergency.event_type.toUpperCase()}</span>
                <span class="alert-time">${time}</span>
            </div>
            <div class="alert-message">
                Severity: ${emergency.severity}<br>
                Radius: ${emergency.radius}m<br>
                Duration: ${Math.round(emergency.duration / 60)}min
            </div>
        `;
        
        alertsList.insertBefore(alert, alertsList.firstChild);
        
        // Keep only last 10 alerts
        while (alertsList.children.length > 10) {
            alertsList.removeChild(alertsList.lastChild);
        }
    }
    
    addEmergencyMarker(emergency) {
        const lat = emergency.position.latitude;
        const lon = emergency.position.longitude;
        
        const icon = L.divIcon({
            className: 'emergency-marker',
            html: `<div class="marker emergency-marker">⚠️</div>`,
            iconSize: [25, 25],
            iconAnchor: [12, 12]
        });
        
        const marker = L.marker([lat, lon], { icon }).addTo(this.map);
        marker.bindPopup(`
            <strong>Emergency Alert</strong><br>
            Type: ${emergency.event_type}<br>
            Severity: ${emergency.severity}<br>
            Radius: ${emergency.radius}m
        `);
        
        // Remove marker after duration
        setTimeout(() => {
            this.map.removeLayer(marker);
        }, emergency.duration * 1000);
    }
    
    updateJobs(jobs) {
        const jobsList = document.getElementById('jobs-list');
        jobsList.innerHTML = '';
        
        Object.values(jobs).forEach(job => {
            this.addJobCard(job);
        });
    }
    
    addJobCard(job) {
        const jobsList = document.getElementById('jobs-list');
        const card = document.createElement('div');
        card.className = `job-card ${job.status}`;
        card.setAttribute('data-job-id', job.job_id);
        
        const time = new Date(job.timestamp).toLocaleTimeString();
        const responses = job.responses ? job.responses.length : 0;
        
        card.innerHTML = `
            <div class="job-header">
                <span class="job-id">${job.job_id}</span>
                <span class="job-type">${job.type}</span>
            </div>
            <div class="job-details">
                Time: ${time}<br>
                Targets: ${job.target_vehicles.join(', ')}<br>
                Responses: ${responses}
            </div>
        `;
        
        jobsList.insertBefore(card, jobsList.firstChild);
    }
    
    updateJobResponse(data) {
        const jobCard = document.querySelector(`[data-job-id="${data.job_id}"]`);
        if (jobCard) {
            const details = jobCard.querySelector('.job-details');
            const responses = data.response ? 1 : 0;
            details.innerHTML = details.innerHTML.replace(/Responses: \d+/, `Responses: ${responses}`);
        }
    }
    
    updateStatistics() {
        const vehicleCount = Object.keys(this.vehicleMarkers).length;
        const infraCount = Object.keys(this.infrastructureMarkers).length;
        const jobCount = document.querySelectorAll('.job-card').length;
        const emergencyCount = document.querySelectorAll('.alert-card').length;
        
        document.getElementById('vehicle-count').textContent = vehicleCount;
        document.getElementById('infra-count').textContent = infraCount;
        document.getElementById('job-count').textContent = jobCount;
        document.getElementById('emergency-count').textContent = emergencyCount;
    }
    
    showJobModal() {
        const modal = document.getElementById('job-modal');
        const vehicleCheckboxes = document.getElementById('vehicle-checkboxes');
        
        // Populate vehicle checkboxes
        vehicleCheckboxes.innerHTML = '';
        Object.keys(this.vehicleMarkers).forEach(vehicleId => {
            const checkbox = document.createElement('div');
            checkbox.className = 'vehicle-checkbox';
            checkbox.innerHTML = `
                <input type="checkbox" id="vehicle-${vehicleId}" value="${vehicleId}">
                <label for="vehicle-${vehicleId}">${vehicleId}</label>
            `;
            vehicleCheckboxes.appendChild(checkbox);
        });
        
        modal.style.display = 'block';
    }
    
    hideJobModal() {
        const modal = document.getElementById('job-modal');
        modal.style.display = 'none';
        document.getElementById('job-form').reset();
    }
    
    createJob() {
        const form = document.getElementById('job-form');
        const formData = new FormData(form);
        
        const jobType = formData.get('type');
        const parameters = formData.get('parameters');
        
        // Get selected vehicles
        const selectedVehicles = [];
        const checkboxes = document.querySelectorAll('#vehicle-checkboxes input[type="checkbox"]:checked');
        checkboxes.forEach(checkbox => {
            selectedVehicles.push(checkbox.value);
        });
        
        if (selectedVehicles.length === 0) {
            alert('Please select at least one vehicle');
            return;
        }
        
        // Parse parameters
        let parsedParameters = {};
        if (parameters.trim()) {
            try {
                parsedParameters = JSON.parse(parameters);
            } catch (e) {
                alert('Invalid JSON in parameters field');
                return;
            }
        }
        
        // Send job creation request
        fetch('/api/create_job', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                type: jobType,
                target_vehicles: selectedVehicles,
                parameters: parsedParameters
            })
        })
        .then(response => response.json())
        .then(data => {
            console.log('Job created:', data);
            this.hideJobModal();
            
            // Immediately add the job to the display
            const newJob = {
                job_id: data.job_id,
                type: jobType,
                timestamp: new Date().toISOString(),
                target_vehicles: selectedVehicles,
                parameters: parsedParameters,
                status: 'pending'
            };
            this.addJobCard(newJob);
            this.updateStatistics();
            
            // Also refresh jobs list from server
            setTimeout(() => {
                this.socket.emit('request_data');
            }, 500);
        })
        .catch(error => {
            console.error('Error creating job:', error);
            alert('Failed to create job');
        });
    }
}

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', () => {
    new Car2XDashboard();
});

// Add custom CSS for map markers
const style = document.createElement('style');
style.textContent = `
    .marker {
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 16px;
        border-radius: 50%;
        width: 30px;
        height: 30px;
        background: rgba(255, 255, 255, 0.9);
        border: 2px solid #3498db;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
    }
    
    .vehicle-marker-emergency {
        border-color: #e74c3c;
        background: rgba(231, 76, 60, 0.1);
    }
    
    .infra-marker-red {
        border-color: #e74c3c;
    }
    
    .infra-marker-yellow {
        border-color: #f39c12;
    }
    
    .infra-marker-green {
        border-color: #27ae60;
    }
    
    .emergency-marker {
        border-color: #e74c3c;
        background: rgba(231, 76, 60, 0.2);
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.1); }
        100% { transform: scale(1); }
    }
`;
document.head.appendChild(style);

