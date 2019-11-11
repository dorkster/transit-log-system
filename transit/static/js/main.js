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
        self.interval = setInterval(function() { self.run(); }, delay);
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

    self.run = function(target_id="", target_action="", target_data="") {
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
            $(self.div_id).html("")
            $(self.div_id).append(response);
            if (!self.first_response) {
                self.first_response = true;
                var hash = window.location.hash.substr(1);
                if (hash && hash != '_')
                    var hash_element = document.getElementById(hash);
                    if (hash_element) {
                        hash_element.scrollIntoView();
                        window.scrollBy(0, -25);
                    }
            }
        });
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

