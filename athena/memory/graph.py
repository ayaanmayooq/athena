from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from neo4j import GraphDatabase, Driver

from athena.core.config import settings
from athena.core.logging import logger as base_logger

graph_logger = base_logger.getChild("graph")


@dataclass
class GraphEntity:
    id: str          # internal graph id (our own UUID-like key)
    name: str
    type: str        # "person", "meeting", "topic", "thing", etc.
    properties: Dict[str, Any]


@dataclass
class GraphRelation:
    subject_id: str
    predicate: str
    object_id: str
    properties: Dict[str, Any]


class GraphMemory:
    """
    Thin wrapper around Neo4j.

    Design goals:
    - Each node has:
        - user_id (to isolate per-user graphs)
        - entity_id (stable app-level id, separate from Neo4j internal id)
        - name
        - type (person, meeting, topic, etc.)
        - extra properties in `props`
    - Each relation has:
        - predicate (string label, e.g. "ATTENDS", "ABOUT")
        - user_id
        - optional extra properties
    """

    def __init__(
        self,
        uri: str,
        user: str,
        password: str,
        database: str = "neo4j",
    ) -> None:
        self._driver: Driver = GraphDatabase.driver(uri, auth=(user, password))
        self._database = database

    def close(self) -> None:
        self._driver.close()

    # ---- internal helper ----

    def _session(self):
        return self._driver.session(database=self._database)

    # ---- entity operations ----

    def upsert_entity(
        self,
        user_id: str,
        name: str,
        type_: str,
        props: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Find or create an entity node for this user.

        Returns the app-level entity_id (string).
        """
        props = props or {}
        # entity_id is a stable unique key: per user + name + type
        # you can change this later (UUID, etc.)
        entity_key = f"{user_id}:{type_.lower()}:{name.lower()}"

        cypher = """
        MERGE (e:Entity {
            user_id: $user_id,
            entity_id: $entity_id
        })
        ON CREATE SET
            e.name = $name,
            e.type = $type,
            e.created_at = datetime(),
            e += $props
        ON MATCH SET
            e.name = $name,
            e.type = $type,
            e.updated_at = datetime(),
            e += $props
        RETURN e.entity_id AS entity_id
        """

        graph_logger.info(
            "GraphMemory.upsert_entity\n"
            "    user=%s name=%s type=%s props=%s",
            user_id,
            name,
            type_,
            props,
        )
        with self._session() as session:
            result = session.run(
                cypher,
                user_id=user_id,
                entity_id=entity_key,
                name=name,
                type=type_,
                props=props,
            )
            record = result.single()
            graph_logger.info(
                "GraphMemory.upsert_entity result\n"
                "    entity_id=%s user=%s name=%s",
                record["entity_id"] if record else None,
                user_id,
                name,
            )
            return record["entity_id"]

    def get_entity(
        self,
        user_id: str,
        entity_id: str,
    ) -> Optional[GraphEntity]:
        cypher = """
        MATCH (e:Entity {user_id: $user_id, entity_id: $entity_id})
        RETURN e
        """

        graph_logger.debug(
            "GraphMemory.get_entity\n    user=%s entity_id=%s",
            user_id,
            entity_id,
        )
        with self._session() as session:
            result = session.run(
                cypher,
                user_id=user_id,
                entity_id=entity_id,
            )
            record = result.single()
            if not record:
                graph_logger.info(
                    "GraphMemory.get_entity miss\n    user=%s entity_id=%s",
                    user_id,
                    entity_id,
                )
                return None
            node = record["e"]
            props = dict(node)
            graph_logger.info(
                "GraphMemory.get_entity hit\n"
                "    user=%s entity_id=%s keys=%s",
                user_id,
                entity_id,
                list(props.keys()),
            )
            return GraphEntity(
                id=props["entity_id"],
                name=props.get("name", ""),
                type=props.get("type", ""),
                properties=props,
            )

    # ---- relation operations ----

    def upsert_relation(
        self,
        user_id: str,
        subject_entity_id: str,
        predicate: str,
        object_entity_id: str,
        props: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Create or update a relationship between two existing entities.
        """
        props = props or {}
        # Normalize predicate to a Neo4j relationship type
        rel_type = predicate.upper().replace(" ", "_")

        cypher = f"""
        MATCH (s:Entity {{user_id: $user_id, entity_id: $sub_id}})
        MATCH (o:Entity {{user_id: $user_id, entity_id: $obj_id}})
        MERGE (s)-[r:{rel_type} {{user_id: $user_id}}]->(o)
        ON CREATE SET
            r.created_at = datetime(),
            r += $props
        ON MATCH SET
            r.updated_at = datetime(),
            r += $props
        """

        graph_logger.info(
            "GraphMemory.upsert_relation\n"
            "    user=%s subj=%s pred=%s obj=%s props=%s",
            user_id,
            subject_entity_id,
            predicate,
            object_entity_id,
            props,
        )
        with self._session() as session:
            session.run(
                cypher,
                user_id=user_id,
                sub_id=subject_entity_id,
                obj_id=object_entity_id,
                props=props,
            )

    def upsert_relation_by_names(
        self,
        user_id: str,
        subject_name: str,
        subject_type: str,
        predicate: str,
        object_name: str,
        object_type: str,
        subject_props: Optional[Dict[str, Any]] = None,
        object_props: Optional[Dict[str, Any]] = None,
        rel_props: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Convenience: create entities by name+type and relate them.
        """
        graph_logger.info(
            "GraphMemory.upsert_relation_by_names\n"
            "    user=%s %s(%s) -%s-> %s(%s)",
            user_id,
            subject_name,
            subject_type,
            predicate,
            object_name,
            object_type,
        )
        sub_id = self.upsert_entity(
            user_id=user_id,
            name=subject_name,
            type_=subject_type,
            props=subject_props,
        )
        obj_id = self.upsert_entity(
            user_id=user_id,
            name=object_name,
            type_=object_type,
            props=object_props,
        )
        self.upsert_relation(
            user_id=user_id,
            subject_entity_id=sub_id,
            predicate=predicate,
            object_entity_id=obj_id,
            props=rel_props,
        )
        graph_logger.info(
            "GraphMemory.upsert_relation_by_names result\n"
            "    subject_id=%s object_id=%s",
            sub_id,
            obj_id,
        )

    # ---- query operations ----

    def get_relations_for_entity(
        self,
        user_id: str,
        entity_id: str,
        direction: str = "both",  # "out", "in", "both"
        limit: int = 50,
    ) -> List[GraphRelation]:
        """
        Get relations connected to a given entity.
        """
        if direction == "out":
            pattern = "(e)-[r]->(n)"
        elif direction == "in":
            pattern = "(n)-[r]->(e)"
        else:
            pattern = "(e)-[r]-(n)"

        cypher = f"""
        MATCH {pattern}
        WHERE e.user_id = $user_id AND e.entity_id = $entity_id
        RETURN r, startNode(r).entity_id AS s_id, endNode(r).entity_id AS o_id
        LIMIT $limit
        """

        graph_logger.debug(
            "GraphMemory.get_relations_for_entity\n"
            "    user=%s entity=%s direction=%s limit=%s",
            user_id,
            entity_id,
            direction,
            limit,
        )
        with self._session() as session:
            result = session.run(
                cypher,
                user_id=user_id,
                entity_id=entity_id,
                limit=limit,
            )
            relations: List[GraphRelation] = []
            for record in result:
                rel = record["r"]
                s_id = record["s_id"]
                o_id = record["o_id"]
                props = dict(rel)
                predicate = rel.type  # relationship type
                relations.append(
                    GraphRelation(
                        subject_id=s_id,
                        predicate=predicate,
                        object_id=o_id,
                        properties=props,
                    )
                )
            graph_logger.info(
                "GraphMemory.get_relations_for_entity result\n"
                "    entity=%s relation_count=%d",
                entity_id,
                len(relations),
            )
            return relations

    def find_entities_by_name(
        self,
        user_id: str,
        name: str,
        type_: Optional[str] = None,
        limit: int = 10,
    ) -> List[GraphEntity]:
        """
        Simple lookup by name (case-insensitive).
        """
        if type_:
            cypher = """
            MATCH (e:Entity)
            WHERE e.user_id = $user_id
              AND toLower(e.name) = toLower($name)
              AND e.type = $type
            RETURN e
            LIMIT $limit
            """
            params = {"user_id": user_id, "name": name, "type": type_, "limit": limit}
        else:
            cypher = """
            MATCH (e:Entity)
            WHERE e.user_id = $user_id
              AND toLower(e.name) = toLower($name)
            RETURN e
            LIMIT $limit
            """
            params = {"user_id": user_id, "name": name, "limit": limit}

        graph_logger.debug(
            "GraphMemory.find_entities_by_name\n"
            "    user=%s name=%s type=%s limit=%s",
            user_id,
            name,
            type_,
            limit,
        )
        with self._session() as session:
            result = session.run(cypher, **params)
            out: List[GraphEntity] = []
            for record in result:
                node = record["e"]
                props = dict(node)
                out.append(
                    GraphEntity(
                        id=props["entity_id"],
                        name=props.get("name", ""),
                        type=props.get("type", ""),
                        properties=props,
                    )
                )
            graph_logger.info(
                "GraphMemory.find_entities_by_name result\n"
                "    name=%s type=%s count=%d",
                name,
                type_,
                len(out),
            )
            return out


# Singleton-style access so other parts of the app can just `from athena.memory.graph import get_graph`
_graph_instance: Optional[GraphMemory] = None


def get_graph() -> GraphMemory:
    global _graph_instance
    if _graph_instance is None:
        _graph_instance = GraphMemory(
            uri=settings.neo4j_uri,
            user=settings.neo4j_user,
            password=settings.neo4j_password,
            database=settings.neo4j_database,
        )
    return _graph_instance
