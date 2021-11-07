'''Connecting to our database.

Connect to ubuntu-database via  terminal via zsh command:
    ssh -L 5432:localhost:5432 -N -f -l root <IP addy from digital ocean>

    ssh root@<IP addy>
    docker ps
We forwarded our cloud localhost to our localhost so we can now connect our database from our local machine.

If container doesn't already exists:
Run docker as a deployment mechanism with the following command on terminal:
    docker run --name=bookstore-db -e POSTGRES_USER=<db_user> -e POSTGRES_PASSWORD=<db_pass>
    -e POSTGRES_DB=bookstore -p 5432:5432 -d postgres:10

To see all open connections, open new tab in terminal and run:
    lsof -i tcp:5432
To kill connection:
    kill -9 <PID>


# execute query to load tables
# Use ':' before field to pull values from dict Value's keys
#query = "insert into books values(:isbn, :name, :author, :year)"
#values = [{"isbn": "isbn2", "name": "book2", "author": "author2", "year": 2018},
#          {"isbn": "isbn3", "name": "book3", "author": "author3", "year": 2017}]

# Try Fetch method
#fetch_cmd = "select * from books where isbn=:isbn"
#values = {"isbn": "isbn2"}

# Create loop to run any async function
#loop = asyncio.get_event_loop()
#loop.run_until_complete(fetch(fetch_cmd, True, values))
'''


import asyncio
from utils.db_object import db


async def execute(query, is_many, values=None):
    if is_many:
        await db.execute_many(query=query, values=values)
    else:
        await db.execute(query=query, values=values)


async def fetch(query, is_one, values=None):
    if is_one:
        result = await db.fetch_one(query=query, values=values)
        if result:
            out = dict(result)
        else:
            out = None
    else:
        result = await db.fetch_all(query=query, values=values)
        out = []
        if result:
            for row in result:
                out.append(dict(row))
        else:
            out = None

    return out
