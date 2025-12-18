/**
 * WebSocket Client for Odin Bitcoin Trading Bot Dashboard
 *
 * Handles real-time communication with the server and prevents
 * browser crashes from WebSocket errors.
 */

class OdinWebSocket {
    constructor() {
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000; // Start with 1 second
        this.maxReconnectDelay = 30000; // Max 30 seconds
        this.isConnecting = false;
        this.isManuallyDisconnected = false;
        this.messageQueue = [];
        this.connectionTimeout = null;

        // Event callbacks
        this.onConnectionChange = null;
        this.onPriceUpdate = null;
        this.onPortfolioUpdate = null;
        this.onTradeSignal = null;
        this.onSystemAlert = null;

        this.init();
    }

    init() {
        console.log("🔌 Initializing WebSocket connection...");
        this.connect();
    }

    connect() {
        if (this.isConnecting || (this.ws && this.ws.readyState === WebSocket.CONNECTING)) {
            console.log("⏳ Connection already in progress...");
            return;
        }

        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            console.log("✅ WebSocket already connected");
            return;
        }

        this.isConnecting = true;

        try {
            // Clear any existing connection timeout
            if (this.connectionTimeout) {
                clearTimeout(this.connectionTimeout);
            }

            // Determine WebSocket URL
            const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
            const wsUrl = `${protocol}//${window.location.host}/ws`;

            console.log(`🔗 Connecting to WebSocket: ${wsUrl}`);

            // Set connection timeout
            this.connectionTimeout = setTimeout(() => {
                if (this.ws && this.ws.readyState === WebSocket.CONNECTING) {
                    console.warn("⏰ WebSocket connection timeout");
                    this.ws.close();
                    this.handleConnectionFailure();
                }
            }, 10000); // 10 second timeout

            this.ws = new WebSocket(wsUrl);
            this.setupEventHandlers();
        } catch (error) {
            console.error("❌ WebSocket connection error:", error);
            this.handleConnectionFailure();
        }
    }

    setupEventHandlers() {
        if (!this.ws) return;

        this.ws.onopen = (event) => {
            console.log("✅ WebSocket connected successfully");
            this.isConnecting = false;
            this.reconnectAttempts = 0;
            this.reconnectDelay = 1000;

            // Clear connection timeout
            if (this.connectionTimeout) {
                clearTimeout(this.connectionTimeout);
                this.connectionTimeout = null;
            }

            // Update connection status
            this.updateConnectionStatus("connected");

            // Send any queued messages
            this.sendQueuedMessages();

            // Request initial data
            this.requestInitialData();
        };

        this.ws.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data);
                this.handleMessage(message);
            } catch (error) {
                console.error("❌ Error parsing WebSocket message:", error);
            }
        };

        this.ws.onclose = (event) => {
            console.log(`🔌 WebSocket closed: Code ${event.code}, Reason: ${event.reason}`);
            this.isConnecting = false;

            // Clear connection timeout
            if (this.connectionTimeout) {
                clearTimeout(this.connectionTimeout);
                this.connectionTimeout = null;
            }

            // Update connection status
            this.updateConnectionStatus("disconnected");

            // Only attempt reconnection if not manually disconnected
            if (!this.isManuallyDisconnected) {
                this.scheduleReconnect();
            }
        };

        this.ws.onerror = (error) => {
            console.error("❌ WebSocket error:", error);
            this.handleConnectionFailure();
        };
    }

    handleConnectionFailure() {
        this.isConnecting = false;

        // Clear connection timeout
        if (this.connectionTimeout) {
            clearTimeout(this.connectionTimeout);
            this.connectionTimeout = null;
        }

        this.updateConnectionStatus("error");

        if (!this.isManuallyDisconnected) {
            this.scheduleReconnect();
        }
    }

    scheduleReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error("❌ Max reconnection attempts reached. Giving up.");
            this.updateConnectionStatus("failed");
            return;
        }

        this.reconnectAttempts++;
        const delay = Math.min(
            this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1),
            this.maxReconnectDelay,
        );

        console.log(
            `🔄 Scheduling reconnect attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts} in ${delay}ms`,
        );

        setTimeout(() => {
            if (!this.isManuallyDisconnected) {
                this.connect();
            }
        }, delay);
    }

    updateConnectionStatus(status) {
        const statusElement = document.getElementById("status-indicator");
        const statusText = document.getElementById("status-text");

        if (statusElement && statusText) {
            switch (status) {
                case "connected":
                    statusElement.className = "status-indicator connected";
                    statusText.textContent = "Connected";
                    break;
                case "connecting":
                    statusElement.className = "status-indicator connecting";
                    statusText.textContent = "Connecting...";
                    break;
                case "disconnected":
                    statusElement.className = "status-indicator disconnected";
                    statusText.textContent = "Disconnected";
                    break;
                case "error":
                    statusElement.className = "status-indicator error";
                    statusText.textContent = "Connection Error";
                    break;
                case "failed":
                    statusElement.className = "status-indicator failed";
                    statusText.textContent = "Connection Failed";
                    break;
            }
        }

        // Call connection change callback
        if (this.onConnectionChange) {
            this.onConnectionChange(status);
        }
    }

    handleMessage(message) {
        console.log("📨 Received message:", message.type);

        switch (message.type) {
            case "connection":
                console.log("🎉 Connection confirmed:", message.message);
                break;

            case "initial_data":
                this.handleInitialData(message.data);
                break;

            case "price_update":
                this.handlePriceUpdate(message.data);
                break;

            case "portfolio_update":
                this.handlePortfolioUpdate(message.data);
                break;

            case "trade_signal":
                this.handleTradeSignal(message.data);
                break;

            case "system_alert":
                this.handleSystemAlert(message.data);
                break;

            case "ping":
                // Respond to ping
                this.send({ type: "pong" });
                break;

            case "pong":
                // Server responded to our ping
                console.log("🏓 Pong received");
                break;

            default:
                console.log("❓ Unknown message type:", message.type);
        }
    }

    handleInitialData(data) {
        console.log("📊 Received initial data");

        if (data.bitcoin_price && this.onPriceUpdate) {
            this.onPriceUpdate(data.bitcoin_price);
        }
    }

    handlePriceUpdate(data) {
        if (this.onPriceUpdate) {
            this.onPriceUpdate(data);
        }
    }

    handlePortfolioUpdate(data) {
        if (this.onPortfolioUpdate) {
            this.onPortfolioUpdate(data);
        }
    }

    handleTradeSignal(data) {
        if (this.onTradeSignal) {
            this.onTradeSignal(data);
        }
    }

    handleSystemAlert(data) {
        if (this.onSystemAlert) {
            this.onSystemAlert(data);
        }
    }

    send(message) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            try {
                this.ws.send(JSON.stringify(message));
                return true;
            } catch (error) {
                console.error("❌ Error sending message:", error);
                return false;
            }
        } else {
            console.log("📤 Queueing message (not connected):", message);
            this.messageQueue.push(message);
            return false;
        }
    }

    sendQueuedMessages() {
        while (this.messageQueue.length > 0) {
            const message = this.messageQueue.shift();
            if (!this.send(message)) {
                // If send fails, put it back at the front of the queue
                this.messageQueue.unshift(message);
                break;
            }
        }
    }

    requestInitialData() {
        this.send({
            type: "request_data",
            request: "initial",
        });
    }

    requestPortfolioData() {
        this.send({
            type: "request_data",
            request: "portfolio",
        });
    }

    requestStrategyData() {
        this.send({
            type: "request_data",
            request: "strategies",
        });
    }

    requestHistoryData(hours = 24) {
        this.send({
            type: "request_data",
            request: "history",
            hours: hours,
        });
    }

    subscribe(channels) {
        this.send({
            type: "subscribe",
            channels: channels,
        });
    }

    ping() {
        this.send({ type: "ping" });
    }

    disconnect() {
        console.log("🔌 Manually disconnecting WebSocket");
        this.isManuallyDisconnected = true;

        if (this.ws) {
            this.ws.close(1000, "Manual disconnect");
        }
    }

    reconnect() {
        console.log("🔄 Manual reconnection requested");
        this.isManuallyDisconnected = false;
        this.reconnectAttempts = 0;
        this.connect();
    }

    getConnectionState() {
        if (!this.ws) return "not_initialized";

        switch (this.ws.readyState) {
            case WebSocket.CONNECTING:
                return "connecting";
            case WebSocket.OPEN:
                return "open";
            case WebSocket.CLOSING:
                return "closing";
            case WebSocket.CLOSED:
                return "closed";
            default:
                return "unknown";
        }
    }

    isConnected() {
        return this.ws && this.ws.readyState === WebSocket.OPEN;
    }
}

