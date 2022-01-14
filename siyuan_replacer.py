from datetime import datetime
from siyuanhelper import helper
import sys
import asyncio


count = 0


async def handle(id, markdown, origin, target):
    global count
    try:
        await helper.updateBlock(id, "markdown", markdown.replace(origin, target))
        count = count + 1
    except Exception:
        print("An Exception Occurred when Handling {}".format(id))


async def main(origin, target):
    global count
    blocks = await helper.query_sql(
        "select id,markdown from blocks where content like '%{}%' and type='p'".format(origin))
    print(blocks)
    if input("Do you want to continue?(y/n)") != "y":
        return
    backup = []
    tasks = []
    for x in blocks:
        id = x["id"]
        markdown = x["markdown"]
        backup.append((id, markdown))
        tasks.append(handle(id, markdown, origin, target))
    await asyncio.gather(*tasks)
    print("Successfully replaced {} blocks.".format(count))
    f = open("replace{}.bak".format(
        datetime.now().strftime(r"%y%m%d%M%S")), "w+")
    backup_text = ""
    for x in backup:
        backup_text = backup_text + "{}:::{}\n".format(x[0], x[1])
    f.write(backup_text)
    f.close()

if len(sys.argv) < 3:
    print("No enought args! run with siyuan_replacer origin_text new_text")
else:
    print(sys.argv)
    asyncio.run(main(sys.argv[1], sys.argv[2]))
