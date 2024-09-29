UNWIND $data as row
MERGE (
    h:Entity {
        id: 
            CASE
                WHEN NOT row.head_span.id = 'id-less' THEN row.head_span.id
                ELSE row.head_span.text 
        END
    }
)
ON CREATE SET h.text = row.head_span.text
MERGE (
    t:Entity {
        id:
            CASE
                WHEN NOT row.tail_span.id = 'id-less' THEN row.tail_span.id
                ELSE row.tail_span.text
            END
    }
)
ON CREATE SET t.text = row.tail_span.text

WITH row, h, t
CALL apoc.merge.relationship(h, toUpper(replace(row.relation, ' ', '_')), {}, {}, t, {})
YIELD rel
RETURN distinct 'done' as result;