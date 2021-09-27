from flask import Blueprint, request, make_response, current_app
from . import db, helper
import jwt
from datetime import datetime, timedelta


bp = Blueprint('admin', __name__, url_prefix='/admin')


@bp.route('register', methods=['POST'])
def register():
	if request.content_type != 'application/json':
		return make_response({'status': 0, 'message': 'Invalid content type'}, 400)

	request_data = request.get_json()

	if helper.user_exists(request_data["email"], "admin"):
		return make_response({'status': 0, 'message': 'Email already in use'}, 409)

	query = '''INSERT INTO admin (admin_id, full_name, role, email, phone_number, pwd) 
	VALUES (UUID_TO_BIN(UUID()), '{}', 'admin', '{}', '{}', '{}')'''.format(request_data['full_name'],  
	request_data['email'], request_data['phone_number'], helper.string_hash(request_data['pwd']))

	conn = db.get_db()
	cur = conn.cursor()
	result = cur.execute(query)
	conn.commit()

	if result < 1:
		return make_response({'status': 0, 'message': 'Couldn\'t save details. Try later'}, 500)
	
	return make_response({'status': 1, 'message': 'Registration Successful'}, 200)		


@bp.route('login', methods=['POST'])
def login():
	if request.content_type != 'application/json':
		return make_response({'status': 0, 'message': 'Invalid content type'}, 400)

	request_data = request.get_json()

	query ='''SELECT BIN_TO_UUID(admin_id) admin_id, full_name, email, phone_number FROM admin 
	WHERE `email` = '{}' AND `pwd` = '{}' LIMIT 1'''.format(request_data['email'], helper.string_hash(request_data['pwd']))

	cur = db.get_db().cursor()
	cur.execute(query)
	result = cur.fetchone()

	if not result:
		return make_response({'status': 0, 'message': 'Incorrect email or password'}, 404)

	user_id = result['admin_id']
	token = jwt.encode(
		{'exp': datetime.now() + timedelta(days=10), 'typ': 'admin', 'sub': user_id}, 
		current_app.config['SCRT'], 
		algorithm='HS256'
	).decode('utf-8')
	response = make_response({"status": 1, "message": "Login successful", "token": token, "user_details": result}, 200)
	# response.set_cookie('token', token, expires=expiration, secure=True, httponly=True, samesite='None')
	return response


@bp.route('profile', methods=['GET'])
def get_profile():
    token = helper.is_logged_in(request.headers['Authorization'].split(' ')[-1], current_app.config['SCRT'])
    if not token or token['type'] != 'admin':
        return make_response({'status': 0, 'message': 'Please login first!'}, 401)

    query = f"SELECT full_name, email, phone_number, role FROM admin WHERE `admin_id` = UUID_TO_BIN('{token['sub']}') LIMIT 1"

    cur = db.get_db().cursor()
    cur.execute(query)
    result = cur.fetchone()
    if not result:
        return make_response({"status": 0, "message": "User not found"}, 404)

    return make_response({"status": 1, "message": "User Found", "user_details": result}, 200)


@bp.route('edit', methods=['PATCH'])
def edit_profile():
    token = helper.is_logged_in(request.headers['Authorization'].split(' ')[-1], current_app.config['SCRT'])
    if not token or token['typ'] != 'admin':
        return make_response({'status': 0, 'message': 'Please login first!'}, 401)

    if request.content_type != 'application/json':
        return make_response({'status': 0, 'message': 'Invalid content type'}, 400)

    request_data = request.get_json()

    query = '''UPDATE admin SET email = '{}', phone_number = '{}' WHERE 
    admin_id = UUID_TO_BIN('{}')'''.format(request_data["email"], request_data["phone"], token['sub'])

    conn = db.get_db()
    cur = conn.cursor()
    result = cur.execute(query)
    conn.commit()

    if result < 1:
        return make_response({'status': 0, 'message': 'Couldn\'t update user details. Try later'}, 500)
    
    return make_response({'status': 1, 'message': 'Update Successful'}, 200)


@bp.route('clients', methods=['GET'])
def get_clients():
    token = helper.is_logged_in(request.headers['Authorization'].split(' ')[-1], current_app.config['SCRT'])
    if token and token['typ'] == 'admin':
        cur = db.get_db().cursor()
        query = 'SELECT BIN_TO_UUID(client_id) client_id, full_name, email, phone_number, address FROM client' 
        cur.execute(query)
        result = cur.fetchall()
        if not result:
            return make_response({'status': 0, 'message': 'No clients found'}, 404)
        return make_response({'status': 1, 'message': 'Request Successful', 'data': result}, 200)
    else:
        return make_response({'status': 0, 'message': 'Must be logged in to complete this request'}, 401)


@bp.route('orders', methods=['GET'])
def get_orders():
    token = helper.is_logged_in(request.headers['Authorization'].split(' ')[-1], current_app.config['SCRT'])
    if token and token['typ'] == 'admin':
        cur = db.get_db().cursor()
        query = '''SELECT BIN_TO_UUID(order_id) order_id, BIN_TO_UUID(client_id) client_id, payment_method, order_location, ordered_at FROM order ORDER BY ordered_at DESC'''
        cur.execute(query)
        result = cur.fetchall()
        if not result:
            return make_response({'status': 0, 'message': 'No orders found'}, 404)
        return make_response({'status': 1, 'message': 'Request Successful', 'data': result}, 200)
    else:
        return make_response({'status': 0, 'message': 'Must be logged in to complete this request'}, 401)


@bp.route('session', methods=['POST'])
def check_session():
    token = helper.is_logged_in(request.headers['Authorization'].split(' ')[-1], current_app.config['SCRT'])
    if token and token['type'] == 'admin':
        return make_response({'status': 1, 'user_type': token['typ']}, 200)
    else:
        return make_response({'status': 0, 'message': 'Must be logged in to complete this request'}, 401)