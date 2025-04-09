from decimal import Decimal  # Add this at the top
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import CustomUserCreationForm, ProductForm, FarmForm
from django.db.models import Q  # Import Q for complex queries
from django.core.paginator import Paginator  # Import Paginator
from django.http import JsonResponse  # Import JsonResponse for JSON responses
import json  # Import json for handling JSON data
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt  # Import csrf_exempt
from .models import Product, Farm, Order  # Import the Product, Farm, and Order models

def home(request):
    return render(request, 'core/home.html')

def about(request):
    return render(request, 'core/about.html')

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()
    return render(request, 'core/register.html', {'form': form})

@login_required
def dashboard(request):
    return render(request, 'core/dashboard.html')


### Add Products Feature ###
@login_required
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.farmer = request.user
            product.save()
            messages.success(request, "Product added successfully!")
            return redirect('add_product')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ProductForm()
    return render(request, 'core/add_product.html', {'form': form})

### Product Management Features ###
@login_required
def my_products(request):
    products = Product.objects.filter(farmer=request.user).order_by('-created_at')
    return render(request, 'core/my_products.html', {'products': products})

@login_required
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id, farmer=request.user)
    product.delete()
    messages.success(request, "Product deleted successfully.")
    return redirect('my_products')

@login_required
def update_product(request, product_id):
    product = get_object_or_404(Product, id=product_id, farmer=request.user)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, "Product updated successfully.")
            return redirect('my_products')
    else:
        form = ProductForm(instance=product)
    return render(request, 'core/update_product.html', {'form': form, 'product': product})


## Farm Management Features ##
@login_required
def add_farm(request):
    if request.method == 'POST':
        form = FarmForm(request.POST, request.FILES)
        if form.is_valid():
            farm = form.save(commit=False)
            farm.farmer = request.user
            farm.save()
            messages.success(request, "Farm registered successfully!")
            return redirect('farm_management')  # or redirect to 'add_farm' to reset form
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = FarmForm()

    return render(request, 'core/add_farm.html', {'form': form})
### Farm view Feature ###
@login_required
def farm_management(request):
    farms = Farm.objects.filter(farmer=request.user)
    return render(request, 'core/farm_management.html', {'farms': farms})

### Update Farm Feature ###
@login_required
def update_farm(request, farm_id):
    farm = get_object_or_404(Farm, id=farm_id, farmer=request.user)

    if request.method == 'POST':
        form = FarmForm(request.POST, request.FILES, instance=farm)
        if form.is_valid():
            form.save()
            messages.success(request, "Farm updated successfully.")
            return redirect('farm_management')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = FarmForm(instance=farm)

    return render(request, 'core/update_farm.html', {'form': form, 'farm': farm})

### Delete Farm Feature ###
@login_required
@require_POST
def delete_farm(request, farm_id):
    farm = get_object_or_404(Farm, id=farm_id, farmer=request.user)
    farm.delete()
    messages.success(request, "Farm deleted successfully.")
    return redirect('farm_management')

@login_required
def orders(request):
    status_filter = request.GET.get('status', 'all')
    orders = Order.objects.filter(product__farmer=request.user)
    
    if status_filter != 'all':
        orders = orders.filter(status=status_filter.capitalize())
    
    status_counts = {
        'all': Order.objects.filter(product__farmer=request.user).count(),
        'pending': Order.objects.filter(product__farmer=request.user, status='Pending').count(),
        'processing': Order.objects.filter(product__farmer=request.user, status='Processing').count(),
        'shipped': Order.objects.filter(product__farmer=request.user, status='Shipped').count(),
        'completed': Order.objects.filter(product__farmer=request.user, status='Completed').count(),
        'cancelled': Order.objects.filter(product__farmer=request.user, status='Cancelled').count(),
    }

    context = {
        'orders': orders.order_by('-created_at'),
        'status_filter': status_filter,
        'status_counts': status_counts
    }
    return render(request, 'core/orders.html', context)

@login_required
@require_POST
def update_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id, product__farmer=request.user)
    new_status = request.POST.get('status')
    
    if new_status in dict(Order.STATUS_CHOICES):
        order.status = new_status
        order.save()
        messages.success(request, f"Order #{order.id} status updated to {new_status}")
    else:
        messages.error(request, "Invalid status update")
    
    return redirect('orders')


### Buyer Features ###

# View products for buyers
@login_required
def browse_products(request):
    products = Product.objects.all()
    pending_orders = Order.objects.filter(buyer=request.user, status='Pending')
    
    # Add category choices to context
    product_categories = Product.CATEGORY_CHOICES
    cart_total = sum(order.total_price for order in pending_orders)
    
    context = {
        'products': products,
        'pending_orders': pending_orders,
        'product_categories': product_categories,
        'cart_total': cart_total
    }
    return render(request, 'core/browse_products.html', context)

# Order Product functionality (This replaces the old Add to Cart functionality)
@login_required
@csrf_exempt  
@require_POST
def order_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    try:
        data = json.loads(request.body)
        quantity = int(data.get('quantity', 1))
        
        if quantity < 1:
            raise ValueError("Quantity must be at least 1kg")
            
        if quantity > product.stock_quantity:
            return JsonResponse({
                'error': f'Only {product.stock_quantity}kg available'
            }, status=400)

        # Create order with Pending status
        order = Order.objects.create(
            buyer=request.user,
            product=product,
            quantity=quantity,
            total_price=quantity * product.price_per_kg,
            status='Pending'  # Changed to Pending
        )
        
        product.stock_quantity -= quantity
        product.save()

        return JsonResponse({
            'success': True,
            'total_price': float(order.total_price),
            'new_stock': product.stock_quantity
        })
        
    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)

## submit order ##
@login_required
@require_POST
def submit_order(request):
    order_ids = request.POST.get('order_ids', '')
    if not order_ids:
        return JsonResponse({'message': 'No orders to submit.'}, status=400)
    
    order_ids = order_ids.split(',')
    orders = Order.objects.filter(id__in=order_ids, buyer=request.user, status='Pending')

    if not orders.exists():
        return JsonResponse({'message': 'No pending orders found.'}, status=400)

    for order in orders:
        order.status = 'Completed'
        order.save()

    return JsonResponse({'message': 'Order submitted successfully'}, status=200)

# Order history view (for the buyer)
@login_required
def order_history(request):
    orders = Order.objects.filter(buyer=request.user).select_related('product').order_by('-created_at')
    context = {
        'orders': orders
    }
    return render(request, 'core/order_history.html', context)