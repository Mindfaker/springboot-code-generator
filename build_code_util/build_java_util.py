import os
import time
from sqlalchemy import create_engine
from sqlalchemy.engine import reflection

# 程序所在的文件夹路径
file_dir_path = os.path.dirname(os.path.abspath(__file__))

type_dict = {
    "<class 'sqlalchemy.dialects.mysql.types.INTEGER'>": "Integer",
    "<class 'sqlalchemy.dialects.mysql.types.TINYINT'>": "Boolean",
    "<class 'sqlalchemy.dialects.mysql.types.VARCHAR'>": "String"
}

logic_dict = {
    "<class 'sqlalchemy.dialects.mysql.types.INTEGER'>": '\t\t        if ({little_camel_case} != null ) {\r\n\tcriteria.and{big_camel_case}EqualTo({little_camel_case});\r\n}',
    "<class 'sqlalchemy.dialects.mysql.types.TINYINT'>": '\t\t        if ({little_camel_case} != null ) {\r\n\tcriteria.and{big_camel_case}EqualTo({little_camel_case});\r\n}',
    "<class 'sqlalchemy.dialects.mysql.types.VARCHAR'>": '\t\t        if (!StringUtils.isEmpty({little_camel_case})) {\r\n\tcriteria.and{big_camel_case}Like("%" + {little_camel_case} + "%");\r\n}'
}

result_code = ""


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


def uppercase_word_first_letter(word):
    return word[0].upper() + word[1:]


# 将_分隔编码转换成驼峰
def exchange_field_2_camel_case(sql_field_name, is_small=True):
    field_list = sql_field_name.split("_")
    target_list = list()
    for i in range(len(field_list)):
        if i == 0 and is_small:
            target_list.append(field_list[i])
        else:
            target_list.append(uppercase_word_first_letter(field_list[i]))
    return "".join(target_list)



# 获取mysql 数据结构对象
def get_mysql_structure(table_name):
    insp = reflection.Inspector.from_engine(engine)
    columns = insp.get_columns(table_name)
    structure_map = {}
    for column in columns:
        structure_map[column.get("name")] = column
    return structure_map


def get_select_columns_list(table_structure):
    """

    当用户没配置专属的数据的时候

    :param table_structure:
    :return:
    """
    # 通常数据库中 默认必有的字段
    default_columns_list = ["id", "add_time", "update_time", "deleted"]
    return [x for x in table_structure.keys() if x not in default_columns_list]


