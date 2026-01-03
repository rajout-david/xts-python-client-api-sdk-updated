from Connect import XTSConnect
import json



with open("cred.json", "r") as keys_file:
    keys = json.load(keys_file)
    

api_key = keys['api_key']
secret_key = keys['secret_key']

API_KEY  = api_key
API_SECRET = secret_key
source = "WEBAPI"

xt_market = XTSConnect(API_KEY, API_SECRET, source)
market_res = xt_market.marketdata_login()



def store_all_instrument_data():
    exchange_segment = [xt_market.EXCHANGE_NSEFO]
    master_response = xt_market.get_master(exchangeSegmentList=exchange_segment)
    print("Master API Response Type:", master_response.get("type"))

    raw_string = master_response["result"]
    lines = raw_string.strip().split("\n")

    instruments = []

    for line in lines:
        if not line.strip():
            continue
        
        parts = line.split("|")
        
        # Sahi index ke hisaab se mapping
        instrument = {
            "exchange": parts[0],                          # NSEFO
            "token": parts[1],                             # exchangeInstrumentID (main token)
            "exchangeInstrumentID": parts[7],              # long ID
            "tradingSymbol": parts[18].strip(),            # short clean symbol (most used)
            "symbol": parts[4].strip(),                    # full symbol
            "instrumentType": parts[5],                    # OPTIDX, FUTIDX, etc.
            "underlying": parts[3],                         # BANKNIFTY, NIFTY, etc.
            "lotSize": int(parts[10]) if parts[10].isdigit() else parts[10],
            "tickSize": parts[11],
            "strikePrice": parts[12] if parts[12] != "-1" else None,  # -1 ko None bana diya
            "optionType": parts[13] if parts[13] != "-" else None,   # - ko None
            "expiryDate": parts[14],                       # 2026-01-29T18:30:00
            "displayName": parts[15]
        }
        
        instruments.append(instrument)

    with open("nfo_master.json", "w", encoding="utf-8") as f:
        json.dump(instruments, f, indent=4, ensure_ascii=False)



def get_ltp(tradingsymbol):
    """
    Trading symbol daal (jaise 'BANKNIFTY26JAN45000CE' ya 'NIFTY26JANFUT')
    → LTP return karega (float)
    """
    MASTER_FILE = "nfo_master.json"
    
    # Master file load kar
    try:
        with open(MASTER_FILE, "r", encoding="utf-8") as f:
            instruments_master = json.load(f)
    except FileNotFoundError:
        print(f"❌ {MASTER_FILE} nahi mili! Pehle master download kar.")
        return None
    except Exception as e:
        print(f"❌ Master file load error: {e}")
        return None

    # Symbol se token nikaal
    token = None
    for inst in instruments_master:
        if inst.get("symbol") == tradingsymbol:
            try:
                token = int(inst["token"])
                break
            except:
                print(f"✗ Token convert nahi hua for {tradingsymbol}")
                return None

    if not token:
        print(f"✗ Symbol not found in master: {tradingsymbol}")
        return None

    instruments = [
        {'exchangeSegment': 2,  'exchangeInstrumentID': token}
    ]

    try:
        response = xt_market.get_quote(
            Instruments=instruments,       # Capital 'I' - exact naam
            xtsMessageCode=1512,           # 1501 = simple LTP, 1502 = full depth (market closed mein 1501 better)
            publishFormat='JSON'
        )
    except Exception as e:
        print(f"✗ API call error: {e}")
        return None

    # Response parse kar
    if response.get("type") == "success":
        list_quotes = response.get("result", {}).get("listQuotes", [])
        return list_quotes
       
    else:
        print(f"✗ API failed: {response.get('description', 'Unknown error')}")
        return 0



if __name__ == '__main__':
    ltp_dict = get_ltp(tradingsymbol="BANKNIFTY26JAN64000CE")
    ltp = json.loads(ltp_dict[0])["LastTradedPrice"]
    print(type(ltp))
