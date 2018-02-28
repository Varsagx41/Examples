from django.db.models import sql
from django.db.models.query import QuerySet
from django.db.models.manager import Manager
from django.db.models.signals import post_save, post_delete
from django.utils.functional import cached_property
from .signals import pure_post_delete, post_update, cache_read
from .conf import settings
from .parser import get_qs_ids
from funcy import once_per
import sys


def connect_first(signal, receiver, sender):
    old_receivers = signal.receivers
    signal.receivers = []
    signal.connect(receiver, sender=sender, weak=False)
    signal.receivers += old_receivers


def model_is_fake(model):
    return model.__module__ == '__fake__'


class CacheQuerySet(QuerySet):
    cp_behavior = None

    def _fetch_all(self):
        cache_read.send(sender=self.model, hit=False)
        super(CacheQuerySet, self)._fetch_all()

    def delete(self):
        '''
        Replaced to simple '_raw_delete' method to prevent
        extra 'SELECT' on delete if there are listeners of
        'post_delete' signal. Send custom 'pure_post_delete'
        signal to avoid conflicts.
        '''
        assert self.query.can_filter(), \
            "Cannot use 'limit' or 'offset' with delete."

        if self._fields is not None:
            raise TypeError("Cannot call delete() after .values() or .values_list()")

        count = sql.DeleteQuery(self.model).delete_qs(self, self.db)
        if count > 0 and self.cp_behavior is not None:
            pure_post_delete.send(sender=self.model, queryset=self, count=count)

        self._result_cache = None
        return count

    def update(self, **kwargs):
        count = super(CacheQuerySet, self).update(**kwargs)
        if count > 0:
            if self.cp_behavior is not None:
                post_update.send(sender=self.model, queryset=self, **kwargs)
        return count

    def _clone(self, **kwargs):
        clone = super(CacheQuerySet, self)._clone(**kwargs)
        clone.cp_behavior = self.cp_behavior
        return clone

    def nocache(self):
        self.cp_behavior = None
        return self

    @cached_property
    def cp_ids(self):
        return get_qs_ids(self)


class CacheManager(Manager):
    cp_behavior = None

    def __init__(self, behavior=None, *args, **kwargs):
        if settings.CACHEPHOBIA_ENABLED:
            self.cp_behavior = behavior
        super(CacheManager, self).__init__(*args, **kwargs)

    @once_per('cls')
    def _install_cachephobia(self, cls):
        if self.cp_behavior is not None:
            self.cp_behavior.contribute_to_class(cls)
            connect_first(post_save, self._post_save, sender=cls)
            connect_first(post_update, self._post_update, sender=cls)

            # For Model.objects.filter(**kwargs).delete()
            connect_first(pure_post_delete, self._pure_post_delete, sender=cls)

            # For instance.delete()
            connect_first(post_delete, self._post_delete, sender=cls)

            # Install auto-created models as their module
            # attributes to make them picklable
            module = sys.modules[cls.__module__]
            if not hasattr(module, cls.__name__):
                setattr(module, cls.__name__, cls)

    def contribute_to_class(self, cls, name):
        super(CacheManager, self).contribute_to_class(cls, name)
        if not model_is_fake(cls):
            self._install_cachephobia(cls)

    def get_queryset(self):
        qs = CacheQuerySet(self.model, using=self._db)
        qs.cp_behavior = self.cp_behavior
        return qs

    def _post_save(self, sender, instance, **kwargs):
        if self.cp_behavior is not None:
            self.cp_behavior.on_save(instance, **kwargs)

    def _post_delete(self, sender, instance=None, **kwargs):
        if self.cp_behavior is not None:
            self.cp_behavior.on_delete(instance=instance, **kwargs)

    def _pure_post_delete(self, sender, queryset=None, count=None, **kwargs):
        if self.cp_behavior is not None:
            self.cp_behavior.on_delete(queryset=queryset, count=count, **kwargs)

    def _post_update(self, sender, queryset, signal, **updated):
        if self.cp_behavior is not None:
            self.cp_behavior.on_update(queryset=queryset, **updated)

    def nocache(self):
        return self.get_queryset().nocache()
