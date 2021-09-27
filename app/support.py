from flask import Blueprint, request, make_response, current_app
from . import db, helper
import jwt
from datetime import datetime, timedelta


bp = Blueprint('support', __name__, url_prefix='/support')


@bp.route('upload', methods=['PUT'])
def upload_console():	
	if request.content_type != 'application/json':
		return make_response({'status': 0, 'message': 'Bad Request'}, 401)

	token = helper.is_logged_in(request.headers['Authorization'].split(' ')[-1], current_app.config['SCRT'])
	if not token:
		return make_response({'status': 0, 'message': 'Please login'}, 401)

	form_data = request.get_json()
	if console_exists(form_data['serial_number']):
		return make_response({'status': 0, 'message': 'The console is already registered'}, 409)

	query = '''INSERT INTO console (console_id, serial_number, client_id, console_type, storage, color, no_of_controllers) 
	VALUES (UUID_TO_BIN(UUID()), '{}', UUID_TO_BIN("{}"), '{}', '{}', '{}', {})'''.format(form_data['serial_number'], 
		token['sub'], form_data['console_type'], form_data['storage'], form_data['color'], form_data['no_of_controllers']
	)

	conn = db.get_db()
	cur = conn.cursor()
	result = cur.execute(query)
	conn.commit()

	if result < 1:
		return make_response({'status': 0, 'message': 'Server Error'}, 500)
	
	return make_response({'status': 1, 'message': 'Console Registered'}, 200)		


@bp.route('all', methods=['GET'])
def get_consoles():
    token = helper.is_logged_in(request.headers['Authorization'].split(' ')[-1], current_app.config['SCRT'])
    if token:
        conn = db.get_db()
        cur = conn.cursor()
        query = '''SELECT BIN_TO_UUID(console_id) console_id, serial_number, BIN_TO_UUID(client_id) client_id, 
        console_type, storage, color, no_of_controllers, booked FROM console'''
        cur.execute(query)
        conn.commit()
        result = cur.fetchall()
        if not result:
            return make_response({'status': 0, 'message': 'No consoles found'}, 404)
        return make_response({'status': 1, 'message': 'Request successful', 'data': result}, 200)
    else:
        return make_response({'status': 0, 'message': 'Must be logged in to complete this request'}, 401)


@bp.route('hire', methods=['PUT'])
def hire_console():
    def console_to_book(db, cursor):
        query = f"SELECT BIN_TO_UUID(console_id) console_id FROM console WHERE booked='false' LIMIT 1"
        cursor.execute(query)
        db.commit()
        result = cursor.fetchone()
        if not result:
            return None
        return result['console_id']

    if request.content_type == 'application/json':
        token = request.headers['Authorization'].split(' ')[-1]
        if token:
            data = request.get_json()
            conn = db.get_db()
            cur = conn.cursor()

            console_id = console_to_book(conn, cur)
            if not console_id:
                return make_response({'status': 0, 'message': 'No consoles available for booking'}, 404)

            booking_query = '''INSERT INTO booking (booking_id, console_id, full_name, id_number, email, address, 
            delivery_date, pickup_date) VALUES (UUID_TO_BIN(UUID()), UUID_TO_BIN('{}'), '{}', '{}', 
            '{}', '{}', '{}', '{}')'''.format(console_id, data['full_name'], data['id_number'], data['email'], 
            data['address'], data['delivery_date'], data['pickup_date'])
            result = cur.execute(booking_query)
            conn.commit()

            if result < 1:
                return make_response({'status': 0, 'message': 'Oops, Something went wrong'}, 500)

            hire_query = f"UPDATE console SET booked='true' WHERE console_id=UUID_TO_BIN('{console_id}') LIMIT 1"
            result = cur.execute(hire_query)
            conn.commit()

            if result < 1:
                return make_response({'status': 1, 'message': 'Oops, Something went wrong'}, 500)

            return make_response({'status': 1, 'message': 'Request Successful'}, 200)
        else:
            return make_response({'status': 0, 'message': 'Must be logged in to complete this request'}, 401)
    else:
        return make_response({'status': 1, 'message': 'Invalid content.'}, 400)


@bp.route('<console_id>', methods=['DELETE'])
def delete_console(console_id):
    if request.content_type != 'application/json':
        return make_response({'status':0, 'message': 'Invalid content type'}, 400)

    token = request.headers['Authorization'].split(' ')[-1]
    request_data = request.get_json()
    if token:
        conn = db.get_db()
        cur = conn.cursor()
        query = f'DELETE FROM console WHERE console_id={console_id}'
        result = cur.execute()
        conn.commit()

        if result > 0:
            return make_response({'status': 1, 'message': 'Request successful'}, 200)

        return make_response({'status': 1, 'message': 'Resource not found'}, 200)
    else:
        return make_response({'status': 0, 'message': 'Must be logged in to complete this request'}, 401)


@bp.route('<console_id>/return', methods=['PATCH'])
def return_console(console_id):
	token = helper.is_logged_in(request.headers['Authorization'].split(' ')[-1], current_app.config['SCRT'])
	if not token:
		return make_response({'status': 0, 'message': 'Please login'}, 401)

	return_query = f"UPDATE console SET booked='false' WHERE console_id=UUID_TO_BIN('{console_id}') LIMIT 1"
	conn = db.get_db()
	cur = conn.cursor()
	result = cur.execute(return_query)
	conn.commit()

	if result < 1:
		return make_response({'status': 1, 'message': 'Oops, Something went wrong'}, 500)

	return make_response({'status': 1, 'message': 'Request Successful'}, 200)