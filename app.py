from app import app, db
from flask_restful import Api
from app.api import ProductsResource, CategoriesResource, OrdersResource, ReviewsResource

api = Api(app)

api.add_resource(ProductsResource, '/api/products')
api.add_resource(CategoriesResource, '/api/categories')
api.add_resource(OrdersResource, '/api/orders')
api.add_resource(ReviewsResource, '/api/reviews')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)