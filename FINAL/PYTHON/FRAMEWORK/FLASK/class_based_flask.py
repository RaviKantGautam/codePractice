from flask import Flask, request, jsonify
from flask.views import MethodView

app = Flask(__name__)

class MyView(MethodView):
    def get(self):
        return jsonify({"message": "GET request received"}), 200

    def post(self):
        data = request.get_json()
        return jsonify({"message": "POST request received", "data": data}), 200

    def delete(self):
        return jsonify({"message": "DELETE request received"}), 200

    def put(self):
        data = request.get_json()
        return jsonify({"message": "PUT request received", "data": data}), 200

    def patch(self):
        data = request.get_json()
        return jsonify({"message": "PATCH request received", "data": data}), 200

app.add_url_rule('/my-view', view_func=MyView.as_view('my_view'))

if __name__ == '__main__':
    app.run(debug=True)