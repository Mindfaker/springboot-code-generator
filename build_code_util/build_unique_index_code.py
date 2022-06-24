import os
from build_java_util import exchange_field_2_camel_case
from build_java import build_param_list_str, UNIQUE_INDEX_SELECT_TEMPLATE, check_line_have_placeholder, get_table_structure

# 代码生成中可能涉及的占位符名称列表
necessary_format_name_list = ["big_camel_case", "little_camel_case",  "index_num", "duplicate_param", "duplicate_logic"]


def format_template_line(line: str, replace_dict: dict):
    """

    给模板插入对应的模板参数

    :param line:
    :param replace_dict:
    :return:
    """
    target_line = line
    for format_name in necessary_format_name_list:
        format_flag = "{" + format_name + "}"
        if format_flag in line:

            target_line = target_line.replace(format_flag, str(replace_dict.get(format_name, "")))
    return target_line


def check_replace_dict(replace_dict: dict):
    """

    检查占位符数量是否匹配

    :param replace_dict:  占位符占用的位置
    :return:
    """
    missing_key_list = [x for x in necessary_format_name_list if x not in replace_dict.keys()]
    return len(missing_key_list) > 0


def build_unique_select_code(template_info, replace_dict):
    """

    给模板添加字段信息

    :param template_info:
    :param replace_dict:
    :return:
    """
    target_code_list = []
    for line in template_info:
        target_code_list.append(format_template_line(line, replace_dict))
    return "".join(target_code_list)


def batch_build_unique_select_fuc(table_name, engine, table_structure):
    pass

# TODO 待完善----------
def build_unique_select_func(duplicate_columns_list: list,  table_name: str, table_structure: dict, index_name: str):
    """

    根据一组唯一索引的字段组合  完成一组唯一索引查询字段的服务链接

    :param table_name: 表名称
    :param index_name:  唯一索引的名称
    :param table_structure: 表的字段结构
    :param duplicate_columns_list:   唯一索引的键的组合
    :return:  一段唯一索引的检索逻辑
    """
    logic_duplicate_columns_list = [x for x in duplicate_columns_list if x != "deleted"]

    logic_list = list()
    logic_format_str = ".and{big_camel_case}EqualTo({little_camel_case})"
    for column in logic_duplicate_columns_list:
        logic_list.append(logic_format_str.format(little_camel_case=exchange_field_2_camel_case(column),
                                                  big_camel_case=exchange_field_2_camel_case(column, False)))

    # 进行format使用的字典
    replace_dict = {"little_camel_case": exchange_field_2_camel_case(table_name),
                    "big_camel_case": exchange_field_2_camel_case(table_name, False),
                    "duplicate_logic": "criteria.andDeletedEqualTo(false)" + "".join(logic_list) + ";",
                    "duplicate_param": build_param_list_str(logic_duplicate_columns_list, table_structure),
                    "index_name": index_name,
                    }

    if not check_replace_dict(replace_dict):
        return build_unique_select_code(UNIQUE_INDEX_SELECT_TEMPLATE, replace_dict)
    else:
        return None


if __name__ == '__main__':
    get_table_structure()
    pass