#!/usr/bin/env python3

from flask import request, session
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from config import app, db, api
from models import User, Recipe

class Signup(Resource):
    def post(self):
        data = request.get_json()

        username = data.get('username')
        password = data.get('password')
        image_url = data.get('image_url')
        bio = data.get('bio')

        if User.query.filter_by(username=username).first():
            return {'error': 'Username already exists'}, 422

        new_user = User(
            username=username,
            image_url=image_url,
            bio=bio
        )
        new_user.password_hash = password
        try:
            db.session.add(new_user)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return {'error': 'Username already exists'}, 422

        session['user_id'] = new_user.id
        return {
            'id': new_user.id,
            'username': new_user.username,
            'image_url': new_user.image_url,
            'bio': new_user.bio
        }, 201

class CheckSession(Resource):
    def get(self):
        user_id = session.get('user_id')
        if user_id:
            user = User.query.get(user_id)
            if user:
                return {
                    'id': user.id,
                    'username': user.username,
                    'image_url': user.image_url,
                    'bio': user.bio
                }, 200
            else:
                return {'error': 'User not found'}, 401
        return {'error': 'Unauthorized'}, 401

class Login(Resource):
    def post(self):
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return {'error': 'Username and password required'}, 400

        user = User.query.filter_by(username=username).first()
        if user and user.authenticate(password):
            session['user_id'] = user.id
            return {
                'id': user.id,
                'username': user.username,
                'image_url': user.image_url,
                'bio': user.bio
            }, 200
        return {'error': 'Unauthorized'}, 401

class Logout(Resource):
    def delete(self):
        if session.get('user_id'):
            session['user_id'] = None
            return {}, 204
        return {'error': 'Unauthorized'}, 401

class RecipeIndex(Resource):
    def get(self):
        user_id = session.get('user_id')
        if not user_id:
            return {'error': 'Unauthorized'}, 401
        user = db.session.get(User, user_id)
        if not user:
            return {'error': 'User not found'}, 404

        recipes = [
            {
                'id': recipe.id,
                'title': recipe.title,
                'instructions': recipe.instructions,
                'minutes_to_complete': recipe.minutes_to_complete
            } for recipe in user.recipes
        ]
        return recipes, 200

    def post(self):
        if session.get('user_id'):
            data = request.get_json()
            title = data.get('title')
            instructions = data.get('instructions')
            minutes_to_complete = data.get('minutes_to_complete')

            errors = {}

            if not title:
                errors['title'] = 'Title is required.'
            if not instructions:
                errors['instructions'] = 'Instructions are required.'
            if minutes_to_complete is None:
                errors['minutes_to_complete'] = 'Minutes to complete is required.'
            elif not isinstance(minutes_to_complete, int) or minutes_to_complete <= 0:
                errors['minutes_to_complete'] = 'Minutes to complete must be a positive integer.'

            if errors:
                return {'errors': errors}, 422

            try:
                new_recipe = Recipe(
                    title=title,
                    instructions=instructions,
                    minutes_to_complete=minutes_to_complete,
                    user_id=session['user_id']
                )
                db.session.add(new_recipe)
                db.session.commit()

                response = {
                    'id': new_recipe.id,
                    'title': new_recipe.title,
                    'instructions': new_recipe.instructions,
                    'minutes_to_complete': new_recipe.minutes_to_complete
                }

                return response, 201

            except ValueError as ve:
                return {'errors': {'instructions': str(ve)}}, 422

        return {'error': 'Unauthorized'}, 401


api.add_resource(Signup, '/signup', endpoint='signup')
api.add_resource(CheckSession, '/check_session', endpoint='check_session')
api.add_resource(Login, '/login', endpoint='login')
api.add_resource(Logout, '/logout', endpoint='logout')
api.add_resource(RecipeIndex, '/recipes', endpoint='recipes')

if __name__ == '__main__':
    app.run(port=5555, debug=True)
