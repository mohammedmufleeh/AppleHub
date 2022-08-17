from multiprocessing import context
from django.shortcuts import redirect, render
from django.contrib.auth import login,logout,authenticate
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth.hashers import make_password, check_password
from django.core.paginator import  EmptyPage, PageNotAnInteger, Paginator

from accounts.models import Accounts
from store.models import Product, Variation
from orders.models import Order
from category.models import category
from .forms import ProductForm, VariationForm


# Create your views here.
@never_cache
@login_required(login_url='manager_login')
def manager_dashboard(request):
    if request.user.is_superadmin:

        user_count = Accounts.objects.filter(is_superadmin=False).count()
        product_count = Product.objects.all().count()
        order_count = Order.objects.filter(is_ordered=True).count()
        category_count = category.objects.all().count

        context = {
            'user_count': user_count,
            'product_count': product_count,
            'order_count' : order_count,
            'category_count' : category_count
        }

        return render(request,'manager/manager_dashboard.html',context)
    else:
        return redirect('home')

# My orders
@login_required(login_url='manager_login')
def admin_order(request):
  current_user = request.user
  
  if request.method == 'POST':
    keyword = request.POST['keyword']
    orders = Order.objects.filter(Q(user=current_user), Q(is_ordered=True), Q(order_number__startswith=keyword) | Q(user__email__startswith=keyword) | Q(first_name__startswith=keyword) | Q(last_name__startswith=keyword) | Q(phone__startswith=keyword)).order_by('-created_at')
    
  else:
    orders = Order.objects.filter(user=current_user, is_ordered=True).order_by('-created_at')
  
  paginator = Paginator(orders, 10)
  page = request.GET.get('page')
  paged_orders = paginator.get_page(page)
  context = {
    'orders': paged_orders,
  }
  return render(request, 'manager/admin_orders.html', context)

@never_cache
@login_required(login_url='manager_login')
def user_management(request):
    if request.method == "POST":
      key = request.POST['key']
      users = Accounts.objects.filter(Q(first_name__startswith=key) | Q(last_name__startswith=key) | Q(username__startswith=key) | Q(email__startswith=key)).order_by('id')
    else:
      users = Accounts.objects.filter(is_superadmin=False).order_by('id')

    paginator = Paginator(users,10)
    page = request.GET.get('page')
    paged_users = paginator.get_page(page)
    context = {
        'users' : paged_users
    }
    return render(request, 'manager/user_management.html',context)


def user_ban(request, user_id):
    user = Accounts.objects.get(id=user_id)
    user.is_active = False
    user.save()
    return redirect('user_management')

def user_unban(request, user_id):
    user = Accounts.objects.get(id=user_id)
    user.is_active = True
    user.save()
    return redirect('user_management')


def category_management(request):
    categories = category.objects.all().order_by('id')

    context = {
        'categories' :categories
    }

    return render(request, 'manager/category_management.html',context)


def add_category(request):
    if request.method == 'POST':
        try:
            category_name = request.POST['category_name']
            category_slug = request.POST['category_slug']
            category_description = request.POST['category_description']
            
            categories = category(
                category_name = category_name,
                slug = category_slug,
                description = category_description
            )
            
            categories.save()
            return redirect('category_management')
        except Exception as e:
            raise e
    return render(request, 'manager/add_category.html')

# Update Category
@never_cache
@login_required(login_url='manager_login')
def update_category(request, category_id):
  try:
    categories = category.objects.get(id=category_id)
    
    if request.method == 'POST':
      category_name = request.POST['category_name']
      category_slug = request.POST['category_slug']
      category_description = request.POST['category_description']
      
      categories.category_name = category_name
      categories.slug = category_slug
      categories.description = category_description
      categories.save()
      
      return redirect('category_management')
    
    context = {
      'category': categories
    }
    return render(request, 'manager/update_category.html', context)
    
  except Exception as e:
    raise e
    
       

@never_cache
@login_required(login_url='manager_login')
def delete_category(request,category_id):
    categories = category.objects.get(id=category_id)
    categories.delete()

    return redirect('category_management')


# Manage Order
@never_cache
@login_required(login_url='manager_login')
def order_management(request):
  if request.method =="POST":
    key = request.POST['key']
    orders = Order.objects.filter(Q(is_ordered=True), Q(order_number__startswith=key) | Q(user__email__startswith=key) | Q(first_name__startswith=key)).order_by('id')
  else:
    orders = Order.objects.filter(is_ordered=True).order_by('id')
    

  context = {
    'orders': orders
  }
  return render(request, 'manager/order_management.html', context)

# Cancel Order
@never_cache
@login_required(login_url='manager_login')
def cancel_order(request, order_number):
  order = Order.objects.get(order_number=order_number)
  order.status = 'Cancelled'
  order.save()
  
  return redirect('order_management')
  