def build_param_list_str(columns_list, table_structure: dict):
    """

    根据  表结构   和   字段列表  创建入参

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

    根据  表结构   和   字段列表   创建controller层的入参

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

    根据  表结构  和  字段列表   创建通用查询的逻辑

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


def build_duplicate_admin_case_param(duplicate_columns_list):
    """

    生成校验唯一索引的查询入参

    :param duplicate_columns_list:
    :return:
    """
    duplicate_format_str = "{little_camel_case}.get{bigColumnName}()"
    duplicate_columns_list = [x for x in duplicate_columns_list if x != "deleted"]
    duplicate_admin_list = list()
    for column in duplicate_columns_list:
        duplicate_admin_list.append(duplicate_format_str
                                    .format(little_camel_case=exchange_field_2_camel_case(column),
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


def get_file_output_path():
    now_path = os.path.abspath(__file__)
    return os.path.join(os.path.dirname(os.path.dirname(now_path)), "service")


def get_admin_file_output_path():
    now_path = os.path.abspath(__file__)
    admin_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(now_path))).replace("server-db", "server-admin-api"), "admin")
    return os.path.join(admin_path, "web")


def read_config(config_file_name="config_info.txt"):
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
        data_list = split_config_data(file_line)
        if data_list == None:
            continue

        if data_list[0].strip() == "select_columns":
            config_data["select_columns"] = list(map(lambda x: x.strip(), data_list[1].split(",")))
        else:
            config_data[data_list[0].strip()] = data_list[1].strip()
    return config_data


# 切割每一条配置文件数据
def split_config_data(config_line):
    if ":" not in config_line:
        return None

    first_spilt_index = config_line.index(":")

    # 没有配置的话
    if config_line[first_spilt_index + 1:].strip() == "":
        return None

    return [config_line[:first_spilt_index], config_line[first_spilt_index + 1:]]


def check_config(config_dict: dict):
    """
    检查读取的参数中是否满足的必要的参数项目
    :return:
    """
    base_config_key = ["table_name", "mysql_host", "mysql_port", "mysql_root", "mysql_password"]
    return [x for x in base_config_key if x not in config_dict.keys()]


def get_service_code(all_config, demo_config_name="demoConfigService"):
    """

    创建service的代码

    :param all_config:
    :param demo_config_name:
    :return:
    """
    table_name = all_config["table_name"]

    f = open(os.path.join(file_dir_path, demo_config_name), encoding="utf-8")
    demo_list = f.readlines()
    f.close()

    target_list = list()
    for demo in demo_list:
        if (
                "big_camel_case" in demo or "little_camel_case" in demo or "select_param" in demo or "select_logic" in demo):
            target_list.append(demo
                               .replace("{big_camel_case}", exchange_field_2_camel_case(table_name, is_small=False))
                               .replace("{little_camel_case}", exchange_field_2_camel_case(table_name))
                               .replace("{select_param}", param_list_str)
                               .replace("{select_logic}", logic_list_str))
        else:
            target_list.append(demo)
    output_file_dir = get_file_output_path() if "service_output_path" not in all_config.keys() else all_config[
        "service_output_path"]

    if not os.path.isdir(output_file_dir):
        print("目标输出的文件路径不存在  将新建之~~~")
        os.mkdir(output_file_dir)

    output_file_path = os.path.join(output_file_dir,
                                    exchange_field_2_camel_case(table_name, is_small=False) + "Service.java")

    out_file = open(output_file_path, "w", encoding="utf-8")
    out_file.write("".join(target_list))
    out_file.close()


def get_admin_code(all_config, demo_config_name="demoConfigAdmin"):
    table_name = all_config["table_name"]
    menu_list = all_config["menu_list"]

    f = open(os.path.join(file_dir_path, demo_config_name), encoding="utf-8")
    demo_list = f.readlines()
    f.close()

    target_list = list()
    for demo in demo_list:
        if (
                "big_camel_case" in demo or "little_camel_case" in demo or "select_param" in demo
                or "select_logic" in demo or "little_camel_case" in demo or "menu_list" in demo):
            target_list.append(demo
                               .replace("{big_camel_case}", exchange_field_2_camel_case(table_name, is_small=False))
                               .replace("{little_camel_case}", exchange_field_2_camel_case(table_name))
                               .replace("{admin_select_param}", admin_select_param + " ,")
                               .replace("{menu_list}", menu_list)
                               .replace("{param_list}",
                                        ",".join([exchange_field_2_camel_case(x) for x in columns_list])))
        else:
            target_list.append(demo)

    output_file_dir = get_admin_file_output_path() if "admin_controller_output_path" not in all_config.keys() else \
        all_config["admin_controller_output_path"]

    if not os.path.isdir(output_file_dir):
        print("目标输出的文件路径不存在  将新建之~~~")
        os.mkdir(output_file_dir)

    output_file_path = os.path.join(output_file_dir, "Admin" + exchange_field_2_camel_case(table_name,
                                                                                           is_small=False) + "Controller.java")

    out_file = open(output_file_path, "w", encoding="utf-8")
    out_file.write("".join(target_list))
    out_file.close()


def get_connection(sql_name, root='engine', password='Engine123S56^&*enginE',
                   host='rm-8vb7856yl4b5q1kf9yo.mysql.zhangbei.rds.aliyuncs.com', port='3306'):
    engine = create_engine("mysql+pymysql://{}:{}@{}:{}/{}".format(root, password, host, port, sql_name))
    return engine


if __name__ == '__main__':
    all_config_data = read_config()

    engine = get_connection(all_config_data["sql_name"], all_config_data["mysql_root"],
                            all_config_data["mysql_password"], all_config_data["mysql_host"],
                            all_config_data["mysql_port"])

    less_base_config_name_list = check_config(all_config_data)
    if len(less_base_config_name_list) != 0:
        print("----------------------" + ",".join(
            less_base_config_name_list) + "为必填项！！！  请检查配置文件， 程序将在2秒后自动关闭" + "------------------------")
        time.sleep(2)

    table_name = all_config_data["table_name"]
    table_structure = get_mysql_structure(table_name)

    if all_config_data.get("select_columns") == None:
        columns_list = get_select_columns_list(table_structure)
    else:
        columns_list = all_config_data.get("select_columns")

    param_list_str = build_param_list_str(columns_list, table_structure)
    logic_list_str = build_logic_list_str(columns_list, table_structure)
    admin_select_param = build_admin_param_list_str(columns_list, table_structure)

    get_service_code(all_config_data)
    get_admin_code(all_config_data)
