function setStatusColor() {
    if ($("#id_status").val() > 0) {
        $("#id_status").addClass("bg-danger text-light");
    }
    else {
        $("#id_status").removeClass("bg-danger text-light");
    }
}

function setCancelDateVisibility() {
    if ($("#id_status").val() == 1) {
        $("#cancel_date").collapse('show');
    }
    else {
        $("#cancel_date").collapse('hide');
    }
}

function setupFormEvents() {
    $("#id_status").on("change", function() { setStatusColor(); setCancelDateVisibility(); });
}

function setupFormEventsTrip() {
    $("#id_name").on("change", onNameChanged);
    $("#id_address").on("change", function() { onAddressChanged(0); });
    $("#id_destination").on("change", function() { onAddressChanged(1); });
    $("#id_driver").on("change", onDriverChange);
    $("#id_trip_type").on("change", onTripTypeChange);
    $("#id_volunteer").on("change", onVolunteerChange);
}

function onNameChanged() {
    var address_datalist = document.getElementById("addresses");
    address_datalist.children[0].value = "";

    var found_client = false;
    for (let i in clients) {
        if (clients[i].fields.name == $("#id_name").val()) {
            found_client = true;

            $("#id_phone_home").val(clients[i].fields.phone_home);
            $("#id_phone_cell").val(clients[i].fields.phone_cell);
            $("#id_phone_alt").val(clients[i].fields.phone_alt);

            if (clients[i].fields.elderly == null)
                $("#id_elderly").prop("selectedIndex", 0);
            else if (clients[i].fields.elderly == true)
                $("#id_elderly").prop("selectedIndex", 1);
            else if (clients[i].fields.elderly == false)
                $("#id_elderly").prop("selectedIndex", 2);

            if (clients[i].fields.ambulatory == null)
                $("#id_ambulatory").prop("selectedIndex", 0);
            else if (clients[i].fields.ambulatory == true)
                $("#id_ambulatory").prop("selectedIndex", 1);
            else if (clients[i].fields.ambulatory == false)
                $("#id_ambulatory").prop("selectedIndex", 2);

            $("#id_tags").val(clients[i].fields.tags);
            createTagList();

            address_datalist.children[0].value = clients[i].fields.address;

            $("#id_reminder_instructions").val(clients[i].fields.reminder_instructions);

            break;
        }
    }

    if (!found_client && $("#id_name").val() != "") {
        if (!confirm("Unable to find '" + $("#id_name").val() + "' in the Clients database. Do you still want to continue?")) {
            $("#id_name").val("");
        }
    }

    var add_client_btn = document.getElementById("add_client_btn");
    if (add_client_btn) {
        if (found_client || $("#id_name").val() == "") {
            $("#id_add_client").val("True");
            toggleAddClient(add_client_btn);
            add_client_btn.classList.add("disabled");
        }
        else {
            $("#id_add_client").val("False");
            toggleAddClient(add_client_btn);
            add_client_btn.classList.remove("disabled");
        }
    }
}

function getClientPhone(target) {
    var phone_input;
    if (target == 2)
        phone_input = "#id_phone_alt";
    else if (target == 1)
        phone_input = "#id_phone_cell";
    else
        phone_input = "#id_phone_home";

    $(phone_input).val("");
    for (i in clients) {
        if (clients[i].fields.name == $("#id_name").val()) {
            if (target == 2)
                $(phone_input).val(clients[i].fields.phone_alt);
            else if (target == 1)
                $(phone_input).val(clients[i].fields.phone_cell);
            else
                $(phone_input).val(clients[i].fields.phone_home);

            break;
        }
    }
}

function getClientAddress(target) {
    var address_input = (target == 1 ? "#id_destination" : "#id_address");
    var phone_input = (target == 1 ? "#id_phone_destination" : "#id_phone_address");
    var add_dest_btn_id = (target == 1 ? "add_dest2_btn" : "add_dest1_btn");
    var add_dest_input = (target == 1 ? "#id_add_dest2" : "#id_add_dest1");

    $(address_input).val("");
    $(phone_input).val("");
    for (i in clients) {
        if (clients[i].fields.name == $("#id_name").val()) {
            $(address_input).val(clients[i].fields.address);
        }
    }

    var add_dest_btn = document.getElementById(add_dest_btn_id);
    if (add_dest_btn) {
        $(add_dest_input).val("True");
        toggleAddDestination(add_dest_btn, target);
        add_dest_btn.classList.add("disabled");
    }
}

