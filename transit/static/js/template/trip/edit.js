function setStatusColor() {
    var status_input = document.getElementById("id_status")
    if (status_input.value > 0) {
        status_input.classList.add("bg-danger", "text-light");
    }
    else {
        status_input.classList.remove("bg-danger", "text-light");
    }
}

function setupFormEvents() {
    var status_input = document.getElementById("id_status")
    status_input.addEventListener("change", setStatusColor);
}

function setupFormEventsTrip() {
    var name_input = document.getElementById("id_name");
    name_input.addEventListener("change", onNameChanged);

    var pickup_input = document.getElementById("id_address");
    var destination_input = document.getElementById("id_destination");
    var pickup_phone_input = document.getElementById("id_phone_address");
    var destination_phone_input = document.getElementById("id_phone_destination");
    pickup_input.addEventListener("change", function() { onAddressChanged(this, pickup_phone_input); });
    destination_input.addEventListener("change", function() { onAddressChanged(this, destination_phone_input); });
}

function onNameChanged() {
    var clients = JSON.parse(JSON.parse(document.getElementById("clients-tag").textContent));

    var name_input = document.getElementById("id_name");
    var address_datalist = document.getElementById("addresses");
    address_datalist.children[0].value = "";

    var found_client = false;
    for (i in clients) {
        if (clients[i].fields.name == name_input.value) {
            found_client = true;

            var phone_home_input = document.getElementById("id_phone_home");
            phone_home_input.value = clients[i].fields.phone_home;
            var phone_cell_input = document.getElementById("id_phone_cell");
            phone_cell_input.value = clients[i].fields.phone_cell;

            var elderly_input = document.getElementById("id_elderly");
            if (clients[i].fields.elderly == null)
                elderly_input.selectedIndex = 0;
            else if (clients[i].fields.elderly == true)
                elderly_input.selectedIndex = 1;
            else if (clients[i].fields.elderly == false)
                elderly_input.selectedIndex = 2;

            var ambulatory_input = document.getElementById("id_ambulatory");
            if (clients[i].fields.ambulatory == null)
                ambulatory_input.selectedIndex = 0;
            else if (clients[i].fields.ambulatory == true)
                ambulatory_input.selectedIndex = 1;
            else if (clients[i].fields.ambulatory == false)
                ambulatory_input.selectedIndex = 2;

            var tags_input = document.getElementById("id_tags");
            tags_input.value = clients[i].fields.tags;
            createTagList();

            address_datalist.children[0].value = clients[i].fields.address;
            break;
        }
    }

    if (!found_client && name_input.value != "") {
        if (!confirm("Unable to find '" + name_input.value + "' in the Clients database. Do you still want to continue?")) {
            name_input.value = "";
        }
    }

    var add_client_btn = document.getElementById("add_client_btn");
    if (add_client_btn) {
        if (found_client || name_input.value == "") {
            document.getElementById("id_add_client").value = "True";
            toggleAddClient(add_client_btn);
            add_client_btn.classList.add("disabled");
        }
        else {
            document.getElementById("id_add_client").value = "False";
            toggleAddClient(add_client_btn);
            add_client_btn.classList.remove("disabled");
        }
    }
}

function getClientPhone(input, phone_type) {
    var clients = JSON.parse(JSON.parse(document.getElementById("clients-tag").textContent));

    var name_input = document.getElementById("id_name");
    $("#" + input).val("");
    for (i in clients) {
        if (clients[i].fields.name == name_input.value) {
            if (phone_type == "home")
                $("#" + input).val(clients[i].fields.phone_home);
            else if (phone_type == "cell")
                $("#" + input).val(clients[i].fields.phone_cell);

            break;
        }
    }
}

function getClientAddress(address_input, phone_input) {
    var clients = JSON.parse(JSON.parse(document.getElementById("clients-tag").textContent));

    var name_input = document.getElementById("id_name");
    $("#" + address_input).val("");
    $("#" + phone_input).val("");
    for (i in clients) {
        if (clients[i].fields.name == name_input.value) {
            $("#" + address_input).val(clients[i].fields.address);
        }
    }
}

function onAddressChanged(address_input, phone_input) {
    var destinations = JSON.parse(JSON.parse(document.getElementById("destinations-tag").textContent));

    for (i in destinations) {
        if (destinations[i].fields.address == address_input.value) {
            phone_input.value = destinations[i].fields.phone;
            break;
        }
    }
}

function getDestinationPhone(address_input, phone_input) {
    var destinations = JSON.parse(JSON.parse(document.getElementById("destinations-tag").textContent));

    $("#" + phone_input).val("");
    for (i in destinations) {
        if (destinations[i].fields.address == $("#" + address_input).val()) {
            $("#" + phone_input).val(destinations[i].fields.phone);
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

