/**
 * WebSocket Manager for Real-Time Updates
 * Handles connections, reconnection, and message routing
 */

class WebSocketManager {
    constructor(options = {}) {
        this.baseUrl = options.baseUrl || (window.location.protocol === 'https:' ? 'wss:' : 'ws:');
        this.reconnectInterval = options.reconnectInterval || 3000;
        this.maxReconnectAttempts = options.maxReconnectAttempts || 5;
        this.heartbeatInterval = options.heartbeatInterval || 30000;

        this.connections = new Map();
        this.messageHandlers = new Map();
        this.reconnectAttempts = new Map();
        this.heartbeatTimers = new Map();

        this.callbacks = {
            onConnect: options.onConnect || (() => { }),
            onDisconnect: options.onDisconnect || (() => { }),
            onError: options.onError || (() => { }),
            onMessage: options.onMessage || (() => { })
        };
    }

    /**
     * Connect to a WebSocket endpoint
     * @param {string} endpoint - WebSocket endpoint path
     * @param {string} id - Unique connection ID
     * @param {object} handlers - Message type handlers
     */
    connect(endpoint, id, handlers = {}) {
        if (this.connections.has(id)) {
            console.warn(`Connection ${id} already exists`);
            return this.connections.get(id);
        }

        const url = `${this.baseUrl}//${window.location.host}${endpoint}`;
        console.log(`[WebSocket] Connecting to ${id}:`, url);

        const ws = new WebSocket(url);

        ws.onopen = () => this.handleOpen(id, ws);
        ws.onmessage = (event) => this.handleMessage(id, event, handlers);
        ws.onclose = () => this.handleClose(id, endpoint);
        ws.onerror = (error) => this.handleError(id, error);

        this.connections.set(id, ws);
        this.messageHandlers.set(id, handlers);

        return ws;
    }

    /**
     * Handle WebSocket open event
     */
    handleOpen(id, ws) {
        console.log(`[WebSocket] Connected: ${id}`);
        this.reconnectAttempts.delete(id);

        // Start heartbeat
        this.startHeartbeat(id);

        // Call callback
        this.callbacks.onConnect(id);
    }

    /**
     * Handle incoming WebSocket message
     */
    handleMessage(id, event, handlers) {
        try {
            const data = JSON.parse(event.data);
            const messageType = data.type;

            console.log(`[WebSocket] Message from ${id}:`, messageType, data);

            // Call type-specific handler if registered
            if (handlers[messageType]) {
                handlers[messageType](data);
            }

            // Call generic message handler
            this.callbacks.onMessage(id, data);

        } catch (error) {
            console.error(`[WebSocket] Failed to parse message from ${id}:`, error);
        }
    }

    /**
     * Handle WebSocket close event
     */
    handleClose(id, endpoint) {
        console.log(`[WebSocket] Disconnected: ${id}`);

        // Clear heartbeat
        this.clearHeartbeat(id);

        // Attempt reconnection
        this.attemptReconnect(id, endpoint);

        // Call callback
        this.callbacks.onDisconnect(id);
    }

    /**
     * Handle WebSocket error
     */
    handleError(id, error) {
        console.error(`[WebSocket] Error in ${id}:`, error);
        this.callbacks.onError(id, error);
    }

    /**
     * Attempt to reconnect to WebSocket
     */
    attemptReconnect(id, endpoint) {
        const attempts = this.reconnectAttempts.get(id) || 0;

        if (attempts >= this.maxReconnectAttempts) {
            console.error(`[WebSocket] Max reconnect attempts reached for ${id}`);
            return;
        }

        const delay = this.reconnectInterval * Math.pow(2, attempts);
        console.log(`[WebSocket] Reconnecting ${id} in ${delay}ms (attempt ${attempts + 1})`);

        setTimeout(() => {
            this.reconnectAttempts.set(id, attempts + 1);
            this.connections.delete(id);
            this.connect(endpoint, id, this.messageHandlers.get(id) || {});
        }, delay);
    }

    /**
     * Start heartbeat for connection
     */
    startHeartbeat(id) {
        this.clearHeartbeat(id);

        const timer = setInterval(() => {
            const ws = this.connections.get(id);
            if (ws && ws.readyState === WebSocket.OPEN) {
                // Send ping
                ws.send(JSON.stringify({ type: 'ping' }));
            }
        }, this.heartbeatInterval);

        this.heartbeatTimers.set(id, timer);
    }

