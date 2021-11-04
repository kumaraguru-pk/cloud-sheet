# Building an Interactive Spreadsheet

Graph Based simple spread sheet, idea is to model the spreadsheet as a graph
Neo4j Aura is used as persistence layer
currently we are defaulting to 10X10 

## Setup

1. Set up your virtualenv: `virtualenv -p python3 cloud-sheet`
2. Source the `activate` script: `source cloud-sheet/bin/activate`
3. Install the dependencies in your virtualenv:
   `pip install -r requirements.txt`
4. Run the server `FLASK_DEBUG=1 FLASK_APP=server.py flask run`
