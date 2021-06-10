function fixDatePicker() {
    // Keep the dropdown from closing when picking a date
    $('#date_dropdown option, #date_dropdown select').click(function(e) {
        e.stopPropagation();
    })
}

function loadTemplate(ajax_loader, template_name, template_id) {
    if (confirm("Are you sure you want to add the '" + template_name + "' template to the schedule?")) {
        ajax_loader.run('', 'load_template', template_id);
    }
}

