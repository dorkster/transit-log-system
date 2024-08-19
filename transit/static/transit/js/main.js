function inputScrollToView(target) {
    if (!target)
        return;

    if (/Mobi|Android/i.test(navigator.userAgent)) {
        target.scrollIntoView();
        window.scrollBy(0, -50);
    }
}

function AjaxLoader(url, div_id) {
    this.first_response = false;
    this.url = url;
    this.div_id = div_id;
    this.extra_data = {};
    this.interval = null;
    this.interval_delay = 10000;

    var self = this;
    self.start = function(delay=self.interval_delay) {
        self.interval_delay = delay;
        if (delay > 0) {
            self.interval = setInterval(function() { self.run(); }, delay);
        }
    }
    self.stop = function() {
        if (self.interval != null)
            clearInterval(self.interval);
        self.interval = null;
    }
    self.restart = function() {
        if (self.interval != null)
            self.stop();
        self.start();
    }

    self.resume = function() {
        self.restart();
        self.run();
    }

    self.animationDone = function() {
        event.currentTarget.style.display = "none";
        event.currentTarget.p_done = true;
    }

    self.animationDoneEarly = function() {
        event.currentTarget.p_done = true;
    }

    self.run = function(target_id="", target_action="", target_data="") {
        ajax_loading = document.querySelector("#ajax-loading");
        ajax_loading.p_done = false;

        ajax_loading.style.animation = 'none';
        ajax_loading.offsetHeight; // trigger reflow
        ajax_loading.style.animation = null;

        ajax_loading.removeEventListener("animationend", self.animationDone);
        ajax_loading.removeEventListener("animationend", self.animationDoneEarly);

        ajax_loading.style.display = "initial";
        ajax_loading.addEventListener("animationend", self.animationDoneEarly);

        if ( $('.ajax-blocker.show').length == 0 || target_action != "") {
            $('.modal.ajax-blocker.show').off('hidden.bs.modal');
            $('.modal.ajax-blocker.show').modal('hide');
            $('.dropdown.ajax-blocker.show').off('hidden.bs.dropdown');

            $.ajax({
                type: "GET",
                url: self.url,
                data: Object.assign({}, {
                    "target_id": target_id,
                    "target_action": target_action,
                    "target_data": target_data
                }, self.extra_data)
            })
            .done(function(response) {
                    $(self.div_id).html(response);
                    if (!self.first_response) {
                        self.first_response = true;
                        var hash = window.location.hash.substr(1);
                        if (hash && hash != '_') {
                            var hash_element = document.getElementById(hash);
                            if (hash_element) {
                                // hash_element.scrollIntoView({behavior: "smooth", block: "center"});
                                if (hash_element.dataset.scrollintoview == "start")
                                    hash_element.scrollIntoView({block: "start"});
                                else
                                    hash_element.scrollIntoView({block: "center"});
                            }
                        }
                    }

                    ajax_loading.addEventListener("animationend", self.animationDone);
                    if (ajax_loading.p_done) {
                        ajax_loading.style.display = "none";
                    }
                    self.restart();
            });
        }
        else {
            self.stop();
            // when the ajax blocker is hidden, fire a new ajax request
            $('.modal.ajax-blocker.show').one('hidden.bs.modal', self.resume);
            $('.dropdown.ajax-blocker.show').one('hidden.bs.dropdown', self.resume);
        }
    }
}

function getCurrentTime(input) {
    var time = new Date();
    var hour = time.getHours();
    var minute = time.getMinutes();

    var time_str = '' + ((hour > 12) ? hour - 12 : hour);
    if (hour == 0)
        time_str = '12';
    time_str += ((minute < 10) ? ':0' : ':') + minute;
    time_str += (hour >= 12) ? ' PM' : ' AM';

    $("#" + input).val(time_str);
}

function setParam(param, value) {
    var url = new URL(location);
    url.searchParams.set(param, value);
    window.open(url, "_self");
}

function RowMover(row_class, ajax_ldr) {
    this.item = "";
    this.row_class = row_class;
    this.button = null;
    this.ajax_loader = ajax_ldr;

    var self = this;

    self.toggle = function(button, item) {
        if (self.item != item) {
            self.clear();

            $("." + row_class).each(function(index, value) {
                $(value).removeClass("mytable-sort-hidden");
                $(value).addClass("ajax-blocker show");
                $(value).children().html("<span class=\"oi oi-resize-height mr-4\"></span>Move selected row to here<span class=\"oi oi-resize-height ml-4\"></span>");

                $(button).removeClass("btn-outline-dark");
                $(button).addClass("btn-primary active");
            });

            button.scrollIntoView({behavior: "smooth", block: "center"});

            self.item = item;
            self.button = button;
        }
        else {
            button.scrollIntoView({behavior: "smooth", block: "center"});
            self.clear();
            self.ajax_loader.resume();
        }
    };

    self.clear = function() {
        $(".btn-row-mover").each(function(index, value) {
            $(value).removeClass("btn-primary active");
            $(value).addClass("btn-outline-dark");
        });

        $("." + row_class).each(function(index, value) {
            $(value).addClass("mytable-sort-hidden");
            $(value).removeClass("ajax-blocker show");
            $(value).children().html("");
        });
        self.item = "";
        self.button = null;
    };

    self.moveItem = function(target) {
        if (self.item != "") {
            var original_item = self.item;
            self.clear();
            self.ajax_loader.run(original_item, "mv", target);
        }
    };

    // handle ajax-blockers
    $(".dropdown.ajax-blocker").on("show.bs.dropdown", function() {
        self.clear();
    });
    $(".modal.ajax-blocker").on("show.bs.modal", function() {
        self.clear();
    });

    // clear when pressing escape
    $(document).keydown(function(e) {
        if (e.key == "Escape") {
            self.clear();
        }
    });
}

