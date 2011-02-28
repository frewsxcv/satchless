from django.conf import settings
from django.utils.importlib import import_module

_partitioners_queue = None
_delivery_providers_queue = None

def partition(cart):
    groups = []
    remaining_items = list(cart.items.all())
    for handler in _partitioners_queue:
        handled_groups, remaining_items = handler.partition(cart,
                                                            remaining_items)
        groups += handled_groups
    if remaining_items:
        raise ImproperlyConfigured('Unhandled items remaining in cart.')
    return groups

def get_delivery_types(delivery_group):
    types = []
    for provider_path, provider in _delivery_providers_queue:
        prov_types = provider.enum_types(delivery_group=delivery_group)
        types.extend([('%s:%s' % (provider_path, t[0]), t[1]) for t in prov_types])
    return types

def get_delivery_formclass(delivery_group, typ):
    provider_path, typ_short = typ.split(':', 1)
    for prov_path, provider in _delivery_providers_queue:
        if provider_path == prov_path:
            return provider.get_formclass(delivery_group, typ_short)
    raise ValueError('No provider found for delivery type %s.' % typ)

def get_delivery_variant(delivery_group, typ, form):
    provider_path, typ_short = typ.split(':', 1)
    for prov_path, provider in _delivery_providers_queue:
        if provider_path == prov_path:
            return provider.get_variant(delivery_group, typ_short, form)
    raise ValueError('No provider found for delivery type %s.' % typ)

def init_queues():
    global _partitioners_queue
    _partitioners_queue = []
    handlers = getattr(settings, 'SATCHLESS_ORDER_PARTITIONERS', [
        'satchless.contrib.order.partitioner.simple',
    ])
    for handler in handlers:
        if isinstance(handler, str):
            mod_name, han_name = handler.rsplit('.', 1)
            module = import_module(mod_name)
            handler = getattr(module, han_name)
        _partitioners_queue.append(handler)
    global _delivery_providers_queue
    _delivery_providers_queue = []
    providers = getattr(settings, 'SATCHLESS_DELIVERY_PROVIDERS', [
        'satchless.delivery.DeliveryProvider',
    ])
    for provider_path in providers:
        mod_name, prov_name = provider_path.rsplit('.', 1)
        module = import_module(mod_name)
        provider = getattr(module, prov_name)()
        _delivery_providers_queue.append((provider_path, provider))

init_queues()
