from neo4j import GraphDatabase, exceptions as GraphException
from neo4j.work.simple import Query
from cypher_helper import CypherHelper

class SheetsGraph:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

# Generic Queries

    def execute_boolean_queries(cls,tx, cypher, function_args, ret_val):
        return list(tx.run(cypher, **function_args))[0][ret_val]

    def check_if_empty(self):
        with self.driver.session() as session:
            return session.read_transaction(self.execute_boolean_queries, CypherHelper.empty_query(), {}, 'new_slate')
    
    def _execute_creation_tx(cls,tx,cypher, function_args):
        return tx.run(cypher, **function_args)
   
    def create_unique_constraint(self, label, field):
        with self.driver.session() as session:
            return session.write_transaction(self._execute_creation_tx, CypherHelper.get_unique_constraint_query(label, field), {})

    def execute_data_queries(cls, tx, cypher, function_args):
        return list(tx.run(cypher, **function_args))
    
# CREATE Methods
    def create_constraints(self):
        if self.check_if_empty():
            try:
                self.create_unique_constraint(label="Sheet", field='id')
            except:
                pass

    def create_cell(self,sheet_id, wsheet_id, cell_id, value=None, formula=None):
        query = CypherHelper.get_cell_create_query(sheet_id, wsheet_id, cell_id)
        with self.driver.session() as session:
            return session.write_transaction(self._execute_creation_tx,query, {'value':value, 'formula':formula})

    def create_sheet(self, sheet_id):
        with self.driver.session() as session:
            return session.write_transaction(self._execute_creation_tx,"CREATE (n:Sheet {id:'" + sheet_id+"', name:'" + sheet_id+"'})", {})
    
    def create_work_sheet(self, sheet_id, worksheet_id):
        with self.driver.session() as session:
            return session.write_transaction(self._execute_creation_tx,CypherHelper.get_sheet_worksheet_create_query(sheet_id, worksheet_id), {})

    def create_work_sheet(self, sheet_name, worksheet_name):
        try:
            self.create_constraints()
            query = CypherHelper.get_sheet_worksheet_create_query(sheet_name, worksheet_name)
            with self.driver.session() as session:
                return session.write_transaction(self._execute_creation_tx,query, {})
        except GraphException.ConstraintError as error:
            print(error.message)

# UPDATE
    def update_cell_value(self, sheet_id, wsheet_id, cell_id, value):
        update_cell_value_query = CypherHelper.get_update_cell_value_query(sheet_id, wsheet_id, cell_id, value)
        with self.driver.session() as session:
            return session.write_transaction(self._execute_creation_tx,update_cell_value_query, {})

    def update_cell_formula(self, sheet_id, wsheet_id, cell_id, formula):
        update_cell_formula_query = CypherHelper.get_update_cell_formula_query(sheet_id, wsheet_id, cell_id, formula)
        with self.driver.session() as session:
            return session.write_transaction(self._execute_creation_tx,update_cell_formula_query, {'formula':formula})

    def drop_specific_impact_relations(self, sheet_id, wsheet_id, parent_cell_id, child_cell_id):
        drop_relations = CypherHelper.drop_specific_impact_relations(sheet_id, wsheet_id, parent_cell_id, child_cell_id)
        with self.driver.session() as session:
            return session.write_transaction(self._execute_creation_tx,drop_relations, {})

    def create_cell_impact_relations(self, sheet_id, wsheet_id, impacting_cell_id, impacted_cell_id):
        create_impact_relations = CypherHelper.create_impact_relations(sheet_id, wsheet_id, impacting_cell_id, impacted_cell_id)
        with self.driver.session() as session:
            return session.write_transaction(self._execute_creation_tx,create_impact_relations, {})

# READ
    def get_work_sheets(self, sheet_id):
        with self.driver.session() as session:
            query = "MATCH (v:Sheet {id:'"+sheet_id+"'})-[:Worksheet]->(p:Worksheet) RETURN p"
            return session.read_transaction(self.execute_data_queries,query, {})

    def get_work_sheet_cells(self, sheet_id, work_sheet_id):
        with self.driver.session() as session:
            query = "MATCH (v:Sheet {id:'"+sheet_id+"'})-[:Worksheet]->(p:Worksheet {id:'"+work_sheet_id+"'})-[:Cell]-(d:Cell) RETURN d"
            return session.read_transaction(self.execute_data_queries,query, {})

    def is_worksheet_exists_in_sheet(self, sheet_id, wsheet_id):
        return_val = 'exists'
        query = CypherHelper.is_sheet_worksheet_exists_query(sheet_id, wsheet_id, return_val)
        with self.driver.session() as session:
            return session.read_transaction(self.execute_boolean_queries,query, {}, return_val)

    def is_sheet_exists(self, sheet_id):
        return_val = 'exists'
        query = CypherHelper.is_sheet_exists_query(sheet_id, return_val)
        with self.driver.session() as session:
            return session.read_transaction(self.execute_boolean_queries,query, {}, return_val)

    def get_all_sheets(self):
        with self.driver.session() as session:
            resp = session.read_transaction(self.execute_data_queries, CypherHelper.get_all_sheets(), {})
            ret = []
            for record in resp:
                ret.append(record['sheet'])
            return ret
    def get_all_worksheets(self, sheet_id):
        with self.driver.session() as session:
            resp = session.read_transaction(self.execute_data_queries, CypherHelper.get_all_worksheets(sheet_id), {})
            ret = []
            for record in resp:
                ret.append(record['worksheet'])
            return ret

    def get_all_sheets_worksheets(self):
        with self.driver.session() as session:
            resp = session.read_transaction(self.execute_data_queries, "MATCH(n:Sheet)-[:Worksheet]->(p:Worksheet) return n.id, p.id", {})
            ret = {}
            for record in resp:
                ret[record[0]] = record[1]
 