// Global WebSocket instance
let odinWebSocket = null;

// Initialize WebSocket when DOM is loaded
document.addEventListener("DOMContentLoaded", function () {
    // Wait a bit before initializing WebSocket to ensure page is fully loaded
    setTimeout(() => {
        initializeWebSocket();
    }, 1000);
});

function initializeWebSocket() {
    try {
        odinWebSocket = new OdinWebSocket();

        // Set up callbacks
        odinWebSocket.onConnectionChange = (status) => {
            console.log(`🔌 Connection status changed: ${status}`);

            // Handle connection status in UI
            if (status === "failed") {
                showNotification(
                    "WebSocket connection failed. Some features may not work.",
                    "error",
                );
            } else if (status === "connected") {
                showNotification("Connected to Odin Trading Bot", "success");
            }
        };

        odinWebSocket.onPriceUpdate = (data) => {
            // Update price display
            updatePriceDisplay(data);
        };

        odinWebSocket.onPortfolioUpdate = (data) => {
            // Update portfolio display
            updatePortfolioDisplay(data);
        };

        odinWebSocket.onTradeSignal = (data) => {
            // Show trading signal notification
            showNotification(`Trading Signal: ${data.signal} at $${data.price}`, "info");
        };

        odinWebSocket.onSystemAlert = (data) => {
            // Show system alert
            showNotification(data.message, data.level || "warning");
        };

        console.log("✅ WebSocket initialized successfully");
    } catch (error) {
        console.error("❌ Failed to initialize WebSocket:", error);
        showNotification("Failed to initialize real-time connection", "error");
    }
}

