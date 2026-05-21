/**
 * Timeshare Deal Portal - Frontend Controller
 * Fetches scanned listings from deals.json, manages dashboard stats,
 * and implements real-time search, filters, and high-fidelity sorting.
 */

// Fallback high-fidelity dataset in case deals.json is missing during initial load
const FALLBACK_DEALS = [
    {
        "resort": "Westin Kaanapali Ocean Resort Villas",
        "unit_type": "2 Bedroom, 2 Bath (Lockoff)",
        "view": "Ocean View",
        "check_in": "2026-07-04",
        "nights": 7,
        "listing_price": 2400.0,
        "listing_id": "TUG-9021",
        "platform": "TUG Classifieds",
        "link": "https://tug2.com/timesharemarketplace/search?KeyWord=Westin+Kaanapali+Ocean+Resort+Villas",
        "owner": "MauiTraveler88",
        "location": "Maui, Hawaii",
        "brand": "Westin",
        "retail_per_night": 850.0,
        "total_retail": 5950.0,
        "price_per_night": 342.86,
        "total_savings": 3550.0,
        "savings_pct": 59.7,
        "score": 94.7,
        "grade": "A",
        "class": "great-deal",
        "notes": "Beautiful resort right on Kaanapali Beach. Lockoff feature gives two separate entries."
    },
    {
        "resort": "Marriott's Maui Ocean Club",
        "unit_type": "1 Bedroom Suite, 2 Bath",
        "view": "Oceanfront",
        "check_in": "2026-07-19",
        "nights": 7,
        "listing_price": 2100.0,
        "listing_id": "TUG-4402",
        "platform": "TUG Classifieds",
        "link": "https://tug2.com/timesharemarketplace/search?KeyWord=Marriott%27s+Maui+Ocean+Club",
        "owner": "AlohaSpirit",
        "location": "Maui, Hawaii",
        "brand": "Marriott",
        "retail_per_night": 750.0,
        "total_retail": 5250.0,
        "price_per_night": 300.0,
        "total_savings": 3150.0,
        "savings_pct": 60.0,
        "score": 95.0,
        "grade": "A+",
        "class": "super-deal",
        "notes": "Premium oceanfront unit in the Lahaina tower. Full access to main pool and amenities."
    },
    {
        "resort": "Disney's Aulani Resort & Spa",
        "unit_type": "2 Bedroom Villa",
        "view": "Island Garden View",
        "check_in": "2026-08-18",
        "nights": 6,
        "listing_price": 2900.0,
        "listing_id": "TUG-1108",
        "platform": "TUG Classifieds",
        "link": "https://tug2.com/timesharemarketplace/search?KeyWord=Disney%27s+Aulani+Resort+%26+Spa",
        "owner": "DVC_Member_Florida",
        "location": "Oahu, Hawaii",
        "brand": "Disney Vacation Club",
        "retail_per_night": 900.0,
        "total_retail": 5400.0,
        "price_per_night": 483.33,
        "total_savings": 2500.0,
        "savings_pct": 46.3,
        "score": 81.3,
        "grade": "A",
        "class": "great-deal",
        "notes": "Stunning family resort with amazing lazy river and beach cove. Disney quality throughout."
    },
    {
        "resort": "Harborside Resort at Atlantis",
        "unit_type": "2 Bedroom Deluxe Villa",
        "view": "Marina View",
        "check_in": "2026-06-19",
        "nights": 7,
        "listing_price": 2200.0,
        "listing_id": "TUG-5591",
        "platform": "TUG Classifieds",
        "link": "https://tug2.com/timesharemarketplace/search?KeyWord=Harborside+Resort+at+Atlantis",
        "owner": "AtlantisLover",
        "location": "Nassau, Bahamas",
        "brand": "Sheraton/Westin",
        "retail_per_night": 800.0,
        "total_retail": 5600.0,
        "price_per_night": 314.29,
        "total_savings": 3400.0,
        "savings_pct": 60.7,
        "score": 90.7,
        "grade": "A+",
        "class": "super-deal",
        "notes": "Includes full passes to the Atlantis Aquaventure waterpark for all guests (up to 6 people)."
    },
    {
        "resort": "Marriott's Grande Vista",
        "unit_type": "2 Bedroom, 2 Bath Villa",
        "view": "Golf Course / Lake View",
        "check_in": "2026-06-04",
        "nights": 7,
        "listing_price": 850.0,
        "listing_id": "TUG-2210",
        "platform": "TUG Classifieds",
        "link": "https://tug2.com/timesharemarketplace/search?KeyWord=Marriott%27s+Grande+Vista",
        "owner": "SunshineDave",
        "location": "Orlando, FL",
        "brand": "Marriott",
        "retail_per_night": 320.0,
        "total_retail": 2240.0,
        "price_per_night": 121.43,
        "total_savings": 1390.0,
        "savings_pct": 62.1,
        "score": 97.1,
        "grade": "A+",
        "class": "super-deal",
        "notes": "Last-minute rental! Extremely spacious villa, perfect for families visiting Orlando theme parks."
    }
];