function focusFromParam() {
    var params = (new URL(document.location)).searchParams;
    var focus = params.get("focus");
    if (focus && focus != "") {
        var focus_elm = $("#" + focus);

        if (focus_elm.attr("type") == "text" || focus_elm.prop("tagName") == "TEXTAREA") {
            var focus_len = focus_elm.val().length;
            focus_elm[0].setSelectionRange(focus_len, focus_len);
        }
        focus_elm.focus()
        focus_elm[0].scrollIntoView({behavior: "smooth", block: "center"});
    }
}

function editCell(url, row_movers=null) {
    var row_movers_cleared = true;

    if (row_movers) {
        for (var i = 0; i < row_movers.length; i++) {
            if (row_movers[i].item != "")
                row_movers_cleared = false;
            row_movers[i].clear();
        }
    }
    if (row_movers_cleared) {
        window.location.assign(url);
    }
}

function checkForm(form, ev) {
    if ($(form).data('submitted'))
        ev.preventDefault();
    else
        $(form).data('submitted', true);
    return true;
}

function cookieRead(c) {
    if (document.cookie.split(";").some( function(item) { return item.trim().indexOf(c) == 0 } )) {
        return document.cookie.split(";").find(row => row.startsWith(c)).split("=")[1];
    }
    else {
        return "";
    }
}

function getTagButtonStyle(tag_name) {
    if (typeof tags !== 'undefined') {
        var lower_tag = tag_name.toLowerCase();
        for (tag_index in tags) {
            if (tags[tag_index].fields["name"].toLowerCase() == lower_tag)
                if (tags[tag_index].fields["style"] == 1)
                    return "btn-warning";
        }
    }
    return "btn-info";
}

function setEditButtonStyleFromHash(prefix, hash, style = 0) {
    if (hash != "" && hash.startsWith(prefix)) {
        if (style == 1) {
            $(hash).addClass('active');
        }
        else {
            $(hash).removeClass('btn-outline-dark');
            $(hash).addClass('btn-outline-primary');
        }
    }
}

function setSearchModal(form_id, modal_id, search_id, search_text, search_func) {
    $(form_id).on('submit', function(e){
        e.preventDefault();
        $(modal_id).modal('hide');
        search_func(search_id);
    });
    $(modal_id).on('show.bs.modal', function(){
        $(search_id).val(search_text);
    });

    if (modal_id == "#modal_filter_search") {
        // this modal has no other controls other than the search box
        // so, we can focus the text box automatically
        $(modal_id).on('shown.bs.modal', function(){
            $(search_id).focus();
            $(search_id).select();
        });
    }
}

function datePickerDaysEnabled(year_id, month_id, day_id) {
    let year = parseInt($(year_id).val());
    let month = parseInt($(month_id).val()) - 1;
    let day = parseInt($(day_id).val());

    let end_of_day_list_offset = (parseInt($(day_id).children('option').length) - 31) - 1;
    let end_of_month = 31;
    let fields_complete = !(isNaN(year) || isNaN(month) || isNaN(day));

    for (let i = 31; i >= 28; i--) {
        let test_date = new Date(year, month, i);
        if (fields_complete && (isNaN(test_date.valueOf()) || (test_date.getFullYear() != year || test_date.getMonth() != month))) {
            $(day_id).children("option").eq(i + end_of_day_list_offset).prop("hidden", true);
            end_of_month = end_of_month - 1;
        }
        else {
            $(day_id).children("option").eq(i + end_of_day_list_offset).prop("hidden", false);
        }
    }
    if (day > end_of_month) {
        $(day_id).val(end_of_month.toString());
    }
}

function setupDatePickerEvents(year_id, month_id, day_id) {
    datePickerDaysEnabled(year_id, month_id, day_id);
    $(month_id).on("change", function() {
        datePickerDaysEnabled(year_id, month_id, day_id);
    });
    $(year_id).on("change", function() {
        datePickerDaysEnabled(year_id, month_id, day_id);
    });
    $(day_id).on("change", function() {
        datePickerDaysEnabled(year_id, month_id, day_id);
    });
}
