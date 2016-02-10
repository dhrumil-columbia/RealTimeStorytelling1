#!/usr/bin/env python

# Set this variable to "threading", "eventlet" or "gevent" to test the
# different async modes, or leave it set to None for the application to choose
# the best option based on available packages.
async_mode = None

if async_mode is None:
    try:
        import eventlet
        async_mode = 'eventlet'
    except ImportError:
        pass

    if async_mode is None:
        try:
            from gevent import monkey
            async_mode = 'gevent'
        except ImportError:
            pass

    if async_mode is None:
        async_mode = 'threading'

    print('async_mode is ' + async_mode)

# monkey patching is necessary because this application uses a background
# thread
if async_mode == 'eventlet':
    import eventlet
    eventlet.monkey_patch()
elif async_mode == 'gevent':
    from gevent import monkey
    monkey.patch_all()

import time
from random import random
from datetime import datetime
from google.transit import gtfs_realtime_pb2
import urllib
from threading import Thread
from flask import Flask, render_template, session, request
from flask_socketio import SocketIO, emit, join_room, leave_room, \
    close_room, rooms, disconnect

#We initialize the flask io server here:
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
thread = None

#this is the background thread function that polls the MTA api every two seconds
#it emits a message to the client page if it receives an alert from mta
print('Train Delayed Alerts')
def background_thread():
    count = 0
    i=1
    k=1
    y=[]
    while True:
        try:
            print "While",i
            feed = gtfs_realtime_pb2.FeedMessage()
            #We poll the MTA API here
            response = urllib.urlopen('http://datamine.mta.info/mta_esi.php?key=<your key>&feed_id=1')
            feed.ParseFromString(response.read())
            for entity in feed.entity:
                j=1
                if entity.alert.informed_entity:
                    #If an alert exists in the entity, we iterate over it
                    for e in entity.alert.informed_entity:
                        x=e.trip.trip_id
                        r=e.trip.route_id
                        print 'Trip id: '+x+' Route id: '+r
                        count= round(random()*10,3)
                        t=str(datetime.now())
                        socketio.emit('my response',
                                      {'data': 'Trip id', 'count': count, 'tid':x, 'rid':r, 'time':t},
                                      namespace='/test')
                        k=k+1
                        y.append(x)
            time.sleep(2)
            i=i+1
        except IOError:
            continue
        except ValueError:
            continue
        except TypeError:
            continue
        except UnicodeDecodeError:
            continue
        except Exception:
            continue
    
#We start the thread here when a client connects to the server        
@app.route('/')
def index():
    global thread
    if thread is None:
        thread = Thread(target=background_thread)
        thread.daemon = True
        thread.start()
    return render_template('index.html')

#this starts the http server when app.py file is run
if __name__ == '__main__':
    socketio.run(app, debug=True)
