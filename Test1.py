import pandas as pd
import requests
from tabulate import tabulate
url = "https://jsonplaceholder.typicode.com/users"
response = requests.get(url)
if response.status_code == 200:
         data = response.json()
         df = pd.DataFrame(data)
         print(tabulate(df, headers='keys', tablefmt='grid')) 

else:
        print("request failed",response.status_code)