    /**
     * Clear heartbeat timer
     */
    clearHeartbeat(id) {
        const timer = this.heartbeatTimers.get(id);
        if (timer) {
            clearInterval(timer);
            this.heartbeatTimers.delete(id);
        }
    }

    /**
     * Send message to WebSocket
     */
    send(id, data) {
        const ws = this.connections.get(id);

        if (!ws) {
            console.warn(`[WebSocket] Connection ${id} not found`);
            return false;
        }

        if (ws.readyState !== WebSocket.OPEN) {
            console.warn(`[WebSocket] Connection ${id} is not open`);
            return false;
        }

        try {
            ws.send(JSON.stringify(data));
            return true;
        } catch (error) {
            console.error(`[WebSocket] Failed to send message to ${id}:`, error);
            return false;
        }
    }

    /**
     * Disconnect from WebSocket
     */
    disconnect(id) {
        const ws = this.connections.get(id);

        if (ws) {
            this.clearHeartbeat(id);
            ws.close(1000, 'Client closing connection');
            this.connections.delete(id);
            this.messageHandlers.delete(id);
            this.reconnectAttempts.delete(id);
        }
    }

    /**
     * Disconnect all connections
     */
    disconnectAll() {
        for (const [id] of this.connections) {
            this.disconnect(id);
        }
    }

    /**
     * Get connection status
     */
    isConnected(id) {
        const ws = this.connections.get(id);
        return ws && ws.readyState === WebSocket.OPEN;
    }

    /**
     * Get all connection statuses
     */
    getStatus() {
        const status = {};
        for (const [id, ws] of this.connections) {
            status[id] = {
                connected: ws.readyState === WebSocket.OPEN,
                readyState: ws.readyState,
                url: ws.url
            };
        }
        return status;
    }
}

/**
 * Screening Progress Monitor
 * Monitors real-time screening progress via WebSocket
 */
class ScreeningProgressMonitor {
    constructor(screeningId, options = {}) {
        this.screeningId = screeningId;
        this.wsManager = options.wsManager || new WebSocketManager();
        this.containerId = options.containerId || 'screening-progress';
        this.autoUpdate = options.autoUpdate !== false;

        this.handlers = {
            progress_update: (data) => this.handleProgressUpdate(data),
            screening_state: (data) => this.handleScreeningState(data),
            screening_complete: (data) => this.handleScreeningComplete(data),
            screening_error: (data) => this.handleScreeningError(data)
        };
    }

    /**
     * Start monitoring screening progress
     */
    start() {
        const endpoint = `/ws/screening/${this.screeningId}/`;
        this.wsManager.connect(endpoint, `screening_${this.screeningId}`, this.handlers);
        console.log(`[Screening Monitor] Started for ${this.screeningId}`);
    }

    /**
     * Stop monitoring
     */
    stop() {
        this.wsManager.disconnect(`screening_${this.screeningId}`);
        console.log(`[Screening Monitor] Stopped for ${this.screeningId}`);
    }

    /**
     * Request refresh of screening state
     */
    requestRefresh() {
        this.wsManager.send(`screening_${this.screeningId}`, {
            type: 'request_refresh'
        });
    }

    /**
     * Handle progress update
     */
    handleProgressUpdate(data) {
        console.log('[Progress Update]:', data);
        this.updateUI(data);

        // Dispatch custom event for other listeners
        window.dispatchEvent(new CustomEvent('screening_progress', { detail: data }));
    }

    /**
     * Handle initial screening state
     */
    handleScreeningState(data) {
        console.log('[Screening State]:', data.data);
        this.renderScreeningState(data.data);
    }

    /**
     * Handle screening completion
     */
    handleScreeningComplete(data) {
        console.log('[Screening Complete]:', data);
        this.showCompletion(data);
        window.dispatchEvent(new CustomEvent('screening_complete', { detail: data }));
    }

    /**
     * Handle screening error
     */
    handleScreeningError(data) {
        console.error('[Screening Error]:', data.message);
        this.showError(data.message);
        window.dispatchEvent(new CustomEvent('screening_error', { detail: data }));
    }

    /**
     * Update progress UI
     */
    updateUI(data) {
        const container = document.getElementById(this.containerId);
        if (!container) return;

        // Update progress bar
        if (data.progress !== undefined) {
            const progressBar = container.querySelector('.progress-bar');
            if (progressBar) {
                progressBar.style.width = `${data.progress}%`;
                progressBar.setAttribute('aria-valuenow', data.progress);
            }
        }

        // Add event to log
        const eventLog = container.querySelector('.event-log');
        if (eventLog) {
            const eventEl = document.createElement('div');
            eventEl.className = 'event-item';
            eventEl.innerHTML = `
                <span class="event-time">${new Date(data.timestamp).toLocaleTimeString()}</span>
                <span class="event-description">${data.description}</span>
            `;
            eventLog.insertBefore(eventEl, eventLog.firstChild);

            // Keep only last 20 events
            while (eventLog.children.length > 20) {
                eventLog.removeChild(eventLog.lastChild);
            }
        }
    }

