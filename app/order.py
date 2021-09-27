from flask import Blueprint, request, make_response, current_app
from . import db, helper
import jwt
from datetime import datetime, timedelta


bp = Blueprint('order', __name__, url_prefix='/order')


@bp.route('upload', methods=['POST'])
def upload_order():	
    if request.content_type != 'application/json':
        return make_response({'status': 0, 'message': 'Bad Request'}, 401)

    token = helper.is_logged_in(request.headers['Authorization'].split(' ')[-1], current_app.config['SCRT'])
    if not token or token['typ'] != 'client':
        return make_response({'status': 0, 'message': 'Please login first!'}, 401)

    form_data = request.get_json()

    conn = db.get_db()
    cur = conn.cursor()

    cur.execute("SELECT UUID() order_id")
    order_id = cur.fetchone()["order_id"]

    query = '''INSERT INTO `order` (order_id, client_id, payment_method, order_location) VALUES (UUID_TO_BIN('{}'), UUID_TO_BIN('{}'), '{}', '{}')'''.format(order_id, token['sub'], form_data['payment_method'], form_data['order_location'])
    result = cur.execute(query)
    conn.commit()

    if result < 1:
        return make_response({'status': 0, 'message': "Server Error. Couldn't save order"}, 500)

    items = form_data["items"]
    if items is not None:
        for item in items:
            if not helper.product_exists(pid=item['product_id']):
                return make_response({'status': 1, 'message': 'Product not found', "product": item}, 404)	

            query = '''INSERT INTO order_item (order_item_id, order_id, product_id, item_quantity) VALUES 
            (UUID_TO_BIN(UUID()), UUID_TO_BIN('{}'), UUID_TO_BIN('{}'), {})'''.format(order_id, item['product_id'], item['quantity'])
            if cur.execute(query) < 1:
                return make_response({'status': 0, 'message': "Server Error. Couldn't save order"}, 500)

    return make_response({'status': 1, 'message': 'Order Registered'}, 200)		


@bp.route('all', methods=['GET'])
def get_orders():
    token = helper.is_logged_in(request.headers['Authorization'].split(' ')[-1], current_app.config['SCRT'])
    if token:
        conn = db.get_db()
        cur = conn.cursor()
        query = '''SELECT BIN_TO_UUID(order_id) order_id, BIN_TO_UUID(client_id) client_id, payment_method, order_location, ordered_at FROM `order` ORDER BY ordered_at DESC'''
        cur.execute(query)
        conn.commit()
        result = cur.fetchall()
        if not result:
            return make_response({'status': 0, 'message': 'No orders found'}, 404)
        return make_response({'status': 1, 'message': 'Request successful', 'data': result}, 200)
    else:
        return make_response({'status': 0, 'message': 'Must be logged in to complete this request'}, 401)


@bp.route('view/<order_id>', methods=['GET'])
def view_order(order_id):
    token = helper.is_logged_in(request.headers['Authorization'].split(' ')[-1], current_app.config['SCRT'])
    if token:
        conn = db.get_db()
        cur = conn.cursor()
        query = '''SELECT BIN_TO_UUID(order_id) order_id, BIN_TO_UUID(client_id) client_id, payment_method, order_location, ordered_at FROM `order` WHERE order_id = UUID_TO_BIN('{}') ORDER BY ordered_at DESC LIMIT 1'''.format(order_id)
        cur.execute(query)
        conn.commit()
        result = cur.fetchone()
        if not result:
            return make_response({'status': 0, 'message': 'Order not found'}, 404)
        return make_response({'status': 1, 'message': 'Request successful', 'data': result}, 200)
    else:
        return make_response({'status': 0, 'message': 'Must be logged in to complete this request'}, 401)


@bp.route('update/<order_id>', methods=['PATCH'])
def edit_order(order_id):
    token = helper.is_logged_in(request.headers['Authorization'].split(' ')[-1], current_app.config['SCRT'])
    if not token or token['typ'] != 'admin':
        return make_response({'status': 0, 'message': 'Please login first!'}, 401)

    form_data = request.get_json()

    edit_query = '''UPDATE `order` SET payment_method = '{}', order_location = '{}' WHERE order_id = UUID_TO_BIN('{}') LIMIT 1'''.format(form_data["payment_method"], form_data["order_location"], order_id)
    conn = db.get_db()
    cur = conn.cursor()
    result = cur.execute(edit_query)
    conn.commit()

    if result < 1:
        return make_response({'status': 1, 'message': 'Server Error. Could not update order!'}, 500)

    return make_response({'status': 1, 'message': 'Request Successful'}, 200)


@bp.route('delete/<order_id>', methods=['DELETE'])
def delete_order(order_id):
    if request.content_type != 'application/json':
        return make_response({'status':0, 'message': 'Invalid content type'}, 400)

    token = helper.is_logged_in(request.headers['Authorization'].split(' ')[-1], current_app.config['SCRT'])
    request_data = request.get_json()

    if token and token['typ'] == 'admin':
        conn = db.get_db()
        cur = conn.cursor()
        del_query = "DELETE FROM `order` WHERE order_id = UUID_TO_BIN('{}')".format(order_id)
        result = cur.execute(del_query)
        conn.commit()

        if result > 0:
            return make_response({'status': 1, 'message': 'Request successful'}, 200)

        return make_response({'status': 1, 'message': 'Order not found'}, 200)

    else:
        return make_response({'status': 0, 'message': 'Must be logged in to complete this request'}, 401)
