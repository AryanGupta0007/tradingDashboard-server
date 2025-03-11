from SmartApi import SmartConnect         
from SmartApi.smartWebSocketV2 import SmartWebSocketV2
from configaryan1812 import *
import logging,threading,time,sys
import pandas as pd
from datetime import datetime
import os

def login():
    """This fx enables user to login and create two objects ie smartApi and sws(for websocket)"""

    smartApi =SmartConnect(api_key=API_KEY)      #smartApi is the object created
    data = smartApi.generateSession(USERNAME,PIN,TOKEN)
    s=data['status']
    if s==True:
        #print(data)
        name=data['data']['name']
        # print("LOGIN SUCCESSFUL FOR",name)                      #PRINT LOGIN SUCCESSFUL MESSAGE
        logging.info(f"LOGIN SUCCESSFUL FOR {name}")
        cash=smartApi.rmsLimit()['data'] 
        cash=cash['availablecash']                   
        # print("AVAILABLE CASH LIMIT IS",cash)                   #PRINT AVAILABLE CASH LIMIT
        logging.info(f"AVAILABLE CASH LIMIT IS {cash}")
    else:
        print("LOGIN UNSUCCESSFUL")
        print("INVALID CREDENTIALS")
        logging.info("LOGIN UNSUCCESSFUL")

    authToken = data['data']['jwtToken']
    refreshToken = data['data']['refreshToken']
    feed_Token = smartApi.getfeedToken()                     # fetch the feedtoken
    res = smartApi.getProfile(refreshToken)
    #logging.info(f'{res["data"]["products"]}')
    logging.info(f'{res["data"]["exchanges"]}')             #exchanged subscribed
    sws = SmartWebSocketV2(authToken, API_KEY, USERNAME, feed_Token ,max_retry_attempt=5) 
    return smartApi,sws

def get_equitytoken(symname:str,exch="NSE"):
    
    if exch=="NSE":
        symname=symname+"-"+"EQ"
    # print(os.getcwd())
    df=pd.read_csv("ANGELFULL.csv", low_memory=False)
    df=df[(df['exch_seg']==exch)&(df['symbol']==symname)]
    df=df[['token','symbol']]
    
    if df.empty!=True:
    
        token=df.iloc[0,0]
        return token

def create_log_file(a:str):
    t=datetime.now()
    t1=t.strftime("%d-%b-%Y %H:%M:%S")
    t2=t.strftime("%d%b%Y %H%M%S")
    filename=a + t2 + ".txt"                                   #logfile name found using tradingdate1
    logging.basicConfig(filename=filename,level=logging.INFO,format="%(asctime)s-%(message)s",datefmt="%d-%b-%Y %H:%M:%S")

def on_data(wsapp,message):
    # global token
    try:
        #print("{}".format(message))
        token=message['token']
        #time_stamp=message['exchange_timestamp']       
        token_ltp=message['last_traded_price']/100
        token_dict[token]=token_ltp
        # print(token_dict)
                       
        data="{}".format(message)
        #logging.info("Ticks:{}".format(message))
        return data
    except Exception as e:
        print("70:",e)
        # logging.info(e)
        
def on_error(wsapp,error):
    print("error")
    logging.info(f"---------Connection Error {error}-----------")

def on_close(wsapp):
    print("Connection Closed")
    logging.info(f"---------Connection closed-----------")

def subscribeSymbol(token_list,sws):
    logging.info(f'Subscribed to new tokens -------  {token_list}')
    sws.subscribe(CORRELATION_ID, FEED_MODE, token_list)

def connectFeed(sws,tokeList =None):

    def on_open(wsapp):
        print("on open")
        token_list=[{"exchangeType":1,"tokens":["26000","26009","26037","26074","14742"]},{"exchangeType":3,"tokens":["99919000","99919012"]}]

        if tokeList : token_list.append(tokeList)
        logging.info(f"on open,TOKEN LIST:{token_list}")
        sws.subscribe(CORRELATION_ID, FEED_MODE,token_list)

    sws.on_open=on_open
    sws.on_data=on_data
    sws.on_error=on_error
    sws.on_close=on_close
    threading.Thread(target=sws.connect,daemon=True).start()

