from pydantic import BaseModel


class codeInfo(BaseModel):
    code: str


class CommonCheckParam(BaseModel):
    mysql_host: str
    mysql_port: int
    mysql_root: str
    mysql_password: str
    sql_name: str
    table_name: str = None


class SelectTableList(BaseModel):
    db_name: str


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


# 对clickhouse  进行筛选查询的条件
class MySqlChangeLogCondition(BaseModel):
    ckTableName: str
    changeTypeList: list
    dbName: str
    tableName: str
    SQL: str
    page: int
    size: int

