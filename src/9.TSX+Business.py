import sys, datetime, json, os
from operator import add
from pyspark.sql.functions import col, lit
from pyspark.sql import SparkSession, functions, types, dataframe
from pyspark.sql.functions import to_date, round, avg, year

TSX_schema = types.StructType([
    types.StructField('REF_DATE', types.StringType()),
    types.StructField('GEO', types.StringType()),
    types.StructField('DGUID', types.StringType()),
    types.StructField('Toronto Stock Exchange Statistics', types.StringType()),
    types.StructField('UOM', types.StringType()),
    types.StructField('UOM_ID', types.IntegerType()),
    types.StructField('SCALAR_FACTOR',types.StringType()),
    types.StructField('SCALAR_ID', types.IntegerType()),
    types.StructField('VECTOR', types.StringType()),
    types.StructField('COORDINATE', types.DoubleType()),
    types.StructField('VALUE', types.DoubleType()),
    types.StructField('STATUS', types.StringType()),
    types.StructField('SYMBOL', types.StringType()),
    types.StructField('TERMINATED', types.StringType()),
    types.StructField('DECIMALS', types.IntegerType()),
])

Business_schema = types.StructType([
    types.StructField('REF_DATE', types.StringType()),
    types.StructField('GEO', types.StringType()),
    types.StructField('DGUID', types.StringType()),
    types.StructField('Leading indicators', types.StringType()),
    types.StructField('Composite index', types.StringType()),
    types.StructField('UOM', types.StringType()),
    types.StructField('UOM_ID', types.IntegerType()),
    types.StructField('SCALAR_FACTOR',types.StringType()),
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

    tsx = spark.read.csv('../data/clean/statcan/10100125/TSX-statistics.csv',schema=TSX_schema) #reading 'TSX' csv Data 
    buss = spark.read.csv('../data/clean/statcan/33100111/Business-indicators.csv',schema=Business_schema) #reading 'BusinessIndicators' csv Data


    ############################################### TSX Operations #################################################
    checkNull = tsx.filter(tsx['REF_DATE'].isNotNull() & tsx['VALUE'].isNotNull()).withColumn('REF_DATE', to_date(tsx['REF_DATE'], 'yyyy-MM'))
    # to select non-null index values for TSX
    tsx1 = checkNull.where(checkNull['UOM']=='Index').where(checkNull['VALUE']>0)
    tsx1 = tsx1.groupby('REF_DATE','Toronto Stock Exchange Statistics').sum('VALUE')
    tsx2= tsx1.withColumnRenamed('sum(VALUE)','Total Stock Value')
    res_tsx = tsx2.where(tsx2['Total Stock Value']>100).orderBy('REF_DATE') # Discard low stock values that do not contribute to industrial GDP 
    res_tsx.coalesce(1).write.csv('../OUTPUT-Folder/TSX_output',header=True,mode='overwrite') # Output -> REF_DATE, Toronto Stock Exchange Statistics, Total Stock Value

    # To find net worth of top 60 Canadian Companies Stock
    res_tsx1 = tsx2.where(tsx2['Toronto Stock Exchange Statistics']=="Standard and Poor's/Toronto Stock Exchange 60 Index")
    res_tsx1 = res_tsx1.withColumnRenamed('Total Stock Value','Total TSX 60 Value').orderBy('REF_DATE')
    res_tsx1 = res_tsx1.select('REF_DATE','Total TSX 60 Value')
    res_tsx1.coalesce(1).write.csv('../OUTPUT-Folder/TSX60_output',header=True,mode='overwrite') # Output -> REF_DATE, Total TSX 60 Value

    
    ########################################### Business Indicators Operations #####################################
    checkNull1 = buss.filter(buss['REF_DATE'].isNotNull() & buss['VALUE'].isNotNull()).withColumn('REF_DATE', to_date(buss['REF_DATE'], 'yyyy-MM'))
    # to select valid Smoothed Composite index values for indicators
    buss1 = checkNull1.where(checkNull1['VALUE']>0).where(checkNull1['Composite index']=='Smoothed')
    buss1 = checkNull1.groupby('REF_DATE','Leading Indicators').sum('VALUE').withColumnRenamed('REF_DATE','YEAR')
    res_buss = buss1.withColumnRenamed('sum(VALUE)','Business Profit Factor').orderBy('YEAR')
    res_buss.coalesce(1).write.csv('../OUTPUT-Folder/BIndicator_output',header='True',mode='overwrite')


    ################################ Relation between TSX stock and Business Indicators #################################
    r_tsx = res_tsx.groupby(year('REF_DATE').alias('REF_DATE')).agg(avg('Total Stock Value').alias('Avg Yearly TSX Stock'))
    final_res = r_tsx.select('REF_DATE','Avg Yearly TSX Stock').orderBy('REF_DATE')
    final_res.coalesce(1).write.csv('../OUTPUT-Folder/TSX-yearly',header=True,mode='overwrite')

       
if __name__ == '__main__':
    spark = SparkSession.builder.appName('TSX+BusinessIndicators').getOrCreate()
    spark.sparkContext.setLogLevel('WARN')
    sc = spark.sparkContext
    main()



  