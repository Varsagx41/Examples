import django.dispatch


pure_post_delete = django.dispatch.Signal(providing_args=["queryset", "count"], use_caching=True)
post_update = django.dispatch.Signal(providing_args=["queryset"], use_caching=True)
cache_read = django.dispatch.Signal(providing_args=["hit"])
# cache_write = django.dispatch.Signal(providing_args=["event"])