// Helper functions for UI updates
function updatePriceDisplay(data) {
    const priceElement = document.getElementById("bitcoin-price");
    const changeElement = document.getElementById("price-change");
    const timestampElement = document.getElementById("price-timestamp");

    if (priceElement && data.price) {
        priceElement.textContent = `$${Number(data.price).toLocaleString("en-US", {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        })}`;
    }

    if (changeElement && data.change_24h) {
        const change = Number(data.change_24h);
        changeElement.textContent = `${change > 0 ? "+" : ""}${change.toFixed(2)}%`;
        changeElement.className = `stat-change ${change >= 0 ? "positive" : "negative"}`;
    }

    if (timestampElement) {
        const timestamp = data.timestamp ? new Date(data.timestamp * 1000) : new Date();
        timestampElement.textContent = `Last updated: ${timestamp.toLocaleTimeString()}`;
    }
}

function updatePortfolioDisplay(data) {
    const valueElement = document.getElementById("portfolio-value");
    const changeElement = document.getElementById("portfolio-change");
    const pnlElement = document.getElementById("daily-pnl");

    if (valueElement && data.total_value) {
        valueElement.textContent = `$${Number(data.total_value).toLocaleString("en-US", {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        })}`;
    }

    if (changeElement && data.daily_pnl_percent) {
        const change = Number(data.daily_pnl_percent);
        changeElement.textContent = `${change > 0 ? "+" : ""}${change.toFixed(2)}%`;
        changeElement.className = `stat-change ${change >= 0 ? "positive" : "negative"}`;
    }

    if (pnlElement && data.daily_pnl) {
        const pnl = Number(data.daily_pnl);
        pnlElement.textContent = `${pnl > 0 ? "+" : ""}$${Math.abs(pnl).toFixed(2)}`;
        pnlElement.className = `stat-value ${pnl >= 0 ? "positive" : "negative"}`;
    }
}

function showNotification(message, type = "info") {
    // Create notification element
    const notification = document.createElement("div");
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <span class="notification-message">${message}</span>
        <button class="notification-close">&times;</button>
    `;

    // Add to container
    const container = document.getElementById("notification-container");
    if (container) {
        container.appendChild(notification);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);

        // Add close button functionality
        const closeBtn = notification.querySelector(".notification-close");
        if (closeBtn) {
            closeBtn.addEventListener("click", () => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            });
        }
    }
}

// Export WebSocket instance for use by other scripts
window.OdinWebSocket = OdinWebSocket;
window.odinWebSocket = odinWebSocket;
