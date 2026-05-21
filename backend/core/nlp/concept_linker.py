"""
Concept Linker - Link entities to external knowledge bases
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import httpx


@dataclass
class LinkedConcept:
    """Represents a linked concept."""
    original_text: str
    canonical_name: str
    concept_id: str
    source: str
    confidence: float
    description: Optional[str]
    url: Optional[str]
    metadata: Dict


class ConceptLinker:
    """
    Link extracted entities to external knowledge bases.
    
    Supports:
    - Wikidata
    - UMLS (biomedical)
    - Custom knowledge bases
    """
    
    def __init__(
        self,
        use_wikidata: bool = True,
        use_umls: bool = False,
        umls_api_key: Optional[str] = None,
    ):
        """
        Initialize the concept linker.
        
        Args:
            use_wikidata: Whether to use Wikidata for linking
            use_umls: Whether to use UMLS for biomedical concepts
            umls_api_key: API key for UMLS
        """
        self.use_wikidata = use_wikidata
        self.use_umls = use_umls
        self.umls_api_key = umls_api_key
        
        # Cache for linked concepts
        self._cache: Dict[str, LinkedConcept] = {}
    
    async def link(self, entity_text: str, entity_type: Optional[str] = None) -> Optional[LinkedConcept]:
        """
        Link an entity to a knowledge base.
        
        Args:
            entity_text: Entity text to link
            entity_type: Optional entity type for context
            
        Returns:
            LinkedConcept if found, None otherwise
        """
        # Check cache
        cache_key = f"{entity_text}:{entity_type}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        linked_concept = None
        
        # Try Wikidata first
        if self.use_wikidata:
            linked_concept = await self._link_wikidata(entity_text, entity_type)
        
        # Try UMLS for biomedical entities
        if not linked_concept and self.use_umls and self.umls_api_key:
            if entity_type in ["CHEMICAL", "DISEASE", "GENE", "PROTEIN"]:
                linked_concept = await self._link_umls(entity_text)
        
        # Cache result
        if linked_concept:
            self._cache[cache_key] = linked_concept
        
        return linked_concept
    
    async def link_batch(
        self,
        entities: List[Dict],
    ) -> List[Optional[LinkedConcept]]:
        """
        Link multiple entities.
        
        Args:
            entities: List of entity dicts with 'text' and optional 'entity_type'
            
        Returns:
            List of LinkedConcept objects (None for unlinked)
        """
        results = []
        
        for entity in entities:
            linked = await self.link(
                entity["text"],
                entity.get("entity_type"),
            )
            results.append(linked)
        
        return results
    
    async def _link_wikidata(
        self,
        text: str,
        entity_type: Optional[str],
    ) -> Optional[LinkedConcept]:
        """Link to Wikidata entity."""
        try:
            # Use Wikidata search API
            url = "https://www.wikidata.org/w/api.php"
            params = {
                "action": "wbsearchentities",
                "format": "json",
                "language": "en",
                "search": text,
                "limit": 5,
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
            
            if data.get("search"):
                result = data["search"][0]
                
                return LinkedConcept(
                    original_text=text,
                    canonical_name=result.get("label", text),
                    concept_id=result["id"],
                    source="wikidata",
                    confidence=0.8,
                    description=result.get("description"),
                    url=f"https://www.wikidata.org/wiki/{result['id']}",
                    metadata={
                        "entity_type": entity_type,
                        "aliases": result.get("aliases", []),
                    },
                )
        except Exception:
            pass
        
        return None
    
    async def _link_umls(self, text: str) -> Optional[LinkedConcept]:
        """Link to UMLS concept."""
        try:
            # UMLS REST API
            url = f"https://uts-ws.nlm.nih.gov/rest/search/current"
            params = {
                "apiKey": self.umls_api_key,
                "string": text,
                "searchType": "words",
                "returnIdType": "concept",
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
            
            if data.get("result", {}).get("results"):
                result = data["result"]["results"][0]
                
                return LinkedConcept(
                    original_text=text,
                    canonical_name=result["name"],
                    concept_id=result["ui"],
                    source="umls",
                    confidence=0.85,
                    description=None,
                    url=f"https://uts.nlm.nih.gov/uts/umls/concept/{result['ui']}",
                    metadata={
                        "rootSource": result.get("rootSource"),
                    },
                )
        except Exception:
            pass
        
        return None
    
    def link_sync(self, entity_text: str, entity_type: Optional[str] = None) -> Optional[LinkedConcept]:
        """
        Synchronous version of link.
        
        Args:
            entity_text: Entity text to link
            entity_type: Optional entity type
            
        Returns:
            LinkedConcept if found
        """
        cache_key = f"{entity_text}:{entity_type}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        linked_concept = None
        
        if self.use_wikidata:
            linked_concept = self._link_wikidata_sync(entity_text, entity_type)
        
        if linked_concept:
            self._cache[cache_key] = linked_concept
        
        return linked_concept
    
    def _link_wikidata_sync(
        self,
        text: str,
        entity_type: Optional[str],
    ) -> Optional[LinkedConcept]:
        """Synchronous Wikidata linking."""
        try:
            url = "https://www.wikidata.org/w/api.php"
            params = {
                "action": "wbsearchentities",
                "format": "json",
                "language": "en",
                "search": text,
                "limit": 5,
            }
            
            with httpx.Client() as client:
                response = client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
            
            if data.get("search"):
                result = data["search"][0]
                
                return LinkedConcept(
                    original_text=text,
                    canonical_name=result.get("label", text),
                    concept_id=result["id"],
                    source="wikidata",
                    confidence=0.8,
                    description=result.get("description"),
                    url=f"https://www.wikidata.org/wiki/{result['id']}",
                    metadata={"entity_type": entity_type},
                )
        except Exception:
            pass
        
        return None
    
    def clear_cache(self) -> None:
        """Clear the linking cache."""
        self._cache.clear()
