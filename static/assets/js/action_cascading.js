document.addEventListener('DOMContentLoaded', function() {
    const actionTypeField = document.querySelector('#id_action_type');
    const directionField = document.querySelector('#id_direction');
    const contactTypeField = document.querySelector('#id_contact_type');
    const referralTypeField = document.querySelector('#id_referral_type');
    
    if (!actionTypeField) return;
    
    function toggleFields() {
        const actionType = actionTypeField.value;
        
        // Hide all conditional fields first
        hideField(directionField);
        hideField(contactTypeField);
        hideField(referralTypeField);
        
        if (actionType === 'call' || actionType === 'email') {
            showField(directionField);
            showField(contactTypeField);
        } else if (actionType === 'referral') {
            showField(referralTypeField);
        }
    }
    
    function hideField(field) {
        if (field) {
            const row = field.closest('.form-row') || field.closest('.field-line');
            if (row) row.style.display = 'none';
            field.value = '';
        }
    }
    
    function showField(field) {
        if (field) {
            const row = field.closest('.form-row') || field.closest('.field-line');
            if (row) row.style.display = 'block';
        }
    }
    
    actionTypeField.addEventListener('change', toggleFields);
    toggleFields(); // Initialize
});