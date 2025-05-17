function fixDatePicker() {
    // Keep the dropdown from closing when picking a date
    $('#date_dropdown .dropdown-menu').click(function(e) {
        e.stopPropagation();
    })
    $("#id_date_day").attr("style", "display: none !important;");
}

function fixSectionPicker() {
    // Keep the dropdown from closing when clicking inside
    $('#section_dropdown').click(function(e) {
        e.stopPropagation();
    });
}

function visibleSave(v, get_checkboxes) {
    var cookie_str = "report_visibility=";

    for (i = 0; i < v.length; i++) {
        if (get_checkboxes == true && $(v.data[i][1]).length) {
            if ($(v.data[i][2]).is(":checked")) {
                v.data[i][0] = 1;
            }
            else {
                v.data[i][0] = 0;
            }
        }
        cookie_str += v.data[i][0].toString();
    }
    cookie_str += ";";

    cookie_str += "path=/transit/report;";
    document.cookie = cookie_str;

    visibleApply(v);
}

function visibleShowAll(v) {
    for (i = 0; i < v.length; i++) {
        v.data[i][0] = 1;
    }
    visibleSave(v, false);
}

function visibleSolo(v, solo_input_id) {
    for (i = 0; i < v.length; i++) {
        if (v.data[i][2] != solo_input_id) {
            $(v.data[i][2]).prop("checked", false);
        }
        else {
            $(v.data[i][2]).prop("checked", true);
        }
    }
    visibleSave(v, true);
}

