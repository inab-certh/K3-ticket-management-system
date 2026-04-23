// static/admin/js/cascading_dropdowns.js
// Cascading dropdowns for Region -> Regional Unit -> Municipality

document.addEventListener('DOMContentLoaded', function() {
    const regionField = document.querySelector('#id_region');
    const regionalUnitField = document.querySelector('#id_regional_unit');
    const municipalityField = document.querySelector('#id_municipality');
    
    if (!regionField || !regionalUnitField || !municipalityField) {
        return; // Exit if fields not found
    }
    
    // Function to clear and disable a dropdown
    function clearAndDisableDropdown(dropdown, placeholder = "--------") {
        dropdown.innerHTML = `<option value="">${placeholder}</option>`;
        dropdown.disabled = true;
    }
    
    // Function to populate dropdown with options
    function populateDropdown(dropdown, options, placeholder = "--------") {
        dropdown.innerHTML = `<option value="">${placeholder}</option>`;
        options.forEach(option => {
            const optionElement = document.createElement('option');
            optionElement.value = option.id;
            optionElement.textContent = option.name;
            dropdown.appendChild(optionElement);
        });
        dropdown.disabled = false;
    }
    
    // Function to get CSRF token
    function getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]').value;
    }
    
    // Handle region change
    regionField.addEventListener('change', function() {
        const regionId = this.value;
        
        // Clear dependent dropdowns
        clearAndDisableDropdown(regionalUnitField, "Επιλέξτε πρώτα περιφέρεια");
        clearAndDisableDropdown(municipalityField, "Επιλέξτε πρώτα περιφεριακή ενότητα");
        
        if (!regionId) {
            return;
        }
        
        // Fetch regional units for selected region
        fetch(`/admin/records/person/get_regional_units/?region_id=${regionId}`, {
            method: 'GET',
            headers: {
                'X-CSRFToken': getCSRFToken(),
                'Content-Type': 'application/json',
            },
        })
        .then(response => response.json())
        .then(data => {
            populateDropdown(regionalUnitField, data, "Επιλέξτε περιφεριακή ενότητα");
        })
        .catch(error => {
            console.error('Error fetching regional units:', error);
            clearAndDisableDropdown(regionalUnitField, "Σφάλμα φόρτωσης");
        });
    });
    
    // Handle regional unit change
    regionalUnitField.addEventListener('change', function() {
        const unitId = this.value;
        
        // Clear municipality dropdown
        clearAndDisableDropdown(municipalityField, "Επιλέξτε πρώτα περιφεριακή ενότητα");
        
        if (!unitId) {
            return;
        }
        
        // Fetch municipalities for selected regional unit
        fetch(`/admin/records/person/get_municipalities/?unit_id=${unitId}`, {
            method: 'GET',
            headers: {
                'X-CSRFToken': getCSRFToken(),
                'Content-Type': 'application/json',
            },
        })
        .then(response => response.json())
        .then(data => {
            populateDropdown(municipalityField, data, "Επιλέξτε δήμο");
        })
        .catch(error => {
            console.error('Error fetching municipalities:', error);
            clearAndDisableDropdown(municipalityField, "Σφάλμα φόρτωσης");
        });
    });
    
    // Initialize on page load
    function initializeDropdowns() {
        const regionValue = regionField.value;
        const unitValue = regionalUnitField.value;
        
        if (!regionValue) {
            clearAndDisableDropdown(regionalUnitField, "Επιλέξτε πρώτα περιφέρεια");
            clearAndDisableDropdown(municipalityField, "Επιλέξτε πρώτα περιφεριακή ενότητα");
        } else if (!unitValue) {
            clearAndDisableDropdown(municipalityField, "Επιλέξτε πρώτα περιφεριακή ενότητα");
        }
    }
    
    // Run initialization
    initializeDropdowns();
    
    // Handle inline formsets (if you have person inline forms)
    const inlineFormsets = document.querySelectorAll('.inline-group');
    inlineFormsets.forEach(formset => {
        const addButton = formset.querySelector('.add-row a');
        if (addButton) {
            addButton.addEventListener('click', function() {
                // Small delay to ensure the new form is added to DOM
                setTimeout(() => {
                    initializeCascadingForInline(formset);
                }, 100);
            });
        }
    });
    
    function initializeCascadingForInline(formset) {
        const newForms = formset.querySelectorAll('.dynamic-form:last-child');
        newForms.forEach(form => {
            const regionField = form.querySelector('[id$="_region"]');
            const regionalUnitField = form.querySelector('[id$="_regional_unit"]');
            const municipalityField = form.querySelector('[id$="_municipality"]');
            
            if (regionField && regionalUnitField && municipalityField) {
                setupCascadingForForm(regionField, regionalUnitField, municipalityField);
            }
        });
    }
    
    function setupCascadingForForm(regionField, regionalUnitField, municipalityField) {
        regionField.addEventListener('change', function() {
            const regionId = this.value;
            clearAndDisableDropdown(regionalUnitField, "Επιλέξτε πρώτα περιφέρεια");
            clearAndDisableDropdown(municipalityField, "Επιλέξτε πρώτα περιφεριακή ενότητα");
            
            if (regionId) {
                fetch(`/admin/records/person/get_regional_units/?region_id=${regionId}`)
                .then(response => response.json())
                .then(data => {
                    populateDropdown(regionalUnitField, data, "Επιλέξτε περιφεριακή ενότητα");
                });
            }
        });
        
        regionalUnitField.addEventListener('change', function() {
            const unitId = this.value;
            clearAndDisableDropdown(municipalityField, "Επιλέξτε πρώτα περιφεριακή ενότητα");
            
            if (unitId) {
                fetch(`/admin/records/person/get_municipalities/?unit_id=${unitId}`)
                .then(response => response.json())
                .then(data => {
                    populateDropdown(municipalityField, data, "Επιλέξτε δήμο");
                });
            }
        });
    }
});