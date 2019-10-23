function inputScrollToView(target) {
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

    var self = this;
    self.start = function(delay=10000) {
        self.interval = setInterval(function() { self.run(); }, delay);
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
                if (hash)
                    document.getElementById(hash).scrollIntoView();
            }
        });
    }
}

