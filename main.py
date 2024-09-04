from flask import Flask, request, render_template, flash, redirect
from apscheduler.schedulers.background import BackgroundScheduler
from flata import Flata, Query
from flata.storages import JSONStorage

from datetime import datetime
from dateutil.parser import parse as dtparse

import feedparser, requests, os

from dotenv import load_dotenv
load_dotenv()


db = Flata('db.json', storage=JSONStorage)
db.table('users')

app = Flask(__name__)
app.secret_key = os.environ['SECRET_KEY']
scheduler = BackgroundScheduler()

def readRSS():
    print('Reading RSS feed...')
    f = feedparser.parse('https://xkcd.com/rss.xml')
    lastimg = f.entries[0]['description'].split('"')[3]

    for user in db.table('users').all():
        print(user)
        last = dtparse(user['last'])
        last = last.replace(tzinfo=None)
        print(last)
        tm = datetime.strptime(f.entries[0]['published'], "%a, %d %b %Y %H:%M:%S %z")
        tm = tm.replace(tzinfo=None)
        print(tm)
        if last < tm:
            print('Alert user!')
            requests.post(f"https://{os.environ['TEXT_GATEWAY']}/text/{user['num']}", json={ "msg": f"{lastimg}" })
            db.table('users').update({'last': tm.isoformat()}, Query().num == user['num'])
    print('Done reading RSS feed!')

job = scheduler.add_job(readRSS, 'interval', minutes=1)

@app.get('/')
def hello():
    return 'pong'

@app.post('/addNum')
def addNum():
    db.table('users').insert({
        "num": request.json['num'],
        "last": "0001-01-01T00:00:00.000000"
    })
    flash('Number added successfully!')
    return redirect('/')

@app.post('/removeNum')
def removeNum():
    db.table('users').remove(Query().num == request.json['num'])
    flash('Number removed successfully!')
    return redirect('/')

scheduler.start()
app.run()