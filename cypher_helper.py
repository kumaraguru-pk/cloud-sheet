class CypherHelper:

    @staticmethod
    def get_sheet_worksheet_create_query(sheet_id, wsheet_id):
        return "MATCH (n:Sheet {id:'" + sheet_id+"', name:'" + sheet_id+"'}) \
                CREATE (m:Worksheet {id:'" + wsheet_id+"', name:'" + wsheet_id +"'}) \
                CREATE (n)-[r:Worksheet {name: n.name + '<->' + m.name}]->(m)"

    @staticmethod
    def get_cell_create_query(sheet_id, wsheet_id, cell_id):
        return "match(n:Sheet {id:'" + sheet_id+"'})-[r:Worksheet]->(m:Worksheet {id:'" + wsheet_id+"'}) \
        CREATE(c:Cell {id:'" + cell_id+"', name:'" + cell_id+"',value:$value, formula:$formula}) CREATE (m)-[k:Cell]->(c)"

    @staticmethod
    def get_update_cell_value_query(sheet_id, wsheet_id, cell_id, value):
        return "match(n:Sheet {id:'" + sheet_id+"'})-[r:Worksheet]->(m:Worksheet {id:'" + wsheet_id+"'})-[p:Cell]->(c:Cell {id:'" + cell_id+"'})  SET c.value = toInteger("+str(value)+")  return c" 

    @staticmethod
    def get_update_cell_formula_query(sheet_id, wsheet_id, cell_id, formula):
        return "match(n:Sheet {id:'" + sheet_id+"'})-[r:Worksheet]->(m:Worksheet {id:'" + wsheet_id+"'})-[p:Cell]->(c:Cell {id:'" + cell_id+"'})  SET c.formula=$formula return c" 


    @staticmethod
    def get_unique_constraint_query(label, field):
            return "CREATE CONSTRAINT ON (x:"+label+") ASSERT x."+field+" IS UNIQUE"

    @staticmethod
    def get_is_cyclic_query(formula_ids, current_cell_id, field, ret_field):
        return "MATCH p = (n:"+field+")-[*]->(f:Cell {id:'"+ current_cell_id+ "'}) where "+ ' or '.join(f'n.id="{w}"' for w in formula_ids)+" with count(nodes(p)) > 0  as "+ret_field+" Return "+ ret_field

    @staticmethod
    def drop_all_relations(sheet_id, wsheet_id, cell_id):
        return "MATCH (n:Sheet {id:'"+sheet_id+"'})-[r:Worksheet]->(n:Worksheet {id:'"+wsheet_id+"'})[r:Cell]->(n:Cell {id:'"+cell_id+"'})-[r:Impacting]->() DELETE r"

    @staticmethod
    def drop_specific_impact_relations(sheet_id, wsheet_id, p_cell_id, c_cell_id):
        return "MATCH (sheet:Sheet {id:'"+sheet_id+"'})-[sheetrel:Worksheet]->(ws:Worksheet {id:'"+wsheet_id+"'})-[wsrel:Cell]->(cell:Cell {id:'"+p_cell_id+"'})-[cellrel:Impacting]->(child:Cell {id:'"+c_cell_id+"'}) DELETE cellrel"

    @staticmethod
    def create_impact_relations(sheet_id, wsheet_id, cell_id_parent, cell_id_child):
        return "MATCH (s1:Sheet {id:'"+sheet_id+"'})-[r1:Worksheet]->(n1:Worksheet {id:'"+wsheet_id+"'})-[r3:Cell]->(c1:Cell {id:'"+cell_id_parent+"'}) \
                MATCH (s2:Sheet {id:'"+sheet_id+"'})-[r2:Worksheet]->(n2:Worksheet {id:'"+wsheet_id+"'})-[r4:Cell]->(c2:Cell {id:'"+cell_id_child+"'}) \
                MERGE (c1)-[r:Impacting {name: c1.name + '<->' + c2.name}]->(c2)"
    
    @staticmethod
    def formula_operand_relation_query(cell_id, operand):
        return "MATCH (s:Cell {id:'"+ cell_id+"'}) MATCH (w:Cell {id:'"+operand+"'}) CREATE (s)-[r:Operand {name: s.id + '->' + w.id}]->(w)"

    @staticmethod
    def node_creation_query(label, value):
        query = "CREATE (w:"+label+"{id: $id, name: $name, description: $description, created_at: $created_at, updated_at:$updated_at, created_by:$created_by, updated_by: $updated_by"
        if value != None:
            query+=", value:$value})"
        else:
            query+="})"
        return query
    
    @staticmethod
    def relation_creation_query(parent_label, child_label, relation_label, weight="1"):
        return "MATCH (s:" + parent_label+ "{id: $parent_id}) MATCH (w:" + child_label+ "{id: $child_id}) CREATE (s)-[r:"+ relation_label+ "{name: s.id + '->' + w.id, weight:toInteger("+weight+")}]->(w)"

    @staticmethod
    def empty_query():
        return  "MATCH (n:Sheet) WITH COUNT(*) = 0  as new_slate RETURN new_slate"

    @staticmethod
    def is_sheet_worksheet_exists_query(sheet_id, wsheet_id, return_val):
        return  "MATCH (n:Sheet {id:'"+sheet_id+"'})-[:Worksheet]->(m:Worksheet {id:'"+wsheet_id+"'}) with count(m) = 1 as "+return_val+" return " +return_val
   
    @staticmethod
    def is_sheet_exists_query(sheet_id, return_val):
        return  "MATCH (n:Sheet {id:'"+sheet_id+"'}) with count(n) = 1 as "+return_val+" return " +return_val


    @staticmethod
    def get_all_sheets():
        return  "MATCH (n:Sheet) return n.id as sheet"

    
    @staticmethod
    def get_all_worksheets(sheet_id):
        return  "MATCH (n:Sheet {id:'" +sheet_id+"'})-[:Worksheet]->(p:Worksheet) return p.id as worksheet"