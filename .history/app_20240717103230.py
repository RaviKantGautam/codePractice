from flask import Flask
from flask.views import MethodView
from flask_pymongo import PyMongo

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
    def post(self, **args, **kwargs):
        if len(pan) != 10:
            return 'Invalid PAN', 400
        return 'Valid PAN', 200

if __name__ == '__main__':
    app.run(debug=True)