def int_to_money_string(val, show_currency=False):
    currency_str = ''
    if show_currency:
        currency_str = '$'

    abs_value = abs(val)
    sign_str = ''

    if (val < 0):
        sign_str = '-'
    if abs_value < 10:
        return sign_str + currency_str + '0.0' + str(abs_value)
    elif abs_value < 100:
        return sign_str + currency_str + '0.' + str(abs_value)
    else:
        val_str = str(abs_value)
        return sign_str + currency_str + val_str[0:len(val_str)-2] + '.' + val_str[len(val_str)-2:]
