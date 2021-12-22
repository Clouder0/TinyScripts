from collections import defaultdict
from siyuanhelper import helper
import asyncio
import re


pat = re.compile("同义词：(.+)")
root_list = defaultdict(list)
tasklist = []
count = {}
visited = set()


async def get_count(id: str):
    count[id] = 0
    try:
        temp = await helper.query_sql("select count() as c \
            from refs where def_block_id = '{}'".format(id))
        count[id] = temp[0]["c"]
    except Exception:
        return


async def dig(id: str, root: str):
    if id in visited:
        return
    visited.add(id)
    root_list[root].append(id)
    tasklist.append(asyncio.create_task(get_count(id)))
    try:
        # Direct Link
        property = await helper.query_sql(
            "select markdown from blocks where id = (select block_id from attributes where root_id='{}' \
                and name='custom-type' and value='property')".format(id))
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
                        tasklist.append(asyncio.create_task(dig(newstr, root)))
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
                tasklist.append(asyncio.create_task(dig(newid, root)))
    except Exception:
        print("Exception occurred when handling {}".format(id))
        return


async def generate(starts: list):
    for x in starts:
        tasklist.append(asyncio.create_task(dig(x, x)))
    await asyncio.gather(*tasklist)
    for x in root_list.keys():
        root_list[x].sort(key=count.get, reverse=True)
        print(root_list[x])
        for y in root_list[x]:
            print(await helper.query_sql("select content from blocks where id = '{}'".format(y)))
