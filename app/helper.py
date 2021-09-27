import jwt
from . import db
from hashlib import sha256


def is_logged_in(token, secret):
	try:
		decoded_token = jwt.decode(token, secret, algorithm='HS256')
		return decoded_token
	except jwt.exceptions.DecodeError as e:
		print("Error: At is_logged_in, " + str(e))
	except jwt.exceptions.ExpiredSignatureError as e:
		print("Error: At is_logged_in, " + str(e))


def string_hash(to_hash):
    return sha256(to_hash.encode()).hexdigest()


def user_exists(email, user_type):
	'''This function checks for an existing user'''
	cur = db.get_db().cursor()
	query = f"SELECT email FROM {user_type} WHERE email = '{email}' LIMIT 1"
	cur.execute(query)
	res = cur.fetchone()
	return res is not None

def product_exists(sno="", pid=""):
	'''This function checks for an existing product'''
	cur = db.get_db().cursor()
	query = "SELECT serial_number FROM product WHERE serial_number = '{}'".format(sno)
	if pid != "":
		query = query + " OR product_id = UUID_TO_BIN('{}')".format(pid)
	query = query + " LIMIT 1"
	cur.execute(query)
	res = cur.fetchone()
	return res is not None