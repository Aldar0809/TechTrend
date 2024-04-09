from flask import jsonify
from flask_restful import Resource
from .models import Product, Category, Order, Review


# Ресурс API для списка продуктов
class ProductsResource(Resource):
    def get(self):
        products = Product.query.all()
        products_data = [{
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "price": product.price
        } for product in products]
        return jsonify(products_data)


# Ресурс API для списка категорий
class CategoriesResource(Resource):
    def get(self):
        categories = Category.query.all()
        categories_data = [{
            "id": category.id,
            "name": category.name,
            "description": category.description
        } for category in categories]
        return jsonify(categories_data)


# Ресурс API для списка заказов
class OrdersResource(Resource):
    def get(self):
        orders = Order.query.all()
        orders_data = [{
            "id": order.id,
            "user_id": order.user_id,
            "customer_name": order.customer_name,
            "customer_address": order.customer_address,
            "payment_method": order.payment_method,
            "created_at": order.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            "status": order.status,
            "total_amount": order.total_amount,
            "order_items": [{
                "id": item.id,
                "product_id": item.product_id,
                "product_name": item.product.name,
                "quantity": item.quantity,
                "unit_price": item.product.price
            } for item in order.order_items]
        } for order in orders]
        return jsonify(orders_data)


# Ресурс API для списка отзывов
class ReviewsResource(Resource):
    def get(self):
        reviews = Review.query.all()
        reviews_data = [{
            "id": review.id,
            "text": review.text,
            "product_id": review.product_id,
            "user_id": review.user_id,
            "timestamp": review.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        } for review in reviews]
        return jsonify(reviews_data)
