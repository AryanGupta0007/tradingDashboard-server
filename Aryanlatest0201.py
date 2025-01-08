from aryanfunctions import *

create_log_file("ARYAN")
connectFeed(SMART_WEB)
# while True:
#      # connectFeed(SMART_WEB)
#      # on_data(wsapp,message)
#      time.sleep(1)
     

const_response = {
  "ADANIENT": {
    "qty": 1,
    "orderType": "BUY",
    "entry": "2600",
    "target": "3000",
    "sl": "2400",
    "ltp": "",
    "entryPrice": "",
    "entryId": "",
    "orderId": "",
    "exitOrderId": "",
    "exitPrice": "",
    "entryStatus": "",
    "exitStatus": ""
  },
  "WIPRO": {
    "qty": 1,
    "orderType": "BUY",
    "entry": "305",
    "target": "",
    "sl": "",
    "ltp": "",
    "entryPrice": "",
    "entryId": "",
    "orderId": "",
    "exitOrderId": "",
    "exitPrice": "",
    "entryStatus": "",
    "exitStatus": ""
  }
}

# const_response={'ADANIENT': {'qty': 1, 'orderType': 'BUY', 'entry': '2600', 'target': '3000', 'sl': '2400', 'ltp': '', 'entryPrice': '', 'entryId': '', 'orderId': '', 'exitOrderId': '', 'exitPrice': '', 'entryStatus': '', 'exitStatus': ''}, 'WIPRO': {'qty': 1, 'orderType': 'BUY', 'entry': '305', 'target': '', 'sl': '', 'ltp': '', 'entryPrice': '', 'entryId': '', 'orderId': '', 'exitOrderId': '', 'exitPrice': '', 'entryStatus': '', 'exitStatus': ''}}
for sym in const_response.keys():
     if "Securityid" not in const_response[sym].keys():
          print(const_response[sym].keys())
          const_response[sym]['Securityid'] = ''

print("USER INPUTS:",const_response)
updated_response=update_ltp(const_response)
updated_response_df=pd.DataFrame(updated_response)
print("UPDATED DICT:",updated_response)
print(updated_response_df)
time.sleep(1)