// Global State
let dealsData = [];
let activeBrandFilter = 'all';
let activeLocationFilter = 'all';
let activeBedroomsFilter = 'all';
let searchQuery = '';
let currentSort = 'score';

// DOM Element Selectors
const dealsGrid = document.getElementById('deals-grid');
const searchInput = document.getElementById('search-input');
const brandFiltersContainer = document.getElementById('brand-filters');
const stateFiltersContainer = document.getElementById('state-filters');
const bedroomFiltersContainer = document.getElementById('bedroom-filters');
const sortSelect = document.getElementById('sort-select');
const resultsCount = document.getElementById('results-count');
const emptyState = document.getElementById('empty-state');
const resetFiltersBtn = document.getElementById('reset-filters-btn');

// Stats Counters
const statTotalDeals = document.getElementById('stat-total-deals');
const statAvgSavings = document.getElementById('stat-avg-savings');
const statTotalSaved = document.getElementById('stat-total-saved');

/**
 * Main application initialization
 */
async function init() {
    setupEventListeners();
    await fetchDeals();
}

/**
 * Fetches deal database from deals.json, falling back to local dataset if needed
 */
async function fetchDeals() {
    try {
        // Shimmer loaders simulation time
        await new Promise(resolve => setTimeout(resolve, 800));
        
        const response = await fetch(`deals.json?t=${Date.now()}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        
        if (data && data.length > 0) {
            dealsData = data;
            console.log("Successfully fetched deals from deals.json");
        } else {
            throw new Error("Empty dataset in JSON");
        }
    } catch (error) {
        console.warn("Could not load deals.json. Loading high-fidelity fallback dataset instead.", error);
        dealsData = FALLBACK_DEALS;
    }
    
    updateStatsPanel(dealsData);
    buildLocationFilters(dealsData);
    applyFiltersAndSorting();
}

/**
 * Dynamically builds location filter buttons from the loaded dataset.
 * Groups by high-level location label (e.g. "Maui, Hawaii" → "Maui").
 */
function buildLocationFilters(deals) {
    // Collect unique locations, preserving display order by frequency
    const locationCounts = {};
    deals.forEach(d => {
        const loc = d.location || '';
        if (loc) locationCounts[loc] = (locationCounts[loc] || 0) + 1;
    });

    // Sort by count desc
    const locations = Object.keys(locationCounts).sort((a, b) => locationCounts[b] - locationCounts[a]);

    // Render buttons
    stateFiltersContainer.innerHTML = `<button class="filter-btn state-btn active" data-location="all">All Locations</button>`;
    locations.forEach(loc => {
        const btn = document.createElement('button');
        btn.className = 'filter-btn state-btn';
        btn.setAttribute('data-location', loc);
        // Shorten label: "Maui, Hawaii" → "Maui, HI", "Orlando, FL" → "Orlando, FL"
        btn.textContent = shortenLocation(loc);
        stateFiltersContainer.appendChild(btn);
    });
}

/**
 * Shortens a location string for compact display in the filter bar.
 * e.g. "Maui, Hawaii" → "Maui, HI"  |  "Nassau, Bahamas" → "Nassau"
 */
function shortenLocation(loc) {
    const stateMap = {
        'Hawaii': 'HI', 'Florida': 'FL', 'California': 'CA',
        'Nevada': 'NV', 'South Carolina': 'SC', 'Colorado': 'CO',
    };
    const parts = loc.split(',').map(s => s.trim());
    if (parts.length === 2) {
        const abbrev = stateMap[parts[1]];
        return abbrev ? `${parts[0]}, ${abbrev}` : parts[0];
    }
    return loc;
}

/**
 * Calculates metrics and updates the top stats panel cards
 */
function updateStatsPanel(deals) {
    if (!deals || deals.length === 0) return;
    
    const count = deals.length;
    
    // Calculate averages and sums
    const totalSavings = deals.reduce((acc, d) => acc + d.total_savings, 0);
    const avgSavingsPct = deals.reduce((acc, d) => acc + d.savings_pct, 0) / count;
    
    // Formatting animations or numeric rendering
    statTotalDeals.innerText = count;
    statAvgSavings.innerText = `${Math.round(avgSavingsPct)}%`;
    statTotalSaved.innerText = `$${Math.round(totalSavings).toLocaleString()}`;
}

/**
 * Setup controller listeners
 */
function setupEventListeners() {
    // Search Listener (Real-time Typing Debounced slightly)
    let searchTimeout;
    searchInput.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            searchQuery = e.target.value.trim().toLowerCase();
            applyFiltersAndSorting();
        }, 150);
    });

    // Brand Buttons Listener
    brandFiltersContainer.addEventListener('click', (e) => {
        if (e.target.classList.contains('filter-btn')) {
            // Manage Active Class
            document.querySelectorAll('#brand-filters .filter-btn').forEach(btn => btn.classList.remove('active'));
            e.target.classList.add('active');
            
            activeBrandFilter = e.target.getAttribute('data-brand');
            applyFiltersAndSorting();
        }
    });

    // Location/State Buttons Listener
    stateFiltersContainer.addEventListener('click', (e) => {
        if (e.target.classList.contains('state-btn')) {
            document.querySelectorAll('#state-filters .state-btn').forEach(btn => btn.classList.remove('active'));
            e.target.classList.add('active');
            activeLocationFilter = e.target.getAttribute('data-location');
            applyFiltersAndSorting();
        }
    });

    // Sort Dropdown Selector
    sortSelect.addEventListener('change', (e) => {
        currentSort = e.target.value;
        applyFiltersAndSorting();
    });

    // Bedroom Buttons Listener
    bedroomFiltersContainer.addEventListener('click', (e) => {
        if (e.target.classList.contains('bedroom-btn')) {
            document.querySelectorAll('#bedroom-filters .bedroom-btn').forEach(btn => btn.classList.remove('active'));
            e.target.classList.add('active');
            activeBedroomsFilter = e.target.getAttribute('data-bedrooms');
            applyFiltersAndSorting();
        }
    });

    // Reset button inside empty state
    resetFiltersBtn.addEventListener('click', resetAllFilters);
}

/**
 * Resets all search and filter conditions
 */
function resetAllFilters() {
    searchInput.value = '';
    searchQuery = '';
    
    document.querySelectorAll('#brand-filters .filter-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelector('#brand-filters .filter-btn[data-brand="all"]').classList.add('active');
    activeBrandFilter = 'all';

    document.querySelectorAll('#state-filters .state-btn').forEach(btn => btn.classList.remove('active'));
    const allLocBtn = document.querySelector('#state-filters .state-btn[data-location="all"]');
    if (allLocBtn) allLocBtn.classList.add('active');
    activeLocationFilter = 'all';

    document.querySelectorAll('#bedroom-filters .bedroom-btn').forEach(btn => btn.classList.remove('active'));
    const allBedBtn = document.querySelector('#bedroom-filters .bedroom-btn[data-bedrooms="all"]');
    if (allBedBtn) allBedBtn.classList.add('active');
    activeBedroomsFilter = 'all';
    
    sortSelect.value = 'score';
    currentSort = 'score';
    
    applyFiltersAndSorting();
}

/**
 * Evaluates filters and sorts, then triggers cards rendering
 */
function applyFiltersAndSorting() {
    let filtered = [...dealsData];

    // 1. Search Query Filter
    if (searchQuery) {
        filtered = filtered.filter(d => 
            d.resort.toLowerCase().includes(searchQuery) ||
            d.location.toLowerCase().includes(searchQuery) ||
            d.brand.toLowerCase().includes(searchQuery) ||
            (d.unit_type && d.unit_type.toLowerCase().includes(searchQuery))
        );
    }

    // 2. Brand Category Filter
    if (activeBrandFilter !== 'all') {
        if (activeBrandFilter === 'other') {
            filtered = filtered.filter(d => 
                !d.brand.toLowerCase().includes('marriott') &&
                !d.brand.toLowerCase().includes('westin') &&
                !d.brand.toLowerCase().includes('disney') &&
                !d.brand.toLowerCase().includes('ritz') &&
                !d.brand.toLowerCase().includes('seasons') &&
                !d.brand.toLowerCase().includes('hyatt')
            );
        } else {
            filtered = filtered.filter(d => 
                d.brand.toLowerCase().includes(activeBrandFilter.toLowerCase())
            );
        }
    }

    // 3. Location Filter
    if (activeLocationFilter !== 'all') {
        filtered = filtered.filter(d => d.location === activeLocationFilter);
    }

    // 4. Bedroom Filter
    if (activeBedroomsFilter !== 'all') {
        filtered = filtered.filter(d => {
            if (!d.unit_type) return false;
            let beds = 1;
            if (d.unit_type.toLowerCase().includes('studio')) {
                beds = 1; // Map studio to 1 BR for filtering
            } else {
                const match = d.unit_type.match(/(\d+)\s*bed/i);
                beds = match ? parseInt(match[1]) : 1;
            }
            if (activeBedroomsFilter === '3') {
                return beds >= 3;
            }
            return beds === parseInt(activeBedroomsFilter);
        });
    }

    // 3. Sorting Algorithms
    filtered.sort((a, b) => {
        if (currentSort === 'score') {
            return b.score - a.score; // Score Descending
        } else if (currentSort === 'discount') {
            return b.savings_pct - a.savings_pct; // Discount Descending
        } else if (currentSort === 'price-asc') {
            return a.listing_price - b.listing_price; // Price Ascending
        } else if (currentSort === 'price-desc') {
            return b.listing_price - a.listing_price; // Price Descending
        } else if (currentSort === 'date') {
            return new Date(a.check_in) - new Date(b.check_in); // Soonest check-in
        }
        return 0;
    });

    renderDeals(filtered);
}

/**
 * Dynamically constructs and inserts Listing Cards into HTML
 */
function renderDeals(deals) {
    dealsGrid.innerHTML = '';
    
    // Update count labels
    resultsCount.innerText = `${deals.length} deals matching`;
    
    // Handle Empty State
    if (deals.length === 0) {
        emptyState.classList.remove('hidden');
        dealsGrid.classList.add('hidden');
        return;
    } else {
        emptyState.classList.add('hidden');
        dealsGrid.classList.remove('hidden');
    }
    
    // Render loop
    deals.forEach(deal => {
        // Resolve Brand Class
        let brandClass = 'brand-other';
        const brandLower = deal.brand.toLowerCase();
        if (brandLower.includes('ritz')) brandClass = 'brand-ritz';
        else if (brandLower.includes('seasons')) brandClass = 'brand-seasons';
        else if (brandLower.includes('marriott')) brandClass = 'brand-marriott';
        else if (brandLower.includes('westin')) brandClass = 'brand-westin';
        else if (brandLower.includes('disney')) brandClass = 'brand-dvc';
        else if (brandLower.includes('hyatt')) brandClass = 'brand-hyatt';
        
        // Format check-in date (safely avoiding timezone-shift bugs by parsing YYYY-MM-DD in local time)
        let checkInDate;
        if (deal.check_in && deal.check_in.includes('-')) {
            const parts = deal.check_in.split('-');
            checkInDate = new Date(parseInt(parts[0], 10), parseInt(parts[1], 10) - 1, parseInt(parts[2], 10));
        } else {
            checkInDate = new Date(deal.check_in);
        }
        const dateOptions = { month: 'short', day: 'numeric', year: 'numeric' };
        const formattedDate = checkInDate.toLocaleDateString('en-US', dateOptions);
        
        // Core Card Template
        const cardHtml = `
            <div class="deal-card animate-fadeIn">
                <!-- Top Row -->
                <div class="card-header-row">
                    <span class="brand-badge ${brandClass}">${deal.brand}</span>
                    <div class="score-badge score-${deal.class}">
                        <span class="score-val">${deal.score}</span>
                        <span class="score-grade">${deal.grade}</span>
                    </div>
                </div>

                <!-- Titles -->
                <div>
                    <h3 class="resort-name">${deal.resort}</h3>
                    <div class="resort-location">
                        <i class="fa-solid fa-location-dot"></i> ${deal.location}
                    </div>
                </div>

                <!-- Info Grid -->
                <div class="listing-meta-grid">
                    <div class="meta-item">
                        <span class="meta-label">Check-in</span>
                        <span class="meta-value">${formattedDate}</span>
                    </div>
                    <div class="meta-item">
                        <span class="meta-label">Duration</span>
                        <span class="meta-value">${deal.nights} Nights</span>
                    </div>
                    <div class="meta-item">
                        <span class="meta-label">Room Size</span>
                        <span class="meta-value">${deal.unit_type}</span>
                    </div>
                    <div class="meta-item">
                        <span class="meta-label">View Profile</span>
                        <span class="meta-value">${deal.view || 'Standard'}</span>
                    </div>
                </div>

                <!-- Pricing Section -->
                <div class="pricing-section">
                    <div class="price-box">
                        <span class="price-label">Rental Cost</span>
                        <span class="price-value">$${Math.round(deal.listing_price).toLocaleString()}</span>
                        <span class="price-retail">Retail: $${Math.round(deal.total_retail).toLocaleString()}</span>
                    </div>
                    <div class="savings-tag ${deal.class === 'super-deal' ? 'super-deal-tag' : ''}">
                        <span class="savings-pct">-${deal.savings_pct}%</span>
                        <span class="savings-label">Save $${Math.round(deal.total_savings).toLocaleString()}</span>
                    </div>
                </div>

                <!-- Notes & Info -->
                <p class="card-notes" title="${deal.notes}">${deal.notes || 'No description notes provided by the seller.'}</p>

                <!-- Actions -->
                <div class="owner-row">
                    <span>Owner: <strong class="owner-name">${deal.owner}</strong></span>
                    <span>Listing ID: ${deal.listing_id}</span>
                </div>
                
                <a href="${deal.link}" target="_blank" class="view-btn">
                    View Classified <i class="fa-solid fa-up-right-from-square"></i>
                </a>
            </div>
        `;
        
        dealsGrid.insertAdjacentHTML('beforeend', cardHtml);
    });
}

// Fire application initialization
document.addEventListener('DOMContentLoaded', init);
