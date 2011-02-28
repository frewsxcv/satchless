from django.shortcuts import redirect
from django.views.generic.simple import direct_to_template
from satchless.cart.models import Cart

from . import models
from . import forms
from . import handler

def checkout(request, typ):
    cart = Cart.objects.get_or_create_from_request(request, typ)
    order = models.Order.objects.create_for_cart(cart, session=request.session)
    delivery_formset = forms.DeliveryMethodFormset(data=request.POST or None, queryset=order.groups.all())
    if request.method == 'POST':
        if delivery_formset.is_valid():
            delivery_formset.save(request.session)
            return redirect('satchless-checkout-delivery_details')
    return direct_to_template(request, 'satchless/order/checkout.html',
            {'order': order, 'delivery_formset': delivery_formset})

def delivery_details(request):
    order = models.Order.objects.get_from_session(request.session)
    delivery_groups_forms = forms.get_delivery_details_forms_for_groups(order, request)
    groups_with_forms = filter(lambda gf: gf[2], delivery_groups_forms)
    if len(groups_with_forms) == 0:
        # all forms are None, no details needed
        return redirect('satchless-checkout-payment_choice')
    if request.method == 'POST':
        are_valid = True
        for group, typ, form in delivery_groups_forms:
            are_valid = are_valid and form.is_valid()
        if are_valid:
            for group, typ, form in delivery_groups_forms:
                variant = handler.get_delivery_variant(group, typ, form)
                group.delivery_variant = variant
                group.save()
            return redirect('satchless-checkout-payment_choice')
    return direct_to_template(request, 'satchless/order/delivery_details.html',
            {'order': order, 'delivery_groups_forms': groups_with_forms})

def payment_choice(request):
    order = models.Order.objects.get_from_session(request.session)
    return direct_to_template(request, 'satchless/order/payment_choice.html',
            {'order': order})
