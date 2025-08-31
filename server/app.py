#!/usr/bin/env python3 
from flask import request, session, make_response
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from config import app, db, api
from models import User, Recipe


class Signup(Resource):
    def post(self):
        data = request.get_json()

        username = data.get("username")
        password = data.get("password")
        image_url = data.get("image_url")
        bio = data.get("bio")

        try:
            new_user = User(
                username=username,
                image_url=image_url,
                bio=bio,
            )
            new_user.password_hash = password  

            db.session.add(new_user)
            db.session.commit()

            # Save user ID in session
            session["user_id"] = new_user.id

            return make_response(
                {
                    "id": new_user.id,
                    "username": new_user.username,
                    "image_url": new_user.image_url,
                    "bio": new_user.bio,
                },
                201,
            )
        except IntegrityError:
            db.session.rollback()
            return make_response({"errors": ["Username already taken."]}, 422)
        except ValueError as e:
            return make_response({"errors": [str(e)]}, 422)


class CheckSession(Resource):
    def get(self):
        user_id = session.get("user_id")

        if user_id:
            user = User.query.get(user_id)
            if user:
                return make_response(
                    {
                        "id": user.id,
                        "username": user.username,
                        "image_url": user.image_url,
                        "bio": user.bio,
                    },
                    200,
                )

        return make_response({"error": "Unauthorized"}, 401)


class Login(Resource):
    def post(self):
        data = request.get_json()

        username = data.get("username")
        password = data.get("password")

        user = User.query.filter_by(username=username).first()

        if user and user.authenticate(password):
            session["user_id"] = user.id
            return make_response(
                {
                    "id": user.id,
                    "username": user.username,
                    "image_url": user.image_url,
                    "bio": user.bio,
                },
                200,
            )

        return make_response({"error": "Invalid username or password"}, 401)


class Logout(Resource):
    def delete(self):
        user_id = session.get("user_id")
        if not user_id:
            return make_response({"error": "Unauthorized"}, 401)

        session.pop("user_id", None)  
        return make_response("", 204)


class RecipeIndex(Resource):
    def get(self):
        user_id = session.get("user_id")
        if not user_id:
            return make_response({"error": "Unauthorized"}, 401)

        recipes = Recipe.query.all()
        recipe_list = []
        for recipe in recipes:
            recipe_list.append({
                "id": recipe.id,
                "title": recipe.title,
                "instructions": recipe.instructions,
                "minutes_to_complete": recipe.minutes_to_complete,
                "user": {
                    "id": recipe.user.id,
                    "username": recipe.user.username,
                    "image_url": recipe.user.image_url,
                    "bio": recipe.user.bio,
                }
            })
        return make_response(recipe_list, 200)

    def post(self):
        user_id = session.get("user_id")
        if not user_id:
            return make_response({"error": "Unauthorized"}, 401)

        data = request.get_json()
        title = data.get("title")
        instructions = data.get("instructions")
        minutes = data.get("minutes_to_complete")

        try:
            new_recipe = Recipe(
                title=title,
                instructions=instructions,
                minutes_to_complete=minutes,
                user_id=user_id
            )
            db.session.add(new_recipe)
            db.session.commit()

            return make_response(
                {
                    "id": new_recipe.id,
                    "title": new_recipe.title,
                    "instructions": new_recipe.instructions,
                    "minutes_to_complete": new_recipe.minutes_to_complete,
                    "user": {
                        "id": new_recipe.user.id,
                        "username": new_recipe.user.username,
                        "image_url": new_recipe.user.image_url,
                        "bio": new_recipe.user.bio,
                    },
                },
                201,
            )

        except ValueError as e:  
            db.session.rollback()
            return make_response({"errors": [str(e)]}, 422)

        except IntegrityError:  
            db.session.rollback()
            return make_response({"errors": ["Invalid recipe data."]}, 422)


# Register resources
api.add_resource(Signup, "/signup", endpoint="signup")
api.add_resource(CheckSession, "/check_session", endpoint="check_session")
api.add_resource(Login, "/login", endpoint="login")
api.add_resource(Logout, "/logout", endpoint="logout")
api.add_resource(RecipeIndex, "/recipes", endpoint="recipes")

if __name__ == "__main__":
    app.run(port=5555, debug=True)
