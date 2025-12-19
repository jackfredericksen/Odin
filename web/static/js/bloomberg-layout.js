/**
 * Bloomberg Layout Manager
 * Handles resizable panels, collapsible sections, and layout persistence
 */

class BloombergLayout {
    constructor() {
        this.panels = {
            left: {
                element: null,
                width: 280,
                minWidth: 200,
                maxWidth: 400,
                collapsed: false
            },
            right: {
                element: null,
                width: 320,
                minWidth: 250,
                maxWidth: 500,
                collapsed: false
            },
            bottom: {
                element: null,
                height: 400,
                minHeight: 200,
                maxHeight: 600,
                collapsed: false
            }
        };

        this.isDragging = false;
        this.currentResizer = null;

        // Load saved panel sizes from localStorage
        this.loadPanelSizes();
    }

    /**
     * Initialize the Bloomberg layout
     */
    init() {
        console.log('📐 Initializing Bloomberg Layout...');

        // Get panel elements
        this.panels.left.element = document.getElementById('left-panel');
        this.panels.right.element = document.getElementById('right-panel');
        this.panels.bottom.element = document.getElementById('bottom-panel');

        // Apply saved panel sizes
        this.applyPanelSizes();

        // Initialize resizers
        this.initResizers();

        // Initialize keyboard shortcuts
        this.initKeyboardShortcuts();

        // Initialize panel toggles
        this.initPanelToggles();

        console.log('✅ Bloomberg Layout initialized');
    }

    /**
     * Initialize resizable panels
     */
    initResizers() {
        // Left panel resizer
        const leftResizer = document.getElementById('left-resizer');
        if (leftResizer) {
            this.initHorizontalResizer(leftResizer, 'left');
        }

        // Right panel resizer
        const rightResizer = document.getElementById('right-resizer');
        if (rightResizer) {
            this.initHorizontalResizer(rightResizer, 'right');
        }

        // Bottom panel resizer
        const bottomResizer = document.getElementById('bottom-resizer');
        if (bottomResizer) {
            this.initVerticalResizer(bottomResizer, 'bottom');
        }
    }

    /**
     * Initialize horizontal resizer (for left/right panels)
     */
    initHorizontalResizer(resizer, panelName) {
        resizer.addEventListener('mousedown', (e) => {
            e.preventDefault();
            this.isDragging = true;
            this.currentResizer = panelName;
            document.body.style.cursor = 'col-resize';
            document.body.style.userSelect = 'none';
        });

        document.addEventListener('mousemove', (e) => {
            if (!this.isDragging || this.currentResizer !== panelName) return;

            const panel = this.panels[panelName];
            if (!panel.element) return;

            let newWidth;
            if (panelName === 'left') {
                newWidth = e.clientX;
            } else if (panelName === 'right') {
                newWidth = window.innerWidth - e.clientX;
            }

            // Constrain to min/max
            newWidth = Math.max(panel.minWidth, Math.min(panel.maxWidth, newWidth));

            // Apply new width
            panel.width = newWidth;
            panel.element.style.width = `${newWidth}px`;

            // Save to localStorage
            this.savePanelSizes();
        });

        document.addEventListener('mouseup', () => {
            if (this.isDragging) {
                this.isDragging = false;
                this.currentResizer = null;
                document.body.style.cursor = '';
                document.body.style.userSelect = '';
            }
        });
    }

    /**
     * Initialize vertical resizer (for bottom panel)
     */
    initVerticalResizer(resizer, panelName) {
        resizer.addEventListener('mousedown', (e) => {
            e.preventDefault();
            this.isDragging = true;
            this.currentResizer = panelName;
            document.body.style.cursor = 'row-resize';
            document.body.style.userSelect = 'none';
        });

        document.addEventListener('mousemove', (e) => {
            if (!this.isDragging || this.currentResizer !== panelName) return;

            const panel = this.panels[panelName];
            if (!panel.element) return;

            const newHeight = window.innerHeight - e.clientY;

            // Constrain to min/max
            const constrainedHeight = Math.max(
                panel.minHeight,
                Math.min(panel.maxHeight, newHeight)
            );

            // Apply new height
            panel.height = constrainedHeight;
            panel.element.style.height = `${constrainedHeight}px`;

            // Save to localStorage
            this.savePanelSizes();
        });

        document.addEventListener('mouseup', () => {
            if (this.isDragging) {
                this.isDragging = false;
                this.currentResizer = null;
                document.body.style.cursor = '';
                document.body.style.userSelect = '';
            }
        });
    }

    /**
     * Toggle panel visibility
     */
    togglePanel(panelName) {
        const panel = this.panels[panelName];
        if (!panel || !panel.element) return;

        panel.collapsed = !panel.collapsed;

        if (panel.collapsed) {
            panel.element.classList.add('collapsed');
            if (panelName === 'bottom') {
                panel.element.style.height = '0px';
            } else {
                panel.element.style.width = '0px';
            }
        } else {
            panel.element.classList.remove('collapsed');
            if (panelName === 'bottom') {
                panel.element.style.height = `${panel.height}px`;
            } else {
                panel.element.style.width = `${panel.width}px`;
            }
        }

        // Update toggle button icon
        this.updateToggleIcon(panelName);

        // Save state
        this.savePanelSizes();

        // Dispatch resize event for charts to redraw
        window.dispatchEvent(new Event('resize'));
    }

