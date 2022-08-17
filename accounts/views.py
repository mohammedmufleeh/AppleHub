
from django.shortcuts import redirect, render
from django.contrib.auth import login,logout,authenticate
from django.views.decorators.cache import never_cache
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password, make_password
from django.db.models import Q

from cart.models import Cart, CartItem
from . models import Accounts
from .forms import RegistrationForm
from cart.views import _cart_id
from cart.models import Cart,CartItem
from orders.models import Order, OrderProduct, Payment

from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode,urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
import requests

# Create your views here.
@login_required(login_url='login')
def user_dashboard(request):
    try:
        current_user = request.user
        total_orders = Order.objects.filter(user=current_user, is_ordered=True).count()
        
        context = {
        'current_user': current_user,
        'total_orders': total_orders
        }
        
        return render(request, 'accounts/user_dashboard.html', context)
    
    except Exception as e:
        raise e
@login_required(login_url='login')
def my_orders(request):
    if request.method =="POST":
        current_user = request.user
        key = request.POST['key']
        orders = Order.objects.filter(Q(user=current_user), Q(order_number__startswith=key) | Q(first_name__startswith=key) | Q(last_name__startswith=key) | Q(phone__startswith=key)).order_by('-id')
    else:
        current_user=request.user
        orders = Order.objects.filter(user=current_user,is_ordered=True).order_by('-created_at')
    context = {
        'orders': orders,
    }
    return render(request, 'accounts/my_orders.html',context)
@login_required(login_url='login')
def cancel_order(request,order_number):
    try:
        order = Order.objects.get(order_number=order_number)
        order.status = "Cancelled"
        order.save()

        return redirect('my_orders')

    except Exception as e:
        raise e
        

@login_required(login_url='signin')
def view_order(request, order_number):
  try:
    order = Order.objects.get(order_number=order_number)
    ordered_products = OrderProduct.objects.filter(order_id=order.id)
    transaction_id = Payment.objects.get(order_number=order_number)
    
    tax = 0
    total = 0
    grand_total = 0
    
    for item in ordered_products:
      total += (item.product_price * item.quantity)
      
    tax = 2*total / 100
    grand_total = total + tax
    
    context = {
      'order': order,
      'ordered_products': ordered_products,
      'transaction_id': transaction_id,
      
      'total': total,
      'tax': tax,
      'grand_total': grand_total
    }
    
    return render(request, 'orders/view_order.html', context)
    
  except Exception as e:
    raise e

@never_cache
@login_required(login_url='signin')
def change_password(request):
  if request.method == 'POST':
    current_user = request.user
    current_password = request.POST['current_password']
    password = request.POST['password']
    confirm_password = request.POST['confirm_password']
    
    if password == confirm_password:
      if check_password(current_password, current_user.password):
        if check_password(password, current_user.password):
          messages.warning(request, 'Current password and new password is same')
        else:
          hashed_password = make_password(password)
          current_user.password = hashed_password
          current_user.save()
          messages.success(request, 'Password changed successfully')
      else:
        messages.error(request, 'Wrong password')
    else:
      messages.error(request, 'Passwords does not match')
  
  return render(request, 'accounts/change_password.html')


def signup(request):
    if request.user.is_authenticated:
        return redirect('home')

    else:
        form = RegistrationForm()
        if request.method == 'POST':
            form = RegistrationForm(request.POST)
            if form.is_valid():
                first_name = form.cleaned_data.get('first_name')
                last_name = form.cleaned_data.get('last_name')
                phone_number = form.cleaned_data.get('phone_number')
                email = form.cleaned_data.get('email')
                username = form.cleaned_data.get('username')
                password = form.cleaned_data.get('password')

                user = Accounts.objects.create_user(first_name=first_name, last_name=last_name, email=email, username=username, password=password )
                user.phone_number = phone_number
                user.save()


                #user activation

                current_site = get_current_site(request)
                mail_subject = "Please activate your account"
                message = render_to_string('accounts/email_verification.html',{
                    'user' : user,
                    'domain' : current_site,
                    'uid' : urlsafe_base64_encode(force_bytes(user.pk)),
                    'token' : default_token_generator.make_token(user)

                })

                to_email = email
                send_email = EmailMessage(mail_subject,  message, to=[to_email])
                send_email.send()

                messages.success(request,"Please confirm your email address. Check your inbox")

                return redirect('login')
        
        context = {'form' : form}
        return render(request,'accounts/signup.html',context) 
        
         
