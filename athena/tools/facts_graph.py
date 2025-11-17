from __future__ import annotations

from typing import Any, Dict, List, Optional, Literal

from athena.core.tool_base import tool
from athena.memory.graph import get_graph, GraphEntity, GraphRelation


@tool(
    name="remember_fact",
    description=(
        "Store a structured fact in Athena's graph memory as a relationship "
        "between two entities (subject and object). "
        "Use this when the user states a fact connecting two things, e.g. "
        "'My mom is Ayesha', 'I have a meeting with Ben', "
        "'Meeting X is about customer service associates', etc."
    ),
    parameters={
        "type": "object",
        "properties": {
            "user_id": {
                "type": "string",
                "description": "Internal user identifier. The agent can inject this."
            },
            "subject_name": {
                "type": "string",
                "description": "Name of the subject entity, e.g. 'me', 'Ayaan', 'Ben', 'Meeting with Ben'."
            },
            "subject_type": {
                "type": "string",
                "description": "Type of subject entity, e.g. 'person', 'meeting', 'topic', 'place', 'project'."
            },
            "predicate": {
                "type": "string",
                "description": (
                    "Relationship between subject and object, e.g. "
                    "'MOTHER_OF', 'ATTENDS', 'ABOUT', 'LIKES', 'WORKS_ON', 'LOCATED_AT'. "
                    "Free-form text is allowed; it will be normalized to an uppercase relationship type."
                ),
            },
            "object_name": {
                "type": "string",
                "description": "Name of the object entity."
            },
            "object_type": {
                "type": "string",
                "description": "Type of object entity, e.g. 'person', 'meeting', 'topic', 'place', 'project'."
            },
            "subject_properties": {
                "type": "object",
                "description": "Optional extra properties for the subject entity (JSON).",
            },
            "object_properties": {
                "type": "object",
                "description": "Optional extra properties for the object entity (JSON).",
            },
            "relation_properties": {
                "type": "object",
                "description": "Optional extra properties for the relation itself (JSON).",
            },
        },
        "required": [
            "user_id",
            "subject_name",
            "subject_type",
            "predicate",
            "object_name",
            "object_type",
        ],
    },
)
def remember_fact(
    user_id: str,
    subject_name: str,
    subject_type: str,
    predicate: str,
    object_name: str,
    object_type: str,
    subject_properties: Optional[Dict[str, Any]] = None,
    object_properties: Optional[Dict[str, Any]] = None,
    relation_properties: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    High-level graph fact storage.

    This will:
    - upsert subject entity (per user_id + name + type)
    - upsert object entity
    - create or update a relationship between them
    """
    graph = get_graph()

    graph.upsert_relation_by_names(
        user_id=user_id,
        subject_name=subject_name,
        subject_type=subject_type,
        predicate=predicate,
        object_name=object_name,
        object_type=object_type,
        subject_props=subject_properties,
        object_props=object_properties,
        rel_props=relation_properties,
    )

    return {
        "status": "ok",
        "stored_fact": {
            "user_id": user_id,
            "subject_name": subject_name,
            "subject_type": subject_type,
            "predicate": predicate,
            "object_name": object_name,
            "object_type": object_type,
        },
    }


@tool(
    name="query_facts",
    description=(
        "Query Athena's graph memory for facts related to a given entity name. "
        "Use this when the user asks what they know about a person, meeting, topic, or place, "
        "e.g. 'What do you know about Ben?', 'What is my meeting with Ben about?', "
        "or 'What do I know about customer service associates?'."
    ),
    parameters={
        "type": "object",
        "properties": {
            "user_id": {
                "type": "string",
                "description": "Internal user identifier. The agent can inject this."
            },
            "entity_name": {
                "type": "string",
                "description": "Name of the entity to query, e.g. 'Ben', 'Meeting with Ben', 'customer service associates'.",
            },
            "entity_type": {
                "type": "string",
                "description": (
                    "Optional type hint for the entity, e.g. 'person', 'meeting', 'topic', 'place'. "
                    "If omitted, all types will be considered."
                ),
            },
            "direction": {
                "type": "string",
                "enum": ["out", "in", "both"],
                "default": "both",
                "description": (
                    "Whether to return outgoing, incoming, or all relations "
                    "around the matched entity."
                ),
            },
            "limit": {
                "type": "integer",
                "default": 25,
                "description": "Maximum number of relations to return.",
            },
        },
        "required": ["user_id", "entity_name"],
    },
)
def query_facts(
    user_id: str,
    entity_name: str,
    entity_type: Optional[str] = None,
    direction: Literal["out", "in", "both"] = "both",
    limit: int = 25,
) -> Dict[str, Any]:
    """
    Return graph relations around the entity with the given name (and optional type).
    """
    graph = get_graph()

    # 1) Find matching entities
    entities: List[GraphEntity] = graph.find_entities_by_name(
        user_id=user_id,
        name=entity_name,
        type_=entity_type,
        limit=5,  # avoid exploding if the name is very common
    )

    if not entities:
        return {
            "status": "not_found",
            "message": f"No entity found with name '{entity_name}'"
                      + (f" and type '{entity_type}'" if entity_type else ""),
        }

    # For now, just use the first match.
    target = entities[0]

    # 2) Get relations for that entity
    relations: List[GraphRelation] = graph.get_relations_for_entity(
        user_id=user_id,
        entity_id=target.id,
        direction=direction,
        limit=limit,
    )

    # 3) For readability, resolve subject/object names + types
    #    (we'll batch-fetch entities for any seen IDs)
    connected_ids = {rel.subject_id for rel in relations} | {
        rel.object_id for rel in relations
    }

    id_to_entity: Dict[str, GraphEntity] = {}
    for ent_id in connected_ids:
        ent = graph.get_entity(user_id=user_id, entity_id=ent_id)
        if ent:
            id_to_entity[ent_id] = ent

    facts: List[Dict[str, Any]] = []
    for rel in relations:
        subj = id_to_entity.get(rel.subject_id)
        obj = id_to_entity.get(rel.object_id)

        facts.append(
            {
                "subject": {
                    "id": rel.subject_id,
                    "name": subj.name if subj else None,
                    "type": subj.type if subj else None,
                },
                "predicate": rel.predicate,
                "object": {
                    "id": rel.object_id,
                    "name": obj.name if obj else None,
                    "type": obj.type if obj else None,
                },
                "properties": rel.properties,
            }
        )

    return {
        "status": "ok",
        "entity": {
            "id": target.id,
            "name": target.name,
            "type": target.type,
            "properties": target.properties,
        },
        "facts": facts,
    }
