from flask import Flask
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

class ValidateP

if __name__ == '__main__':
    app.run(debug=True)