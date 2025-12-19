/**
 * Section Manager - Handles tab-based navigation between dashboard sections
 * Sections: Price & Market, Charts & Analytics, Social Intelligence, Trading Journal
 */

class SectionManager {
    constructor() {
        this.sections = ['price', 'charts', 'social', 'journal'];
        this.activeSection = 'price'; // Default section
        this.sectionData = {};
        this.lazyLoaded = {
            price: false,
            charts: false,
            social: false,
            journal: false
        };
    }

    /**
     * Initialize section manager
     */
    init() {
        console.log('📑 Initializing Section Manager...');

        // Attach tab click handlers
        this.attachTabHandlers();

        // Keyboard shortcuts
        this.initKeyboardShortcuts();

        // Load initial section (Price & Market)
        this.switchSection('price');

        console.log('✅ Section Manager initialized');
    }

    /**
     * Attach click handlers to tab buttons
     */
    attachTabHandlers() {
        const tabs = document.querySelectorAll('[data-section-tab]');

        tabs.forEach(tab => {
            tab.addEventListener('click', (e) => {
                e.preventDefault();
                const section = tab.dataset.sectionTab;
                this.switchSection(section);
            });
        });
    }

    /**
     * Initialize keyboard shortcuts for section switching
     */
    initKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Alt+1: Price & Market
            if (e.altKey && e.key === '1') {
                e.preventDefault();
                this.switchSection('price');
            }

            // Alt+2: Charts & Analytics
            if (e.altKey && e.key === '2') {
                e.preventDefault();
                this.switchSection('charts');
            }

            // Alt+3: Social Intelligence
            if (e.altKey && e.key === '3') {
                e.preventDefault();
                this.switchSection('social');
            }

            // Alt+4: Trading Journal
            if (e.altKey && e.key === '4') {
                e.preventDefault();
                this.switchSection('journal');
            }
        });
    }

    /**
     * Switch to a different section
     */
    switchSection(sectionName) {
        if (!this.sections.includes(sectionName)) {
            console.warn(`⚠️ Invalid section: ${sectionName}`);
            return;
        }

        console.log(`🔄 Switching to section: ${sectionName}`);

        // Update active section
        this.activeSection = sectionName;

        // Update tab active states
        this.updateTabStates(sectionName);

        // Hide all sections
        this.sections.forEach(section => {
            const sectionEl = document.getElementById(`section-${section}`);
            if (sectionEl) {
                sectionEl.classList.remove('active');
                sectionEl.style.display = 'none';
            }
        });

        // Show active section
        const activeSectionEl = document.getElementById(`section-${sectionName}`);
        if (activeSectionEl) {
            activeSectionEl.classList.add('active');
            activeSectionEl.style.display = 'block';
        }

        // Lazy load section data if not loaded yet
        if (!this.lazyLoaded[sectionName]) {
            this.loadSectionData(sectionName);
            this.lazyLoaded[sectionName] = true;
        } else {
            // Refresh section data
            this.refreshSectionData(sectionName);
        }

        // Save preference to localStorage
        localStorage.setItem('odin-active-section', sectionName);

        // Dispatch event for other components
        document.dispatchEvent(new CustomEvent('section-changed', {
            detail: { section: sectionName }
        }));
    }

    /**
     * Update tab button active states
     */
    updateTabStates(activeSectionName) {
        const tabs = document.querySelectorAll('[data-section-tab]');

        tabs.forEach(tab => {
            if (tab.dataset.sectionTab === activeSectionName) {
                tab.classList.add('active');
            } else {
                tab.classList.remove('active');
            }
        });
    }

    /**
     * Load section data (first time)
     */
    async loadSectionData(sectionName) {
        console.log(`📥 Loading data for section: ${sectionName}`);

        try {
            switch (sectionName) {
                case 'price':
                    await this.loadPriceSection();
                    break;
                case 'charts':
                    await this.loadChartsSection();
                    break;
                case 'social':
                    await this.loadSocialSection();
                    break;
                case 'journal':
                    await this.loadJournalSection();
                    break;
            }
        } catch (error) {
            console.error(`❌ Error loading ${sectionName} section:`, error);
        }
    }

    /**
     * Refresh section data (already loaded)
     */
    async refreshSectionData(sectionName) {
        // Only refresh if section is active for more than 30 seconds
        const now = Date.now();
        const lastRefresh = this.sectionData[sectionName]?.lastRefresh || 0;

        if (now - lastRefresh > 30000) { // 30 seconds
            await this.loadSectionData(sectionName);
        }
    }

    /**
     * Load Price & Market section
     */
    async loadPriceSection() {
        console.log('📊 Loading Price & Market data...');

        if (window.dashboard) {
            // Use existing dashboard methods
            await Promise.allSettled([
                window.dashboard.loadBitcoinPrice(),
                window.dashboard.loadMarketDepth(),
                window.dashboard.loadIndicators()
            ]);
        }

        this.sectionData.price = {
            lastRefresh: Date.now(),
            loaded: true
        };
    }

    /**
     * Load Charts & Analytics section
     */
    async loadChartsSection() {
        console.log('📈 Loading Charts & Analytics data...');

        if (window.dashboard) {
            await Promise.allSettled([
                window.dashboard.loadPriceHistory(),
                window.dashboard.loadIndicators(),
                window.dashboard.calculateSupportResistance(),
                window.dashboard.calculateFibonacci(),
                window.dashboard.detectPatterns()
            ]);
        }

        this.sectionData.charts = {
            lastRefresh: Date.now(),
            loaded: true
        };
    }

    /**
     * Load Social Intelligence section
     */
    async loadSocialSection() {
        console.log('🌐 Loading Social Intelligence data...');

        // Initialize Social Intelligence module if not already initialized
        if (!window.socialIntelligence && window.SocialIntelligence) {
            window.socialIntelligence = new SocialIntelligence();
            await window.socialIntelligence.init();
        } else if (window.socialIntelligence) {
            // Refresh data if already initialized
            await window.socialIntelligence.loadAllData();
        }

        this.sectionData.social = {
            lastRefresh: Date.now(),
            loaded: true
        };
    }

    /**
     * Load Trading Journal section
     */
    async loadJournalSection() {
        console.log('📝 Loading Trading Journal data...');

        // Initialize Trading Journal module if not already initialized
        if (!window.tradingJournal && window.TradingJournal) {
            window.tradingJournal = new TradingJournal();
            await window.tradingJournal.init();
        } else if (window.tradingJournal) {
            // Refresh data if already initialized
            await window.tradingJournal.loadAllData();
        }

        this.sectionData.journal = {
            lastRefresh: Date.now(),
            loaded: true
        };
    }

    /**
     * Get active section name
     */
    getActiveSection() {
        return this.activeSection;
    }

    /**
     * Check if section is loaded
     */
    isSectionLoaded(sectionName) {
        return this.lazyLoaded[sectionName] || false;
    }

    /**
     * Get section data
     */
    getSectionData(sectionName) {
        return this.sectionData[sectionName] || null;
    }

    /**
     * Restore last active section from localStorage
     */
    restoreLastSection() {
        const lastSection = localStorage.getItem('odin-active-section');
        if (lastSection && this.sections.includes(lastSection)) {
            this.switchSection(lastSection);
        }
    }
}

// Auto-initialize on window load
if (typeof window !== 'undefined') {
    window.SectionManager = SectionManager;
}
