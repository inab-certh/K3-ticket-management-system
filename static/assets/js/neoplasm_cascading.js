// static/assets/js/neoplasm_cascading.js
// Cascading dropdowns for ICD10 Category -> Subcategory -> Code

document.addEventListener('DOMContentLoaded', function() {
    const categoryField = document.querySelector('#id_icd10_category');
    const subcategoryField = document.querySelector('#id_icd10_subcategory');
    const codeField = document.querySelector('#id_icd10_code');
    
    if (!categoryField || !subcategoryField || !codeField) {
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
    
    // Handle category change
    categoryField.addEventListener('change', function() {
        const categoryId = this.value;
        
        // Clear dependent dropdowns
        clearAndDisableDropdown(subcategoryField, "Επιλέξτε πρώτα κατηγορία");
        clearAndDisableDropdown(codeField, "Επιλέξτε πρώτα υποκατηγορία");
        
        if (!categoryId) {
            return;
        }
        
        // Fetch subcategories for selected category
        fetch(`/admin/records/neoplasm/get_subcategories/?category_id=${categoryId}`, {
            method: 'GET',
            headers: {
                'X-CSRFToken': getCSRFToken(),
                'Content-Type': 'application/json',
            },
        })
        .then(response => response.json())
        .then(data => {
            populateDropdown(subcategoryField, data, "Επιλέξτε υποκατηγορία");
        })
        .catch(error => {
            console.error('Error fetching subcategories:', error);
            clearAndDisableDropdown(subcategoryField, "Σφάλμα φόρτωσης");
        });
    });
    
    // Handle subcategory change
    subcategoryField.addEventListener('change', function() {
        const subcategoryId = this.value;
        
        // Clear code dropdown
        clearAndDisableDropdown(codeField, "Επιλέξτε πρώτα υποκατηγορία");
        
        if (!subcategoryId) {
            return;
        }
        
        // Fetch codes for selected subcategory
        fetch(`/admin/records/neoplasm/get_codes/?subcategory_id=${subcategoryId}`, {
            method: 'GET',
            headers: {
                'X-CSRFToken': getCSRFToken(),
                'Content-Type': 'application/json',
            },
        })
        .then(response => response.json())
        .then(data => {
            populateDropdown(codeField, data, "Επιλέξτε συγκεκριμένο τύπο");
        })
        .catch(error => {
            console.error('Error fetching codes:', error);
            clearAndDisableDropdown(codeField, "Σφάλμα φόρτωσης");
        });
    });
    
    // Initialize on page load
    function initializeDropdowns() {
        const categoryValue = categoryField.value;
        const subcategoryValue = subcategoryField.value;
        
        if (!categoryValue) {
            clearAndDisableDropdown(subcategoryField, "Επιλέξτε πρώτα κατηγορία");
            clearAndDisableDropdown(codeField, "Επιλέξτε πρώτα υποκατηγορία");
        } else if (!subcategoryValue) {
            clearAndDisableDropdown(codeField, "Επιλέξτε πρώτα υποκατηγορία");
        }
    }
    
    // Run initialization
    initializeDropdowns();
    
    // Handle inline formsets (if you have medical history inline forms)
    const inlineFormsets = document.querySelectorAll('.inline-group');
    inlineFormsets.forEach(formset => {
        const addButton = formset.querySelector('.add-row a');
        if (addButton) {
            addButton.addEventListener('click', function() {
                setTimeout(() => {
                    initializeCascadingForInline(formset);
                }, 100);
            });
        }
    });
    
    function initializeCascadingForInline(formset) {
        const newForms = formset.querySelectorAll('.dynamic-form:last-child');
        newForms.forEach(form => {
            const categoryField = form.querySelector('[id$="_icd10_category"]');
            const subcategoryField = form.querySelector('[id$="_icd10_subcategory"]');
            const codeField = form.querySelector('[id$="_icd10_code"]');
            
            if (categoryField && subcategoryField && codeField) {
                setupCascadingForForm(categoryField, subcategoryField, codeField);
            }
        });
    }
    
    function setupCascadingForForm(categoryField, subcategoryField, codeField) {
        categoryField.addEventListener('change', function() {
            const categoryId = this.value;
            clearAndDisableDropdown(subcategoryField, "Επιλέξτε πρώτα κατηγορία");
            clearAndDisableDropdown(codeField, "Επιλέξτε πρώτα υποκατηγορία");
            
            if (categoryId) {
                fetch(`/admin/records/neoplasm/get_subcategories/?category_id=${categoryId}`)
                .then(response => response.json())
                .then(data => {
                    populateDropdown(subcategoryField, data, "Επιλέξτε υποκατηγορία");
                });
            }
        });
        
        subcategoryField.addEventListener('change', function() {
            const subcategoryId = this.value;
            clearAndDisableDropdown(codeField, "Επιλέξτε πρώτα υποκατηγορία");
            
            if (subcategoryId) {
                fetch(`/admin/records/neoplasm/get_codes/?subcategory_id=${subcategoryId}`)
                .then(response => response.json())
                .then(data => {
                    populateDropdown(codeField, data, "Επιλέξτε συγκεκριμένο τύπο");
                });
            }
        });
    }
});