from multiprocessing import context
from django.shortcuts import redirect, render
from django.contrib.auth import login,logout,authenticate
from django.views.decorators.cache import never_cache
from django.contrib import messages

from cart.models import Cart, CartItem
from . models import Accounts
from .forms import RegistrationForm
from cart.views import _cart_id
from cart.models import Cart,CartItem

from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode,urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
import requests

# Create your views here.



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
                message = render_to_string('email_verification.html',{
                    'user' : 'user',
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
        return render(request,'signup.html',context) 
        
         
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
        return render(request,'login.html')    
@never_cache
def signout(request):
    logout(request)
    return redirect('login')