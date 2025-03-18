import eventlet
eventlet.monkey_patch()
from flask import Flask, request, jsonify
from markupsafe import escape
from configaryan1812 import *
from aryanfunctions import *
from flask_cors import CORS
import logging, time
from flask_socketio import SocketIO, emit
import time
import json
import collections
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
create_log_file("ARYAN")



app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///example.db'  # Use your database URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Avoid overhead

db = SQLAlchemy(app)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String, unique=True)
    entry = db.Column(db.String, nullable=True)
    target = db.Column(db.String, nullable=True)
    sl = db.Column(db.String, nullable=True)
    type = db.Column(db.String, default="BUY")
    qty = db.Column(db.String, nullable=True)
    entryId = db.Column(db.String, nullable=True)
    exitId = db.Column(db.String, nullable=True)
    entryPrice = db.Column(db.String, nullable=True)
    exitPrice = db.Column(db.String, nullable=True)
    entryStatus = db.Column(db.String, nullable=True)
    exitStatus = db.Column(db.String, nullable=True)
    def __repr__(self):
        return f"{self.id} symbol: {self.symbol} entry: {self.entry} target: {self.target} sl: {self.sl}, type: {self.type} qty: {self.qty}" 


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(80), unique=True, nullable=False)
    
    def __repr__(self):
        return f'<Message {self.message}>'
    
CORS(app, resources={r"/*": {"origins": "*"}})  # Allow CORS for React frontend
connectFeed(SMART_WEB)
socketio = SocketIO(app, async_mode="eventlet", cors_allowed_origins="*")
logging.basicConfig(level=logging.INFO)

with app.app_context():
# db.drop_all()   # Drops all existing tables
    db.create_all()
    
request_state = []
order_state = []
ltp_state = []
message_state = []
thread_lock = threading.Lock()


@app.route("/add_message", methods=["POST", "OPTIONS"])
def add_message():
    if request.method == "OPTIONS":
        # Preflight request
        response = jsonify({"message": "Preflight request"})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
        return response
    print("Request Headers:", request.headers)
    print("Request Data:", request.data)
    
    data = request.json
    print("datat ", data)
    message = data.get("message")
    new_message = Message(message=message)
    db.session.add(new_message)  # Add to session
    db.session.commit()
    print("Received message:", message)

    # Simulating database save
    return jsonify({"message": f"Message '{new_message}' added!"}), 200

def get_all_orders():
    try:
        orders = Order.query.all()
        return orders
    except Exception as error:
        return []
        
@app.route("/messages", methods=["GET", "OPTIONS"])
def get_messages():
    
    messages = Message.query.all()
    # print(f"messages {messages}")    
    if (messages == []):
        return jsonify({"messages": []}), 200 

    messages_list = [m.message for m in messages]
    # print(messages_list)
    return jsonify({"messages": messages_list}), 200


def call_updateddata(data: list):
    global order_state, request_state, message_state
    try:
        try:
            # print(data, order_state, request_state, message_state, type(data))
            updatedData, order_state, messages = update_ltp(request_state, order_state, request_state, message_state)
        except Exception as error:
            print(f'116: {error}')
        # print(f"messages {messages}")
        socketio.emit('orderExecuted', order_state)
        if len(messages) > 0:
            for message in messages: 
                # print(f"message {message}")       
                new_message = Message(message=message)
                db.session.add(new_message)
                db.session.commit()
                # print(f"message {message} added!")
            

    except Exception as e:

        # return data
        print("29:", e)
        return jsonify({"error": str(e)})
    # print("32:",updatedData)
    # print(data)
    return updatedData

def subscribe_symbol(sym):
    token_list = []
    securityid = get_equitytoken(sym)
    token_list.append(securityid)
    subscribeList = [{"exchangeType": 1, "tokens": token_list}]
    subscribeSymbol(subscribeList, SMART_WEB)
    return securityid

@app.route("/getSecurityKey", methods=["POST"])
def fetchSecurityKey():
    data = request.json
    global token_list
    token_list = []

    # print("recieved subscribing data ", data)

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
    # print(f'ltpPostdata: {data}')
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

def merge_orders(request_state, order_state):
    merged_orders = {}

    for req in request_state:
        for symbol, req_data in req.items():
            merged_orders[symbol] = {**req_data}  # Copy request data

    for ord in order_state:
        for symbol, ord_data in ord.items():
            if symbol in merged_orders:
                merged_orders[symbol].update(ord_data)  # Merge order data
            else:
                merged_orders[symbol] = ord_data  # If no request, just add order

    # Convert merged dictionary into a list of dicts
    return [{**{'symbol': symbol}, **data} for symbol, data in merged_orders.items()]

