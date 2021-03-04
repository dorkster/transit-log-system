import re

from django.core.paginator import Paginator

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

def get_paginated_ranges(page, page_range, items_per_page):
    page_start = page.number - page_range - 1
    if page_start > page.paginator.num_pages - (page_range*2) - 1:
        page_start = page.paginator.num_pages - (page_range*2) - 1

    page_end = page.number + page_range
    if page_end < (page_range*2) + 1:
        page_end = (page_range*2) + 1

    item_count_start = ((page.number - 1) * items_per_page) + 1

    item_count_end = page.paginator.count
    if page.number * items_per_page < page.paginator.count:
        item_count_end = page.number * items_per_page

    return {'page_start': page_start, 'page_end': page_end, 'item_count_start': item_count_start, 'item_count_end': item_count_end }

