import pandas as pd
import pandas.io.data as web
import datetime
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
import sys

pd.options.mode.chained_assignment = None

#%pylab


start = datetime.datetime(2010, 1, 1)
end = datetime.datetime(2013, 1, 27)

UNIVERSAL_BUFFER = 0.005
RESISTANCE_BUFFER = 0.005
SUPPORT_BUFFER = 0.005

SYMBOLS_CSV = 'ticker_symbols_top_mrktcap.xlsx'

SYMBOLS = [str(x[0]) for x in pd.read_excel(SYMBOLS_CSV, encoding='utf-8').values.tolist()]

TOP_PICKS_dict = {}
TOP_PICKS_order = pd.Series()


def find_index_of_MaxValue(df, col): return df[col].idxmax()

def find_index_of_MinValue(df, col): return df[col].idxmin()

def find_index_of_RecentIndex(df): return df.sort_index(ascending=False).ix[0].name

def calculate_slope (sliced_df, col='Close'):
    start = sliced_df.sort_index(ascending=True).ix[0]
    startValue = start[col]
    startIndex = start.name
    end = sliced_df.sort_index(ascending=False).ix[0]
    endValue = end[col]
    endIndex = end.name
    duration = endIndex - startIndex
    rise = endValue - startValue
    slope = rise / duration.days
    return slope

def help_calculate_trendPoint(startIndex, currentIndex, startValue, slope):
    mini_duration = currentIndex - startIndex
    trendPoint = startValue + int(mini_duration.days) * slope
    return trendPoint

def add_trendline (sliced_df, trend_type):
    slope = calculate_slope (df=sliced_df)
    startIndex = sliced_df.ix[0].name
    startValue = sliced_df.ix[0].Close
    sliced_df[trend_type+'-'+'trend'] = [help_calculate_trendPoint(startIndex=startIndex, 
			                                         currentIndex=x[1].name, 
			                                         startValue=startValue, 
			                                         slope=slope) 
                          for x in sliced_df.sort().iterrows()]
    return sliced_df

def plot (df, symbol):
	df[['Close', 'support-trend', 'resistance-trend', 'support-lowerBounds','resistance-lowerBounds', 
		'support-upperBounds','resistance-upperBounds', ]].plot(title=symbol)

def calculate_lowerBounds (sliced_df_with_trend, trend_type):
	lower_bounds_col_name = trend_type+'-'+'lowerBounds'
	sliced_df_with_trend[lower_bounds_col_name] = sliced_df_with_trend[trend_type+'-'+'trend']*(1-UNIVERSAL_BUFFER)
	return sliced_df_with_trend

def calculate_upperBounds (sliced_df_with_trend, trend_type):
	upperBound_col_name = trend_type+'-'+'upperBounds'
	sliced_df_with_trend[upperBound_col_name] = sliced_df_with_trend[trend_type+'-'+'trend']*(1+UNIVERSAL_BUFFER)
	return sliced_df_with_trend

def count_touches (df, trend_type):
	if trend_type == 'resistance':
		num_touches = len(df[(df.Close > df['resistance'+'-'+'trend']*(1+UNIVERSAL_BUFFER)) & (df.Close < df['resistance'+'-'+'trend']*(1-UNIVERSAL_BUFFER))])
	if trend_type == 'support':
		num_touches = len(df[(df.Close < df['support'+'-'+'trend']*(1+UNIVERSAL_BUFFER)) & (df.Close > df['support'+'-'+'trend']*(1-UNIVERSAL_BUFFER))])
	return num_touches

def check_valid_trend (df, startdate, trend_type):
	mini_df = df.ix[startdate:]
	if trend_type == 'resistance':
		num_breaks = len(mini_df[mini_df.Close > mini_df['resistance'+'-'+'trend']*(1+UNIVERSAL_BUFFER)])
	if 	trend_type == 'support':
		num_breaks = len(mini_df[mini_df.Close < mini_df['support'+'-'+'trend']*(1-UNIVERSAL_BUFFER)])
	if num_breaks = 0: 
		return True
	else: return False

def find_best_trend (df, trend_type):
	best_score = 0
	best_trend_date = None
	days = df.index.to_list()
	for start in days:
		sliced_df = df.ix[start:]
		sliced_df_with_trend = add_trendline (sliced_df, trend_type)
		if check_valid_trend (sliced_df_with_trend, startdate=day, trend_type) == True: 
			end = find_index_of_RecentIndex(sliced_df_with_trend)
			num_days = end - start
			num_touches = count_touches (sliced_df_with_trend, trend_type)
			score = num_days * num_touches
			if score > best_score: 
				best_trend_date = someDate
				best_score = score
	package = {'trend_type': trend_type, 'best_score': best_score, 'best_trend_date': best_trend_date}			 
	return package


def apply_algo_helper (stock, symbol, trend_type, PREV_DF):

	if trend_type == 'support':
		start = find_index_of_MinValue(stock, 'Close')
	else:
		start = find_index_of_MaxValue(stock, 'Close')
	end = find_index_of_RecentIndex(stock)
	duration = end - start
	slope = calculate_slope(df=stock, col='Close', startIndex=start, endIndex=end, duration=duration )
	sliced_stock = stock.ix[start:end]
	sliced_stock_with_trend = calculate_trendPoints(sliced_stock, slope, trend_type)
	sliced_stock_with_trend = sliced_stock_with_trend.reset_index()
	stock = stock.reset_index()
	sliced_stock_with_trend = sliced_stock_with_trend[[trend_type+'-'+'trend', 'Date']]
	sliced_stock_with_trend_with_lowerbounds = calculate_lowerBounds(sliced_stock_with_trend, trend_type )
	sliced_stock_with_trend_with_upperbounds = calculate_upperBounds(sliced_stock_with_trend_with_lowerbounds, trend_type)
	new_df = pd.merge(stock,sliced_stock_with_trend, how='left', on='Date')
	new_df.set_index('Date', inplace=True)


	if PREV_DF is not None:
		new_df = pd.merge(new_df, PREV_DF, how='left')


	if trend_type == 'support':
		num_breaks = count_support_breaks(new_df)
		num_touches = count_support_touches(new_df)
	else:
		num_breaks = count_resistance_breaks(new_df)
		num_touches = count_resistance_touches(new_df)


	if num_breaks == 0:
		print symbol, trend_type, "not broken: ", num_touches
		TOP_PICKS_dict[symbol] = {'touches': num_touches, 'df': new_df}
		TOP_PICKS_order.loc[symbol] = num_touches
	else: 
		print symbol, trend_type, "broken: ", num_breaks


	if PREV_DF is None:
		return new_df
	else: return new_df




def run_algo (stocks):
	count_fails = 0
	for symbol in stocks:
		if count_fails < 5:
			try:
				stock_df = web.DataReader(symbol, 'yahoo', start, end)
				first_df = apply_algo_helper(stock=stock_df, symbol=symbol, trend_type='resistance', PREV_DF=None)
				final_df = apply_algo_helper(stock=stock_df, symbol=symbol, trend_type='support', PREV_DF=first_df)
				#print final_df.tail()
			except Exception as e:
				print "failed on: ", symbol, "reason: ", e
				count_fails += 1
				#print 'Error on line {}'.format(sys.exc_info()[-1].tb_lineno)

	for ticker in TOP_PICKS_order.order(ascending=False)[:5].index:
		plot(TOP_PICKS_dict[ticker]['df'], ticker)


if __name__ == "__main__":
	run_algo(SYMBOLS)

	