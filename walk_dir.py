import os
import csv
fcd = open("data_list_cn_nd.csv", "r")
file_key_map = {}
for line in fcd:
    target_key, file_name = line.strip().split(",")
    file_key_map[file_name] = target_key
nd_line_cnt = len(file_key_map)
print(nd_line_cnt)

fc = open("data_list_cn.csv", "w")
writer = csv.writer(fc)
head_line = ["type", "path"]
lines = []
lines.append(head_line)

data_dir = "data/ace_2005_td_v7/data/Chinese"
sub_dir = ["bn", "nw", "wl"]
hit = 0
miss = 0
for sub in sub_dir:
    directory = os.path.join(data_dir, sub, "adj")
    for dir, subdir, files in os.walk(directory):
        for file in files:
            prefix = ".".join(file.split(".")[:-1])
            suffix = file.split(".")[-1]
            if suffix == 'sgm':
                if prefix in file_key_map:
                    hit += 1
                    target_key = file_key_map[prefix]
                    del file_key_map[prefix]
                else:
                    target_key = "dev"
                    miss += 1
                lines.append([target_key, os.path.join(sub, "adj", prefix)])

writer.writerows(lines)
line_cnt = len(lines)
print(file_key_map)
print("目标数据{}条，总计找到数据{}条, 其中命中数据{}条，额外数据{}条".format(nd_line_cnt, line_cnt, hit, miss))
