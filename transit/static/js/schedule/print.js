function printFilter(field, data) {
    if (field == "reset") {
        $("#id_driver").val("");
        $("#id_vehicle").val("");
        $("#id_search").val("");
        $("#id_hide_completed").val("");
        $("#id_hide_canceled").val("");
        $("#id_hide_nolog").val("");
    }
    else if (field == "driver") {
        $("#id_driver").val(data);
    }
    else if (field == "vehicle") {
        $("#id_vehicle").val(data);
    }
    else if (field == "search") {
        $("#id_search").val(data);
    }
    else if (field == "toggle_completed") {
        var current_val = $("#id_hide_completed").val();
        if (current_val == "" || current_val == "0")
            $("#id_hide_completed").val("1");
        else
            $("#id_hide_completed").val("0");
    }
    else if (field == "toggle_canceled") {
        var current_val = $("#id_hide_canceled").val();
        if (current_val == "" || current_val == "0")
            $("#id_hide_canceled").val("1");
        else
            $("#id_hide_canceled").val("0");
    }
    else if (field == "toggle_nolog") {
        var current_val = $("#id_hide_nolog").val();
        if (current_val == "" || current_val == "0")
            $("#id_hide_nolog").val("1");
        else
            $("#id_hide_nolog").val("0");
    }

    $("#filter_form").submit();
}

