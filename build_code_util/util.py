

def uppercase_word_first_letter(word):
    """

    将单词的首字母大写

    :param word:
    :return:
    """
    return word[0].upper() + word[1:]


def exchange_field_2_camel_case(sql_field_name, is_small=True):
    """

    将_分隔编码转换成驼峰

    :param sql_field_name:   _分割的字段名
    :param is_small:   是否用小驼峰
    :return:
    """
    field_list = sql_field_name.split("_")
    target_list = list()
    for i in range(len(field_list)):
        if i == 0 and is_small:
            target_list.append(field_list[i])
        else:
            target_list.append(uppercase_word_first_letter(field_list[i]))
    return "".join(target_list)
