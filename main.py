from fastapi import FastAPI, responses
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from flask import Flask
import json
from flask import request, jsonify, make_response
# from flask_cors import *
from pydantic import BaseModel
from build_code_util import build_java
from generic_object import *
from clickhouse_selecter import SelectClickhouseData


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


@app.post("/check_connect")
def check_connect(web_config: CommonCheckParam):
    return {"message": build_java.check_connect(web_config.dict())}


@app.post("/get_table_info")
def get_table_info(web_config: CommonCheckParam):
    return {"message": build_java.get_table_structure(web_config.dict())}


@app.post("/what")
def build_code_oo(web_config: ParamGo):
    web_config.dict()
    data_config = web_config.dict()
    aa = build_java.build_code_main_process(data_config, data_config.get("type", "service"))
    aa = aa.replace(" ", "&nbsp").replace("<", "&lt;").replace(">", "&gt;")
    return codeInfo(code=aa)


@app.post("/select_data_by_ck")
def select_data_by_ck(sql_condition: MySqlChangeLogCondition):
    conn_setting = {'host': "cdh5", 'user': 'root', 'password': 'Engine1314enginE'}
    ck = SelectClickhouseData(conn_setting, sql_filter_condition=sql_condition)
    return codeInfo(code=ck.select_data_from_db())


if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=8000)
