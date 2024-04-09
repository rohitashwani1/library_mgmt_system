from typing import Union
from fastapi import FastAPI,Query
from fastapi.responses import HTMLResponse
from pymongo.mongo_client import MongoClient
from bson import ObjectId
from pydantic import BaseModel,Field
from typing import Dict,Optional
from fastapi.encoders import jsonable_encoder

class Address(BaseModel):
    city: str
    country: str

class Student(BaseModel):
    name: str
    age: int
    address: Address

app = FastAPI()
uri = "mongodb+srv://rohitas:sitaram1@cluster0.5sei3hk.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(uri)
db = client["cloud_intern"]
collection = db["Students"]


@app.get("/",response_class=HTMLResponse)
def welcome():
    ans = "<h1>Welcome to Library Management System</h1>"
    return ans


@app.post("/students",status_code=201)
def post_data(student: Student):
    student = student.dict()
    id = collection.insert_one(student)
    return {"id":str(id.inserted_id)}


@app.get("/students",status_code=200)
def get_data(country: str = Query(None), age: int = Query(None)):
    # Prepare filter based on query parameters
    filter_params = {}
    if country:
        filter_params["address.country"] = country
        print(country)
    if age is not None:
        filter_params["age"] = {"$gte": age}
    data = list(collection.find(filter_params))
    ret_data = []
    for i in data:
        tmp = {}
        tmp["name"] = i["name"]
        tmp["age"] = i["age"]
        ret_data.append(tmp)
    return {"data":ret_data}


@app.get("/students/{id}",status_code=200)
def get_data(id: str):
    id = ObjectId(id)
    data = collection.find_one({"_id": id})
    del data["_id"]
    return data


@app.patch("/students/{id}",status_code=204)
def patch_student(id: str, student: dict):
    id = ObjectId(id)
    item = collection.find_one({"_id":id})
    if 'name' in student:
        item['name'] = student['name']
    if 'age' in student:
        item['age'] = student['age']
    if 'address' in student:
        if 'city' in student['address']:
            item['address']['city'] = student['address']['city']
        if 'country' in student['address']:
            item['address']['country'] = student['address']['country']
    collection.find_one_and_update(filter={"_id":id},update={"$set" : item})
    return {}


@app.delete("/students/{id}",status_code=200)
def delete_student(id: str):
    id = ObjectId(id)
    deleted_item = collection.find_one_and_delete({"_id": id})
    return {}