@socketio.on('connect')
def handle_connect():
    from flask import request  # Import request here
    print(f"request: {request}")
    with thread_lock:
        global order_state
        print(f"client {request.sid} connected")
        orders = get_all_orders()
        print(f'existing orders: {orders}' )
        if orders != []:
            # print(f'existing orders: {orders}')
            for order in orders:
                print(order)
                securityId = subscribe_symbol(order.symbol)
                request = {
                    order.symbol: {
                        'id': order.id,
                        'entry': order.entry,
                        'target': order.target,
                        'sl': order.sl,
                        'orderType': order.type,
                        'qty': order.qty,
                        'securityId': securityId
                        }
                    }    
                newOrder = {
                    order.symbol: {
                        'id': order.id,
                        'securityId': securityId,
                        'entryId': order.entryId,
                        'exitOrderID': order.exitId,
                        'entryPrice': order.entryPrice,
                        'exitPrice': order.exitPrice,
                        'entryStatus': order.entryStatus,
                        'exitStatus': order.exitStatus
                    }
                } 
                print(f'order: {newOrder}, request: {request}')
                symbolsRequestState = [str(list(d.keys())[0]) for d in request_state]  # Extracts all keys from the first dictionary
                symbolsOrderState = [str(list(d.keys())[0]) for d in order_state]  # Extracts all keys from the first dictionary
                if order.symbol not in symbolsOrderState:
                    order_state.append(newOrder)
                if order.symbol not in symbolsRequestState:
                    print('here')
                    request_state.append(request)
                print(order_state)
        emit('message', {'data': 'connnected to client', 'orderState': order_state, 'requestState': request_state})



@socketio.on('startLtp')
def handle_start_ltp(data):
    # print(":fhslfhas")

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

    # print("LTP Monitoring Started:", ltp_state)
    print(f"current request state: {request_state}")
    print(f"current order state: {order_state}") 
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
            # print(f"ltpState {ltp_state}")
            if ltp_state:
                # Emit updated LTP state
                socketio.emit('ltpUpdate', {
                    'ltpState': ltp_state
                })

        
@socketio.on('disconnect')
def handle_disconnect():
    
    global request_state, order_state
    objs = merge_orders(request_state=request_state, order_state=order_state)
    existing_orders = {o.symbol: o for o in Order.query.all()}  # Fetch all orders
    print(f'objs {objs}')
    print(f'existing_orders: {existing_orders}')
    # for symbol in existing_orders:
        # Extract symbols from objs
    symbols_from_objs = {order["symbol"] for order in objs}
    # Extract symbols from existing_orders
    symbols_from_existing_orders = set(existing_orders.keys())
    # Find symbols present in existing_orders but missing in objs
    symbols_to_remove = symbols_from_existing_orders - symbols_from_objs
    print(f'symbols to remove: {symbols_to_remove}')
    # Handle missing symbols (e.g., delete from DB)
    for symbol in symbols_to_remove:
        Order.query.filter(Order.symbol == symbol).delete()  # Delete all "BUY" orders
        db.session.commit()
        
    for order_data in objs:
        print(f'order_data {order_data}')
        symbol = order_data["symbol"]

        if symbol in existing_orders:  # Update existing order
            
            order = existing_orders[symbol]
            order.entry = order_data.get("entry", order.entry)
            order.target = order_data.get("target", order.target)
            order.sl = order_data.get("sl", order.sl)
            order.type = order_data.get("orderType", order.type)
            order.qty = order_data.get("qty", order.qty)
            order.entryId = order_data.get("entryId", order.entryId)
            order.exitId = order_data.get("exitOrderID", order.exitId)
            order.entryPrice = order_data.get("entryPrice", order.entryPrice)
            order.exitPrice = order_data.get("exitPrice", order.exitPrice)
            order.entryStatus = order_data.get("entryStatus", order.entryStatus)
            order.exitStatus = order_data.get("exitStatus", order.exitStatus)
            print(f'order {order}')
        else:  # Create new order   
            
            order = Order(
                symbol=symbol,
                entry=order_data.get("entry"),
                target=order_data.get("target"),
                sl=order_data.get("sl"),
                type=order_data.get("orderType"),
                qty=order_data.get("qty"),
                entryId=order_data.get("entryId"),
                exitId=order_data.get("exitOrderID"),
                entryPrice=order_data.get("entryPrice"),
                exitPrice=order_data.get("exitPrice"),
                entryStatus=order_data.get("entryStatus"),
                exitStatus=order_data.get("exitStatus"),
            )
            print(f'order {order}')
            db.session.add(order)  # Add to session

    db.session.commit()  # Commit all changes
    request_state = []
    order_state = []

    print(f"client {request.sid} disconnected")    

def update_order_and_ltp_state():
    global request_state, order_state, ltp_state
    print(f'updating ltp and order state, {order_state}, {request_state}')
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
    # print(f"updated ltpState {ltp_state} and orderState {order_state}")


@socketio.on('updateRequestState')
def handle_update_request_state(data):
    """Update requestState dynamically when received from client"""
    global request_state, order_state, ltp_state
    print("jlsdjflasjfljaf", data)
    print("request update", data)
    request_state = data  # Merge updated fields
    update_order_and_ltp_state()
    # print(f"Request State Updated: {request_state}")
    eventlet.spawn_n(handle_start_ltp, {'requestState': request_state, 'ltpState': [], 'orderState': order_state})
    # socketio.emit('startLtp', request_state)

@socketio.on('updateMessageState')
def handle_update_message_state(data):
    """Update requestState dynamically when received from client"""
    global message_state
    # print("jlsdjflasjfljaf", data)
    # print("request update", data)
    message_state = data  # Merge updated fields

    # print(f"message State Updated: {message_state}")
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
    socketio.run(app, debug=True, port=5001)
    