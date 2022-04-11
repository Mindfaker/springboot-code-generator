from fastapi import FastAPI
import uvicorn
from build_code_util import  build_java

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}



@app.get("/build_code")
async def build_code(config_dict: str):
    eval(config_dict)
    return build_java(config_dict)



if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=8000)