# def place_order_equity_dict(brokerobject,response_dict,sym,exc="NSE"):         
       
        # token=response_dict[sym]["securityId"]
        # trans_type=response_dict[sym]['orderType']
        # ord_price=response_dict[sym]['entry']
        # qt=response_dict[sym]["qty"]
        # if qt!="":
        #     qt=int(qt)
        # else:
        #     print("Qty cant  be empty")
        # print("112:",token,trans_type,ord_price,qt)
        # updated_sym=sym+"-EQ"
        # orderparams = {"variety": "NORMAL","tradingsymbol": updated_sym,"symboltoken": token,"transactiontype": trans_type,
        #             "exchange": exc,"ordertype": "LIMIT","producttype": "CARRYFORWARD","duration": "DAY","price": ord_price,
        #             "squareoff": "0","stoploss": "0","quantity": qt}

        # logging.info(f"ORDER PARAMETERS: {orderparams}")
        # orderid = brokerobject.placeOrder(orderparams)
        # # print("119:",orderid)
        # if orderid!=None or orderid!="":
        #     # print(sym,":",orderid)
        #     response_dict[sym]["EntryId"]=orderid
        #     logging.info(f"ORDER PLACED AT: {orderid}")
        #     order_book_complete=SMART_API_OBJ.orderBook()
        #     # print("128:",response_dict[sym]['tradeCount'])
        #     if order_book_complete['message']=="SUCCESS" and order_book_complete['data']!="":
        #         order_book_complete_df=pd.DataFrame(order_book_complete['data'])
        #         order_book_complete_df=order_book_complete_df[["symboltoken","orderid","status","orderstatus"]]
        #         order_status_df=order_book_complete_df[order_book_complete_df["orderid"]==orderid]
        #         order_status=order_status_df["orderstatus"].iloc[0]
        #         response_dict[sym]['entryStatus']=order_status
        #         response_dict[sym]['tradeCount']=response_dict[sym]['tradeCount']+1
        #         # print(sym,":",orderid,":",order_status)

        #     print("138:",response_dict)
        #     return response_dict
        # else:
        #     print(f"Order placement failed: {orderid}")

# def fetchSecurityKey(response):
#     global token_list
#     token_list=[]
#     data=response
# #     data = request.json
# #     print("recieved subscribing data ", data)
    
#     for id in data.keys():
#         sym = 
#         securityid=get_equitytoken(sym)

#         data[sym]['securityId'] = securityid
#         token_list.append(securityid)
#     subscribeList=[{"exchangeType":1,"tokens":token_list}]
#     subscribeSymbol(subscribeList,SMART_WEB)
#     time.sleep(2)

#     return data
tradeCount = 0
def check_entry_occured_or_not(sym, order_state, request_state):
    try:
        if order_state == []:
            return "PENDING" 
        for e in order_state:
            # print("1234", sym)
            if list(e.keys())[0] == sym:
                return "PLACED"
            return "PENDING"
    except Exception as e:
        print("168", e)
        
        

def update_ltp(response:list, order_state, request_state): 
    global token_list
    global tradeCount
    # print("hehehhe", response)
    for sym_dict in response:
        print("sub dict", sym_dict)
        sym=list(sym_dict.keys())[0]
        token=sym_dict[sym]['securityId']
        entry = sym_dict[sym]['entry']
        order_type = sym_dict[sym]['orderType']
        target = sym_dict[sym]['target']
        qty = sym_dict[sym]['qty']
        sl = sym_dict[sym]['sl']
        
        
        if token not in token_dict:
            token_list.append(token)
            subscribeList=[{"exchangeType":1,"tokens":token_list}]
            subscribeSymbol(subscribeList,SMART_WEB)
            # time.sleep(5)
        try:
            sym_ltp=token_dict[token]
            sym_dict[sym]['ltp']=sym_ltp
            sym_ltp = int(sym_ltp)
            # print(f"response {sym_dict}")
            if not (entry == "" or target == "" or qty == "" or sl == ""):   
                # print("entered in the order area") 
                occured_or_not = check_entry_occured_or_not(sym, order_state, request_state)
                print(occured_or_not)
                if occured_or_not == "PENDING":
                    print(f"type: {order_type} entry: {int(entry)} ltp: {(sym_ltp)}")
                    if (order_type == "BUY" and int(entry) > int(sym_ltp)) or (order_type == "SELL" and int(entry) < int(sym_ltp)):
                        print("Final destination")
                        tradeCount += 1
                        if (tradeCount % 2 == 1):
                            order_state = place_order_equity_dict(SMART_API_OBJ, token, sym, order_type, "ENTRY", sym_ltp, qty, order_state=order_state)  
                elif occured_or_not == "PLACED":
                    if (order_type == "BUY" and sym_ltp > int(target)) or (order_type == "BUY" and sym_ltp < int(sl)):
                        order_state =place_order_equity_dict(SMART_API_OBJ, token, sym, order_type="SELL", entry_or_exit="EXIT", ltp=sym_ltp, qty=qty, order_state=order_state)
                    
                    if (order_type == "SELL" and sym_ltp < int(target)) or (order_type == "SELL" and sym_ltp > int(sl)):
                        order_state = place_order_equity_dict(SMART_API_OBJ, token, sym, order_type="BUY", entry_or_exit="EXIT", ltp=sym_ltp, qty=qty, order_state=order_state)
        except Exception as error:
            print("error", error)           
    return response, order_state


# def place_order(data):
    
#     global request_state, order_state, ltp_state    
#     print("75:",data)
#     for i in data:                                      # iterete list and called place_order fx 
        
#         symbol=list(i.keys())[0]
#         i[symbol]['entry']=int(i[symbol]['entry'])
#         # i[symbol]['entry']=int(i[symbol]['entry'])
#         print(type(i[symbol]['entry']))
#         if i[symbol]['entry']>=i[symbol]['ltp'] and i[symbol]['tradeCount']==0 :
#             print("83:ENTRY PRICE",i[symbol]['entry'],"for",symbol,"is greater than LTP:",i[symbol]['ltp'])
#             print("GOING TO PLACE FRESH ORDER")
#             updated_response=place_order_equity_dict(SMART_API_OBJ,i,symbol)
#             print("86:",updated_response)
#             final_updated_response.append(updated_response) # append updated response received from place order fx
#         else:
#             print(symbol,"Trade count not 0")
#             final_updated_response.append(i)

