from fastapi import FastAPI, responses
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from flask import Flask
import json
from flask import request, jsonify, make_response
# from flask_cors import *
from pydantic import BaseModel
from build_code_util import build_java
from build_unique_index_code import *


class codeInfo(BaseModel):
    code: str


class CommonCheckParam(BaseModel):
    mysql_host: str
    mysql_port: int
    mysql_root: str
    mysql_password: str
    sql_name: str
    table_name: str = None


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


@app.post("/check_connect")
def check_connect(web_config: CommonCheckParam):
    return {"message": build_java.check_connect(web_config.dict())}


@app.post("/get_table_info")
def get_table_info(web_config: CommonCheckParam):
    engine = build_java.get_connection(web_config.sql_name, web_config.mysql_root,
                                       web_config.mysql_password, web_config.mysql_host, web_config.mysql_port)

    table_structure = build_java.get_table_structure(web_config.dict())
    unique_columns_list = build_java.get_duplicate_columns_list(web_config.table_name, engine=engine)

    return build_unique_select_func(unique_columns_list, web_config.table_name, table_structure, 1)
    # return {"message": build_java.get_table_structure(web_config.dict())}


@app.post("/what")
def build_code_oo(web_config: ParamGo):
    # engine = build_java.get_connection(web_config.sql_name, web_config.mysql_root,
    #                                    web_config.mysql_password, web_config.mysql_host, web_config.mysql_port)
    #
    # table_structure = build_java.get_table_structure(web_config.dict())
    # unique_columns_list = build_java.get_duplicate_columns_list(web_config.table_name, engine=engine)
    #
    # kk = build_unique_select_func(unique_columns_list[0], web_config.table_name, table_structure, 1)
    # print(kk)

    web_config.dict()
    data_config = web_config.dict()
    aa = build_java.build_code_main_process(data_config, data_config.get("type", "service"))
    aa = aa.replace(" ", "&nbsp").replace("<", "&lt;").replace(">", "&gt;")
    return codeInfo(code=aa)


if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=8000)
