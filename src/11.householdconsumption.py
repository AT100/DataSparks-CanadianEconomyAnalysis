import sys
assert sys.version_info >= (3, 5) # make sure we have Python 3.5+

from pyspark.sql import SparkSession, functions, types
from pyspark.sql.functions import to_date,lit,year,avg,round
import datetime

#Anaysing the overall househols expenditure values

consumption_schema = types.StructType([
	types.StructField('REF_DATE', types.StringType()),
	types.StructField('GEO', types.StringType()),
	types.StructField('DGUID', types.StringType()),
	types.StructField('Prices',types.StringType()),
	types.StructField('Seasonal adjustment', types.StringType()),
	types.StructField('Estimates', types.StringType()),
	types.StructField('UOM', types.StringType()),
	types.StructField('UOM_ID', types.StringType()),
	types.StructField('SCALAR_FACTOR',types.StringType()),
	types.StructField('SCALAR_ID', types.StringType()),
	types.StructField('VECTOR', types.StringType()),
	types.StructField('COORDINATE', types.StringType()),
	types.StructField('VALUE', types.StringType()),
	types.StructField('STATUS', types.StringType()),
	types.StructField('SYMBOL', types.StringType()),
	types.StructField('TERMINATED', types.StringType()),
	types.StructField('DECIMALS', types.StringType()),
])


def main():

	########################Processing Detailed household final consumption expenditure, Canada, quarterly Data##################################
	exp_df = spark.read.csv('../data/clean/statcan/household_consumption.csv', schema=consumption_schema)

	#filter out null values for required columns
	exp_notnull_df = exp_df.filter(exp_df['REF_DATE'].isNotNull() | exp_df['GEO'].isNotNull() | exp_df['Estimates'].isNotNull() |exp_df['VALUE'].isNotNull())

	#fetch data for the last 10 years
	exp_decade_df = exp_notnull_df.where(exp_notnull_df['REF_DATE'].between(datetime.datetime.strptime('2010-01-01', '%Y-%m-%d'), datetime.datetime.strptime('2020-10-01','%Y-%m-%d')))

	#Fecting only "Seasonally adjusted at quarterly rates values
	exp_seasonal_df = exp_decade_df.filter(exp_decade_df['Seasonal adjustment'] == lit('Seasonally adjusted at quarterly rates'))

	#Fetch only 'Household final consumption expenditure' Estimates of expenditure
	exp = exp_seasonal_df.filter(exp_seasonal_df['Estimates'] == lit('Household final consumption expenditure'))

	#Take Get onyl current prices
	exp_prices = exp.filter(exp['Prices'] == lit('Current prices'))

	#fetch only required columns
	exp_req = exp_prices.select('REF_DATE',(exp_prices['VALUE']).alias('household_expenditure'))

	#convert 'REF_DATE' to date type
	exp_date = exp_req.withColumn('REF_DATE', to_date(exp_req['REF_DATE'], 'yyyy-MM'))

	#convert 'VALUE' to int type
	exp_int_df = exp_date.withColumn('household_expenditure', (exp_date['household_expenditure']).cast(types.IntegerType()))

	#Get yearly average data for Household final consumption expenditure
	exp_avg = exp_int_df.groupBy(year('REF_DATE').alias('YEAR')).agg(avg(exp_int_df['household_expenditure']).alias('household_expenditure*(10^6)')).orderBy('YEAR')

	exp_avg.write.csv('../OUTPUT-Folder/house_expenditure_output', header='true', mode='overwrite')

if __name__ == '__main__':
    spark = SparkSession.builder.appName('Canada Household expenditure').getOrCreate()
    assert spark.version >= '2.4' # make sure we have Spark 2.4+
    spark.sparkContext.setLogLevel('WARN')
    sc = spark.sparkContext
    main()
