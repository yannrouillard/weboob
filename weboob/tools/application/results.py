# -*- coding: utf-8 -*-

# Copyright(C) 2010-2011 Christophe Benz
#
# This file is part of weboob.
#
# weboob is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# weboob is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with weboob. If not, see <http://www.gnu.org/licenses/>.

import weboob.tools.date as date_utils
from weboob.capabilities import UserError
from datetime import date


__all__ = ['ResultsCondition', 'ResultsConditionError']


class IResultsCondition(object):
    def is_valid(self, obj):
        raise NotImplementedError()


class ResultsConditionError(UserError):
    pass


class Condition(object):
    def __init__(self, left, op, right):
        self.left = left  # Field of the object to test
        self.op = op
        self.right = right


def is_egal(left, right):
    return left == right


def is_notegal(left, right):
    return left != right


def is_sup(left, right):
    return left < right


def is_inf(left, right):
    return left > right


def is_in(left, right):
    return left in right

functions = {'!=': is_notegal, '=': is_egal, '>': is_sup, '<': is_inf, '|': is_in}


class ResultsCondition(IResultsCondition):
    condition_str = None

    # Supported operators
    # =, !=, <, > for float/int/decimal
    # =, != for strings
    # We build a list of list. Return true if each conditions of one list is TRUE
    def __init__(self, condition_str):
        or_list = []
        for _or in condition_str.split(' OR '):
            and_list = []
            for _and in _or.split(' AND '):
                operator = None
                for op in ['!=', '=', '>', '<', '|']:
                    if op in _and:
                        operator = op
                        break
                if operator is None:
                    raise ResultsConditionError(u'Could not find a valid operator in sub-expression "%s". Protect the complete condition expression with quotes, or read the documentation in the man manual.' % _and)
                try:
                    l, r = _and.split(operator)
                except ValueError:
                    raise ResultsConditionError(u'Syntax error in the condition expression, please check documentation')
                and_list.append(Condition(l, operator, r))
            or_list.append(and_list)
        self.condition = or_list
        self.condition_str = condition_str

    def is_valid(self, obj):
        d = dict(obj.iter_fields())
        # We evaluate all member of a list at each iteration.
        for _or in self.condition:
            myeval = True
            for condition in _or:
                if condition.left in d:
                    # We have to change the type of v, always gived as string by application
                    typed = type(d[condition.left])
                    try:
                        if isinstance(d[condition.left], date_utils.date):
                            tocompare = date(*[int(x) for x in condition.right.split('-')])
                        else:
                            tocompare = typed(condition.right)
                        myeval = functions[condition.op](tocompare, d[condition.left])
                    except:
                        myeval = False
                else:
                    raise ResultsConditionError(u'Field "%s" is not valid.' % condition.left)
                # Do not try all AND conditions if one is false
                if not myeval:
                    break
            # Return True at the first OR valid condition
            if myeval:
                return True
        # If we are here, all OR conditions are False
        return False

    def __str__(self):
        return unicode(self).encode('utf-8')

    def __unicode__(self):
        return self.condition_str
