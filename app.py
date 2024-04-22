from typing import Union
from fastapi import FastAPI,Query,Request,HTTPException
from fastapi.responses import HTMLResponse
from pymongo.mongo_client import MongoClient
from bson import ObjectId
from pydantic import BaseModel,Field
from typing import Dict,Optional
from fastapi.encoders import jsonable_encoder
from starlette.responses import HTMLResponse
import redis

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

redis_client = redis.Redis(
    host="redis-18863.c330.asia-south1-1.gce.redns.redis-cloud.com", port=18863,
    username="default",
    password="EBsbnOG81IQNCO3PbOwGmnDgfPWiJeqK",
)

@app.middleware("http")
async def api_rate_limiter(request: Request, call_next):
    user_id = request.headers['user_id']
    TIME_DURATION = 60*60*24  # Time duration in seconds (24 hours)
    RATE_LIMIT = 10      # API calls allowed in TIME_DURATION (Meaning 10 calls permitted in 24 hours)

    cur_count = redis_client.incr(user_id)
    
    # If the key is set for the first time, set the expiry time
    if cur_count == 1:
        redis_client.expire(user_id, TIME_DURATION)
    
    # If the count exceeds the limit, return the response and time left after which the user can make the request.
    if cur_count > 2*RATE_LIMIT:
        seconds = redis_client.ttl(user_id)
        seconds = seconds % (24 * 3600)
        hour = seconds // 3600
        seconds %= 3600
        minutes = seconds // 60
        seconds %= 60
        response = HTMLResponse(f'<html><body><h3>Rate Limit exceeded.</h3><h3>Try again in {str(hour)} hours, {str(minutes)} minutes, {str(seconds)} seconds.</h3></body></html>')
        return response
    
    # If the count is within the limit, proceed with the request.
    return await call_next(request)


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



