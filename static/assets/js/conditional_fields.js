// static/assets/js/conditional_fields.js
// Conditional fields for disability-related fields

document.addEventListener('DOMContentLoaded', function() {
    const disabilityCheckbox = document.querySelector('#id_disability');
    const certifiedDisabilityField = document.querySelector('#id_certified_disability');
    const disabilityPercentageField = document.querySelector('#id_disability_percentage');
    
    if (!disabilityCheckbox) {
        return; // Exit if disability checkbox not found
    }
    
    // Function to show/hide disability-related fields
    function toggleDisabilityFields() {
        const isDisabilityChecked = disabilityCheckbox.checked;
        
        // Get the field containers (Django wraps fields in divs)
        const certifiedContainer = certifiedDisabilityField?.closest('.field-certified_disability') || 
                                 certifiedDisabilityField?.closest('.form-row');
        const percentageContainer = disabilityPercentageField?.closest('.field-disability_percentage') || 
                                  disabilityPercentageField?.closest('.form-row');
        
        if (certifiedContainer) {
            certifiedContainer.style.display = isDisabilityChecked ? 'block' : 'none';
            
            // Clear the field if hiding
            if (!isDisabilityChecked && certifiedDisabilityField) {
                certifiedDisabilityField.checked = false;
            }
        }
        
        if (percentageContainer) {
            percentageContainer.style.display = isDisabilityChecked ? 'block' : 'none';
            
            // Clear the field if hiding
            if (!isDisabilityChecked && disabilityPercentageField) {
                disabilityPercentageField.value = '';
            }
        }
        
        // Also disable/enable the fields for better UX
        if (certifiedDisabilityField) {
            certifiedDisabilityField.disabled = !isDisabilityChecked;
        }
        if (disabilityPercentageField) {
            disabilityPercentageField.disabled = !isDisabilityChecked;
        }
    }
    
    // Initialize on page load
    toggleDisabilityFields();
    
    // Add event listener for checkbox changes
    disabilityCheckbox.addEventListener('change', toggleDisabilityFields);
    
    // Handle inline formsets (if you have person inline forms)
    function initializeConditionalFieldsForInlines() {
        const inlineFormsets = document.querySelectorAll('.inline-group');
        
        inlineFormsets.forEach(formset => {
            const addButton = formset.querySelector('.add-row a');
            if (addButton) {
                addButton.addEventListener('click', function() {
                    // Small delay to ensure the new form is added to DOM
                    setTimeout(() => {
                        setupConditionalFieldsForNewInline(formset);
                    }, 100);
                });
            }
        });
    }
    
    function setupConditionalFieldsForNewInline(formset) {
        const newForms = formset.querySelectorAll('.dynamic-form:last-child');
        
        newForms.forEach(form => {
            const disabilityCheckbox = form.querySelector('[id$="_disability"]');
            const certifiedField = form.querySelector('[id$="_certified_disability"]');
            const percentageField = form.querySelector('[id$="_disability_percentage"]');
            
            if (disabilityCheckbox) {
                setupConditionalForForm(disabilityCheckbox, certifiedField, percentageField);
            }
        });
    }
    
    function setupConditionalForForm(disabilityCheckbox, certifiedField, percentageField) {
        function toggleFields() {
            const isChecked = disabilityCheckbox.checked;
            
            if (certifiedField) {
                const container = certifiedField.closest('.form-row') || certifiedField.closest('.field-certified_disability');
                if (container) {
                    container.style.display = isChecked ? 'block' : 'none';
                }
                certifiedField.disabled = !isChecked;
                if (!isChecked) certifiedField.checked = false;
            }
            
            if (percentageField) {
                const container = percentageField.closest('.form-row') || percentageField.closest('.field-disability_percentage');
                if (container) {
                    container.style.display = isChecked ? 'block' : 'none';
                }
                percentageField.disabled = !isChecked;
                if (!isChecked) percentageField.value = '';
            }
        }
        
        // Initialize and add listener
        toggleFields();
        disabilityCheckbox.addEventListener('change', toggleFields);
    }
    
    // Initialize for existing inline forms
    initializeConditionalFieldsForInlines();
	
	// Employment status conditional fields
	const employmentStatusField = document.querySelector('#id_status');

	// Unemployment fields
	const unemploymentCardField = document.querySelector('#id_unemployment_card');
	const unemploymentDateField = document.querySelector('#id_unemployment_registration_date');

	// Employment fields
	const professionField = document.querySelector('#id_profession');
	const specializationField = document.querySelector('#id_specialization');
	const employmentTypeField = document.querySelector('#id_employment_type');
	const employerNameField = document.querySelector('#id_employer_name');
	const employerLegalFormField = document.querySelector('#id_employer_legal_form');
	const hireDateField = document.querySelector('#id_hire_date');
	const workScheduleField = document.querySelector('#id_work_schedule');
	const contractTypeField = document.querySelector('#id_contract_type');

	if (employmentStatusField) {
		function toggleEmploymentFields() {
			const status = employmentStatusField.value;
			
			// Get unemployment field containers
			const unemploymentCardContainer = unemploymentCardField?.closest('.field-unemployment_card') || 
											unemploymentCardField?.closest('.form-row');
			const unemploymentDateContainer = unemploymentDateField?.closest('.field-unemployment_registration_date') || 
											unemploymentDateField?.closest('.form-row');
			
			// Get employment field containers
			const professionContainer = professionField?.closest('.field-profession') || 
									  professionField?.closest('.form-row');
			const specializationContainer = specializationField?.closest('.field-specialization') || 
										  specializationField?.closest('.form-row');
			const employmentTypeContainer = employmentTypeField?.closest('.field-employment_type') || 
										  employmentTypeField?.closest('.form-row');
			const employerNameContainer = employerNameField?.closest('.field-employer_name') || 
										employerNameField?.closest('.form-row');
			const employerLegalFormContainer = employerLegalFormField?.closest('.field-employer_legal_form') || 
											 employerLegalFormField?.closest('.form-row');
			const hireDateContainer = hireDateField?.closest('.field-hire_date') || 
									hireDateField?.closest('.form-row');
			const workScheduleContainer = workScheduleField?.closest('.field-work_schedule') || 
										workScheduleField?.closest('.form-row');
			const contractTypeContainer = contractTypeField?.closest('.field-contract_type') || 
										contractTypeField?.closest('.form-row');
			
			// Hide all conditional fields first
			const allConditionalContainers = [
				unemploymentCardContainer, unemploymentDateContainer,
				professionContainer, specializationContainer, employmentTypeContainer,
				employerNameContainer, employerLegalFormContainer, hireDateContainer,
				workScheduleContainer, contractTypeContainer
			];
			
			allConditionalContainers.forEach(container => {
				if (container) container.style.display = 'none';
			});
			
			// Show relevant fields based on status
			if (status === 'unemployed') {
				// Show unemployment fields
				if (unemploymentCardContainer) unemploymentCardContainer.style.display = 'block';
				if (unemploymentDateContainer) unemploymentDateContainer.style.display = 'block';
				
				// Clear employment fields
				[professionField, specializationField, employmentTypeField, employerNameField, 
				 employerLegalFormField, hireDateField, workScheduleField, contractTypeField].forEach(field => {
					if (field) {
						if (field.type === 'checkbox') {
							field.checked = false;
						} else {
							field.value = '';
						}
					}
				});
				
			} else if (status === 'employed' || status === 'retired_employed') {
				// Show employment fields
				[professionContainer, specializationContainer, employmentTypeContainer,
				 employerNameContainer, employerLegalFormContainer, hireDateContainer,
				 workScheduleContainer, contractTypeContainer].forEach(container => {
					if (container) container.style.display = 'block';
				});
				
				// Clear unemployment fields
				if (unemploymentCardField) unemploymentCardField.checked = false;
				if (unemploymentDateField) unemploymentDateField.value = '';
			}
			
			// For other statuses (retired, housework, student, other), all conditional fields stay hidden
		}
		
		// Initialize on page load
		toggleEmploymentFields();
		
		// Add event listener for status changes
		employmentStatusField.addEventListener('change', toggleEmploymentFields);
	}
});