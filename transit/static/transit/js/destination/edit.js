function setUpdateTripsDateVisibility() {
    if ($("#id_update_trips").val() == 2 || $("#id_update_trips").val() == 3) {
        $("#update_trips_date").collapse('show');
    }
    else {
        $("#update_trips_date").collapse('hide');
    }
}

function setupFormEvents() {
    $("#id_update_trips").on("change", setUpdateTripsDateVisibility);
}
