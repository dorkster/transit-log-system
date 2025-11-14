function setResolvedColor() {
    if ($("#id_is_resolved").val() == "True") {
        $("#id_is_resolved").addClass("bg-success text-light");
        $("#resolution_details").collapse("show");
    }
    else {
        $("#id_is_resolved").removeClass("bg-success text-light");
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
    $("#id_is_resolved").on("change", setResolvedColor);
    $("#id_priority").on("change", setPrioritySelectColor);
}