    /**
     * Render initial screening state
     */
    renderScreeningState(state) {
        const container = document.getElementById(this.containerId);
        if (!container) return;

        container.innerHTML = `
            <div class="screening-state">
                <h3>${state.job_title}</h3>
                <div class="progress">
                    <div class="progress-bar" role="progressbar" style="width: 0%"></div>
                </div>
                <div class="event-log"></div>
            </div>
        `;
    }

    /**
     * Show completion message
     */
    showCompletion(data) {
        const container = document.getElementById(this.containerId);
        if (!container) return;

        const alertEl = document.createElement('div');
        alertEl.className = 'alert alert-success';
        alertEl.innerHTML = `
            <h4>Screening Complete</h4>
            <p>Screening has finished successfully.</p>
        `;
        container.appendChild(alertEl);
    }

    /**
     * Show error message
     */
    showError(message) {
        const container = document.getElementById(this.containerId);
        if (!container) return;

        const alertEl = document.createElement('div');
        alertEl.className = 'alert alert-danger';
        alertEl.innerHTML = `
            <h4>Error</h4>
            <p>${message}</p>
        `;
        container.appendChild(alertEl);
    }
}

/**
 * Notification Manager
 * Receives and displays real-time notifications
 */
class NotificationManager {
    constructor(options = {}) {
        this.wsManager = options.wsManager || new WebSocketManager();
        this.position = options.position || 'top-right';
        this.duration = options.duration || 5000;
        this.maxNotifications = options.maxNotifications || 5;

        this.notifications = [];
        this.handlers = {
            notification: (data) => this.showNotification(data),
            application_screened: (data) => this.handleApplicationScreened(data),
            screening_started: (data) => this.handleScreeningStarted(data)
        };
    }

    /**
     * Start notification listener
     */
    start() {
        this.wsManager.connect('/ws/notifications/', 'notifications', this.handlers);
        console.log('[Notification Manager] Started');
    }

    /**
     * Show notification
     */
    showNotification(data) {
        const notification = {
            id: `notif_${Date.now()}`,
            title: data.title,
            message: data.message,
            level: data.level || 'info',
            timestamp: new Date()
        };

        this.notifications.push(notification);
        this.render(notification);

        // Auto-remove after duration
        setTimeout(() => this.removeNotification(notification.id), this.duration);

        // Keep only max notifications
        if (this.notifications.length > this.maxNotifications) {
            const old = this.notifications.shift();
            document.getElementById(old.id)?.remove();
        }
    }

    /**
     * Handle application screened notification
     */
    handleApplicationScreened(data) {
        this.showNotification({
            title: 'Application Screened',
            message: `${data.candidate_name} (Score: ${data.score})`,
            level: 'success'
        });
    }

    /**
     * Handle screening started notification
     */
    handleScreeningStarted(data) {
        this.showNotification({
            title: 'Screening Started',
            message: `Screening started for: ${data.job_title}`,
            level: 'info'
        });
    }

    /**
     * Remove notification
     */
    removeNotification(id) {
        this.notifications = this.notifications.filter(n => n.id !== id);
        document.getElementById(id)?.remove();
    }

    /**
     * Render notification
     */
    render(notification) {
        const container = document.getElementById('notification-container') || this.createContainer();

        const el = document.createElement('div');
        el.id = notification.id;
        el.className = `alert alert-${notification.level} notification`;
        el.innerHTML = `
            <strong>${notification.title}</strong>
            <p>${notification.message}</p>
            <button type="button" class="close" data-dismiss="alert">&times;</button>
        `;

        el.querySelector('.close')?.addEventListener('click', () => {
            this.removeNotification(notification.id);
        });

        container.appendChild(el);
    }

    /**
     * Create notification container
     */
    createContainer() {
        const container = document.createElement('div');
        container.id = 'notification-container';
        container.className = `notifications notifications-${this.position}`;
        document.body.appendChild(container);
        return container;
    }
}

// Export classes for use in templates
window.WebSocketManager = WebSocketManager;
window.ScreeningProgressMonitor = ScreeningProgressMonitor;
window.NotificationManager = NotificationManager;
