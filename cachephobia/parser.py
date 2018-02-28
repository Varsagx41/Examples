from django.db.models.sql import OR
from django.db.models.lookups import Lookup, Exact, In, IsNull


def get_qs_ids(queryset, only=False):
    where = queryset.query.where
    if only and len(where) != 1:
        return None

    pkname = queryset.model._meta.pk.attname
    value, info = _find(where, pkname, lookups=(Exact, In))

    if value is not None:
        if isinstance(value, (list, tuple)):
            value = list(value)
        else:
            value = [value]

    return value


def _find(where, what, lookups=(Exact,), negate=False, op_or=False,
          extra=None):

    if isinstance(where, Lookup):
        if isinstance(where, lookups):
            attname = where.lhs.target.attname
            if attname == what:
                extra['lookup'] = where
                return where.rhs, extra
    else:
        if where.negated and not negate:
            return None, None

        if where.connector == OR and not op_or:
            return None, None

        if extra is None:
            extra = {'negated': False, 'op': 'AND', 'lookup': None}

        new_extra = {}
        new_extra['negated'] = extra['negated'] | where.negated
        new_extra['op'] = 'OR' if where.connector == OR or extra['op'] == 'OR' else 'AND'

        for child in where.children:
            value, info = _find(child, what, lookups, negate, op_or, new_extra)
            if value is not None:
                return value, info

    return None, None
