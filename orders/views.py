from django.shortcuts import redirect, render
from cart.models import CartItem
from orders.models import Order
from .models import Payment
from .forms import OrderForm
import datetime

from django.contrib.auth.decorators import login_required

import razorpay
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseBadRequest
# Create your views here.


def place_order(request, quantity=0, total=0):
    current_user = request.user


    cart_items =CartItem.objects.filter(user=current_user)
    if cart_items.count() < 1:
        return redirect('store')

    grand_total = 0
    tax  = 0
    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        quantity += cart_item.quantity
    tax = (2 * total)/100
    grand_total = total + tax


    if request.method == 'POST':
        form = OrderForm(request.POST)

        if form.is_valid():
            data = Order()
            data.user = current_user
            data.first_name = form.cleaned_data['first_name']
            data.last_name = form.cleaned_data['last_name']
            data.phone = form.cleaned_data['phone']
            data.email = form.cleaned_data['email']
            data.address_line_1 = form.cleaned_data['address_line_1']
            data.address_line_2 = form.cleaned_data['address_line_2']
            data.city = form.cleaned_data['city']
            data.state = form.cleaned_data['state']
            data.country = form.cleaned_data['country']
            data.order_note = form.cleaned_data['order_note']
            data.order_total = grand_total
            data.tax = tax
            data.ip = request.META.get('REMOTE_ADDR')
            data.save()

            # Generate Order number
            year = int(datetime.date.today().strftime('%Y'))
            month = int(datetime.date.today().strftime('%m'))
            date = int(datetime.date.today().strftime('%d'))
            d = datetime.date(year, month, date)
            current_date = d.strftime("%Y%m%d")
            order_number = current_date + str(data.id)
            data.order_number = order_number
            data.save()
            
            request.session['order_number'] = order_number
      
            return redirect('payment')
    
        else:
        
            return redirect('checkout')

@csrf_exempt
def payment_status(request):
    response = request.POST
    params_dict = {
        'razorpay_order_id': response['razorpay_order_id'],
        'razorpay_payment_id': response['razorpay_payment_id'],
        'razorpay_signature': response['razorpay_signature']
    }
    

    
    # authorize razorpay client with API Keys.
    razorpay_client = razorpay.Client(
      auth=(settings.RAZOR_KEY_ID, settings.RAZOR_KEY_SECRET))
    client = razorpay_client
    try:
      status = client.utility.verify_payment_signature(params_dict)
      transaction = Payment.objects.get(order_id=response['razorpay_order_id'])
      transaction.status = status
      transaction.payment_id = response['razorpay_payment_id']
      transaction.save()

      # get order
      order_number = transaction.order_number
      order = Order.objects.get(is_ordered=False, order_number=order_number)
      order.payment = transaction
      order.is_ordered = True
      order.save()
      
      
      return redirect('payment_success')
    
    except:
      transaction = Payment.objects.get(order_id=response['razorpay_order_id'])
      transaction.delete()
      return redirect('payment_fail')


@login_required(login_url='signin')
@csrf_exempt
def payment(request, total=0):
  current_user = request.user
  cart_item = CartItem.objects.filter(user=current_user)
  
  tax = 0
  grand_total = 0
  
  for item in cart_item:
    total += (item.product.price * item.quantity)
    
  tax = (1 * total) / 100
  grand_total = total + tax
  
  order_number = request.session['order_number']
  
  order = Order.objects.get(user=current_user, is_ordered=False, order_number=order_number)
  
  
  currency = 'INR'
  razorpay_client = razorpay.Client(auth=(settings.RAZOR_KEY_ID, settings.RAZOR_KEY_SECRET))

  response_payment  = razorpay_client.order.create(dict(amount=int(grand_total) * 100,currency=currency))
  order_id = response_payment['id']
  order_status = response_payment['status']
  if order_status == 'created':
    payDetails = Payment(
      user = current_user,
      order_id = order_id,
      order_number = order_number,
      amount_paid = grand_total 
    )
    payDetails.save()

    
  context = {
    'order': order,
    'cart_items': cart_item,
    'total': total,
    'tax': tax,
    'grand_total': grand_total,
    
    'payment': response_payment,
    'razorpay_merchant_key':settings.RAZOR_KEY_ID,
    'grand_total': grand_total,
  }
  return render(request, 'orders/payments.html', context)

def payment_success(request):
  return render(request, 'orders/success.html')

def payment_fail(request):
  return render(request, 'orders/fail.html')