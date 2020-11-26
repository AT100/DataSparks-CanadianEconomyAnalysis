import sys
assert sys.version_info >= (3, 5) # make sure we have Python 3.5+

from pyspark.sql import SparkSession, functions, types
from pyspark.sql.functions import to_date,lit,year,avg,round
import datetime

cpi_schema = types.StructType([
    types.StructField('REF_DATE', types.StringType()),
    types.StructField('GEO', types.StringType()),
    types.StructField('DGUID', types.StringType()),
    types.StructField('Products and product groups', types.StringType()),
    types.StructField('UOM', types.StringType()),
    types.StructField('UOM_ID', types.IntegerType()),
    types.StructField('SCALAR_FACTOR', types.StringType()),
	types.StructField('SCALAR_ID', types.IntegerType()),
    types.StructField('VECTOR', types.StringType()),
    types.StructField('COORDINATE', types.DoubleType()),
    types.StructField('VALUE', types.DoubleType()),
	types.StructField('STATUS', types.StringType()),
    types.StructField('SYMBOL', types.StringType()),
    types.StructField('TERMINATED', types.StringType()),
	types.StructField('DECIMALS', types.IntegerType()),
])

	
def main():
	cpi_df = spark.read.csv('../Canada_CPI.csv', schema=cpi_schema)

	#filter out null values for required columns
	notnull_df = cpi_df.filter(cpi_df['REF_DATE'].isNotNull() | cpi_df['GEO'].isNotNull() | cpi_df['VALUE'].isNotNull())

	#filter out "All-items" only from 'Products and product groups' columns
	allitems_df = notnull_df.filter(notnull_df['Products and product groups'] == lit('All-items'))

	#convert 'REF_DATE' to date type
	date_df = allitems_df.withColumn('REF_DATE', to_date(allitems_df['REF_DATE'], 'yyyy-MM'))

	#fetch data for the last 10 years
	decade_df = date_df.where(date_df['REF_DATE'].between(datetime.datetime.strptime('2010-01-01', '%Y-%m-%d'), datetime.datetime.strptime('2020-10-01','%Y-%m-%d')))

	#Taking only the provinces
	province_df = decade_df.filter(~decade_df['GEO'].contains(','))

	#take the yearly avg of cpi values for each province and restructure the dataframe based on provinces
	result_cpi_df = province_df.groupby(year('REF_DATE').alias('YEAR')).pivot('GEO').agg(round(avg('VALUE'),2)).orderBy('YEAR')

	result_cpi_df.write.csv('../Canada_CPI_output', header='true', mode='overwrite')
	
if __name__ == '__main__':
    spark = SparkSession.builder.appName('CPI Analysis').getOrCreate()
    assert spark.version >= '2.4' # make sure we have Spark 2.4+
    spark.sparkContext.setLogLevel('WARN')
    sc = spark.sparkContext
    main()