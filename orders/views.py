from datetime import datetime, date

from django.core.mail import EmailMessage
from django.template.loader import render_to_string

from carts.models import CartItem
from orders.forms import OrderForm
from store.models import Product
from .models import Order, Payment, OrderProduct
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from .models import Order, Payment
from django.contrib.auth.decorators import login_required
import uuid


# Create your views here.


@login_required
def payments(request, order_id):
    # Get the order object
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if request.method == 'POST':
        # Generate a unique payment ID
        payment_id = str(uuid.uuid4())

        # Create a Payment record
        payment = Payment(
            user=request.user,
            payment_id=payment_id,
            payment_method='Cash',  # Since the only payment method is cash
            amount_paid=order.order_total,
            status='Completed'  # Assuming the payment is successful
        )
        payment.save()

        # Associate the payment with the order
        order.payment = payment
        order.status = 'Completed'  # Update order status
        order.is_ordered = True
        order.save()

        # moving to order table
        cart_items = CartItem.objects.filter(user=request.user)

        for item in cart_items:
            orderproduct = OrderProduct()
            orderproduct.order_id = order.id
            orderproduct.payment = payment
            orderproduct.user_id = request.user.id
            orderproduct.product_id = item.product_id
            orderproduct.quantity = item.quantity
            orderproduct.product_price = item.product.price
            orderproduct.ordered = True
            orderproduct.save()

            cart_item = CartItem.objects.get(id=item.id)
            product_variation = cart_item.variations.all()
            orderproduct = OrderProduct.objects.get(id=orderproduct.id)
            orderproduct.variations.set(product_variation)
            orderproduct.save()

            # when product is sold, quantity is reduced
            product = Product.objects.get(id=item.product_id)
            product.stock -= item.quantity
            product.save()

            # clear from cart
            CartItem.objects.filter(user=request.user).delete()

            # Send order recieved email
            mail_subject = 'Thank you for your order! '
            message = render_to_string('orders/order_received_email.html', {
                'user': request.user,
                'order': order,
            })
            to_email = request.user.email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()

            # Redirect to the invoice page

            return redirect('order_confirmation', order_id=order.id)  # Redirect to an order confirmation page

    return redirect('store')  # Redirect to an order confirmation page


def order_confirmation(request, order_id):
    # Retrieve the order and associated details
    order = get_object_or_404(Order, id=order_id)
    ordered_products = OrderProduct.objects.filter(order=order)

    # Calculate subtotal
    subtotal = sum(item.product_price * item.quantity for item in ordered_products)

    context = {
        'order': order,
        'order_number' : order.order_number,
        'ordered_products': ordered_products,
        'subtotal': subtotal,
        'transID': order.payment.payment_id,
        'payment': order.payment
    }

    return render(request, 'orders/order_confirmation.html', context)


def place_order(request, total=0, quantity=0):
    current_user = request.user

    # If the cart count is less than or equal to 0, then redirect back to shop
    cart_items = CartItem.objects.filter(user=current_user)
    cart_count = cart_items.count()
    if cart_count <= 0:
        return redirect('store')

    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        quantity += cart_item.quantity

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            # Store all the billing information inside Order table
            data = Order()
            data.user = current_user
            data.first_name = form.cleaned_data['first_name']
            data.last_name = form.cleaned_data['last_name']
            data.phone = form.cleaned_data['phone']
            data.email = form.cleaned_data['email']
            data.address_line_1 = form.cleaned_data['address_line_1']
            data.city = form.cleaned_data['city']
            data.order_note = form.cleaned_data['order_note']
            data.order_total = total
            data.ip = request.META.get('REMOTE_ADDR')
            data.save()

            yr = int(datetime.today().strftime('%Y'))
            dt = int(datetime.today().strftime('%d'))
            mt = int(datetime.today().strftime('%m'))
            d = date(yr, mt, dt)
            current_date = d.strftime("%Y%m%d")
            order_number = current_date + str(data.id)
            data.order_number = order_number
            data.save()

            order = Order.objects.get(user=current_user, is_ordered=False, order_number=order_number)
            context = {
                'order': order,
                'cart_items': cart_items,
                'total': total,
            }
            return render(request, 'orders/payments.html', context)
    else:
        return redirect('checkout')
