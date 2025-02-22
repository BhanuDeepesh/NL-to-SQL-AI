We have created NL to Sql converter which does the following:
1. It takes in JSON or YAML file and the query from the user.
2. It also allows the user to decide on which format the user wants the output, which can be either JSON or YAML.
3. It first compares the query for any spelling mistakes and gives options to select from .
4. Next it fetches the required tables into the file based on the relevancy to the query 
