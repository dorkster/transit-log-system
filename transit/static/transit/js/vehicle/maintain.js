function updateDateDay() {
    if ($("#id_inspection_date_month").val() == "" && $("#id_inspection_date_year").val() == "") {
        $("#id_inspection_date_day").val("");
    }
    else {
        $("#id_inspection_date_day").val(1);
    }
}

function setupFormEvents() {
    $("#id_inspection_date_month").on("change", updateDateDay);
    $("#id_inspection_date_year").on("change", updateDateDay);
}
