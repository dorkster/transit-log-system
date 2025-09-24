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

