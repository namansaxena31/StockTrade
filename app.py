from flask import Flask, render_template, jsonify
from alpha_vantage.timeseries import TimeSeries
import pandas as pd
import ta
import pandas_ta as pt
from datetime import date

app = Flask(__name__)

#data display route
@app.route("/")
def data():
        return csvdata()

#functions
def price_action(ohlc):

    #get all data
    t0_close = ohlc.iloc[-1]["Close"]
    t0_high = ohlc.iloc[-1]["High"]
    t0_low = ohlc.iloc[-1]["Low"]

    t1_high = ohlc.iloc[-2]["High"]
    t1_low = ohlc.iloc[-2]["Low"]

    t2_high = ohlc.iloc[-3]["High"]

    t3_high = ohlc.iloc[-4]["High"]
    t3_open = ohlc.iloc[-4]["Open"]
    t3_close = ohlc.iloc[-4]["Close"]

    condition_1 = t0_close > t1_high
    condition_2 = t0_high > t1_high
    condition_3 = t0_low > t1_low
    condition_4 = t0_close > t2_high
    condition_5 = t0_close > t3_high
    condition_6 = t3_open > t3_close

    if(condition_1 and condition_2 and condition_3 and condition_4 and condition_5 and condition_6):
        return 3
    else:
        return 0

def rvgi(ohlc):
    return 0

def macd(ohlc):
    macd = ta.trend.MACD(close=ohlc['Close'], window_slow=26, window_fast=12, window_sign=9)

    ohlc['MACD'] = macd.macd()
    ohlc['MACD_Signal'] = macd.macd_signal()
    print(ohlc)
    macd_t0 = ohlc['MACD'].iloc[-1]
    macd_signal_t0 = ohlc['MACD_Signal'].iloc[-1]

    macd_t1 = ohlc['MACD'].iloc[-2]
    macd_signal_t1 = ohlc['MACD_Signal'].iloc[-2]

    if macd_t0 > macd_signal_t0 and macd_t1 < macd_signal_t1:
        return 3
    elif macd_t0 > macd_signal_t0 and macd_t1 > macd_signal_t1:
        return 1
    elif macd_t0 > 0 and macd_t1 < 0:
        return 3
    elif macd_t0 > 0 and macd_t1 > 0:
        return 1
    else:
        return 0

def roc(ohlc):
    df = ta.momentum.ROCIndicator(close=ohlc['Close'], window = 9, fillna = False)

    roc_values = df.roc()
    roc = roc_values.iloc[-1]
    if roc>0:
        return 3
    else:
        return 0

def ft(ohlc):
    fish = pt.fisher(high=ohlc['High'], low=ohlc['Low'], length=14)
    print(fish)
    ft_t0 = fish[f'FISHERT_14_1'].iloc[-1]
    ft_signal_t0 = fish[f'FISHERTs_14_1'].iloc[-1]

    ft_t1 = fish[f'FISHERT_14_1'].iloc[-2]
    ft_signal_t1 = fish[f'FISHERTs_14_1'].iloc[-2]

    if ft_t0 > ft_signal_t0 and ft_t1 < ft_signal_t1:
        return 3
    elif ft_t0 > ft_signal_t0 and ft_t1 > ft_signal_t1:
        return 1
    elif ft_t0 > 0 and ft_t1 < 0:
        return 3
    elif ft_t0 > 0 and ft_t1 > 0:
        return 1
    else:
        return 0

def apidata():
    try:
        nse_stocks = [
                'AXISBANK.NS',
                'SBIN.NS',
                'HEROMOTOCO.NS',
                'LODHA.NS',
                'TCS.NS',
                'DRREDDY.NS',
                'JINDALSTEL.NS',
                'ITC.NS',
                'RELIANCE.NS',
                'ADANIENT.NS'
            ]

        results =[]
        ts = TimeSeries(key='N1VQFT3FYJXPCW1E', output_format='pandas')

        for stock in nse_stocks:

            data, meta = ts.get_daily(symbol='ITC.BSE', outputsize='compact')  

            # Filter by date range
            data = data.rename(columns={
                "1. open": "Open",
                "2. high": "High",
                "3. low": "Low",
                "4. close": "Close"
            }).reset_index()

            ohlc = data[["date", "Open", "High", "Low", "Close"]]
            results.append({"Stock": stock.split(".")[0], "Score": price_action(ohlc)})

        df = pd.DataFrame(results)
        return jsonify(df.to_dict(orient="records"))
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def csvdata():
    nse_stocks = [
            'AXISBANK.NS',
            'SBIN.NS',
            'HEROMOTOCO.NS',
            'LODHA.NS',
            'TCS.NS',
            'DRREDDY.NS',
            'JINDALSTEL.NS',
            'ITC.NS',
            'RELIANCE.NS',
            'ADANIENT.NS'
        ]
    
    results = []
    for stock in nse_stocks:
        stock_name = stock.replace('.NS', '') + '.csv'
        try:
            df = pd.read_csv(stock_name)

            # Check if file is empty or has no data rows
            if df.empty:
                print(f"Skipping {stock_name}: File is empty")
                continue

            # df = df.iloc[::-1].reset_index(drop=True)  # Reverse to make latest row first
            print(f"Loaded {stock_name}: {df.shape[0]} rows")

            # Rename columns safely
            rename_map = {
                'Date  ': 'Date',
                'Close Price  ': 'Close',
                'High Price  ': 'High',
                'Low Price  ': 'Low',
                'Open Price  ': 'Open'
            }
            df.rename(columns=rename_map, inplace=True)

            # Check if all required columns exist
            required_cols = ['Date','Close', 'High', 'Low', 'Open']
            if not all(col in df.columns for col in required_cols):
                print(f"Skipping {stock_name}: Missing columns")
                continue

            # Take last 30 rows and clean numeric values
            ohlc = (
                df[required_cols]
                .tail(100)
                .reset_index(drop=True)
            )

            for col in ['Close', 'High', 'Low', 'Open']:
                ohlc[col] = pd.to_numeric(ohlc[col].astype(str).str.replace(',', ''), errors='coerce')

            # Calculate scores
            pa_score = price_action(ohlc)  
            rvgi_score = rvgi(ohlc)      
            macd_score = macd(ohlc)    
            roc_score = roc(ohlc)
            ft_score = ft(ohlc)
            composite_score = (pa_score + macd_score + roc_score + ft_score)/4 
            results.append({
                "PA Score": pa_score,
                # "RVGI Score": rvgi_score,
                "MACD Score": macd_score,
                "ROC Score": roc_score,
                "FT Score": ft_score,
                "Composite Score": composite_score,
                "Stock": stock.split('.')[0],
            })

        except FileNotFoundError:
            print(f"File not found: {stock_name}")
        except Exception as e:
            print(f"Error processing {stock_name}: {e}")

    # Convert to DataFrame and return JSON
    df_result = pd.DataFrame(results)
    df_result = df_result.sort_values(by='Composite Score', ascending=False)
    return jsonify(df_result.to_dict(orient="records"))
            
            

if __name__ == "__main__":
    app.run(debug=True)
