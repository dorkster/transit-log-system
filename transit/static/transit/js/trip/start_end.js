function showFullMiles(mile_data) {
    var shift_start_miles = "";
    var shift_prev_miles = "";

    if ($("#id_vehicle").length) {
        // get selected vehicle from form
        var vehicle_index = $("#id_vehicle").prop("selectedIndex");
        if (vehicle_index != 0) {
            var current_vehicle = document.getElementById("id_vehicle").options[vehicle_index].text;
            shift_start_miles = mile_data["start"][current_vehicle];
            shift_prev_miles = mile_data["prev"][current_vehicle];
        }
    }
    else {
        // no form, assume the first vehicle
        for (var key in mile_data["start"]) {
            shift_start_miles = mile_data["start"][key];
            break;
        }
        for (var key in mile_data["prev"]) {
            shift_prev_miles = mile_data["prev"][key];
            break;
        }
    }

    $("#full_miles_desc").html("");

    var new_miles = validateMilesString($("#id_miles").val(), false);
    var prefix_miles = "";
    if (new_miles != "") {
        prefix_miles = shift_start_miles.substring(0, shift_start_miles.length - new_miles.length);
        $("#full_miles_desc").append('<span class="text-info">Match to the odometer:</span>');
    }
    var combined_miles = prefix_miles + new_miles;

    $("#full_miles").html("");
    $("#full_miles").append('<span class="text-muted">' + prefix_miles + '</span><strong>' + new_miles + '</strong>');

    $("#mile_suggestion").hide();
    if (shift_prev_miles != "" && combined_miles != "") {
        if (parseFloat(combined_miles) < parseFloat(shift_prev_miles)) {
            var prev_prefix_miles = shift_prev_miles.substring(0, shift_prev_miles.length - new_miles.length);

            if ((combined_miles == prev_prefix_miles + new_miles) || (parseFloat(prev_prefix_miles + new_miles) < parseFloat(shift_prev_miles))) {
                if (prev_prefix_miles == "") {
                    prev_prefix_miles = "1";
                }
                else {
                    prev_prefix_miles = (parseFloat(prev_prefix_miles) + 1).toString();
                }
            }

            var suggest_prefix = "";
            var suggest_suffix = "";

            var suggest_miles = prev_prefix_miles + new_miles;
            if (suggest_miles.length > combined_miles.length) {
                suggest_suffix = suggest_miles;
            }
            else {
                for (var i = 0; i < suggest_miles.length; i++) {
                    if (suggest_miles.charAt(i) == combined_miles.charAt(i)) {
                        suggest_prefix += suggest_miles.charAt(i);
                    }
                    else {
                        break;
                    }
                }
                suggest_suffix = suggest_miles.substring(suggest_prefix.length, suggest_miles.length);
            }

            $("#full_miles").append('<span class="text-danger"><strong><span class="ml-3 oi oi-warning"></span></strong></span>');
            $("#mile_suggestion").show();
            $("#mile_suggestion_prefix").html(suggest_prefix);
            $("#mile_suggestion_suffix").html(suggest_suffix);
            $("#mile_suggestion_button").data("suggestion", suggest_suffix);
        }
    }
}

function useSuggestion(button, mile_data) {
    $("#id_miles").val($(button).data("suggestion"));
    showFullMiles(mile_data);
}

function setupFormEvents(mile_data, trip_date=null) {
    $("#id_miles").on("change", function() { showFullMiles(mile_data); });
    $("#id_miles").on("input", function() { showFullMiles(mile_data); });
    $("#id_vehicle").on("change", function() { showFullMiles(mile_data); });

    if (trip_date != null) {
        $("#id_driver").on("change", function() { ajaxSetVehicleFromDriver(mile_data, trip_date); });
    }
}

function toggleAdditionalPickup(item_id) {
    var list_item = document.getElementById(item_id);
    if (list_item) {
        var additional_pickups = {};
        var json_field = document.getElementById("id_additional_pickups");
        if (json_field && json_field.value)
            additional_pickups = JSON.parse(json_field.value);

        if (list_item.classList.contains("active")) {
            list_item.classList.remove("active", "border", "border-white");
            additional_pickups[list_item.dataset.id] = false;
        }
        else {
            list_item.classList.add("active", "border", "border-white");
            additional_pickups[list_item.dataset.id] = true;
        }

        if (json_field)
            json_field.value = JSON.stringify(additional_pickups);
    }
}

function ajaxSetVehicleFromDriver(mile_data, trip_date) {
    $.ajax({
        type: "GET",
        url: ajax_set_vehicle_from_driver_url,
        data: {
            "year":trip_date["year"],
            "month":trip_date["month"],
            "day":trip_date["day"],
            "driver":$("#id_driver option:selected").val(),
        }
    })
    .done(function(response) {
        if (response.vehicle != "") {
            $("#id_vehicle option").filter(function() {
                return $(this).val() == response.vehicle;
            }).prop("selected", true);
        }
        else {
            $("#id_vehicle").prop("selectedIndex", 0);
        }
        showFullMiles(mile_data);
    });
}

