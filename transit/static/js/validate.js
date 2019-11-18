function validateTime(input) {
    if (input.value == "")
        return;

    var val_upper = input.value.toUpperCase();
    var val_stripped = val_upper.replace(/[^0-9A-Z]/g, '');

    var val_numonly = val_stripped.replace(/[^0-9]/g, '');
    if (val_numonly.length > 4)
        val_numonly = val_numonly.substring(val_numonly.length - 4, val_numonly.length)
    else if (val_numonly.length == 0) {
        input.value = "";
        return;
    }

    var AMPM = "";
    if (val_stripped.endsWith("AM"))
        AMPM = "AM";
    else if (val_stripped.endsWith("PM"))
        AMPM = "PM";

    var val_hour = "0";
    if (val_numonly.length == 4 || val_numonly.length == 2)
        val_hour = val_numonly.substring(0, 2);
    else if (val_numonly.length > 0)
        val_hour = val_numonly.substring(0, 1);

    var int_hour = parseInt(val_hour, 10) % 24;
    // when AMPM is undefined, treat 1-6 as PM (i.e. 13-18)
    if (AMPM == "" && int_hour >= 1 && int_hour <= 6) {
        int_hour += 12;
        AMPM = "PM";
    }
    else if (AMPM == "" && int_hour >= 12) {
        AMPM = "PM";
    }
    else if (AMPM == "") {
        AMPM = "AM";
    }

    if (int_hour >= 12)
        int_hour -= 12;

    val_hour = int_hour.toString();
    if (int_hour == 0)
        val_hour = "12";

    var val_minute = "0";
    if (val_numonly.length > 2)
        val_minute = val_numonly.substring(val_numonly.length - 2, val_numonly.length);

    var int_minute = parseInt(val_minute, 10) % 60;
    val_minute = int_minute.toString();
    while (val_minute.length < 2)
        val_minute = '0' + val_minute;

    input.value = val_hour + ":" + val_minute + " " + AMPM;
}

function validateMilesString(value, strip_leading_zero) {
    if (value == "")
        return "";

    var val_stripped = value.replace(/[^0-9\.]/g, '');

    if (val_stripped == "")
        return "";

    var val_split = val_stripped.split(".");

    var val_new = val_split[0];
    if (val_new == "")
        val_new = "0";

    if (strip_leading_zero && val_new != "0.0") {
        while (val_new.substring(0,1) == "0" && val_new.length > 1) {
            val_new = val_new.substring(1);
        }
    }

    if (val_split.length > 1) {
        if (val_split[1] != "")
            val_new += "." + val_split[1].substring(0,1);
        else
            val_new += ".0";
    }
    else {
        val_new += ".0";
    }

    return val_new;
}

function validateMiles(input, strip_leading_zero) {
    input.value = validateMilesString(input.value, strip_leading_zero);
}

function validateFuel(input) {
    if (input.value == "")
        return;

    var val_stripped = input.value.replace(/[^0-9\.]/g, '');

    if (val_stripped == "") {
        input.value = "";
        return;
    }

    var val_split = val_stripped.split(".");

    var val_new = val_split[0];
    if (val_new == "")
        val_new = "0";

    if (val_split.length > 1) {
        if (val_split[1] != "")
            val_new += "." + val_split[1].substring(0,1);
        else
            val_new += ".0";
    }
    else {
        val_new += ".0";
    }

    input.value = val_new;
}

function validatePhone(input) {
    if (input.value == "")
        return;

    var val_stripped = input.value.replace(/[^0-9]/g, '');

    if (val_stripped == "") {
        input.value = "";
        return;
    }

    var val_new = "";
    if (val_stripped.length == 11) {
        val_new = val_stripped.substring(0,1) + "-";
        val_new += val_stripped.substring(1,4) + "-";
        val_new += val_stripped.substring(4,7) + "-";
        val_new += val_stripped.substring(7,11);
    }
    else if (val_stripped.length == 10) {
        val_new = val_stripped.substring(0,3) + "-";
        val_new += val_stripped.substring(3,6) + "-";
        val_new += val_stripped.substring(6,10);
    }
    else if (val_stripped.length == 7) {
        val_new = val_stripped.substring(0,3) + "-";
        val_new += val_stripped.substring(3,7);
    }

    input.value = val_new;
}

function validateColor(input) {
    if (input.value == "")
        return;

    var val_upper = input.value.toUpperCase();
    var val_stripped = val_upper.replace(/[^0-9A-F]/g, '');

    if (val_stripped.length < 3)
        input.value = "";
    if (val_stripped.length == 3)
        input.value = val_stripped + val_stripped;
    else if (val_stripped.length > 3 && val_stripped.length < 6)
        input.value = val_stripped.substring(0,3) + val_stripped.substring(0,3);
    else if (val_stripped.length == 6 || val_stripped.length == 7)
        input.value = val_stripped.substring(0,6);
    else if (val_stripped.length >= 8)
        input.value = val_stripped.substring(0,8);
}

function validateMoney(input) {
    if (input.value == "")
        return;

    var val_stripped = input.value.replace(/[^0-9\.]/g, '');

    if (val_stripped == "") {
        input.value = "";
        return;
    }

    var val_split = val_stripped.split(".");

    var val_new = val_split[0];
    if (val_new == "")
        val_new = "0";

    if (val_split.length > 1) {
        if (val_split[1] != ""){
            var val_cents = val_split[1].replace(/[^0-9]/g, '').substring(0,2);
            while (val_cents.length < 2) {
                val_cents += "0";
            }
            val_new += "." + val_cents;
        }
        else
            val_new += ".00";
    }
    else {
        val_new += ".00";
    }

    input.value = val_new;
}

