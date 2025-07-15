from django.shortcuts import render, redirect, get_object_or_404
from .models import Product
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import RegisterForm
from .models import Product, Order, OrderItem


# Product Listing + Search (open to everyone)
def product_list(request):
    query = request.GET.get('q')
    products = Product.objects.filter(name__icontains=query) if query else Product.objects.all()
    return render(request, 'store/product_list.html', {'products': products})

# Add product to cart (login required)
@login_required
def add_to_cart(request, product_id):
    cart = request.session.get('cart', {})
    product_id_str = str(product_id)

    if product_id_str in cart:
        cart[product_id_str] += 1
    else:
        cart[product_id_str] = 1

    request.session['cart'] = cart
    request.session.modified = True  # ✅ This line ensures the session is saved
    return redirect('product_list')

# View Cart (login required)
@login_required
def view_cart(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total = 0

    for pid, qty in cart.items():
        product = get_object_or_404(Product, id=pid)
        item_total = product.price * qty
        cart_items.append({
            'product': product,
            'quantity': qty,
            'item_total': item_total
        })
        total += item_total

    return render(request, 'store/cart.html', {
        'cart_items': cart_items,
        'total': total
    })

# Remove an item from cart (login required)
@login_required
def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})
    cart.pop(str(product_id), None)
    request.session['cart'] = cart
    return redirect('view_cart')

# Clear the entire cart (login required)
@login_required
def clear_cart(request):
    request.session['cart'] = {}
    return redirect('view_cart')

# Update item quantity in the cart (login required)
@login_required
def update_cart_quantity(request, product_id):
    if request.method == 'POST':
        try:
            new_quantity = int(request.POST.get('quantity', 1))
        except ValueError:
            new_quantity = 1

        cart = request.session.get('cart', {})
        product_id_str = str(product_id)

        if new_quantity > 0:
            cart[product_id_str] = new_quantity
        else:
            cart.pop(product_id_str, None)

        request.session['cart'] = cart

    return redirect('view_cart')


# Checkout (login required)
@login_required
def checkout(request):
    cart = request.session.get('cart', {})

    if not cart:
        messages.warning(request, "Your cart is empty!")
        return redirect('view_cart')

    cart_items = []
    total = 0

    for pid, qty in cart.items():
        product = get_object_or_404(Product, id=pid)
        item_total = product.price * qty
        cart_items.append({
            'product': product,
            'quantity': qty,
            'item_total': item_total
        })
        total += item_total

    # If it's a POST request, it means the user confirmed the order
    if request.method == 'POST':
        order = Order.objects.create(user=request.user, total=total)
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item['product'],
                quantity=item['quantity'],
                price=item['product'].price
        )
        # Here you could optionally save the order to DB
        request.session['cart'] = {}  # Clear cart
        return render(request, 'store/order_complete.html', {
            'cart_items': cart_items,
            'total': total,
        })

    # If it's a GET request, show order summary with Confirm button
    return render(request, 'store/checkout.html', {
        'cart_items': cart_items,
        'total': total,
    })

@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'store/my_orders.html', {'orders': orders})

def register_view(request):
    if request.user.is_authenticated:
        return redirect('product_list')  # redirect to home/product list if already logged in

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # auto login after registration
            return redirect('product_list')  # redirect to home after registration
    else:
        form = RegisterForm()

    return render(request, 'store/register.html', {'form': form})
