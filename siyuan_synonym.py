from collections import defaultdict
from siyuanhelper import helper
import asyncio
import re


pat = re.compile("同义词：(.+)")
tasklist = []
fa = {}
count = {}
title = {}
visited = set()
root_list = defaultdict(list)


def find(id: str):
    if id not in fa:
        fa[id] = id
        return id
    if fa[id] == id:
        return id
    fa[id] = find(fa[id])
    return fa[id]


def unite(ida: str, idb: str):
    find(ida)
    find(idb)
    fa[fa[ida]] = fa[idb]


async def get_count_title(id: str):
    count[id] = 0
    try:
        temp = await helper.query_sql("select count() as c \
            from refs where def_block_id = '{}'".format(id))
        count[id] = temp[0]["c"]
        temp = await helper.query_sql("select content from blocks where id = '{}'".format(id))
        title[id] = temp[0]["content"]
    except Exception:
        print("Exception occurred when getting the count and title of {}".format(id))
        return


async def dig(id: str):
    if id in visited:
        return
    find(id)
    visited.add(id)
    await get_count_title(id)
    try:
        # Direct Link
        property = await helper.query_sql(
            "select markdown from blocks where id = (select block_id from attributes where root_id='{}' \
                and name='custom-type' and value='property')".format(id))
        queue = []
        matches = pat.finditer(property[0]["markdown"])
        for x in matches:
            str = x.group(1)
            newid = list()
            bracket = 0
            skip = 0
            for y in str:
                if y == '(':
                    bracket = bracket + 1
                elif y == ')':
                    bracket = bracket - 1
                    if bracket == 0:
                        newstr = (''.join(newid)).strip()
                        unite(id, newstr)
                        queue.append(asyncio.create_task(dig(newstr)))
                        newid.clear()
                elif y == '\"' or y == '\'':  # avoid anchor text
                    skip = skip ^ 1
                elif skip == 0:
                    newid.append(y)
        # Back Link
        backlinks = await helper.query_sql("select content,root_id from blocks where id in \
            (select parent_id from blocks where id in \
            (select block_id from refs where def_block_id = '{}'))".format(id))
        for x in backlinks:
            if "同义词" in x["content"]:
                newid = x["root_id"]
                unite(id, newid)
                queue.append(asyncio.create_task(dig(newid)))
        await asyncio.gather(*queue)
    except Exception:
        print("Exception occurred when handling {}".format(id))


async def generate(starts: list):
    for x in starts:
        tasklist.append(asyncio.create_task(dig(x)))
    await asyncio.gather(*tasklist)
    for id in fa.keys():
        root_list[find(id)].append(id)
    roots = list(root_list.keys())
    for x in roots:
        root_list[x].sort(key=count.get, reverse=True)
    for x in roots:
        if len(root_list[x]) > 1:
            for y in range(1, len(root_list[x])):
                count[root_list[x][0]] = count[root_list[x][0]] + \
                    count[root_list[x][y]]
    roots.sort(key=sort_key, reverse=True)
    return roots, root_list, title


def sort_key(root_id):
    return count[root_list[root_id][0]]
