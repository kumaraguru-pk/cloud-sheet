import flask
from werkzeug.utils import ArgumentValidationError
app = flask.Flask(__name__)
from sheets import *
from flask import jsonify
sheet_manager = SheetManager()


@app.route("/sheets/<sheet_id>/worksheets/<wsheet_id>",methods=['GET'])
def index(sheet_id, wsheet_id):
    sheet_manager.create(sheet_id, wsheet_id)
    rows = [str(i+1) for i in range(10)]
    columns = [chr(i+ord('A')) for i in range(10)]
    worksheet_local = {}
    for row in rows:
        for col in columns:
            if col+row in sheet_manager.sheets[sheet_id].worksheets[wsheet_id].cells:
                info = {
                    'value':sheet_manager.sheets[sheet_id].worksheets[wsheet_id].cells[col+row].value,
                    'formula':sheet_manager.sheets[sheet_id].worksheets[wsheet_id].cells[col+row].formula
                    }
                worksheet_local[col+row] = info
            else:
                worksheet_local[col+row] = {}
    return flask.render_template('index.html', rows=rows, columns=columns, worksheet_local=worksheet_local, sheet_id=sheet_id, wsheet_id=wsheet_id)

@app.route('/sheets/<sheet_id>/worksheets/<wsheet_id>/cell/<cell_id>/<value>', methods=['PUT'])
def update_cell(sheet_id, wsheet_id, cell_id,value):
    # show the user profile for that user
    try:
        return jsonify(sheet_manager.sheets[sheet_id].worksheets[wsheet_id].update_cell(cell_id,value))
    except CircularReferenceException as err:
        return "Circular reference", 422
    except ArgumentValidationError as err:
        return "Circular reference", 400

    

@app.route("/sheets", methods=['GET'])
def get_all_sheets():
   return { 'sheets': sheet_manager.get_all_sheets()}

@app.route("/sheets/<sheet_id>/worksheets", methods=['GET'])
def get_all_worksheets(sheet_id):
   return { 'work_sheets': sheet_manager.get_all_worksheets(sheet_id)}