    /**
     * Update toggle button icon based on panel state
     */
    updateToggleIcon(panelName) {
        const button = document.getElementById(`toggle-${panelName}-panel`);
        if (!button) return;

        const panel = this.panels[panelName];
        const icons = {
            left: { collapsed: '▶', expanded: '◀' },
            right: { collapsed: '◀', expanded: '▶' },
            bottom: { collapsed: '▲', expanded: '▼' }
        };

        const icon = panel.collapsed ? icons[panelName].collapsed : icons[panelName].expanded;
        button.textContent = icon;
        button.setAttribute('aria-label', panel.collapsed ? `Expand ${panelName} panel` : `Collapse ${panelName} panel`);
    }

    /**
     * Initialize panel toggle buttons
     */
    initPanelToggles() {
        ['left', 'right', 'bottom'].forEach(panelName => {
            const button = document.getElementById(`toggle-${panelName}-panel`);
            if (button) {
                button.addEventListener('click', () => this.togglePanel(panelName));
                this.updateToggleIcon(panelName);
            }
        });
    }

    /**
     * Initialize keyboard shortcuts
     */
    initKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl+1: Toggle left panel
            if (e.ctrlKey && e.key === '1') {
                e.preventDefault();
                this.togglePanel('left');
            }

            // Ctrl+2: Toggle right panel
            if (e.ctrlKey && e.key === '2') {
                e.preventDefault();
                this.togglePanel('right');
            }

            // Ctrl+3: Toggle bottom panel
            if (e.ctrlKey && e.key === '3') {
                e.preventDefault();
                this.togglePanel('bottom');
            }

            // Ctrl+R: Refresh all data
            if (e.ctrlKey && e.key === 'r') {
                e.preventDefault();
                if (window.dashboard && typeof window.dashboard.loadAllData === 'function') {
                    window.dashboard.loadAllData();
                }
            }
        });
    }

    /**
     * Apply saved panel sizes
     */
    applyPanelSizes() {
        Object.keys(this.panels).forEach(panelName => {
            const panel = this.panels[panelName];
            if (!panel.element) return;

            if (panelName === 'bottom') {
                panel.element.style.height = panel.collapsed ? '0px' : `${panel.height}px`;
            } else {
                panel.element.style.width = panel.collapsed ? '0px' : `${panel.width}px`;
            }

            if (panel.collapsed) {
                panel.element.classList.add('collapsed');
            }
        });
    }

    /**
     * Save panel sizes to localStorage
     */
    savePanelSizes() {
        const sizes = {};
        Object.keys(this.panels).forEach(panelName => {
            const panel = this.panels[panelName];
            sizes[panelName] = {
                width: panel.width,
                height: panel.height,
                collapsed: panel.collapsed
            };
        });
        localStorage.setItem('bloomberg-panel-sizes', JSON.stringify(sizes));
    }

    /**
     * Load panel sizes from localStorage
     */
    loadPanelSizes() {
        const saved = localStorage.getItem('bloomberg-panel-sizes');
        if (!saved) return;

        try {
            const sizes = JSON.parse(saved);
            Object.keys(sizes).forEach(panelName => {
                if (this.panels[panelName]) {
                    this.panels[panelName].width = sizes[panelName].width || this.panels[panelName].width;
                    this.panels[panelName].height = sizes[panelName].height || this.panels[panelName].height;
                    this.panels[panelName].collapsed = sizes[panelName].collapsed || false;
                }
            });
        } catch (e) {
            console.warn('⚠️ Failed to load saved panel sizes:', e);
        }
    }

    /**
     * Reset panels to default sizes
     */
    resetPanels() {
        this.panels.left.width = 280;
        this.panels.right.width = 320;
        this.panels.bottom.height = 400;
        this.panels.left.collapsed = false;
        this.panels.right.collapsed = false;
        this.panels.bottom.collapsed = false;

        this.applyPanelSizes();
        this.savePanelSizes();

        Object.keys(this.panels).forEach(panelName => {
            this.updateToggleIcon(panelName);
        });

        window.dispatchEvent(new Event('resize'));
    }

    /**
     * Get current layout state
     */
    getState() {
        const state = {};
        Object.keys(this.panels).forEach(panelName => {
            state[panelName] = {
                width: this.panels[panelName].width,
                height: this.panels[panelName].height,
                collapsed: this.panels[panelName].collapsed
            };
        });
        return state;
    }
}

// Auto-initialize on window load
if (typeof window !== 'undefined') {
    window.BloombergLayout = BloombergLayout;
}
