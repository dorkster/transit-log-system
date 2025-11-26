function setResolvedColor() {
    if ($("#id_status").val() == "1") {
        $("#id_status").addClass("bg-success text-light");
        $("#resolution_details").collapse("show");
    }
    else {
        $("#id_status").removeClass("bg-success text-light");
        $("#resolution_details").collapse("hide");
    }
}

function setPrioritySelectColor() {
    var default_classname = "form-control form-control-width-fix";
    $("#id_priority").removeClass();

    if ($("#id_priority").val() == "2")
        $("#id_priority").addClass(default_classname + " bg-danger text-light");
    else if ($("#id_priority").val() == "1")
        $("#id_priority").addClass(default_classname + " bg-warning");
    else
        $("#id_priority").addClass(default_classname);
}

function setupFormEvents() {
    $("#id_status").on("change", setResolvedColor);
    $("#id_priority").on("change", setPrioritySelectColor);
}
