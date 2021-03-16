# Copyright © 2019-2021 Justin Jacobs
#
# This file is part of the Transit Log System.
#
# The Transit Log System is free software: you can redistribute it and/or modify it under the terms
# of the GNU General Public License as published by the Free Software Foundation,
# either version 3 of the License, or (at your option) any later version.
#
# The Transit Log System is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# The Transit Log System.  If not, see http://www.gnu.org/licenses/

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

