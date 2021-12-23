from siyuan_synonym import generate
from siyuanhelper import helper
import asyncio
import sys
import pyclip


# pyclip is required for this script, use `pip install pyclip` to install.


async def main(id: str):
    blocks = await helper.query_sql(
        "select root_id from refs where def_block_id='{}'".format(id))
    blocks = [x["root_id"] for x in blocks]
    roots, root_list, title = (await generate(blocks))
    text = ""
    for x in roots:
        for y in root_list[x]:
            text = text + "(({} '{}'))\n".format(y,
                                                 title[y].replace('\'', r'&apos;'))
        text = text + '\n\n'
    pyclip.copy(text)


if len(sys.argv) == 2:
    id = sys.argv[1]
    id = id.replace("((", "").replace("))", "").replace("siyuan://blocks/", "")
    id = id.split(" ")[0]
    asyncio.run(main(id))
