function showFullMiles(mile_data) {
    var shift_start_miles = mile_data["start"]
    var shift_prev_miles = mile_data["prev"];

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

function setupFormEvents(mile_data) {
    $("#id_miles").on("change", function() { showFullMiles(mile_data); });
    $("#id_miles").on("input", function() { showFullMiles(mile_data); });
}

