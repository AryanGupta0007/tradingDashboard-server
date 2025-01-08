from flask import Flask, request, jsonify 
from markupsafe import escape
from aryanfunctions import *
from flask_cors import CORS
import logging,time
  
app = Flask(__name__) 
create_log_file("ARYAN")

app = Flask(__name__)
CORS(app)                                                   # Allow CORS for React frontend
connectFeed(SMART_WEB)

logging.basicConfig(level=logging.INFO)

def call_updateddata(data:list):

    try:
        # print("19:",data)  
        updatedData = update_ltp(data)

        # if updatedData!='':
        # print(f"Updated data: {updatedData}")
           
    except Exception as e:
        
        # return data
        print("29:",e)
        return jsonify({"error": str(e)})
    
    # print("32:",updatedData)
    # print(data)
    return updatedData

@app.route("/getSecurityKey", methods=["POST"])
def fetchSecurityKey():
    
    data = request.json
    global token_list
    token_list=[]
    
    print("recieved subscribing data ", data)
   
    for sym in data.keys():
        securityid=get_equitytoken(sym)

        data[sym]['securityId'] = securityid
        token_list.append(securityid)

    subscribeList=[{"exchangeType":1,"tokens":token_list}]
    subscribeSymbol(subscribeList,SMART_WEB)
    time.sleep(2)
    # for sym in data.keys():
        # data[sym]['securityId'] = 12
    return data

@app.route("/ltp", methods=["POST"])
def fetch_ltp_post():
    data = request.json
    # print(f"Received data: {data}")
    # for sym in data.keys():
    #     if "Securityid" not in data[sym].keys():
    #         # print(const_response[sym].keys())
    #         data[sym]['Securityid'] = ''
    # time.sleep(5)
    # print("76:",data)
    # sys.exit()
    final_updated_data=call_updateddata(data)
    print("78:",final_updated_data)
    return final_updated_data
    # print(f"32:Updated data: {data}")
    # Mock response:
        
    # time.sleep(5)
    # logging.info(f"{data}")ḥ

@app.route('/index', methods=["GET"])
def get_index_values():

    global token

    response = SMART_API_OBJ.getMarketData(mode="FULL",exchangeTokens={"NSE": ["26000", "26009","26037","26074"],"BSE": ["99919000"]})
    response=response['data']['fetched']
    indexes={}
    for i in response:
       
        index_data={i['tradingSymbol']:{"securityId":i["symbolToken"],'previousDayClose':i['close'],"currentValue":"","difference":"","percentageDifference":""}}
        indexes.update(index_data)
    
    for x in indexes:
        indexes[x]['currentValue']=token_dict[indexes[x]['securityId']]
        indexes[x]['currentValue']=float(indexes[x]['currentValue'])
        
    for key,value in indexes.items():
        previous_close = value['previousDayClose']
        current_value = value['currentValue']
        value['difference'] = current_value - previous_close
        value['difference']=round(value['difference'],2)
        value['percentageDifference']=value['difference']/value['previousDayClose']*100
        value['percentageDifference']=round(value['percentageDifference'],2)
    
    # print(indexes)
    return indexes


if __name__ == '__main__':
    app.run(debug=True, port=5001)  