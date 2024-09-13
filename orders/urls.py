from django.urls import path
from . import views

urlpatterns = [
    path('place_order/', views.place_order, name='place_order'),
    path('payment/<int:order_id>/', views.payments, name='payments'),
    path('order_confirmation/<str:order_id>/', views.order_confirmation, name='order_confirmation'),

]
