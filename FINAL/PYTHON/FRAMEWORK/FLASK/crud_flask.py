from flask import Flask, request, jsonify
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True)
    name = Column(String)

engine = create_engine("sqlite:///items.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

app = Flask(__name__)

@app.errorhandler(400)
def not_handled(error):
    return jsonify({"error": "Not handled"}), 400

@app.route("/items", methods=["GET"])
def get_items():
    # Example data, replace with your actual data source
    print("Cookies")
    print(request.cookies)
    print("Headers:")
    print(request.headers)
    print("Args:")
    print(request.args)
    items = [
        {"id": 1, "name": "Item 1"},
        {"id": 2, "name": "Item 2"},
    ]
    return jsonify(items)

@app.route("/items", methods=["POST"])
def create_item():
    data = request.get_json()
    # Example response, replace with your actual data handling logic
    new_item = {"id": 3, "name": data.get("name")}
    return jsonify(new_item), 201

@app.route("/items/<int:item_id>", methods=["GET"])
def get_item(item_id):
    item = session.query(Item).filter_by(id=item_id).first()
    if item:
        return jsonify({"id": item.id, "name": item.name})
    return jsonify({"error": "Item not found"}), 404

@app.route("/items/<int:item_id>", methods=["PUT"])
def update_item(item_id):
    data = request.get_json()
    item = session.query(Item).filter_by(id=item_id).first()
    if item:
        item.name = data.get("name")
        session.commit()
        return jsonify({"id": item.id, "name": item.name})
    return jsonify({"error": "Item not found"}), 404

@app.route("/items/<int:item_id>", methods=["DELETE"])
def delete_item(item_id):
    item = session.query(Item).filter_by(id=item_id).first()
    if item:
        session.delete(item)
        session.commit()
        return jsonify({"message": "Item deleted successfully"})
    return jsonify({"error": "Item not found"}), 404

if __name__ == "__main__":
    app.run(debug=True)
