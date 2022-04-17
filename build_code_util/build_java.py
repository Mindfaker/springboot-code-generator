import os
import sys
import pymysql

from sqlalchemy import create_engine
from sqlalchemy.engine import reflection

admin_root = os.path.join(os.path.dirname(os.path.dirname(__file__)), "util")
sys.path.append(admin_root)

from build_java_util import exchange_field_2_camel_case
from config.build_code_config import placeholder_list, config_param_list

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


def read_template(template_name: str) -> list:
    """

    读取模板的数据

    :param template_name:
    :return:
    """
    f = open(os.path.join(get_template_path(), template_name), encoding="utf-8")
    demo_list = f.readlines()
    f.close()
    return demo_list


def get_template_path():
    """

    返回模板所在的文件路劲

    :return:
    """
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "code_template")


# 服务的模板  和  后台的模板
SERVICE_TEMPLATE = read_template("service_template")
ADMIN_TEMPLATE = read_template("admin_controller_template")


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
    return ",  ".join(param_info_list) + ","


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


def build_duplicate_admin_case_param(table_name, duplicate_columns_list):
    """

    生成校验唯一索引的查询入参

    :param table_name:
    :param duplicate_columns_list:
    :return:
    """
    duplicate_format_str = "{little_camel_case}.get{bigColumnName}()"
    duplicate_columns_list = [x for x in duplicate_columns_list if x != "deleted"]
    duplicate_admin_list = list()
    for column in duplicate_columns_list:
        duplicate_admin_list.append(duplicate_format_str
                                    .format(little_camel_case=exchange_field_2_camel_case(table_name),
                                            bigColumnName=exchange_field_2_camel_case(column, is_small=False)))
    return ",  ".join(duplicate_admin_list)


def build_duplicate_logic(duplicate_columns_list):
    """

    创建查询唯一索引的逻辑

    :param duplicate_columns_list:
    :return:
    """
    target_duplicate_columns_list = [x for x in duplicate_columns_list if x != "deleted"]
    logic_list = list()
    logic_format_str = ".and{big_camel_case}EqualTo({little_camel_case})"
    for column in target_duplicate_columns_list:
        logic_list.append(logic_format_str.format(little_camel_case=exchange_field_2_camel_case(column),
                                                  big_camel_case=exchange_field_2_camel_case(column, False)))
    return "\t\tcriteria.andDeletedEqualTo(false)" + "".join(logic_list) + ";"


def check_line_have_placeholder(line):
    """

    检查一行模板是否有  占位符

    :param line:
    :return:
    """
    for placeholder in placeholder_list:
        if placeholder in line:
            return True
    return False


def build_code(template, table_name, replace_dict):
    """

    根据模板创建代码

    :param template:
    :param table_name:
    :param replace_dict:
    :return:
    """
    code_list = list()
    for line in template:
        if check_line_have_placeholder(line):
            code_list.append(line
                             .replace("{big_camel_case}", exchange_field_2_camel_case(table_name, is_small=False))
                             .replace("{little_camel_case}", exchange_field_2_camel_case(table_name))
                             .replace("{select_param}", replace_dict["param_list_str"])
                             .replace("{select_logic}", replace_dict["logic_list_str"])
                             .replace("{menu_list}", replace_dict["menu_list"])
                             .replace("{admin_select_param}", replace_dict["admin_select_param"])
                             .replace("{duplicate_admin_case_param}", replace_dict["duplicate_admin_case_param"])
                             .replace("{duplicate_param}", replace_dict["duplicate_param"])
                             .replace("{duplicate_logic}", replace_dict["duplicate_logic"])
                             .replace("{param_list}", replace_dict["param_list"]))
        else:
            code_list.append(line)
    return "".join(code_list)


# todo 等待实现
def check_config_info():
    print("对传入的参数进行必要性校验")
    pass


def exchange_format_dict_from_input_param(format_dict, input_param: dict, format_key_list: list) -> dict:
    """

    将 前端输入参数中  生成直接需要的参数  传递给  生成参数的字典中

    :param format_dict:
    :param input_param:
    :param format_key_list:
    :return:
    """
    for key in format_key_list:
        if key in input_param.keys():
            format_dict[key] = input_param.get(key)
    return format_dict


def check_connect(all_config_dict):
    """

    检查数据库连接是否成功

    :param all_config_dict:
    :return:
    """
    engine = get_connection(all_config_dict["sql_name"], all_config_dict["mysql_root"],
                            all_config_dict["mysql_password"],
                            all_config_dict["mysql_host"], all_config_dict["mysql_port"])
    try:
        engine.table_names()
        return True
    except Exception as e:
        return False


def get_table_structure(all_config_dict):
    """

    根据前端的数据  检查一个表的所有字段

    :param all_config_dict:
    :return:
    """
    engine = get_connection(all_config_dict["sql_name"], all_config_dict["mysql_root"],
                            all_config_dict["mysql_password"],
                            all_config_dict["mysql_host"], all_config_dict["mysql_port"])
    table_name = all_config_dict["table_name"]
    table_structure = get_mysql_structure(table_name, engine=engine)
    return table_structure