function onAddressChanged(target) {
    var address_input = (target == 1 ? "#id_destination" : "#id_address");
    var phone_input = (target == 1 ? "#id_phone_destination" : "#id_phone_address");
    var add_dest_btn_id = (target == 1 ? "add_dest2_btn" : "add_dest1_btn");
    var add_dest_input = (target == 1 ? "#id_add_dest2" : "#id_add_dest1");

    var found_destination = false;
    for (i in destinations) {
        if (destinations[i].fields.address == $(address_input).val()) {
            found_destination = true;
            $(phone_input).val(destinations[i].fields.phone);
            break;
        }
    }

    var add_client_selected = (target == 0 && $("#id_add_client").val() == "True");
    if (!found_destination && $(address_input).val() != "" && !add_client_selected) {
        if (!confirm("Unable to find '" + $(address_input).val() + "' in the Destinations database. Do you still want to continue?")) {
            $(address_input).val("");
        }
    }

    var add_dest_btn = document.getElementById(add_dest_btn_id);
    if (add_dest_btn) {
        if (found_destination || $(address_input).val() == "") {
            $(add_dest_input).val("True");
            toggleAddDestination(add_dest_btn, target);
            add_dest_btn.classList.add("disabled");
        }
        else {
            if (!add_client_selected) {
                $(add_dest_input).val("False");
                toggleAddDestination(add_dest_btn, target);
            }
            add_dest_btn.classList.remove("disabled");
        }
    }
}

function getDestinationPhone(target) {
    var address_input = (target == 1 ? "#id_destination" : "#id_address");
    var phone_input = (target == 1 ? "#id_phone_destination" : "#id_phone_address");

    $(phone_input).val("");
    for (i in destinations) {
        if (destinations[i].fields.address == $(address_input).val()) {
            $(phone_input).val(destinations[i].fields.phone);
            break;
        }
    }
}

function setFare(fare_str) {
    $('#id_fare').val(fare_str);
    $('#fare_modal').modal('hide');
}

function showFareDialog() {
    $('#fare_modal').modal({backdrop: 'static', keyboard: false});
    $('#fare_modal').modal('show');
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

function toggleReturnTrip(btn) {
    var field = document.getElementById("id_create_return_trip");
    if (field) {
        if (field.value == "False") {
            field.value = "True";
            btn.classList.remove("btn-outline-dark");
            btn.classList.add("btn-primary");
            btn.firstChild.classList.remove("oi-circle-x");
            btn.firstChild.classList.add("oi-circle-check");
        }
        else {
            field.value = "False";
            btn.classList.remove("btn-primary");
            btn.classList.add("btn-outline-dark");
            btn.firstChild.classList.remove("oi-circle-check");
            btn.firstChild.classList.add("oi-circle-x");
        }
    }
}

function toggleAddClient(btn) {
    var field = document.getElementById("id_add_client");
    if (field) {
        if (field.value == "False") {
            field.value = "True";
            btn.classList.remove("btn-outline-dark");
            btn.classList.add("btn-primary");
            btn.firstChild.classList.remove("oi-circle-x");
            btn.firstChild.classList.add("oi-circle-check");

            var dest_field = document.getElementById("id_add_dest1");
            if (dest_field && dest_field.value == "True") {
                var dest_btn = document.getElementById("add_dest1_btn");
                if (dest_btn) {
                    toggleAddDestination(dest_btn, 0);
                }
            }
        }
        else {
            field.value = "False";
            btn.classList.remove("btn-primary");
            btn.classList.add("btn-outline-dark");
            btn.firstChild.classList.remove("oi-circle-check");
            btn.firstChild.classList.add("oi-circle-x");
            onAddressChanged(0);
        }
    }
}

function toggleAddDestination(btn, target) {
    var target_id = (target == 1 ? "id_add_dest2" : "id_add_dest1");
    var field = document.getElementById(target_id);
    if (field) {
        if (field.value == "False") {
            field.value = "True";
            btn.classList.remove("btn-outline-dark");
            btn.classList.add("btn-primary");
            btn.firstChild.classList.remove("oi-circle-x");
            btn.firstChild.classList.add("oi-circle-check");
        }
        else {
            field.value = "False";
            btn.classList.remove("btn-primary");
            btn.classList.add("btn-outline-dark");
            btn.firstChild.classList.remove("oi-circle-check");
            btn.firstChild.classList.add("oi-circle-x");
        }
    }
}

function onDriverChange() {
    let driver_id = $("#id_driver option:selected").val();
    if (driver_id != "") {
        $("#id_vehicle option").filter(function() {
            return $(this).val() == driver_vehicle_pairs[driver_id]["vehicle"];
        }).prop("selected", true);
    }
    else {
        $("#id_vehicle").prop("selectedIndex", 0);
    }
}

function onTripTypeChange() {
    var other_selected = $("#id_trip_type option:selected").text() == "Other";
    if (other_selected && $("#id_tags").val() == "") {
        showTagDialog();
    }
}

function onVolunteerChange() {
    let volunteer_driver = "";
    for (driver in driver_vehicle_pairs) {
        if (driver_vehicle_pairs[driver]['volunteer'] == 1) {
            volunteer_driver = driver;
        }
    }
    if ($("#id_volunteer").val() != "") {
        $("#id_driver option").filter(function() {
            return $(this).val() == volunteer_driver;
        }).prop("selected", true);
        onDriverChange();
    }
}

function focusVolunteer() {
    $("#id_volunteer").focus();
    $("#id_volunteer")[0].scrollIntoView({behavior: "smooth", block: "center"});
}

