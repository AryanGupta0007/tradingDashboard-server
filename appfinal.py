import eventlet
eventlet.monkey_patch()
from flask import Flask, request, jsonify
from markupsafe import escape
from aryanfunctions import *
from flask_cors import CORS
import logging, time
from flask_socketio import SocketIO, emit
import time

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


def call_updateddata(data: list):
    global order_state, request_state
    try:
        print(data)
        updatedData, order_state = update_ltp(data, order_state, request_state)
        if (len(order_state) > 1):
            print(f"order_state {order_state}")
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


# @app.route('/index', methods=["GET"])
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

    global request_state, order_state, ltp_state
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
                
            
            # eventlet.sleep(3)  # Sleep for 3 seconds before next update

@socketio.on('disconnect')
def handle_disconnect():
    print(f"client {request.sid} disconnected")    

@socketio.on('updateRequestState')
def handle_update_request_state(data):
    """Update requestState dynamically when received from client"""
    global request_state, order_state
    print("jlsdjflasjfljaf", data)
    print("request update", data)
    request_state = data  # Merge updated fields
    print(f"Request State Updated: {request_state}")
    eventlet.spawn_n(handle_start_ltp, {'requestState': request_state, 'ltpState': [], 'orderState': order_state})
    # socketio.emit('startLtp', request_state)

if __name__ == '__main__':
    #     app.run(debug=True, port=5001)
    socketio.run(app, debug=True, port=5001)  