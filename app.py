from flask import Flask
from flask.views import MethodView
from flask import jsonify
from flask_pymongo import PyMongo
import re

app = Flask(__name__)
app.config['MONGO_URI'] = 'mongodb://localhost:27017/test_db_11'  # Replace with your MongoDB URI

mongo = PyMongo(app)

collection = mongo.db.get_collection('test_collect_11')

inventory = mongo.db.inventory

@app.route('/')
def index():
    cursor = inventory.find({})
    return str(list(cursor))

class ValidatePan(MethodView):

    def post(self, *args, **kwargs):
        request_body = self.request.get_json()
        pan = request_body.get('pan')
        if pan:
            if re.match(r'^[A-Za-z]{5}\d{4}[A-Za-z]$', pan):
                request_body['valid'] = True
            else:
                request_body['valid'] = False
            return jsonify(request_body, 200)
        else:
            return {'status': 'error', 'message': 'Pan is required'}, 400

if __name__ == '__main__':
    app.run(debug=True)