# Accept Order
@never_cache
@login_required(login_url='manager_login')
def accept_order(request, order_number):
  order = Order.objects.get(order_number=order_number)
  order.status = 'Accepted'
  order.save()
  
  return redirect('order_management')

# Complete Order
@never_cache
@login_required(login_url='manager_login')
def complete_order(request, order_number):
  order = Order.objects.get(order_number=order_number)
  order.status = 'Completed'
  order.save()
  
  return redirect('order_management')

  # Product Management
@never_cache
@login_required(login_url='manager_login')
def product_management(request):
  if request.method == "POST":
    key = request.POST['key']
    products = Product.objects.filter(Q(product_name__startswith=key) | Q(slug__startswith=key) | Q(category__category_name__startswith=key)).order_by('id')
  else:
    products = Product.objects.all().order_by('id')

  paginator = Paginator(products, 10)
  page = request.GET.get('page')
  paged_products = paginator.get_page(page)
  
  context = {
    'products': paged_products
  }
  return render(request, 'manager/product_management.html', context)

# Add Product
@never_cache
@login_required(login_url='manager_login')
def add_product(request):
  if request.method == 'POST':
    form = ProductForm(request.POST, request.FILES)
    if form.is_valid():
        form.save()
        return redirect('product_management')
  else:
    form = ProductForm()
    context = {
      'form': form
    }
    return render(request, 'manager/add_product.html', context)

# Edit Product
@never_cache
@login_required(login_url='manager_login')
def edit_product(request, product_id):
  product = Product.objects.get(id=product_id)
  form = ProductForm(instance=product)
  
  if request.method == 'POST':
    try:
      form = ProductForm(request.POST, request.FILES, instance=product)
      if form.is_valid():
        form.save()
        
        return redirect('product_management')
    
    except Exception as e:
      raise e

  context = {
    'product': product,
    'form': form
  }
  return render(request, 'manager/edit_product.html', context)

# Delete Product
@never_cache
@login_required(login_url='manager_login')
def delete_product(request, product_id):
  product = Product.objects.get(id=product_id)
  product.delete()
  return redirect('product_management')

# Manage Variation
@never_cache
@login_required(login_url='manager_login')
def variation_management(request):
  if request.method == 'POST':
    keyword = request.POST['keyword']
    variations = Variation.objects.filter(Q(product__product_name__startswith=keyword) | Q(variation_category__startswith=keyword) | Q(variation_value__startswith=keyword)).order_by('id')
  
  else:
    variations = Variation.objects.all().order_by('id')
  
  paginator = Paginator(variations, 10)
  page = request.GET.get('page')
  paged_variations = paginator.get_page(page)
  
  context = {
    'variations': paged_variations
  }
  return render(request, 'manager/variation_management.html', context)


# Add Variation
@never_cache
@login_required(login_url='manager_login')
def add_variation(request):
  
  if request.method == 'POST':
    form = VariationForm(request.POST)
    if form.is_valid():
      form.save()
      return redirect('variation_management')
  
  else:
    form = VariationForm()
  
  context = {
    'form': form
  }
  return render(request, 'manager/add_variation.html', context)


# Update Variation
@never_cache
@login_required(login_url='manager_login')
def update_variation(request, variation_id):
  variation = Variation.objects.get(id=variation_id)
  
  if request.method == 'POST':
    form = VariationForm(request.POST ,instance=variation)
    if form.is_valid():
      form.save()
      return redirect('variation_management')
  
  else:
    form = VariationForm(instance=variation)
  
  context = {
    'variation': variation,
    'form': form
  }
  return render(request, 'manager/update_variation.html', context)

  #Delete variation
@never_cache
@login_required(login_url='manager_login')
def delete_variation(request, variation_id):
  variation = Variation.objects.get(id=variation_id)
  variation.delete()
  return redirect('variation_management')


# Admin change password
@never_cache
@login_required(login_url='manager_login')
def admin_change_password(request):
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
  
  return render(request, 'manager/admin_password.html')

@never_cache
def manager_login(request):
    if request.user.is_authenticated:
        if request.user.is_superadmin:
            return redirect('manager_dashboard')
        else:
            return redirect('home')
    else:
        if request.method == 'POST':
            email = request.POST['email']
            password = request.POST['password']

            user = authenticate(request,username=email, password=password)
            if user is not None:
                if user.is_superadmin:
                    login(request,user)
                    return redirect('manager_dashboard')
                else:
                     messages.error(request, 'This is not a admin account')      
            else:
                messages.error(request, 'Email or Password is incorrect')
    return render(request,'manager/admin_login.html')
@never_cache
def manager_logout(request):
    logout(request)
    return redirect('manager_login')
