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
    $("#mile_suggestion_error").hide();
    $("#mile_suggestion_typo_warning").hide();

    if (shift_prev_miles != "" && combined_miles != "") {
        var high_mileage_threshold = 250;

        var combined_miles_f = parseFloat(combined_miles);
        var shift_prev_miles_f = parseFloat(shift_prev_miles);

        if (combined_miles_f < shift_prev_miles_f || combined_miles_f >= shift_prev_miles_f + high_mileage_threshold) {
            var suggestions = [];

            var scored_suggestion = scoreSuggestion(combined_miles, shift_prev_miles, new_miles);
            if (scored_suggestion[1] <= high_mileage_threshold) {
                suggestions.push(scored_suggestion);
            }

            // try dropping the first character
            var shortened_new_miles = new_miles;
            if (shortened_new_miles.length > 3) {
                shortened_new_miles = shortened_new_miles.substring(1);
                var scored_suggestion = scoreSuggestion(combined_miles, shift_prev_miles, shortened_new_miles);
                if (scored_suggestion[1] <= high_mileage_threshold) {
                    suggestions.push(scored_suggestion);
                }
            }

            // try reformatting as if a decimal character was missed
            if (new_miles.length >= 3 && new_miles.endsWith(".0")) {
                var missed_decimal_miles = new_miles.slice(0, -3) + "." + new_miles.slice(-3, -2);
                var scored_suggestion = scoreSuggestion(combined_miles, shift_prev_miles, missed_decimal_miles);
                if (scored_suggestion[1] <= high_mileage_threshold) {
                    suggestions.push(scored_suggestion);
                }
            }

            // sort by score
            suggestions.sort(function(a, b) {
                return a[1] - b[1];
            });

            var suggest_prefix = "";
            var suggest_suffix = "";

            $("#full_miles").append('<span class="text-danger"><strong><span class="ml-3 oi oi-warning"></span></strong></span>');

            if (suggestions.length > 0) {
                var suggest_miles = suggestions[0][0];
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

                $("#mile_suggestion").show();
                $("#mile_suggestion_prefix").html(suggest_prefix);
                $("#mile_suggestion_suffix").html(suggest_suffix);
                $("#mile_suggestion_button").data("suggestion", suggest_suffix);
            }
            else {
                $("#mile_suggestion_error").show();
            }
        }
    }
}

function scoreSuggestion(combined_miles, shift_prev_miles, new_miles) {
    var prev_prefix_miles = shift_prev_miles.substring(0, shift_prev_miles.length - new_miles.length);

    if ((combined_miles == prev_prefix_miles + new_miles) || (parseFloat(prev_prefix_miles + new_miles) < parseFloat(shift_prev_miles))) {
        if (prev_prefix_miles == "") {
            prev_prefix_miles = "1";
        }
        else {
            prev_prefix_miles = (parseFloat(prev_prefix_miles) + 1).toString();
        }
    }

    var suggest_miles = prev_prefix_miles + new_miles;
    var score = Math.abs(parseFloat(suggest_miles) - parseFloat(shift_prev_miles));

    return [suggest_miles, score];
}

function useSuggestion(button, mile_data) {
    $("#id_miles").val($(button).data("suggestion"));
    showFullMiles(mile_data);
}

function mileageErrorTryAgain(mile_data) {
    $("#id_miles").val("");
    showFullMiles(mile_data);
    $("#id_miles").focus();
}

function setupFormEvents(mile_data, trip_date=null) {
    $("#id_miles").on("change", function() { showFullMiles(mile_data); });
    $("#id_miles").on("input", function() { showFullMiles(mile_data); });
    $("#id_vehicle").on("change", function() { showFullMiles(mile_data); });

    if (trip_date != null) {
        $("#id_driver").on("change", function() { onDriverChange(); showFullMiles(mile_data); });
    }
}

function setupSimpleFormEvents(trip_date=null) {
    if (trip_date != null) {
        $("#id_driver").on("change", function() { onDriverChange(); });
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

function toggleHomeDropOff(btn, trip_destination, client_address) {
    var field = document.getElementById("id_home_drop_off");
    var trip_dest_badge = document.getElementById("trip_dest_badge");
    var additional_trips_dest = document.getElementById("additional_trips_dest");

    if (field) {
        if (field.value == "False") {
            if (confirm("Change destination to '" + client_address + "'?") == true) {
                field.value = "True";
                btn.classList.remove("btn-outline-dark");
                btn.classList.add("btn-primary");
                btn.firstChild.classList.remove("oi-circle-x");
                btn.firstChild.classList.add("oi-circle-check");

                if (trip_dest_badge) {
                    trip_dest_badge.innerHTML = client_address;
                }
                if (additional_trips_dest) {
                    additional_trips_dest.innerHTML = client_address;
                }
            }
        }
        else {
            field.value = "False";
            btn.classList.remove("btn-primary");
            btn.classList.add("btn-outline-dark");
            btn.firstChild.classList.remove("oi-circle-check");
            btn.firstChild.classList.add("oi-circle-x");

            if (trip_dest_badge) {
                trip_dest_badge.innerHTML = trip_destination;
            }
            if (additional_trips_dest) {
                additional_trips_dest.innerHTML = trip_destination;
            }
        }
    }
}

