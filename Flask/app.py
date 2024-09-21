import json
import mimetypes

from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text
from flask_marshmallow import Marshmallow
from flask_cors import CORS
import os
from werkzeug.routing import ValidationError
import requests
from Backend.Fast.LocationFinder import *

app = Flask(__name__, static_folder="web/static",
            template_folder="web/templates")
CORS(app, origins=['http://0.0.0.0:5055/webhook', 'http://127.0.0.1:5055/webhook', 'http://localhost:5055/webhook',
                   'http://localhost:5005/webhooks/rest/webhook'])
"""
# Decorator to add CORS headers to the response
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

# Apply the decorator to all routes
@app.after_request
def after_request(response):
    return add_cors_headers(response)
"""

basedir = os.path.abspath(os.path.dirname(__file__))
print(basedir)
app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///' + \
    os.path.join(basedir, 'SZA.db')
app.config['SQLALCHEMY_TRACK_MODIFICATION'] = False

db = SQLAlchemy(app)
ma = Marshmallow(app)


class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    locationID = db.Column(db.Integer)
    locationName = db.Column(db.String(100))
    propertyLink = db.Column(db.String(100))
    latitude = db.Column(db.String(100))
    longitude = db.Column(db.String(100))
    address = db.Column(db.String(100))
    pincode = db.Column(db.Integer)

    def __init__(self, locationID, locationName, propertyLink, latitude, longitude, address, pincode):
        self.locationID = locationID
        self.locationName = locationName
        self.propertyLink = propertyLink
        self.latitude = latitude
        self.longitude = longitude
        self.address = address
        self.pincode = pincode


with app.app_context():
    db.create_all()
"""
>>> from project import app, db
>>> app.app_context().push()
>>> db.create_all()
"""


class LocationSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        fields = ('name', 'latitude', 'longitude', 'startingPrice', 'googleMapLink', 'imageUrl',
                  'genderName', 'micromarketId', 'micromarketName', 'cityId', 'citySlug', 'gender')


location_schema = LocationSchema()
locations_schema = LocationSchema(many=True)


# Add new location
@app.route("/location", methods=['POST'])
def add_location():
    id = 0
    locationID = request.json["locationID"]
    locationName = request.json["locationName"]
    propertyLink = request.json["propertyLink"]
    latitude = request.json["latitude"]
    longitude = request.json["longitude"]
    address = request.json["address"]
    pincode = request.json["pincode"]

    new_location = Location(locationID, locationName,
                            propertyLink, latitude, longitude, address, pincode)

    db.session.add(new_location)
    db.session.commit()
    # return location_schema.jsonify(new_location,many=False)

    # Validate and deserialize input
    schema = LocationSchema()
    try:
        print(type(new_location))
        data = schema.load(request.get_json())
    except ValidationError as err:
        return jsonify(err.messages), 422

    # Process the valid data (e.g., save to database)
    # ...

    return jsonify({'message': 'User created successfully', 'data': data}), 201


# location filter
@app.route("/filter", methods=['POST'])
def location_filter():
    """
       parameters = {
            'lat': 12.9784,
            'long': 77.6408,
            'radius': 5
        }
        """
    lat = request.json["lat"]
    long = request.json["long"]
    radius = request.json["radius"]
    print(lat)
    print(long)
    print(radius)
    parameters = {'input_lat': lat, 'input_long': long, 'radius': radius}
    schema = LocationSchema(many=True)

    query = text('SELECT * FROM SZA WHERE ( 6371 * ACOS( COS(RADIANS(90 - latitude)) * COS(RADIANS(90 - :input_lat)) + SIN(RADIANS(90 - latitude)) * SIN(RADIANS(90 - :input_lat)) * COS(RADIANS(longitude - :input_long)) ) ) <= :radius;')
    print(query)
    results = db.session.execute(query, parameters)

    data = schema.dump(results)
    for i in results:
        print(i.json())
    return data

# Add new location


@app.route("/query", methods=['POST'])
async def get_query():
    query = request.json["query"]
    #print(query)
    myobj = {"query":query}
    x = requests.post(" http://127.0.0.1:5008/find", json=myobj)

    final_answer = x.json()
    final_answer = eval(final_answer["Answer"])
    print(final_answer)
    print(type(final_answer))
    
    
    location_name = final_answer['location_name']
    print(location_name)
    longitude = final_answer['longitude']
    latitude = final_answer['latitude']
    pincode = final_answer['pincode']
    min_price = final_answer['min_price']
    max_price = final_answer['max_price']
    # print(await load(location_name))
    print(location_name)
    
    #return load(location_name)


@app.route('/find', methods=['POST'])
def find():
    query = json.loads(request.data)["query"]

    print(query)
    url = 'http://localhost:11434/api/generate'
    myobj = {"model": "llama3", "stream": False, "prompt": "''' You have to summarized answer "
             "In the following query extract the location name"
                                                           " and pincode and longitude and latitude and radius and minimum and maximum budget."
                                                           "If able to convert the extracted location name into latitude and longitude do it other wise dont convert."
                                                           "if you not sure say "". return the value with the only dictionary format location_name, longitude, latitude pincode, min_price, max_price variables. Output should be a dictionary format, Should not contain any other string."""
                                                           "'Query:'. Show only answer and dont add the query in the "
                                                           "answer "
                                                           "block.\n\nQuery:" + query + ".'''"}
    print(myobj)
    x = requests.post(url, json=myobj)

    final_answer = x.json()

    print(final_answer['response'])
    
    # return jsonify({'data': query_results})
    return {"Answer": final_answer['response']}


# if __name__ == '__main__':
#     app.run(debug=True, port=5003)

# https://medium.com/@nithinbharathwaj/marshmallow-with-python-flask-263e1fd5911f
