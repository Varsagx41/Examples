from django.db.models.fields.related import RelatedField
from django.db.models import DateTimeField, DateField, TimeField
from django.utils.functional import cached_property
from .redis import cache
from .conf import settings, logger
import datetime
from time import mktime
import ujson as json


class Behavior(object):
    model = None
    key = None
    where = {}

    def __init__(self, timeout=None, where=None):
        if timeout is not None:
            self.timeout = timeout
        else:
            self.timeout = settings.CACHEPHOBIA_DEFAULTS['timeout']
        if where is not None:
            self.where = where

    def contribute_to_class(self, model):
        if self.model is None:
            self.model = model
        if self.key is None:
            self.key = model.__name__.lower()

    def _obj_to_values(self, obj):
        values = {}
        for field in obj._meta.fields:
            values[field.attname] = self._convert_for_values(getattr(obj, field.attname))
        return values

    def _values_to_obj(self, values):
        new_values = {}
        for key, value in values.iteritems():
            new_values[key] = self._convert_for_obj(key, value)

        return self.model(**new_values)

    def _convert_for_values(self, value):
        if isinstance(value, (datetime.datetime, datetime.date)):
            return int(mktime(value.timetuple()))
        elif isinstance(value, datetime.time):
            return value.strftime("%H:%M")
        else:
            return value

    def _convert_for_obj(self, key, value):
        field = self.model._meta.get_field(key)
        if isinstance(field, DateTimeField):
            return datetime.datetime.fromtimestamp(value)
        elif isinstance(field, DateField):
            return datetime.date.fromtimestamp(value)
        elif isinstance(field, TimeField):
            return datetime.time(*map(int, value.split(':')))
        else:
            return value

    def _serialize(self, values):
        return json.dumps(values)

    def _deserialize(self, value):
        return json.loads(value)

    def get(self, pk):
        '''
        Required method.
        Get values from cache, otherwise get values from DB
        and set values in cache.
        Required, because in future versions it can be implemented
        in '_fetch_all' queryset method.
        Return: dictionary of values
        '''
        pass

    def get_many(self, pks):
        '''
        Required method.
        Get many values from cache, not found values get from DB
        and set this values in cache.
        Required, because in future versions it can be implemented
        in '_fetch_all' queryset method.
        Return: {pk: {values}, ...}
        '''
        pass

    def set(self, obj, created=False, pipe=None, extra=None):
        '''
        Recommended method (useful for inheritance).
        Args: obj = <instance of model>,
              created = <bool> if new object has been created in DB,
              pipe = <redis pipeline>,
              extra = <dict> that need to append to result,
        Return: same as get method
        '''
        pass

    def set_many(self, obj, created=False, extra=None):
        '''
        Recommended method (useful for inheritance).
        Args: objs = <instances of model>,
              created = <bool> if new objects have been created in DB,
              extra = <dict> that need to append to result,
        Return: same as get_many method
        '''
        pass

    def on_save(self, instance, **kwargs):
        '''
        Required for cache invalidation.
        Method that will be called from 'post_save' signal.
        '''
        pass

    def on_delete(self, instance=None, queryset=None, count=None, **kwargs):
        '''
        Required for cache invalidation.
        Method that will be called from custom 'pure_post_delete' signal.
        'post_delete' is not used to avoid conflicts.
        '''
        pass

    def on_update(self, queryset, **updated):
        '''
        Required for cache invalidation.
        Method that will be called from custom 'post_update' signal.
        '''
        pass

    # def invalidate_all(self):
        '''
        Any method starting with 'invalidate_' can be used
        from './manage.py invalidate'.
        Args: any arguments, that can be passed through console
        Return: number of invalidated entries
        '''
        # pass


