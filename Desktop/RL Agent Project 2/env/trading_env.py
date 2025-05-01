from gym_trading_env.environments import TradingEnv
import pandas as pd

def create_trading_env(csv_path):

    df = pd.read_csv(csv_path, skiprows=[1, 2])
    df['Date'] = pd.to_datetime(df.index)
    df.set_index('Date', inplace=True)
    
    column_mapping = {
        'Close': 'close',
        'Open': 'open',
        'High': 'high',
        'Low': 'low',
        'Volume': 'volume'
    }
    df = df.rename(columns=column_mapping)
    
    df['close_feature'] = df['close']
    df['volume_feature'] = df['volume']
    df['high_feature'] = df['high']
    df['low_feature'] = df['low']
    
    return TradingEnv(
        df=df,
        positions=[-1, 0, 1],  # short selling, holding, and buying
        trading_fees=0.001,    
        borrow_interest_rate=0.0001  
    )