def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Accounts._default_manager.get(pk=uid)
    except(TypeError, ValueError, OverflowError, Accounts.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_verified = True
        user.save()
        messages.success(request, 'Congratulation! your account is now activated')
        return redirect('register')
    else:
        messages.error(request, 'Invalid Activation link!!')
        return redirect('register')


@never_cache
def signin(request):
    if request.user.is_authenticated:
        return redirect('home')
    else:
        if request.method == 'POST':
            email = request.POST['email']
            password = request.POST['password']

            user = authenticate(request,username=email, password=password)
            if user is not None:
                if user.is_verified:
                    try:
                        cart = Cart.objects.get(cart_id=_cart_id(request))
                        is_cart_item_exists = CartItem.objects.filter(cart=cart).exists
                        if is_cart_item_exists:
                            cart_item = CartItem.objects.filter(cart=cart)

                        # getting product variation by cart id

                            product_variation =[]
                            for item in cart_item:
                                variation = item.variation.all()
                                product_variation.append(list(variation))

                            cart_item = CartItem.objects.filter(user=user)
                            existing_variation_list = []
                            id = []
                            for item in cart_item:
                                existing_variation = item.variation.all()
                                existing_variation_list.append(list(existing_variation))
                                id.append(item.id)

                            for pr in product_variation:
                                if pr in existing_variation_list:
                                    index = existing_variation_list.index(pr)
                                    item_id = id[index]
                                    item = CartItem.objects.get(id=item_id)
                                    item.quantity += 1
                                    item.user = user
                                    item.save()
                                else:
                                    cart_item =CartItem.objects.filter(cart=cart)
                                    for item in cart_item:
                                        item.user = user
                                        item.save()
                    except:
                        pass
                    
                    login(request,user)
                    url = request.META.get('HTTP_REFERER')

                    try:
                        query = requests.utils.urlparse(url).query
                        params = dict(x.split('=') for x in query.split('&'))
                        if 'next' in params:
                            next_page = params['next']
                            return redirect(next_page)
                    except:
                        return redirect('home')    
                else:
                   messages.warning(request, 'Account is not activated. please check your email') 
            else:
                messages.error(request, 'Email or Password is incorrect') 
        return render(request, 'accounts/login.html')  

def forgotPassword(request):
    if request.method =='POST':
        email = request.POST['email']
        if Accounts.objects.filter(email=email).exists():
            user = Accounts.objects.get(email__exact=email)

            current_site = get_current_site(request)
            mail_subject = "Reset Your Password"
            message = render_to_string('accounts/reset_passwrod.html',{
                'user' : user,
                'domain' : current_site,
                'uid' : urlsafe_base64_encode(force_bytes(user.pk)),
                'token' : default_token_generator.make_token(user)

            })

            to_email = email
            send_email = EmailMessage(mail_subject,  message, to=[to_email])
            send_email.send()

            messages.success(request, "Check inbox and reset password.")
            return redirect('login')
        else:
            messages.error(request, 'Account does not exist!')
            return redirect('forgotPassword')
    return render(request, 'accounts/forgotPassword.html') 

def resetpassword_validate(request, uidb64,token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Accounts._default_manager.get(pk=uid)
    except(TypeError, ValueError, OverflowError, Accounts.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        request.session['uid'] = uid
        messages.success(request, 'please reset your password')
        return redirect('resetPassword')

def resetPassword(request):
    if request.method == 'POST':
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password == confirm_password:
            uid = request.session.get('uid')
            user = Accounts.objects.get(pk=uid)
            user.set_password(password)
            user.save()
            messages.success(request, 'password reset succesful')
            return redirect('login')
        else:
            messages.error(request, 'password do not match!')
            return redirect('resetPassword')
    else:
        return render(request, 'accounts/resetPassword.html')



@never_cache
def signout(request):
    logout(request)
    return redirect('login')