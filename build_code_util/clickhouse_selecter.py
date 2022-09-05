from clickhouse_driver import connect, Client
from pydantic import BaseModel
from generic_object import MySqlChangeLogCondition
import time


class SelectClickhouseData(object):
    def __init__(self, connection_settings, sql_filter_condition: MySqlChangeLogCondition,
                 ck_table_name: str = "mysql_change_log", ck_db_name: str = "engine",
                 filter_priority_list: list = ["dbName", "tableName", "changeTypeList", "SQL"]):
        self.conn_setting = connection_settings
        self.client = Client(**self.conn_setting)
        self.ck_table_name = ck_table_name
        self.change_type_dict = {0: "数据库结构变化或MYSQL自身事务", 1: "修改数据及逻辑删除", 2: "创建数据", 3: "物理删除数据"}
        self.ck_db_name = ck_db_name
        self.init_sql = r"SELECT  * from {db_name}.{table_name}  {filter_condition} ORDER  BY finishTime  DESC  {page_split}"
        self.sql_filter_condition = vars(sql_filter_condition)
        self.filter_priority_list = filter_priority_list
        if not self.check_sql_filter_condition():
            raise ValueError("查询条件过于宽泛 或 单次查询数据条目大于10000")
        self.table_field_list = self.get_table_structure()
        with self.client as cursor:
            db_list = cursor.execute('SHOW DATABASES')
            db_name_list = [x[0] for x in db_list]
            if db_list is None or len(db_list) == 0:
                raise ValueError("clickhouse 集群异常")
            if self.ck_db_name not in db_name_list:
                raise ValueError("clickhouse 中不存在 %s 数据库" % self.ck_db_name)

    def get_table_structure(self):
        """读取数据表的结构  按顺序返回目标表的字段列表"""
        table_structure = self.client.execute(
            'desc {db_name}.{table_name}'.format(db_name=self.ck_db_name, table_name=self.ck_table_name))
        table_field_list = [x[0] for x in table_structure]
        if len(table_field_list) == 0:
            raise RuntimeError("查询不到对应的表结构！  无法完成数据序列化")
        return table_field_list

    def check_sql_filter_condition(self):
        """检查查询条件是否合理"""
        return "dbName" in self.sql_filter_condition.keys() and "tableName" in self.sql_filter_condition and 0 < self.sql_filter_condition.get(
            "size") <= 10000

    def build_sql_condition(self):
        """创建查询SQL的条件"""
        filter_condition_list = []

        for filter_priority in self.filter_priority_list:
            if filter_priority in self.sql_filter_condition.keys():
                if filter_priority == "SQL":
                    filter_condition_list.append(" `{key}` LIKE '%{value}%' ".format(key=filter_priority,
                                                                                     value=self.sql_filter_condition.get(
                                                                                         filter_priority)))
                elif filter_priority == "changeTypeList":
                    type_list_length = len(self.sql_filter_condition.get(filter_priority))
                    if type_list_length == 0:
                        continue
                    elif type_list_length == 4:
                        continue
                    elif type_list_length == 1:
                        filter_condition_list.append(" {key} = {value} ".format(key="changeType",
                                                                                value=self.sql_filter_condition.get(
                                                                                    filter_priority)[0]))
                    else:
                        filter_condition_list.append(" {key} in ({value}) ".format(key="changeType", value=",".join(
                            list(map(lambda x: str(x), self.sql_filter_condition.get(filter_priority))))))
                else:
                    filter_condition_list.append(" {key} = '{value}' ".format(key=filter_priority,
                                                                              value=self.sql_filter_condition.get(
                                                                                  filter_priority)))

        return "where  " + " AND ".join(filter_condition_list)

    def build_page_split(self):
        """创建数据查询的分页"""
        if self.sql_filter_condition.get("page") is None or self.sql_filter_condition.get("page") <= 0:
            page = 1
        else:
            page = self.sql_filter_condition.get("page")

        if self.sql_filter_condition.get("size") is None or self.sql_filter_condition.get("size") <= 0:
            size = 20
        else:
            size = self.sql_filter_condition.get("size")

        return " LIMIT {start} , {size} ".format(start=(page - 1) * size, size=size) if page > 1 else " LIMIT " + str(size)

    def build_sql(self):
        """创建查询的SQL"""
        return self.init_sql.format(db_name=self.ck_db_name, table_name=self.ck_table_name,
                                    filter_condition=self.build_sql_condition(), page_split=self.build_page_split())

    def select_data_from_db(self):
        """完成数据查询及序列化的主要流程"""
        run_sql = self.build_sql()
        print("执行SQL语句:  \n" + run_sql)
        data_list = self.client.execute(run_sql)
        result_data_list = [dict(zip(self.table_field_list, x)) for x in data_list]
        return self.format_data_info(result_data_list)

    def build_update_sql_content_dict(self, update_str_list: list):
        """对更新内容的数据进行解析  转换成字典"""
        key_list = []
        value_list = []
        # 处理SQL中update语句中的更新内容的数据
        for update_str in update_str_list:
            if "=" in update_str:
                split_flag = "="
            elif " IS " in update_str:
                split_flag = " IS "
            else:
                return None
            split_list = update_str.replace("`", "").split(split_flag)
            if len(split_list) == 2:
                value = str.strip(split_list[1])
                if value == "NULL":
                    continue
                else:
                    value = int(value) if value.isdigit() else value
                key_list.append(str.strip(split_list[0]))
                value_list.append(value)
        return dict(zip(key_list, value_list))

    def explain_update_sql(self, update_sql: str):
        """对更新类型的SQL进行解释   提取出更新的内容"""
        split_data_list = update_sql.replace("UPDATE", "").replace("LIMIT 1;", "").split("WHERE")

        # SQL语句中的更新内容的语句
        update_data_list = split_data_list[0].split("SET")[1].split(", ")
        raw_data_list = split_data_list[1].split("AND")

        # 更新内容的SQL语句解析成字典
        update_dict = self.build_update_sql_content_dict(update_data_list)
        raw_dict = self.build_update_sql_content_dict(raw_data_list)

        # 修改成 只对数据的任何变动进行统计   不再细拆分
        all_value_key_list = list(update_dict.keys())
        all_value_key_list.extend(list(raw_dict.keys()))
        all_value_key_set = set(all_value_key_list)
        return [{x: [update_dict.get(x, ""), raw_dict.get(x, "")]} for x in all_value_key_set if update_dict.get(x, "") != raw_dict.get(x, "")]


        # # 更新中进行添加的数据
        # add_key_list = [{x: [update_dict.get(x), "\t"]} for x in update_dict.keys() if x not in raw_dict.keys()]
        # deleted_key_list = []
        # update_key_list = []
        #
        # for key in raw_dict.keys():
        #     if key not in update_dict.keys():
        #         deleted_key_list.append({key: ["\t", raw_dict[key]]})
        #     elif raw_dict.get(key) != update_dict.get(key):
        #         update_key_list.append({key: [update_dict[key], raw_dict[key]]})
        # return add_key_list, update_key_list, deleted_key_list, update_dict, raw_dict

    def format_data_info(self, raw_data_list: list):
        """对原始的查询数据进行必要的转化"""
        for raw_data in raw_data_list:
            raw_data["finishTimeInfo"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(raw_data["finishTime"]))
            raw_data["changeTypeInfo"] = self.change_type_dict.get(raw_data["changeType"], "未知的变动类型")

            # 如果是update类型的话进行额外解读
            if raw_data.get("changeType") == 1:
                raw_data["updateKeyInfo"] = self.explain_update_sql(raw_data.get("SQL"))

            # # 如果是update类型的话进行额外解读
            # if raw_data.get("changeType") == 1:
            #     raw_data["addKeyInfo"], raw_data["updateKeyInfo"], raw_data["deletedKeyInfo"], raw_data["updatedDataInfo"], raw_data["preUpdateDataInfo"] = self.explain_update_sql(raw_data.get("SQL"))
        return raw_data_list

if __name__ == '__main__':
    conditionInfo = MySqlChangeLogCondition()
    conditionInfo.page = 1
    conditionInfo.size = 1
    conditionInfo.ckTableName = "mysql_change_log"
    conditionInfo.changeTypeList = [1]
    conditionInfo.dbName = "yq_gyh"
    conditionInfo.tableName = "wx_order"
    conditionInfo.SQL = "320381199303300319"

    conn_setting = {'host': "cdh5", 'user': 'root', 'password': 'Engine1314enginE'}
    ck = SelectClickhouseData(conn_setting, sql_filter_condition=conditionInfo)
    print(ck.select_data_from_db())


