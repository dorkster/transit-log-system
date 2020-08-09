import re

def int_to_money_string(val, show_currency=False, blank_zero=False):
    if blank_zero and val == 0:
        return ''

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

def money_string_to_int(val):
    num_only = ''
    matches = re.findall('\d*', val)
    for i in matches:
        num_only += i

    if num_only == '':
        return 0
    else:
        return int(num_only)