def build_code_main_process(all_config_dict, code_type):
    """

    创建代码的主要流程

    :param all_config_dict:  前端提供的主要配置参数
    :param code_type:   需要生成的代码类型  目前应该 只有 service 和 admin
    :return:
    """

    # 用来替换模板的数据
    format_dict = dict()

    engine = get_connection(all_config_dict["sql_name"], all_config_dict["mysql_root"],
                            all_config_dict["mysql_password"],
                            all_config_dict["mysql_host"], all_config_dict["mysql_port"])

    check_config_info()
    table_name = all_config_dict["table_name"]

    get_table_all_name(all_config_dict)

    table_structure = get_mysql_structure(table_name, engine=engine)

    # 查询使用的字段名称
    if all_config_dict.get("select_columns") is None:
        columns_list = get_select_columns_list(table_structure)
    else:
        columns_list = parse_param_to_list(all_config_dict.get("select_columns"))

    # 唯一索引的字段名称
    if all_config_dict.get("unique_index_columns") is None:
        unique_columns_list = get_duplicate_columns_list(table_name, engine=engine)
    else:
        unique_columns_list = parse_param_to_list(all_config_dict.get("unique_index_columns"))

    unique_columns_list = [x for x in unique_columns_list if x != "deleted"]

    # 生成填充模板需要的参数
    format_dict["param_list_str"] = build_param_list_str(columns_list, table_structure)
    format_dict["logic_list_str"] = build_logic_list_str(columns_list, table_structure)
    format_dict["admin_select_param"] = build_admin_param_list_str(columns_list, table_structure)
    format_dict["duplicate_param"] = build_param_list_str(unique_columns_list, table_structure)
    format_dict["duplicate_admin_case_param"] = build_admin_param_list_str(unique_columns_list, table_structure)
    format_dict["duplicate_admin_case_param"] =\
        build_duplicate_admin_case_param(table_name=table_name, duplicate_columns_list=unique_columns_list)
    format_dict["duplicate_logic"] = build_duplicate_logic(unique_columns_list)
    format_dict["param_list"] = ",".join([exchange_field_2_camel_case(x) for x in columns_list])

    format_dict = exchange_format_dict_from_input_param(format_dict, all_config_dict, config_param_list)

    if code_type == "service":
        template = SERVICE_TEMPLATE
    elif code_type == "admin":
        template = ADMIN_TEMPLATE
    else:
        return ""

    return build_code(template=template, table_name=all_config_dict["table_name"], replace_dict=format_dict)


# 切割每一条配置文件数据
def split_config_data(config_line):
    if ":" not in config_line:
        return None

    first_spilt_index = config_line.index(":")

    # 没有配置的话
    if config_line[first_spilt_index + 1: ].strip() == "":
        return None

    return [config_line[:first_spilt_index],   config_line[first_spilt_index + 1: ]]


def read_config(config_file_name = "config_info.txt"):
    """
    读取解析配置文件
    :param config_file_name:  配置文件的名称
    :return:
    """

    # 如果配置文件不存在则返回空值
    config_file_path = os.path.join(file_dir_path, config_file_name)
    if not os.path.exists(config_file_path):
        return None
    config_data = {}
    f = open(config_file_path, encoding="utf-8")
    file_line_list = f.readlines()
    for file_line in file_line_list:

        # 进行数据分隔
        data_list =   split_config_data(file_line)
        if data_list == None:
            continue

        if data_list[0].strip() == "select_columns" or data_list[0].strip() == "unique_index_columns":
            config_data["select_columns"] = list(map(lambda x: x.strip(), data_list[1].split(",")))
        else:
            config_data[data_list[0].strip()] = data_list[1].strip()
    return config_data


if __name__ == '__main__':
    pass




def read_config():
    """
    读取解析配置文件
    :param config_file_name:  配置文件的名称
    :return:
    """

    # 如果配置文件不存在则返回空值
    config_file_path = r"D:\workproject\digital-collection-server\server-db\src\main\java\cn\exploring\engine\server\db\util\config_info.txt"
    config_data = {}
    f = open(config_file_path, encoding="utf-8")
    file_line_list = f.readlines()
    for file_line in file_line_list:

        # 进行数据分隔
        data_list = split_config_data(file_line)
        if data_list is None:
            continue

        if data_list[0].strip() == "select_columns" or data_list[0].strip() == "unique_index_columns":
            config_data["select_columns"] = list(map(lambda x: x.strip(), data_list[1].split(",")))
        else:
            config_data[data_list[0].strip()] = data_list[1].strip()
    return config_data


def parse_param_to_list(list_param):
    if type(list_param) == list:
        return list_param

    return list(map(lambda x: x.strip(), list_param.split(",")))


# 切割每一条配置文件数据
def split_config_data(config_line):
    if ":" not in config_line:
        return None

    first_spilt_index = config_line.index(":")

    # 没有配置的话
    if config_line[first_spilt_index + 1:].strip() == "":
        return None

    return [config_line[:first_spilt_index], config_line[first_spilt_index + 1:]]


def test_main():
    config_data_dict = read_config()
    aa = build_code_main_process(config_data_dict, "service")
    return aa


if __name__ == '__main__':
    config_data_dict = read_config()
    aa = build_code_main_process(config_data_dict, "service")
    print(aa)
