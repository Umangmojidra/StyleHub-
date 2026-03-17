"""
app.py - StyleHub E-Commerce Application Entry Point
"""
from flask import Flask, redirect, url_for, render_template
from flask_bcrypt import Bcrypt
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY

bcrypt = Bcrypt(app)

from routes.auth_routes    import auth_bp, bcrypt as auth_bcrypt
from routes.product_routes import products_bp
from routes.cart_routes    import cart_bp
from routes.order_routes   import orders_bp
from routes.payment_routes import payment_bp
from routes.admin_routes   import admin_bp

app.register_blueprint(auth_bp)
app.register_blueprint(products_bp)
app.register_blueprint(cart_bp)
app.register_blueprint(orders_bp)
app.register_blueprint(payment_bp)
app.register_blueprint(admin_bp)

auth_bcrypt.init_app(app)


@app.route('/')
def root():
    return redirect(url_for('products.index'))


@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500


if __name__ == '__main__':
    app.run(debug=Config.DEBUG, host='0.0.0.0', port=5000)
