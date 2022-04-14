from fastapi import FastAPI, responses
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from flask import Flask
import json
from flask import request, jsonify, make_response
from flask_cors import *
from pydantic import BaseModel
from build_code_util import build_java

class codeInfo(BaseModel):
    code: str

class ParamGo(BaseModel):
    sql_name: str
    table_name: str
    select_columns: str
    menu_list: str
    mysql_host: str
    mysql_port: int
    mysql_root: str
    mysql_password: str
    type: str

app = FastAPI()
# app = Flask(__name__)
# CORS(app, origins="*")

#  设置跨域
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": build_java.test_main()}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


@app.post("/what")
def build_code_oo(web_config: ParamGo):
    web_config.dict()
    # aa = UserOut()
    # aa.email = "liu_cheng_jiu@163.com"
    # aa.username = "faker"
    # return web_config
    # return aa
    # if request.headers.get('Content-Type') == 'application/x-www-form-urlencoded':
    #     print("hello")
    # elif request.headers.get('Content-Type') == 'application/json':
    #     r = request.json
    # print(request.form.get("type"))
    # print(request.form)
    # print(request.stream.read())
    # data = request.get_json()
    # print(data)
    # return  ""
    data_config = web_config.dict()
    # headers = {"Content-Type": "application/json"}
    return codeInfo( code = build_java.build_code_main_process(data_config, data_config.get("type", "service")))


if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=8000)


