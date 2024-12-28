# Code for ETL operations on Country-GDP data

# Importing the required libraries
from bs4 import BeautifulSoup
import requests
import pandas as pd
import numpy as np
import sqlite3
from datetime import datetime 

# Log File: code_log.txt

def log_progress(message):
    ''' This function logs the mentioned message of a given stage of the
    code execution to a log file. Function returns nothing'''
    
    timestamp_format = '%Y-%h-%d-%H:%M:%S' 
    now = datetime.now()
    timestamp = now.strftime(timestamp_format) 
    with open("./code_log.txt","a") as f: 
        f.write(timestamp + ' : ' + message + '\n')

def extract(url, table_attribs):
    ''' This function aims to extract the required
    information from the website and save it to a data frame. The
    function returns the data frame for further processing. '''
    
    page = requests.get(url).text
    soup = BeautifulSoup(page, "html.parser")
    df = pd.DataFrame(columns = table_attribs_input)

    table = soup.find_all("tbody")[0]
    rows = table.find_all('tr')
    for row in rows:
        col = row.find_all("td")
        if len(col)!=0:
            name = col[1].find_all('a')[1]['title']
            amount = float(col[2].contents[0].replace("\n",''))
            
            data_dict = {'Name':name,
                        'MC_USD_Billion':amount}
            
            df1 =  pd.DataFrame(data_dict, index = [0])
            df = pd.concat([df,df1], ignore_index = True)

    # print(df)
    return df

def transform(df, csv_path):
    ''' This function accesses the CSV file for exchange rate
    information, and adds three columns to the data frame, each
    containing the transformed version of Market Cap column to
    respective currencies'''
    
    rates = pd.read_csv(csv_path)
    dict = rates.set_index('Currency').to_dict()['Rate']

    df['MC_GBP_Billion'] = [ np.round(x * dict['GBP'],2) for x in df['MC_USD_Billion']]
    df['MC_EUR_Billion'] = [ np.round(x * dict['EUR'],2) for x in df['MC_USD_Billion']]
    df['MC_INR_Billion'] = [ np.round(x * dict['INR'],2) for x in df['MC_USD_Billion']]
    
    # print(df)
    return df

def load_to_csv(df, output_path):
    ''' This function saves the final data frame as a CSV file in
    the provided path. Function returns nothing.'''
    
    df.to_csv(output_path, index = False)

def load_to_db(df, sql_connection, table_name):
    ''' This function saves the final data frame to a database
    table with the provided name. Function returns nothing.'''
    
    df.to_sql(table_name, sql_connection, if_exists='replace', index=False)

def run_query(query_statement, sql_connection):
    ''' This function runs the query on the database table and
    prints the output on the terminal. Function returns nothing. '''
    
    print(query_statement)
    query_output = pd.read_sql(query_statement, sql_connection)
    print(query_output)

''' Here, you define the required entities and call the relevant
functions in the correct order to complete the project. Note that this
portion is not inside any function.'''

# Declaring known values

url = 'https://web.archive.org/web/20230908091635 /https://en.wikipedia.org/wiki/List_of_largest_banks'
table_attribs_input =  ['Name','MC_USD_Billion']
table_attribs_output = ['Name','MC_USD_Billion','MC_GBP_Billion','MC_EUR_Billion','MC_INR_Billion']
path_output = './Largest_banks_data.csv'
database = 'Banks.db'
table_name = 'Largest_banks'

log_progress("Preliminaries complete. Initiating ETL process")


# Call extract() function
df = extract(url, table_attribs_input)
log_progress("Data extraction complete. Initiating Transformation process")


# Call transform() function	
df = transform(df,"data/exchange_rate.csv")
log_progress("Data transformation complete. Initiating Loading process")


# Call load_to_csv()
load_to_csv(df, path_output)
log_progress("Data saved to CSV file.")


#Initiate SQLite3 connection
sql_connection = sqlite3.connect('Banks.db')
log_progress("SQL Connection initiated")


# Call load_to_db()
load_to_db(df, sql_connection, table_name)
log_progress("Data loaded to Database as a table, Executing queries")


# Call run_query()

# Print the contents of the entire table
query_statement = f"SELECT * FROM {table_name}"
run_query(query_statement, sql_connection)

# Print the average market capitalization of all the banks in Billion USD.
query_statement = f"SELECT AVG(MC_GBP_Billion) FROM {table_name}"
run_query(query_statement, sql_connection)

# Print only the names of the top 5 banks
query_statement = f"SELECT Name from {table_name} LIMIT 5"
run_query(query_statement, sql_connection)

log_progress("Process Complete")

# Close SQLite3 connection	
sql_connection.close()
log_progress("Server Connection closed")