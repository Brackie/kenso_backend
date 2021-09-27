from flask import Blueprint, request, make_response, current_app
from . import db, helper
import jwt
from datetime import datetime, timedelta


bp = Blueprint('product', __name__, url_prefix='/product')


@bp.route('upload', methods=['POST'])
def upload_product():	
	if request.content_type != 'application/json':
		return make_response({'status': 0, 'message': 'Bad Request'}, 401)

	token = helper.is_logged_in(request.headers['Authorization'].split(' ')[-1], current_app.config['SCRT'])
	if not token or token['typ'] != 'admin':
		return make_response({'status': 0, 'message': 'Please login first!'}, 401)

	form_data = request.get_json()
	if helper.product_exists(sno=form_data['serial_number']):
		return make_response({'status': 0, 'message': 'The product exists!'}, 409)

	query = '''INSERT INTO product (product_id, serial_number, product_name, product_type, product_description) VALUES (UUID_TO_BIN(UUID()), '{}', '{}', '{}', '{}')'''.format(form_data['serial_number'], form_data['product_name'], form_data['product_type'], form_data['product_description'])

	conn = db.get_db()
	cur = conn.cursor()
	result = cur.execute(query)
	conn.commit()

	if result < 1:
		return make_response({'status': 0, 'message': "Server Error. Couldn't save product"}, 500)
	
	return make_response({'status': 1, 'message': 'product Registered'}, 200)		


@bp.route('all', methods=['GET'])
def get_products():
    token = helper.is_logged_in(request.headers['Authorization'].split(' ')[-1], current_app.config['SCRT'])
    if token:
        conn = db.get_db()
        cur = conn.cursor()
        query = '''SELECT BIN_TO_UUID(product_id) product_id, serial_number, product_name, product_type, product_description FROM product ORDER BY uploaded_at DESC'''
        cur.execute(query)
        conn.commit()
        result = cur.fetchall()
        if not result:
            return make_response({'status': 0, 'message': 'No products found'}, 404)
        return make_response({'status': 1, 'message': 'Request successful', 'data': result}, 200)
    else:
        return make_response({'status': 0, 'message': 'Must be logged in to complete this request'}, 401)


@bp.route('view/<product_id>', methods=['GET'])
def view_product(product_id):
    token = helper.is_logged_in(request.headers['Authorization'].split(' ')[-1], current_app.config['SCRT'])
    if token:
        conn = db.get_db()
        cur = conn.cursor()
        query = '''SELECT BIN_TO_UUID(product_id) product_id, serial_number, product_name, product_type, product_description, uploaded_at FROM product WHERE product_id = UUID_TO_BIN('{}')'''.format(product_id)
        cur.execute(query)
        conn.commit()
        result = cur.fetchone()
        if not result:
            return make_response({'status': 0, 'message': 'Product not found'}, 404)
        return make_response({'status': 1, 'message': 'Request successful', 'data': result}, 200)
    else:
        return make_response({'status': 0, 'message': 'Must be logged in to complete this request'}, 401)


@bp.route('update/<product_id>', methods=['PATCH'])
def edit_product(product_id):
    token = helper.is_logged_in(request.headers['Authorization'].split(' ')[-1], current_app.config['SCRT'])
    if not token or token['typ'] != 'admin':
        return make_response({'status': 0, 'message': 'Please login first!'}, 401)

    form_data = request.get_json()

    edit_query = '''UPDATE product SET serial_number = '{}', product_name = '{}', product_type = '{}', product_description = '{}' WHERE product_id=UUID_TO_BIN('{}') LIMIT 1'''.format(form_data["serial_number"], form_data["product_name"], form_data["product_type"], form_data["product_description"], product_id)
    conn = db.get_db()
    cur = conn.cursor()
    result = cur.execute(edit_query)
    conn.commit()

    if result < 1:
        return make_response({'status': 1, 'message': 'Server Error. Could not update product!'}, 500)

    return make_response({'status': 1, 'message': 'Request Successful'}, 200)


@bp.route('delete/<product_id>', methods=['DELETE'])
def delete_product(product_id):
    if request.content_type != 'application/json':
        return make_response({'status':0, 'message': 'Invalid content type'}, 400)

    token = helper.is_logged_in(request.headers['Authorization'].split(' ')[-1], current_app.config['SCRT'])
    request_data = request.get_json()

    if token and token['typ'] == 'admin':
        conn = db.get_db()
        cur = conn.cursor()
        del_query = "DELETE FROM product WHERE product_id = UUID_TO_BIN('{}')".format(product_id)
        result = cur.execute(del_query)
        conn.commit()

        if result > 0:
            return make_response({'status': 1, 'message': 'Request successful'}, 200)

        return make_response({'status': 1, 'message': 'Product not found'}, 200)

    else:
        return make_response({'status': 0, 'message': 'Must be logged in to complete this request'}, 401)
