import os
from sqlalchemy import create_engine
from sqlalchemy.engine import reflection

from util.build_java_util import exchange_field_2_camel_case

default_columns_list = ["id", "add_time", "update_time", "deleted"]

# 程序所在的文件夹路径
file_dir_path = os.path.dirname(os.path.abspath(__file__))

type_dict = {
    "<class 'sqlalchemy.dialects.mysql.types.INTEGER'>": "Integer",
    "<class 'sqlalchemy.dialects.mysql.types.TINYINT'>": "Boolean",
    "<class 'sqlalchemy.dialects.mysql.types.VARCHAR'>": "String"
}

logic_dict = {
    "<class 'sqlalchemy.dialects.mysql.types.INTEGER'>": '\t\t        if ({little_camel_case} != null ) {'
                                                         '\r\n\tcriteria.and{big_camel_case}EqualTo({'
                                                         'little_camel_case});\r\n}',
    "<class 'sqlalchemy.dialects.mysql.types.TINYINT'>": '\t\t        if ({little_camel_case} != null ) {'
                                                         '\r\n\tcriteria.and{big_camel_case}EqualTo({'
                                                         'little_camel_case});\r\n}',
    "<class 'sqlalchemy.dialects.mysql.types.VARCHAR'>": '\t\t        if (!StringUtils.isEmpty({little_camel_case})) '
                                                         '{\r\n\tcriteria.and{big_camel_case}Like("%" + {'
                                                         'little_camel_case} + "%");\r\n} '
}


def get_connection(sql_name, root='engine', password='Engine123S56^&*enginE',
                   host='rm-8vb7856yl4b5q1kf9yo.mysql.zhangbei.rds.aliyuncs.com', port='3306'):
    """

    创建mysql连接

    :param sql_name:
    :param root:
    :param password:
    :param host:
    :param port:
    :return:
    """
    engine = create_engine("mysql+pymysql://{}:{}@{}:{}/{}".format(root, password, host, port, sql_name))
    return engine


def get_mysql_structure(table_name, engine):
    """

    获取mysql的 表的结构对象

    :param table_name:
    :param engine:
    :return:
    """
    insp = reflection.Inspector.from_engine(engine)
    columns = insp.get_columns(table_name)
    structure_map = {}
    for column in columns:
        structure_map[column.get("name")] = column
    return structure_map


def get_select_columns_list(table_structure):
    """

    当用户没配置专属的数据的时候,  使用所有的非默认字段进行创建基础查询

    :param table_structure:
    :return:
    """
    return [x for x in table_structure.keys() if x not in default_columns_list]


def get_duplicate_columns_list(table_name, engine) -> list:
    """

    读取表的索引信息  并返回每组唯一索引数据

    :param engine:
    :param table_name:  表名称
    :return:  该表的所有唯一索引的组合
    """
    insp = reflection.Inspector.from_engine(engine)
    index_list = insp.get_indexes(table_name)
    index_list = [x["column_names"] for x in index_list if x["type"] == "UNIQUE"]

    #  TODO 目前只完成一个唯一索引的开发
    if len(index_list) == 0:
        return None
    else:
        return index_list[0]


def build_param_list_str(columns_list, table_structure: dict):
    """

    将字段列表 转换成 查询条件

    :param columns_list:
    :param table_structure:
    :return:
    """
    param_info_list = list()

    for column in columns_list:
        column_type = type(table_structure[column]["type"])
        if str(column_type) in type_dict.keys():
            param_info_list.append(type_dict[str(column_type)] + " " + exchange_field_2_camel_case(column))
    return ",  ".join(param_info_list)


def build_admin_param_list_str(columns_list, table_structure: dict):
    """

    将字段列表  转换成  管理后台的查询条件

    :param columns_list:
    :param table_structure:
    :return:
    """
    param_info_list = list()

    for column in columns_list:
        column_type = type(table_structure[column]["type"])
        if str(column_type) in type_dict.keys():
            param_info_list.append(
                "@RequestParam " + type_dict[str(column_type)] + " " + exchange_field_2_camel_case(column))
    return ",  ".join(param_info_list)


def build_logic_list_str(columns_list, table_structure):
    """

    将字段列表  转换成  查询的逻辑

    :param columns_list:
    :param table_structure:
    :return:
    """
    logic_str_list = list()
    for column in columns_list:
        column_type = table_structure[column]['type']
        if str(column_type) in logic_dict.keys():
            logic_str_list.append(
                logic_dict[str(column_type)].format(big_camel_case=exchange_field_2_camel_case(column, is_small=False),
                                                    little_camel_case=exchange_field_2_camel_case(column)))
    return "\r\n".join(logic_str_list)


def build_code():
    pass
