"""App views."""

# Django
from django.contrib import messages
from django.db.models import F
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.http.response import JsonResponse
from django.views.generic import ListView, CreateView, UpdateView, TemplateView
from json import loads

# Models
from .models import Product, ShoppingCart, Order as OrderModel, OrderDetail

# Paypal
from .paypal import Order

# Utilities
from .utils import random_code


class HomeView(ListView):
    """Home view."""
    
    model = Product
    queryset = Product.objects.all()
    template_name = 'views/index.html'
    context_object_name = 'products'

    def get_context_data(self, **kwargs):
        shopping_cart = ShoppingCart.objects.filter(user=self.request.user).count()
        context = super(HomeView, self).get_context_data(**kwargs)
        context['checkout'] = shopping_cart
        return context

class AddShoppingCart(CreateView):
    """Add shopping cart view."""

    def post(self, request, *args, **kwargs):
        body = request.POST
        product_id = body['product_id']
        product_query = Product.objects.get(id=product_id)
        if product_id:
            price = product_query.price
            try:
                shopping = ShoppingCart.objects.get(product_id=product_id, user=request.user)
                messages.add_message(request, messages.ERROR, 'El producto ya se encuentra agregado')
            except ShoppingCart.DoesNotExist:
                shopping = ShoppingCart(product_id=product_id, price=price, quantity=1, user=request.user)
                shopping.save()
                messages.add_message(request, messages.SUCCESS, 'El producto se agrego al carrito')
        return redirect(reverse_lazy('index'))

class CheckoutView(ListView):
    """Checkout view."""

    template_name = 'views/checkout.html'
    context_object_name = 'objects'

    def get_queryset(self):
        return ShoppingCart.objects.filter(user=self.request.user).order_by('created_at')


class QuantityUpgradeView(UpdateView):
    """Quantity upgrade view.
    Increase the quantity of a product that belongs to a logged in user's shopping cart."""

    def post(self, request, *args, **kwargs):
        shopping_cart = ShoppingCart.objects.get(pk=kwargs['pk'])
        if shopping_cart:
            shopping_cart.quantity = F('quantity') + 1
            shopping_cart.save()
        return redirect(reverse_lazy('checkout'))


class QuantityDowngradeView(UpdateView):
    """Quantity downgrade view.
    Decrease the quantity of a product that belongs to a logged in user's shopping cart
    as long as the quantity is greater than one. Otherwise, the product will be removed.
    """

    def post(self, request, *args, **kwargs):
        shopping_cart = ShoppingCart.objects.get(pk=kwargs['pk'])
        if shopping_cart:
            if shopping_cart.quantity > 1:
                shopping_cart.quantity = F('quantity') - 1
                shopping_cart.save()
            elif shopping_cart.quantity == 1:
                shopping_cart.delete()
        return redirect(reverse_lazy('checkout'))

class PaymentCheckout(CreateView):
    """Payment checkout view."""

    def post(self, request, *args, **kwargs):
        body_unicode = request.body.decode('utf-8')
        body = loads(body_unicode)
        order_id = body['orderID']

        shopping_cart = ShoppingCart.objects.filter(user=request.user).all()
        total_price = round(sum(round(d.price * d.quantity, 2) for d in shopping_cart), 2)

        order = Order().get_order(order_id)
        order_price = float(order.result.purchase_units[0].amount.value)
        from pdb import set_trace
        set_trace()
        if order_price == total_price:
            return self._order_capture(
                order_id, order_price, request, shopping_cart
            )

        return JsonResponse({
            'error': 'Sucedio un error al realizar el cobro'
        })
    
    def _order_capture(self, order_id, order_price, request, shopping_cart):
        order_capture = Order().capture_order(order_id, debug=True)

        code = f'PC-{random_code(5)}'
        order = OrderModel.objects.create(price=order_price, user=request.user, code=code)
        if order:
            order_id = order.pk
            for value in shopping_cart:
                OrderDetail.objects.create(
                    order_id=order_id,
                    product_id=value.product.id,
                    quantity=value.quantity,
                    price=value.price
                )
            ShoppingCart.objects.filter(user=request.user).delete()
        
        data = {
            'id': order_capture.result.id,
            'name': order_capture.result.payer.name.given_name
        }

        return JsonResponse(data)

class ConfirmationView(TemplateView):
    """Confirmation view."""

    template_name = 'views/confirmation.html'

class OrderView(ListView):
    """Order view."""

    template_name = 'views/orders.html'
    context_object_name = 'objects'

    def get_queryset(self):
        return OrderModel.objects.filter(user=self.request.user).all()

class OrderDetailView(ListView):
    """Order detail view."""

    template_name = 'views/order_detail.html'
    context_object_name = 'objects'

    def get_queryset(self):
        return OrderDetail.objects.filter(order__code=self.kwargs['code']).all()

    def get_context_data(self, **kwargs):
        order = OrderModel.objects.get(code=self.kwargs['code'])
        context = super(OrderDetailView, self).get_context_data(**kwargs)
        context['order'] = order
        return context