class LonerBehavior(Behavior):
    '''
    To control cache of one object (JSON)
    '''

    def _get_key(self, pk):
        return '%s:%s' % (self.key, pk)

    def _get_keys(self, pks):
        keys = []
        for pk in pks:
            keys.append('%s:%s' % (self.key, pk))
        return keys

    def _delete_by_ids(self, queryset):
        ids = queryset.cp_ids
        if ids is not None:
            keys = self._get_keys(ids)
            cache.delete(*keys)
        else:
            logger.debug('[CACHEPHOBIA] <DELETE/UPDATE> Request without specified IDs that can not be invalidated')

        return ids

    def get(self, pk):
        cached = cache.get(self._get_key(pk))
        if cached is not None:
            # cache_read.send(sender=self.model, hit=True)
            return self._deserialize(cached)
        else:
            try:
                obj = self.model.objects.get(pk=pk, **self.where)
            except self.model.DoesNotExist:
                return None
            else:
                return self.set(obj)

    def get_many(self, pks):
        if len(pks) == 0: return {}

        pks = tuple(set(pks))
        keys = self._get_keys(pks)
        mcached = cache.mget(keys)

        result = {}
        misses = []
        # hit = False
        for i, cached in enumerate(mcached):
            if cached is None:
                misses.append(pks[i])
                result[pks[i]] = None
            else:
                result[pks[i]] = self._deserialize(cached)
                # hit = True

        # if hit:
        #     cache_read.send(sender=self.model, hit=True)

        if len(misses) > 0:
            objs = self.model.objects.filter(pk__in=misses, **self.where)
            if len(objs) > 0:
                set_result = self.set_many(objs)
                result.update(set_result)

        return result

    def set(self, obj, created=False, pipe=None, extra=None):
        values = self._obj_to_values(obj)
        if extra is not None:
            values.update(extra)

        serialized = self._serialize(values)
        if pipe is None:
            cache.set(self._get_key(obj.pk), serialized, self.timeout)
        else:
            pipe.set(self._get_key(obj.pk), serialized, self.timeout)

        return values

    def set_many(self, objs, created=False, extra=None):
        result = {}
        pipe = cache.pipeline()
        for obj in objs:
            if obj is not None:
                result[obj.pk] = self.set(obj, created=created, pipe=pipe, extra=extra)
            else:
                result[obj.pk] = None
        pipe.execute()
        return result

    def on_save(self, instance, **kwargs):
        self.set(instance, created=kwargs['created'])

    def on_delete(self, instance=None, queryset=None, count=None, **kwargs):
        if queryset is not None:
            self._delete_by_ids(queryset)
        elif instance is not None:
            cache.delete(self._get_key(instance.pk))

    def on_update(self, queryset, **updated):
        self._delete_by_ids(queryset)

    def invalidate_all(self):
        keys = cache.keys('%s:*' % (self.key))
        if len(keys) > 0:
            return cache.delete(*keys)
        return 0

    def invalidate_pk(self, pk):
        return cache.delete(self._get_key(pk))


class PrimitiveHerdBehavior(Behavior):
    '''
    To control cache of all objects in model (for very small models).
    When often need to get all objects, but rarely to add, delete or update
    '''

    @cached_property
    def _key_all(self):
        return '%s:all' % (self.key)

    def get(self, pk):
        all_values = self.get_all()
        return all_values.get(str(pk), None)

    def get_many(self, pks):
        all_values = self.get_all()
        result = {}
        for pk in pks:
            result[pk] = all_values.get(str(pk), None)
        return result

    def get_all(self):
        cached = cache.get(self._key_all)
        if cached is not None:
            #cache_read.send(sender=self.model, hit=True)
            return self._deserialize(cached)
        else:
            objs = self.model.objects.filter(**self.where)
            return self.set(objs)

    def set(self, objs, created=False, pipe=None, extra=None):
        values = {}
        for obj in objs:
            values[str(obj.pk)] = self._obj_to_values(obj)
        serialized = self._serialize(values)
        if pipe is None:
            cache.set(self._key_all, serialized, self.timeout)
        else:
            pipe.set(self._key_all, serialized, self.timeout)

        return values

    def on_save(self, instance, **kwargs):
        cache.delete(self._key_all)

    def on_delete(self, instance=None, queryset=None, count=None, **kwargs):
        cache.delete(self._key_all)

    def on_update(self, queryset, **updated):
        cache.delete(self._key_all)

    def invalidate_all(self):
        return cache.delete(self._key_all)


class AdvancedHerdBehavior(LonerBehavior):
    '''
    To control cache of all objects in model (for small models).
    When often need to get, add, delete or update objects, but
    sometimes need to get all objects.
    '''

    @cached_property
    def _key_all_ids(self):
        return '%s:all.ids' % (self.key)

    def get_all(self):
        ids = map(int, cache.smembers(self._key_all_ids))
        if not ids:
            ids = self.model.objects.values_list('pk', flat=True).filter(**self.where)
            cache.sadd(self._key_all_ids, *ids)
        return self.get_many(ids)

    def set(self, obj, created=False, pipe=None, extra=None):
        values = super(AdvancedHerdBehavior, self).set(obj, created=created, pipe=pipe, extra=extra)
        if created:
            cache.sadd(self._key_all_ids, obj.pk)
        return values

    def set_many(self, objs, created=False, extra=None):
        result = super(AdvancedHerdBehavior, self).set_many(objs, created=created, extra=extra)
        if created:
            cache.sadd(self._key_all_ids, *result.keys())
        return result

    def on_delete(self, instance=None, queryset=None, count=None, **kwargs):
        if queryset is not None:
            ids = self._delete_by_ids(queryset)
            cache.srem(self._key_all_ids, ids)
        elif instance is not None:
            cache.delete(self._get_key(instance.pk))
            cache.srem(self._key_all_ids, instance.pk)

    def invalidate_idslist(self):
        return cache.delete(self._key_all_ids)
