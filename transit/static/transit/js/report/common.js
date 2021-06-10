function ReportVisibility() {
    this.data = [];
    this.length = 0;

    var self = this;
    self.addSection = function(div_id, checkbox_id, is_visible=1) {
        self.data.push([is_visible, div_id, checkbox_id]);
        self.length += 1;
    }
}

function visibleLoad(v) {
    var cookie_str = cookieRead("report_visibility");

    for (i = 0; i < v.length; i++) {
        v.data[i][0] = 1;
    }
    for (i = 0; i < cookie_str.length; i++) {
        v.data[i][0] = parseInt(cookie_str.charAt(i));
    }

    visibleApply(v);
}

function visibleApply(v) {
    var show_all_btn = false;

    for (i = 0; i < v.length; i++) {
        if ($(v.data[i][1]).length) {
            if (v.data[i][0] == 1) {
                $(v.data[i][2]).prop("checked", true);
                $(v.data[i][1]).removeClass("d-none");
            }
            else {
                $(v.data[i][2]).prop("checked", false);
                $(v.data[i][1]).addClass("d-none");
                show_all_btn = true;
            }
        }
    }

    if (show_all_btn == true) {
        $("#vis_all").removeClass("d-none");
    }
    else {
        $("#vis_all").addClass("d-none");
    }
}
