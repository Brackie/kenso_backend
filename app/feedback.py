from flask import Blueprint, request, make_response, current_app
from . import db, helper
import jwt
from datetime import datetime, timedelta


bp = Blueprint('feedback', __name__, url_prefix='/feedback')


@bp.route('upload', methods=['POST'])
def upload_feedback():	
    if request.content_type != 'application/json':
        return make_response({'status': 0, 'message': 'Bad Request'}, 401)

    token = helper.is_logged_in(request.headers['Authorization'].split(' ')[-1], current_app.config['SCRT'])
    if not token or token['typ'] != 'client':
        return make_response({'status': 0, 'message': 'Please login first!'}, 401)

    form_data = request.get_json()

    conn = db.get_db()
    cur = conn.cursor()

    query = '''INSERT INTO `feedback` (message_id, client_id, subject, message) VALUES (UUID_TO_BIN(UUID()), UUID_TO_BIN('{}'), '{}', '{}')'''.format(token['sub'], form_data['subject'], form_data['message'])
    result = cur.execute(query)
    conn.commit()

    if result < 1:
        return make_response({'status': 0, 'message': "Server Error. Couldn't save message"}, 500)

    return make_response({'status': 1, 'message': 'Message Received :)'}, 200)


@bp.route('all', methods=['GET'])
def get_feedbacks():
    token = helper.is_logged_in(request.headers['Authorization'].split(' ')[-1], current_app.config['SCRT'])
    if token:
        conn = db.get_db()
        cur = conn.cursor()
        query = '''SELECT BIN_TO_UUID(message_id) message_id, BIN_TO_UUID(client_id) client_id, subject, message, sent_at FROM `feedback` ORDER BY sent_at DESC'''
        cur.execute(query)
        conn.commit()
        result = cur.fetchall()
        if not result:
            return make_response({'status': 0, 'message': 'No messages found'}, 404)
        return make_response({'status': 1, 'message': 'Request successful', 'data': result}, 200)
    else:
        return make_response({'status': 0, 'message': 'Must be logged in to complete this request'}, 401)


@bp.route('view/<message_id>', methods=['GET'])
def view_feedback(message_id):
    token = helper.is_logged_in(request.headers['Authorization'].split(' ')[-1], current_app.config['SCRT'])
    if token:
        conn = db.get_db()
        cur = conn.cursor()
        query = '''SELECT BIN_TO_UUID(message_id) message_id, BIN_TO_UUID(client_id) client_id, subject, message, sent_at FROM `feedback` WHERE message_id = UUID_TO_BIN('{}') ORDER BY sent_at DESC LIMIT 1'''.format(message_id)
        cur.execute(query)
        conn.commit()
        result = cur.fetchone()
        if not result:
            return make_response({'status': 0, 'message': 'Message not found'}, 404)
        return make_response({'status': 1, 'message': 'Request successful', 'data': result}, 200)
    else:
        return make_response({'status': 0, 'message': 'Must be logged in to complete this request'}, 401)


@bp.route('delete/<message_id>', methods=['DELETE'])
def delete_feedback(message_id):
    if request.content_type != 'application/json':
        return make_response({'status':0, 'message': 'Invalid content type'}, 400)

    token = helper.is_logged_in(request.headers['Authorization'].split(' ')[-1], current_app.config['SCRT'])
    request_data = request.get_json()

    if token and token['typ'] == 'admin':
        conn = db.get_db()
        cur = conn.cursor()
        del_query = "DELETE FROM `feedback` WHERE message_id = UUID_TO_BIN('{}')".format(message_id)
        result = cur.execute(del_query)
        conn.commit()

        if result > 0:
            return make_response({'status': 1, 'message': 'Request successful'}, 200)

        return make_response({'status': 1, 'message': 'Message not found'}, 200)

    else:
        return make_response({'status': 0, 'message': 'Must be logged in to complete this request'}, 401)
