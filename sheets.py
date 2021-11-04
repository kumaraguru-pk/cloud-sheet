import re

from werkzeug.utils import ArgumentValidationError
from sheet_graph import SheetsGraph

class InputValidator:
    def __init__(self) -> None:
        self.digit_exp = re.compile("^[-]?((\d+(\.\d*)?)|(\.\d+))$")
        self.formula_exp = re.compile("^[-]?((\d+(\.\d*)?)|(\.\d+))$")

    def is_valid_sum_formula(self, value) -> bool:
        try:
            if len(value) <= 0 or '=' != value[0]:
                return False
            operands = list(filter(None, value[1:].split("+")))
            if len(operands) <= 0:
                return False
            for op in operands:
                if (
                    ord(op[0]) >= 65
                    and ord(op[0]) <= 74
                    and int(op[1:]) > 0
                    and int(op[1:]) <= 10
                ):
                    continue
                else:
                    return False
            return True
        except Exception as err:
            print(err)
            raise ArgumentValidationError("Invalid formula")

    def is_valid_digit(self, value) -> bool:
        return self.digit_exp.match(value) is not None

class CircularReferenceException(Exception):
    pass


class SheetManager:
    def __init__(self):
        self.sheets = {}
        self.validator = InputValidator()
        self.sheet_graph = SheetsGraph(
            "neo4j+ssc://e265c1e7.databases.neo4j.io",
            "neo4j",
            "9z-UC5O1fxUEcFdpq6SSpOj_RdI4FMRptIKSVpgyBto",
        )
    def close(self):
        self.sheet_graph.close()

    def get_all_sheets_worksheets(self):
        return self.sheet_graph.get_all_sheets_worksheets()

    def get_all_worksheets(self, sheet_id):
        return self.sheet_graph.get_all_worksheets(sheet_id)

    def get_all_sheets(self):
        return self.sheet_graph.get_all_sheets()

    def create(self, sheet_id, worksheet_id):
        if sheet_id not in self.sheets and self.sheet_graph.is_sheet_exists(sheet_id):
            self.sheets[sheet_id] = Sheet(sheet_id, self.sheet_graph)
            self.load_sheet(sheet_id)
        if sheet_id not in self.sheets:
            self.sheets[sheet_id] = Sheet(sheet_id, self.sheet_graph)
            self.sheet_graph.create_sheet(sheet_id)
        
        if worksheet_id not in self.sheets[sheet_id].worksheets:
            self.sheets[sheet_id].create(worksheet_id, self.validator)
        else:
            self.load_worksheet(sheet_id, worksheet_id)

    def load_sheet(self, sheet_id):
        res = self.sheet_graph.get_work_sheets(sheet_id)
        for record in res:
             if record[0]['id'] not in self.sheets[sheet_id].worksheets:
                 self.sheets[sheet_id].worksheets[ record[0]['id']] = Worksheet(sheet_id, record[0]['id'], self.validator, self.sheet_graph)

    def load_worksheet(self, sheet_id, worksheet_id):
        res = self.sheet_graph.get_work_sheet_cells(sheet_id,worksheet_id)
        for record in res:
            if record[0]['id'] not in self.sheets[sheet_id].worksheets[worksheet_id].cells:
                self.sheets[sheet_id].worksheets[worksheet_id].cells[record[0]['id']] = Cell(sheet_id, worksheet_id, 
                record[0]['id'],self.sheet_graph,record[0]['name'],record[0]['value'],record[0]['formula'], True)
        # update impacts once all cells are created
        for item in self.sheets[sheet_id].worksheets[worksheet_id].cells.items():
            if item[1].formula:
                for op in item[1].formula.split('+'):
                    self.sheets[sheet_id].worksheets[worksheet_id].cells[op].impacting.append(self.sheets[sheet_id].worksheets[worksheet_id].cells[item[0]])
class Sheet:
    def __init__(self, sheet_id, sheets_graph):
        self.worksheets = {}
        self.id = sheet_id
        self.sheets_graph = sheets_graph

    def create(self, worksheet_id, validator):
        if worksheet_id in self.worksheets:
            return 
        self.worksheets[worksheet_id] = Worksheet(
            self.id, worksheet_id, validator, self.sheets_graph
        )
        self.sheets_graph.create_work_sheet(self.id, worksheet_id)


