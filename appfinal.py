import eventlet
eventlet.monkey_patch()
from flask import Flask, request, jsonify
from markupsafe import escape
from aryanfunctions import *
from flask_cors import CORS
import logging, time
from flask_socketio import SocketIO, emit
import time
import json
import collections

app = Flask(__name__)
create_log_file("ARYAN")

app = Flask(__name__)
CORS(app)  # Allow CORS for React frontend
connectFeed(SMART_WEB)
socketio = SocketIO(app, async_mode="eventlet", cors_allowed_origins="*")
logging.basicConfig(level=logging.INFO)
request_state = []
order_state = []
ltp_state = []


def are_lists_equal_as_sets(list1, list2):
    return collections.Counter(map(json.dumps, list1)) == collections.Counter(map(json.dumps, list2))


def call_updateddata(data: list):
    global order_state, request_state, message_state
    try:
        print(data)
        prevOrderState = order_state
        updatedData, order_state, message_state = update_ltp(data, order_state, request_state, message_state)
        order_placed = are_lists_equal_as_sets(prevOrderState, order_state)
        if order_placed:
            socketio.emit('messageUpdated', message_state)
        print(f"order_state after update ltp {order_state}")
        socketio.emit('orderExecuted', order_state)
            

    except Exception as e:

        # return data
        print("29:", e)
        return jsonify({"error": str(e)})
    # print("32:",updatedData)
    # print(data)
    return updatedData


@app.route("/getSecurityKey", methods=["POST"])
def fetchSecurityKey():
    data = request.json
    global token_list
    token_list = []

    print("recieved subscribing data ", data)

    for sym in data.keys():
        securityid = get_equitytoken(sym)

        data[sym]['securityId'] = securityid
        token_list.append(securityid)

    subscribeList = [{"exchangeType": 1, "tokens": token_list}]
    subscribeSymbol(subscribeList, SMART_WEB)
    time.sleep(2)
    return data


def fetch_ltp_post(data):
    if data == []:
        return data
    
    final_updated_data = call_updateddata(data)
    return final_updated_data

def is_strong_alnum(s):
    return any(c.isalpha() for c in s) and any(c.isdigit() for c in s)


@app.route('/symbols', methods=["GET"])
def get_symbols():
    df = pd.read_csv("ANGELFULL.csv")
    symbols = list(df['name'])
    for s in symbols:
        if is_strong_alnum(str(s)) == True:
            print(s)
            symbols.remove(s)
        else:
            continue
        
    # print(symbols)
    return list(symbols)     


@app.route('/index', methods=["GET"])
def get_index_values():
    global token

    response = SMART_API_OBJ.getMarketData(mode="FULL", exchangeTokens={"NSE": ["26000", "26009", "26037", "26074"],
                                                                        "BSE": ["99919000"]})
    response = response['data']['fetched']
    indexes = {}
    for i in response:
        index_data = {
            i['tradingSymbol']: {"securityId": i["symbolToken"], 'previousDayClose': i['close'], "currentValue": "",
                                 "difference": "", "percentageDifference": ""}}
        indexes.update(index_data)

    for x in indexes:
        indexes[x]['currentValue'] = token_dict[indexes[x]['securityId']]
        indexes[x]['currentValue'] = float(indexes[x]['currentValue'])

    for key, value in indexes.items():
        previous_close = value['previousDayClose']
        current_value = value['currentValue']
        value['difference'] = current_value - previous_close
        value['difference'] = round(value['difference'], 2)
        value['percentageDifference'] = value['difference'] / value['previousDayClose'] * 100
        value['percentageDifference'] = round(value['percentageDifference'], 2)

    # print(indexes)
    return indexes


@socketio.on('connect')
def handle_connect():
    print(f"client {request.sid} connected")
    emit('message', {'data': 'connnected to client'})

@socketio.on('startLtp')
def handle_start_ltp(data):
    print(":fhslfhas")

    global request_state, order_state, ltp_state, message_state
    if not data.get('requestState'):
        return

    if ltp_state == []:
        for item in request_state:
            symbol = list(item.keys())[0]
    
            ltp = {
                "id": item[symbol]["id"],
                "ltp": "",
                "securityId": item[symbol]["securityId"]
            }
            ltp_state.append({symbol: ltp})

    print("LTP Monitoring Started:", ltp_state)

    
    request_state = data['requestState']
    eventlet.spawn_n(emit_ltp_updates)  # Use eventlet.spawn_n to prevent blocking
    # eventlet.spawn_n(emit_index_updates)
  # Start background LTP updates




def emit_ltp_updates():
    """Continuously fetch and emit LTP updates"""
    with app.app_context():
        while True:
            global ltp_state, order_state, request_state
            time.sleep(1)
            ltp_state = fetch_ltp_post(request_state)
            print(f"ltpState {ltp_state}")
            if ltp_state:
                # Emit updated LTP state
                socketio.emit('ltpUpdate', {
                    'ltpState': ltp_state
                })

        
@socketio.on('disconnect')
def handle_disconnect():
    print(f"client {request.sid} disconnected")    

def update_order_and_ltp_state(request_state, ltp_state, order_state):
    request_state_symbols = []
    for e in request_state:
        symbol = list(e.keys())[0]
        request_state_symbols.append(symbol)

    for e in order_state:
        symbol = list(e.keys())[0]
        if symbol not in request_state_symbols:
            order_state.remove(e)

    for e in ltp_state:
        symbol = list(e.keys())[0]
        if symbol not in request_state_symbols:
            ltp_state.remove(e)
    print(f"updated ltpState {ltp_state} and orderState {order_state}")
    return order_state, ltp_state


@socketio.on('updateRequestState')
def handle_update_request_state(data):
    """Update requestState dynamically when received from client"""
    global request_state, order_state, ltp_state
    print("jlsdjflasjfljaf", data)
    print("request update", data)
    request_state = data  # Merge updated fields

    order_state, ltp_state = update_order_and_ltp_state(request_state, ltp_state, order_state)
    print(f"Request State Updated: {request_state}")
    eventlet.spawn_n(handle_start_ltp, {'requestState': request_state, 'ltpState': [], 'orderState': order_state})
    # socketio.emit('startLtp', request_state)

@socketio.on('updateMessageState')
def handle_update_message_state(data):
    """Update requestState dynamically when received from client"""
    global message_state
    print("jlsdjflasjfljaf", data)
    print("request update", data)
    message_state = data  # Merge updated fields

    print(f"message State Updated: {message_state}")
    eventlet.spawn_n(handle_start_ltp, {'requestState': request_state, 'ltpState': [], 'orderState': order_state})
    # socketio.emit('startLtp', request_state)

# @socketio.on('deleteSymbolFromRequestState')
# def handleSymbolDelete(data):
#     global request_state, ltp_state, order_state
#     symbol = list(data.keys())[0]
#     for e in request_state:
#         if (list(e.keys())[0]) == symbol:
#             request_state.pop(e)
#     for e in order_state:
#         if (list(e.keys())[0]) == symbol:
#             request_state.pop(e)
#     for e in ltp_state:
#         if (list(e.keys())[0]) == symbol:
#             request_state.pop(e)
#     print(f"Request State Updated: {request_state} {order_state} {ltp_state}")
#     eventlet.spawn_n(handle_start_ltp, {'requestState': request_state, 'ltpState': [], 'orderState': order_state})
            

if __name__ == '__main__':
    #     app.run(debug=True, port=5001)
    socketio.run(app, debug=True, port=5001)  