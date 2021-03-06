import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)


db_drop_and_create_all()

# ROUTES
'''
GET /drinks
    it is public endpoint
    it contain the drink.short() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
    or appropriate status code indicating reason for failure
'''
@app.route('/drinks')
def get_drinks():
    try:
        drinks = list(map(Drink.short, Drink.query.all()))
        return jsonify({
            "success": True,
            "drinks": drinks
        })
    except:
        abort(422)


'''
GET /drinks-detail
    it require the 'get:drinks-detail' permission
    it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
    or appropriate status code indicating reason for failure
'''
@app.route('/drinks-detail')
@requires_auth('get:drinks-detail')
def drinks_detail(payload):
    try:
        drinks = list(map(Drink.long, Drink.query.all()))
        return jsonify({
            "success": True,
            "drinks": drinks
        })
    except:
        abort(422)


'''
POST /drinks
    it should create a new row in the drinks table
    it should require the 'post:drinks' permission
    it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the newly created drink
    or appropriate status code indicating reason for failure
'''
@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def add_drink(payload):
    body = request.get_json()
    if body is None:
        abort(400)
    title = body.get('title', None)
    recipe = body.get('recipe', None)
    if (recipe is None) or (title is None):
        abort(400)

    # define Drink instance
    try:
        drink = Drink()
        drink.title = title
        if isinstance(recipe, dict):
            recipe = [recipe]
        drink.recipe = json.dumps(recipe)
        drink.insert()
        new_drink = Drink.query.get(drink.id)
        return jsonify({
            "success": True,
            "drinks": [new_drink.long()]
        })
    except:
        abort(422)


'''
PATCH /drinks/<id>
    where <id> is the existing model id
    it should respond with a 404 error if <id> is not found
    it should update the corresponding row for <id>
    it should require the 'patch:drinks' permission
    it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the updated drink
    or appropriate status code indicating reason for failure
'''
@app.route('/drinks/<int:drink_id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def update_drink(payload, drink_id):
    # search for the drink in the db
    drink = Drink.query.filter(Drink.id == drink_id).one_or_none()
    if drink is None:
        abort(404)
    # get the request body
    body = request.get_json()
    if body is None:
        abort(400)
    title = body.get('title', None)
    recipe = body.get('recipe', None)
    try:
        if title:
            drink.title = title
        if recipe:
            if isinstance(recipe, dict):
                recipe = [recipe]
            drink.recipe = json.dumps(recipe)
        drink.update()
        updated_drink = Drink.query.get(drink_id)
        return jsonify({
            "success": True,
            "drinks": [updated_drink.long()]
        })
    except:
        abort(422)


'''
DELETE /drinks/<id>
    where <id> is the existing model id
    it should respond with a 404 error if <id> is not found
    it should delete the corresponding row for <id>
    it should require the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
    or appropriate status code indicating reason for failure
'''
@app.route('/drinks/<int:drink_id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(payload, drink_id):
    # search for the drink in the db
    drink = Drink.query.filter(Drink.id == drink_id).one_or_none()
    if drink is None:
        abort(404)
    try:
        drink.delete()
        return jsonify({
            "success": True,
            "delete": drink_id
        })
    except:
        abort(422)


# Error Handling
'''
Example error handling for unprocessable entity
'''
@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422


'''
error handler for 404
'''
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "resource not found"
    }), 404


@app.errorhandler(400)
def not_found(error):
    return jsonify({
        "success": False,
        "error": 400,
        "message": "bad request"
    }), 400


'''
 error handler for AuthError
'''
@app.errorhandler(AuthError)
def handle_AuthError(error):
    payload = dict(error.error)
    return jsonify({
        "success": False,
        "error": error.status_code,
        "message": payload["description"]
    }), error.status_code