class Worksheet:
    def __init__(self, sheet_id, worksheet_id, input_validator, sheets_graph):
        self.cells = {}  # cell id with cell just for easy lookup
        self.id = worksheet_id
        self.input_validator = input_validator
        self.sheets_graph = sheets_graph
        self.sheet_id = sheet_id

    def detect_circle_in_formula(self, start, end) -> bool:
        if not start:
            return False
        if start.id == end.id:
            raise CircularReferenceException(f"Cycle Detected {start.id} --> {end.id}")
        for op in start.impacting:
            if self.detect_circle_in_formula(op, end):
                raise CircularReferenceException(f"Cycle Detected {start.id} --> {end.id}")
        return False

    def remove_impacts_as_necessary(self, curr_cell, old_impact_set, new_impact_set):
        cells_to_be_updated = old_impact_set - new_impact_set
        for impacting_cell in cells_to_be_updated:
            for impacted_cell in self.cells[impacting_cell].impacting:
                if impacted_cell.id == curr_cell.id:
                    self.cells[impacting_cell].impacting.remove(impacted_cell)
                    self.sheets_graph.drop_specific_impact_relations(
                        self.sheet_id, self.id, impacting_cell, curr_cell.id
                    )

    def update_cell_formula(self, curr_cell, value):
        ops = value.split("+")
        old_ops = []
        if curr_cell.formula and value != curr_cell.formula:
            # need o drop and add new impacts
            old_ops = curr_cell.formula.split("+")
        total = 0
        for op in ops:
            if op not in self.cells:
                self.cells[op] = Cell(self.sheet_id, self.id, op,self.sheets_graph, op, None, None)
            else:
                self.detect_circle_in_formula(curr_cell, self.cells[op])
            
            self.cells[op].impacting.append(curr_cell)
            self.sheets_graph.create_cell_impact_relations(
                    self.sheet_id, self.id, op, curr_cell.id
            )
            if self.cells[op].value:
                total += self.cells[op].value
        curr_cell.value = total
        self.remove_impacts_as_necessary(curr_cell, set(old_ops), set(ops))
        curr_cell.formula = value

    def recalculate(self, cell, updated_cells):
        if cell.formula:
            total = 0
            for op in cell.formula.split("+"):
                total += 0 if not self.cells[op].value else self.cells[op].value
            cell.value = total
            updated_cells[cell.id] = {'value': cell.value, 'formula':cell.formula}
        for dep in cell.impacting: 
            self.recalculate(dep, updated_cells)
        
    def update_cell(self, cell_id, value):
        updated_cells = {}
        if cell_id not in self.cells:
            self.cells[cell_id] = Cell(self.sheet_id, self.id, cell_id, self.sheets_graph, cell_id, None, None)
        curr_cell = self.cells[cell_id]
        if self.input_validator.is_valid_digit(value):
            if curr_cell.formula:
                self.remove_impacts_as_necessary(curr_cell, set(curr_cell.formula.split("+")), set())
            curr_cell.value = int(value)  # DFS on the dependents if any
            curr_cell.formula = None
            updated_cells[curr_cell.id] = {'value': curr_cell.value, 'formula':curr_cell.formula}
        elif self.input_validator.is_valid_sum_formula(value):
            value = value[1:]
            self.update_cell_formula(curr_cell, value)
            updated_cells[curr_cell.id] = {'value': curr_cell.value, 'formula':curr_cell.formula}
        else:
            raise ArgumentValidationError("Invalid input")

        for dep in curr_cell.impacting:
            self.recalculate(dep, updated_cells)
        return updated_cells


class Cell:
    def __init__(self, sheet_id, wsheet_id, cell_id, sheets_graph,name,value,formula, load_cell = False):
        """
        Lets assume A1 is this Cell
        _impacting = This is the incoming edges basically other cells relying on this cell for value ! B4 = A1 + C4+ C4 which means B4 will be part of this
        so any changes to the A1 should be bubbled up all the way to all dependents
        """
        self._impacting = []  # referred by others
        self._value = value
        self._description = ""
        self._formula = formula
        self._id = cell_id
        self._name = name
        self.sheets_graph = sheets_graph
        self._sheet_id = sheet_id
        self._wsheet_id = wsheet_id
        if not load_cell:
            self.sheets_graph.create_cell(self._sheet_id, self._wsheet_id, self._id, None, None)

    @property
    def id(self):
        return self._id

    @property
    def impacting(self):
        return self._impacting

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value
        self.sheets_graph.update_cell_value(
            self._sheet_id, self._wsheet_id, self._id, self._value
        )

    @property
    def formula(self):
        return self._formula

    @formula.setter
    def formula(self, formula):
        self._formula = formula
        self.sheets_graph.update_cell_formula(self._sheet_id, self._wsheet_id, self._id, formula)
