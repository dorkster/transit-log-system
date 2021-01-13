function setupRequiredFields(fields) {
    for (i in fields) {
        $(fields[i]).attr("required", true);
    }
}

function initCheckboxByField(cb, field) {
    if ($(field).val() == "") {
        $(cb).prop("checked", true);
        toggleFieldByCheckbox(cb, field);
    }
}

function toggleFieldByCheckbox(cb, field) {
    if ($(cb).is(":checked")) {
        $(field).attr("required", false);
        $(field).attr("disabled", true);
        $(field).val("");
    }
    else {
        $(field).attr("required", true);
        $(field).attr("disabled", false);
    }
}

function checkAlertAddress() {
    if ($("#id_address").val() != "" || $("#toggle_address").is(":checked") == true) {
        $("#alert_address").addClass("d-none");
    }
    else {
        $("#alert_address").removeClass("d-none");
    }
}

function checkAlertPhone() {
    var has_number = ($("#id_phone_home").val() != "" || $("#id_phone_cell").val() != "");
    var both_checked = ($("#toggle_phone_home").is(":checked") == true && $("#toggle_phone_cell").is(":checked") == true);
    if (has_number || both_checked) {
        $("#alert_phone").addClass("d-none");
    }
    else {
        $("#alert_phone").removeClass("d-none");
    }
}

function checkAlertInfo() {
    if ($("#id_elderly").val() == "unknown" || $("#id_ambulatory").val() == "unknown") {
        $("#alert_info").removeClass("d-none");
    }
    else {
        $("#alert_info").addClass("d-none");
    }
}

function addTag(tag) {
    if ($('#id_tags').val() == "") {
        $('#id_tags').val(tag);
        createTagList();
        $('#tag_modal').modal('hide');
        return;
    }

    var split_tags = $('#id_tags').val().split(',');
    for (i in split_tags) {
        if ($.trim(split_tags[i]) == tag) {
            createTagList();
            $('#tag_modal').modal('hide');
            return;
        }
    }

    $('#id_tags').val($('#id_tags').val() + ("," + tag));

    createTagList();
    $('#tag_modal').modal('hide');
}

function removeTag(tag_index) {
    var tag_str = "";
    var split_tags = $('#id_tags').val().split(',');
    for (i in split_tags) {
        if (i == tag_index)
            continue;

        tag_str += $.trim(split_tags[i]);
        if (i < split_tags.length - 1 && tag_str != "") {
            tag_str += ",";
        }
    }
    $('#id_tags').val(tag_str);

    createTagList();
}

function showTagDialog() {
    $('#tag_modal').modal('show');
}

function createTagList() {
    $('#tag_list').html("");

    var split_tags = $('#id_tags').val().split(',');
    for (i in split_tags) {
        split_tags[i] = $.trim(split_tags[i]);
        if (split_tags[i] != "") {
            $('#tag_list').append('<a class="btn btn-sm ' + getTagButtonStyle(split_tags[i]) + ' text-bold m-1" href="#_" onclick="removeTag(' + i.toString() + ')"><span class="oi oi-tag mr-2"></span>' + split_tags[i] + '<span class="ml-3 oi oi-x"></span></a>');
        }
    }
    $('#tag_list').append('<a class="btn btn-sm btn-secondary" href="#_" onclick="showTagDialog()" title="Add a tag"><span class="oi oi-plus"></span></a> ');
}

function setupFormEvents() {
    $("#toggle_address").on("click", function() { toggleFieldByCheckbox("#toggle_address", "#id_address"); checkAlertAddress(); } );
    $("#toggle_phone_home").on("click", function() { toggleFieldByCheckbox("#toggle_phone_home", "#id_phone_home"); checkAlertPhone(); } );
    $("#toggle_phone_cell").on("click", function() { toggleFieldByCheckbox("#toggle_phone_cell", "#id_phone_cell"); checkAlertPhone(); } );

    $("#id_address").on("change", checkAlertAddress);
    $("#id_phone_home").on("change", checkAlertPhone);
    $("#id_phone_cell").on("change", checkAlertPhone);
    $("#id_elderly").on("change", checkAlertInfo);
    $("#id_ambulatory").on("change", checkAlertInfo);
}