#     print("92:",final_updated_response)
#     return final_updated_response


def place_order_equity_dict(brokerobject, token, sym, order_type, entry_or_exit, ltp, qty, order_state, exc="NSE"):         
    try:
        global sym_ltp
        trans_type=order_type
        ord_price=ltp
        qt=qty
        if qt!="":
            qt=int(qt)
        else:
            print("Qty cant  be empty")
        print("132:",token,trans_type,ord_price,qt,type(ord_price))
        updated_sym=sym+"-EQ"
        orderparams = {"variety": "NORMAL","tradingsymbol": updated_sym,"symboltoken": token,"transactiontype": trans_type,
                    "exchange": exc,"ordertype": "LIMIT","producttype": "INTRADAY","duration": "DAY","price": ord_price,
                    "squareoff": "0","stoploss": "0","quantity": qt}

        logging.info(f"ORDER PARAMETERS: {orderparams}")
        orderid = brokerobject.placeOrder(orderparams)
        # orderid = "gjasljlasjdfl"
        
        # print("119:",orderid)
        if orderid!=None or orderid!="":
            if (entry_or_exit == "ENTRY"): 
                order_data = {
                    sym: {
                        "entryId": orderid,
                        "entryPrice": ltp,
                        "entryStatus": "COMPLETED",
                        "exitStatus": "PENDING"
                    }
                }
                print(f"just before appending new order, {order_state}")
                order_state.append(order_data)
                # print(f"order_state {order_state}")
            elif(entry_or_exit == "EXIT"):
                for e in order_state:
                    e[sym]['exitID'] = orderid
                    e[sym]['exitStatus'] = 'COMPLETED'
                    e['exitPrice'] = ltp
            return order_state
        return 

        # print(sym,":",orderid)
            
            # logging.info(f"ORDER PLACED AT: {orderid}")
            # order_book_complete=SMART_API_OBJ.orderBook()
            # # print("128:",response_dict[sym]['tradeCount'])
            # if order_book_complete['message']=="SUCCESS" and order_book_complete['data']!="":
            #     order_book_complete_df=pd.DataFrame(order_book_complete['data'])
            #     # print("131:",order_book_complete_df.columns)
            
            #     order_book_complete_df=order_book_complete_df[["symboltoken","orderid","status","orderstatus","averageprice"]]
            #     order_status_df=order_book_complete_df[order_book_complete_df["orderid"]==orderid]
            #     print("134:",order_status_df)
            #     order_status=order_status_df["orderstatus"].iloc[0]
            # # if response_dict[sym]['tradeCount']==0:
            # if order_status=='complete':
            #     entry_order_price=order_status_df['averageprice'].iloc[0] 
    except Exception as e:
        print("@3242", e)

        
                    # response_dict[sym]['tradeCount']=response_dict[sym]['tradeCount']+1
                # response_dict[sym]['tradeCount']=response_dict[sym]['tradeCount']
                # print("156:",response_dict,response_dict[sym])
                
        # elif response_dict[sym]['tradeCount']==1:
        #      response_dict[sym]['exitId']=orderid
        #      logging.info(f"ORDER PLACED AT: {orderid}")
        #      order_book_complete=SMART_API_OBJ.orderBook()
        #     # print("128:",response_dict[sym]['tradeCount'])
        #      if order_book_complete['message']=="SUCCESS" and order_book_complete['data']!="":
        #         order_book_complete_df=pd.DataFrame(order_book_complete['data'])
        #         # print("131:",order_book_complete_df.columns)
            
        #         order_book_complete_df=order_book_complete_df[["symboltoken","orderid","status","orderstatus","averageprice"]]
        #         order_status_df=order_book_complete_df[order_book_complete_df["orderid"]==orderid]
        #         print("134:",order_status_df)
        #         order_status=order_status_df["orderstatus"].iloc[0]
                
        #      response_dict[sym]['exitStatus']=order_status
        #      if order_status=="complete":
        #         exit_order_price=order_status_df['averageprice'].iloc[0] 
        #         response_dict[sym]["exitPrice"]=exit_order_price
        #         response_dict[sym]['tradeCount']=response_dict[sym]['tradeCount']-1
        #         response_dict[sym]['tradeCount']=response_dict[sym]['tradeCount']
        #         print("150:",response_dict)
        #      elif order_status=="open":  
        #         #  time.sleep(2)
        #          response_dict[sym]["entryPrice"]=""
        #      else:
        #         response_dict[sym]["entryPrice"]=""

        # print("AFTER PLACING ORDER UPDATED DICT 147:",response_dict)
    # return 
        
login_result=login()
SMART_API_OBJ=login_result[0]                                    # create smart api object for trading 
SMART_WEB=login_result[1]           

global trade_count
token_dict={}
token_list=[]
# trade_count=0


