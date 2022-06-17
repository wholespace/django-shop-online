from argparse import Action
import email
from multiprocessing import context
from operator import sub
from os import access
import re
from cv2 import cartToPolar
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import View, TemplateView, CreateView, FormView
from numpy import product
from .models import *
from django.contrib.auth import authenticate, login, logout
from .forms import CheckoutForm, CustomerRegistrationForm, CustomerLoginForm

# Create your views here.
class HomeView(TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['my_name'] = "MarkPage2k1"
        context['product_list'] = Product.objects.all().order_by("-id")
        return context

class AllProductView(TemplateView):
    template_name = 'all_products.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        return context

class ProductDetailView(TemplateView):
    template_name = 'product_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        url_slug = self.kwargs['slug']
        product = Product.objects.get(slug=url_slug)
        product.view_count += 1
        product.save()
        context['product'] = product

        return context

class AddToCartView(TemplateView):
    template_name = 'add_to_cart.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # get product id from requested id
        product_id = self.kwargs['pro_id']
        # get product
        product_obj = Product.objects.get(id=product_id)


        # check if cart exits
        # del self.request.session['cart_id']
        cart_id = self.request.session.get('cart_id', None)
        
        if cart_id:
            cart_obj = Cart.objects.get(id=cart_id)
            this_product_in_cart = cart_obj.cartproduct_set.filter(product=product_obj)

            # items already exists in cart
            if this_product_in_cart.exists():
                cart_product = this_product_in_cart.last()
                cart_product.quantity += 1
                cart_product.subtotal += product_obj.selling_price
                cart_product.save()
                cart_obj.total += product_obj.selling_price
                cart_obj.save()

            # new items is added in cart
            else:
                cart_product = CartProduct.objects.create(
                    cart=cart_obj, product=product_obj, rate=product_obj.selling_price, quantity=1, subtotal=product_obj.selling_price)
                cart_obj.total += product_obj.selling_price
                cart_obj.save()
        else:
            cart_obj = Cart.objects.create(total=0)
            self.request.session['cart_id'] = cart_obj.id

            cart_product = CartProduct.objects.create(
                    cart=cart_obj, product=product_obj, rate=product_obj.selling_price, quantity=1, subtotal=product_obj.selling_price)
            cart_obj.total += product_obj.selling_price
            cart_obj.save() 

        return context


class MyCartView(TemplateView):
    template_name = 'my_cart.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart_id = self.request.session.get("cart_id", None)
        if cart_id:
            cart = Cart.objects.get(id=cart_id)
        else:
            cart = None
        context['cart'] = cart
        return context

class ManageCartView(View):
    def get(self, request, *args, **kwargs):
        cp_id = self.kwargs["cp_id"]
        action =  request.GET.get("action")
        cp_object = CartProduct.objects.get(id=cp_id)
        cart_obj =  cp_object.cart

        if action == "inc":
            cp_object.quantity += 1
            cp_object.subtotal += cp_object.rate
            cp_object.save()
            cart_obj.total += cp_object.rate
            cart_obj.save()

        elif action == "dcr":
            cp_object.quantity -= 1
            cp_object.subtotal -= cp_object.rate
            cp_object.save()
            cart_obj.total -= cp_object.rate
            cart_obj.save()
            if cp_object.quantity == 0:
                cp_object.delete()
        elif action == "rmv":
            cart_obj.total -= cp_object.subtotal
            cart_obj.save()
            cp_object.delete()
        else:
            pass

        return redirect("shop_app:my_cart")

class EmptyCartView(View):
    def get(self, request, *args, **kwargs):
        cart_id = self.request.session.get('cart_id', None)
        if cart_id:
            cart = Cart.objects.get(id=cart_id)
            cart.cartproduct_set.all().delete()
            cart.total = 0
            cart.save()
        return redirect("shop_app:my_cart")

class CheckoutView(CreateView):
    template_name = 'checkout.html'
    form_class = CheckoutForm
    success_url = reverse_lazy("shop_app:home")


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart_id = self.request.session.get("cart_id", None)
        if cart_id:
            cart_obj = Cart.objects.get(id=cart_id)
        else:
            cart_obj = None
        context['cart'] = cart_obj
        return context
    
    def form_valid(self, form):
        cart_id = self.request.session.get("cart_id")
        if cart_id:
            cart_obj = Cart.objects.get(id=cart_id)
            form.instance.cart = cart_obj
            form.instance.subtotal = cart_obj.total
            form.instance.discount = 0
            form.instance.total = cart_obj.total
            form.instance.order_status = "Order Received"
            del self.request.session['cart_id']
        else:
            return redirect("shop_app:home")
        return super().form_valid(form)


class CustomerRegistrationView(CreateView):
    template_name = "customer_registration.html"
    form_class = CustomerRegistrationForm
    success_url = reverse_lazy("shop_app:home")

    def form_valid(self, form):
        username = form.cleaned_data.get("username")
        password = form.cleaned_data.get("password")
        email = form.cleaned_data.get("email")
        user = User.objects.create_user(username, email, password)
        form.instance.user = user
        login(self.request, user)

        return super().form_valid(form)

class CustomerLogoutView(View):
    def get(self, request):
        logout(request)
        return redirect("shop_app:home")

class CustomerLoginView(FormView):
    template_name = "customer_login.html"
    form_class = CustomerLoginForm
    success_url = reverse_lazy("shop_app:home")

    # # form_valid method is a type of post method and is available in createview formview and updateview
    def form_valid(self, form):
        uname = form.cleaned_data.get("username")
        pword = form.cleaned_data["password"]
        usr = authenticate(username=uname, password=pword)
        if usr is not None and Customer.objects.filter(user=usr).exists():
            login(self.request, usr)
        else:
            return render(self.request, self.template_name, {"form": self.form_class, "error": "Invalid credentials"})

        return super().form_valid(form)

    # def get_success_url(self):
    #     if "next" in self.request.GET:
    #         next_url = self.request.GET.get("next")
    #         return next_url
    #     else:
    #         return self.success_url


class AboutView(TemplateView):
    template_name = 'about.html'

class ContactView(TemplateView):
    template_name = 'contact.html'
