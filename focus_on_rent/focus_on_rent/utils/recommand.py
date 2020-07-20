#!/usr/bin/python
# -*- coding: UTF-8 -*-
from math import sqrt
import operator


# 1.构建用户-->物品的倒排
def load_data(files):
    data = {}
    for line in files:
        user, score, item = line.split(",")
        data.setdefault(user, {})
        data[user][item] = score
    print("----1.用户：物品的倒排----")
    print(data)
    return data


# 2.计算
# 2.1 构造物品-->物品的共现矩阵
# 2.2 计算物品与物品的相似矩阵
def similarity(data):
    # 2.1 构造物品：物品的共现矩阵
    N = {}  # 喜欢物品i的总人数
    C = {}  # 喜欢物品i也喜欢物品j的人数
    for user, item in data.items():
        for i, score in item.items():
            N.setdefault(i, 0)
            N[i] += 1
            C.setdefault(i, {})
            for j, scores in item.items():
                if j not in i:
                    C[i].setdefault(j, 0)
                    C[i][j] += 1

    print("---2.构造的共现矩阵---")
    print('N:', N)
    print('C', C)

    # 2.2 计算物品与物品的相似矩阵
    W = {}
    for i, item in C.items():
        W.setdefault(i, {})
        for j, item2 in item.items():
            W[i].setdefault(j, 0)
            W[i][j] = C[i][j]/sqrt(N[i]*N[j])
    print("---3.构造的相似矩阵---")
    print(W)
    return W


# 3.根据用户的历史记录，给用户推荐物品
def recommand_list(data, W, user, k=3, N=10, owner_list=None):
    rank = {}
    owner_list = [] if owner_list is None else owner_list
    for i, score in data[user].items():  # 获得用户user历史记录，如A用户的历史记录为{'a': '1', 'b': '1', 'd': '1'}
        for j, w in sorted(W[i].items(), key=operator.itemgetter(1), reverse=True)[0:k]:  # 获得与物品i相似的k个物品
            if j not in data[user].keys() and j not in owner_list:  # 该相似的物品不在用户user的记录里
                rank.setdefault(j, 0)
                rank[j] += float(score) * w

    print("---4.推荐----")
    print(sorted(rank.items(), key=operator.itemgetter(1), reverse=True)[0:N])
    return sorted(rank.items(), key=operator.itemgetter(1), reverse=True)[0:N]


if __name__ == '__main__':
    # 用户，兴趣度，物品
    # uid_score_bid = ['A,1,a', 'A,1,b', 'A,1,d', 'B,1,b', 'B,1,c', 'B,1,e', 'C,1,c', 'C,1,d', 'D,1,b', 'D,1,c', 'D,1,d','E,1,a', 'E,1,d']
    # data = load_data(uid_score_bid)  # 获得数据
    data = {'A': {'a': '1', 'b': '1', 'd': '1'}, 'B': {'b': '1', 'c': '1', 'e': '1'}, 'C': {'c': '1', 'd': '1'}, 'D': {'b': '1', 'c': '1', 'd': '1'}, 'E': {'a': '1', 'd': '1'}}
    W = similarity(data)  # 计算物品相似矩阵
    recommand = recommand_list(data, W, 'A', 3, 10)  # 推荐