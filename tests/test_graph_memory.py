import pytest

from athena.memory.graph import get_graph, GraphEntity, GraphRelation
import os, sys, pytest


@pytest.mark.neo4j
def test_neo4j_connection_and_basic_query():
    """
    Sanity check: can we connect to Neo4j and run a trivial query?
    If this fails, your URI/user/password/database are wrong
    or Neo4j is not running.
    """
    graph = get_graph()

    # lowest-level check: just run RETURN 1
    with graph._session() as session:  # type: ignore[attr-defined]
        result = session.run("RETURN 1 AS n")
        record = result.single()
        assert record is not None
        assert record["n"] == 1


@pytest.mark.neo4j
def test_upsert_entity_and_relation_roundtrip():
    """
    Test that we can:
    - upsert entities
    - upsert a relation between them
    - query those relations back
    """
    graph = get_graph()
    user_id = "test-user"

    # 1) Upsert two entities and a relation between them
    # Example: "Ayaan" WORKS_ON "Athena"
    graph.upsert_relation_by_names(
        user_id=user_id,
        subject_name="Ayaan",
        subject_type="person",
        predicate="WORKS_ON",
        object_name="Athena",
        object_type="project",
        subject_props={"role": "owner"},
        object_props={"kind": "ai_assistant"},
        rel_props={"since": "2025-01-01"},
    )

    # 2) Find the subject entity by name
    entities = graph.find_entities_by_name(
        user_id=user_id,
        name="Ayaan",
        type_="person",
        limit=5,
    )

    assert entities, "Expected at least one entity named 'Ayaan' for test-user"
    subject = entities[0]

    # 3) Fetch relations around that entity
    relations = graph.get_relations_for_entity(
        user_id=user_id,
        entity_id=subject.id,
        direction="out",
        limit=10,
    )

    assert relations, "Expected at least one outgoing relation from 'Ayaan'"

    # 4) Assert at least one relation looks like WORKS_ON -> Athena
    found = False
    for rel in relations:
        if rel.predicate == "WORKS_ON":
            # sanity: the object should be Athena
            obj_entity = graph.get_entity(user_id=user_id, entity_id=rel.object_id)
            assert obj_entity is not None
            assert obj_entity.name.lower() == "athena"
            found = True
            break

    assert found, "Expected a WORKS_ON relation from 'Ayaan' to 'Athena'"
