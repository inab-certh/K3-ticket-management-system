class GeographySelector {
    constructor(regionSelect, unitSelect, municipalitySelect) {
        this.regionSelect = document.getElementById(regionSelect);
        this.unitSelect = document.getElementById(unitSelect);
        this.municipalitySelect = document.getElementById(municipalitySelect);
        
        this.init();
    }
    
    init() {
        this.regionSelect.addEventListener('change', () => {
            this.loadRegionalUnits();
        });
        
        this.unitSelect.addEventListener('change', () => {
            this.loadMunicipalities();
        });
    }
    
    async loadRegionalUnits() {
        const regionId = this.regionSelect.value;
        
        // Clear dependent dropdowns
        this.clearSelect(this.unitSelect);
        this.clearSelect(this.municipalitySelect);
        
        if (!regionId) return;
        
        try {
            const response = await fetch(`/api/regional-units/?region_id=${regionId}`);
            const data = await response.json();
            
            this.populateSelect(this.unitSelect, data.units, 'Επιλέξτε Περιφερειακή Ενότητα');
        } catch (error) {
            console.error('Error loading regional units:', error);
        }
    }
    
    async loadMunicipalities() {
        const unitId = this.unitSelect.value;
        
        // Clear municipality dropdown
        this.clearSelect(this.municipalitySelect);
        
        if (!unitId) return;
        
        try {
            const response = await fetch(`/api/municipalities/?unit_id=${unitId}`);
            const data = await response.json();
            
            this.populateSelect(this.municipalitySelect, data.municipalities, 'Επιλέξτε Δήμο');
        } catch (error) {
            console.error('Error loading municipalities:', error);
        }
    }
    
    clearSelect(selectElement) {
        selectElement.innerHTML = '<option value="">-- Επιλέξτε --</option>';
        selectElement.disabled = true;
    }
    
    populateSelect(selectElement, options, placeholder) {
        selectElement.innerHTML = `<option value="">${placeholder}</option>`;
        
        options.forEach(option => {
            const optionElement = document.createElement('option');
            optionElement.value = option.id;
            optionElement.textContent = option.name;
            selectElement.appendChild(optionElement);
        });
        
        selectElement.disabled = false;
    }
}

// Usage in templates:
// new GeographySelector('id_region', 'id_regional_unit', 'id_municipality');