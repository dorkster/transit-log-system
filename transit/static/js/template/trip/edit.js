function setStatusColor() {
    if ($("#id_status").val() > 0) {
        $("#id_status").addClass("bg-danger text-light");
    }
    else {
        $("#id_status").removeClass("bg-danger text-light");
    }
}

function setupFormEvents() {
    $("#id_status").on("change", setStatusColor);
}

function setupFormEventsTrip() {
    $("#id_name").on("change", onNameChanged);
    $("#id_address").on("change", function() { onAddressChanged(0); });
    $("#id_destination").on("change", function() { onAddressChanged(1); });
}

function onNameChanged() {
    var address_datalist = document.getElementById("addresses");
    address_datalist.children[0].value = "";

    var found_client = false;
    for (i in clients) {
        if (clients[i].fields.name == $("#id_name").val()) {
            found_client = true;

            $("#id_phone_home").val(clients[i].fields.phone_home);
            $("#id_phone_cell").val(clients[i].fields.phone_cell);

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
    var phone_input = (target == 1 ? "#id_phone_cell" : "#id_phone_home");

    $(phone_input).val("");
    for (i in clients) {
        if (clients[i].fields.name == $("#id_name").val()) {
            if (target == 1)
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

    $(address_input).val("");
    $(phone_input).val("");
    for (i in clients) {
        if (clients[i].fields.name == $("#id_name").val()) {
            $(address_input).val(clients[i].fields.address);
        }
    }
}

function onAddressChanged(target) {
    var address_input = (target == 1 ? "#id_destination" : "#id_address");
    var phone_input = (target == 1 ? "#id_phone_destination" : "#id_phone_address");

    for (i in destinations) {
        if (destinations[i].fields.address == $(address_input).val()) {
            $(phone_input).val(destinations[i].fields.phone);
            break;
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
