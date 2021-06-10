function checklistFail(id) {
    $('#fail_' + id).removeClass("btn-outline-dark");
    $('#fail_' + id).addClass("btn-danger");
    $('#pass_' + id).removeClass("btn-success");
    $('#pass_' + id).addClass("btn-outline-dark");

    checklist_data[id].status = 1;

    $('#id_checklist').val(JSON.stringify(checklist_data));
    validateFailPass();

    $('#issuebox_' + id).collapse('show');
}

function checklistPass(id) {
    $('#fail_' + id).removeClass("btn-danger");
    $('#fail_' + id).addClass("btn-outline-dark");
    $('#pass_' + id).removeClass("btn-outline-dark");
    $('#pass_' + id).addClass("btn-success");

    checklist_data[id].status = 2;
    $('#id_checklist').val(JSON.stringify(checklist_data));

    validateFailPass();

    $('#issuebox_' + id).collapse('hide');
}

function validateFailPass() {
    for (var key in checklist_data) {
        if (checklist_data.hasOwnProperty(key))
            if (checklist_data[key].status == 0) {
                // invalid form, disable the submit button
                $('#submit').prop('disabled', true);
                return
            }
    }

    // valid form, enable the submit button
    $('#submit').prop('disabled', false);
}

function updateIssuePriority(input, key) {
    if (input.value == "2") {
        input.classList.remove("bg-warning");
        input.classList.add("bg-danger", "text-light");
    }
    else if (input.value == "1") {
        input.classList.remove("bg-danger", "text-light");
        input.classList.add("bg-warning");
    }
    else {
        input.classList.remove("bg-danger", "bg-warning", "text-light");
    }

    checklist_data[key].issue_prio = parseInt(input.value);
    $('#id_checklist').val(JSON.stringify(checklist_data));
}

function updateIssue(input, key) {
    checklist_data[key].issue = input.value;
    $('#id_checklist').val(JSON.stringify(checklist_data));
}

