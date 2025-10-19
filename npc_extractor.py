"""
NPC Extractor Module
Uses Azure OpenAI to identify and extract NPC stat blocks from text
"""

import re
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict
from openai import AzureOpenAI

from config import Config


@dataclass
class NPCData:
    """Data structure for NPC information"""
    name: str
    description: Optional[str] = None
    
    # Core RPG stats (generic, can be adapted for different systems)
    level: Optional[int] = None
    hit_points: Optional[str] = None
    armor_class: Optional[str] = None
    
    # Attributes/Abilities
    strength: Optional[int] = None
    dexterity: Optional[int] = None
    constitution: Optional[int] = None
    intelligence: Optional[int] = None
    wisdom: Optional[int] = None
    charisma: Optional[int] = None
    
    # Skills and abilities
    skills: List[str] = field(default_factory=list)
    abilities: List[str] = field(default_factory=list)
    equipment: List[str] = field(default_factory=list)
    
    # Combat
    attacks: List[str] = field(default_factory=list)
    damage_resistances: List[str] = field(default_factory=list)
    damage_immunities: List[str] = field(default_factory=list)
    condition_immunities: List[str] = field(default_factory=list)
    
    # D&D/Pathfinder specific
    challenge_rating: Optional[str] = None
    experience_points: Optional[int] = None
    alignment: Optional[str] = None
    size: Optional[str] = None
    creature_type: Optional[str] = None
    
    # Star Wars D6 specific
    force_sensitive: Optional[bool] = None
    force_points: Optional[int] = None
    dark_side_points: Optional[int] = None
    character_points: Optional[int] = None
    
    # Metadata
    source_file: Optional[str] = None
    source_page: Optional[int] = None
    canonical: bool = True  # True for rulebook NPCs, False for campaign-specific
    game_system: Optional[str] = None
    confidence_score: float = 1.0
    raw_text: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {k: v for k, v in asdict(self).items() if v is not None}


class NPCExtractor:
    """Extracts NPC data from text using Azure OpenAI"""
    
    def __init__(self, config: Config):
        """
        Initialize NPC extractor with Azure OpenAI
        
        Args:
            config: Application configuration
        """
        self.config = config
        
        # Initialize Azure OpenAI client
        self.client = AzureOpenAI(
            azure_endpoint=config.azure_endpoint,
            api_key=config.azure_api_key,
            api_version=config.azure_api_version
        )
        
        self.deployment_name = config.azure_deployment_name
        self.confidence_threshold = config.npc_confidence_threshold
    
    def extract_npcs_from_chunks(
        self,
        chunks: List[str],
        source_file: str
    ) -> List[NPCData]:
        """
        Extract NPCs from text chunks
        
        Args:
            chunks: List of text chunks
            source_file: Source file path
            
        Returns:
            List of extracted NPCs
        """
        npcs = []
        
        # First, identify which chunks contain NPC data
        npc_chunks = self._identify_npc_chunks(chunks)
        
        # Then extract NPCs from identified chunks
        for chunk_indices in npc_chunks:
            # Combine related chunks for full NPC context
            combined_text = ' '.join([chunks[i] for i in chunk_indices])
            
            # Extract NPC data
            extracted_npcs = self._extract_npc_from_text(combined_text, source_file)
            npcs.extend(extracted_npcs)
        
        return npcs
    
    def _identify_npc_chunks(self, chunks: List[str]) -> List[List[int]]:
        """
        Identify which chunks contain NPC stat blocks
        
        Args:
            chunks: List of text chunks
            
        Returns:
            List of chunk index groups that contain NPCs
        """
        npc_chunk_groups = []
        
        # Use pattern matching first for efficiency
        npc_patterns = [
            r'(?i)\b(?:str|strength)\s*:?\s*\d+',
            r'(?i)\b(?:dex|dexterity)\s*:?\s*\d+',
            r'(?i)\b(?:con|constitution)\s*:?\s*\d+',
            r'(?i)\b(?:int|intelligence)\s*:?\s*\d+',
            r'(?i)\b(?:wis|wisdom)\s*:?\s*\d+',
            r'(?i)\b(?:cha|charisma)\s*:?\s*\d+',
            r'(?i)\bhit\s*points?\s*:?\s*\d+',
            r'(?i)\barmor\s*class\s*:?\s*\d+',
            r'(?i)\bchallenge\s*(?:rating)?\s*(?:\()?cr(?:\))?\s*:?\s*[\d/]+',
            r'(?i)\b(?:level|hd|hit\s*dice)\s*:?\s*\d+',
        ]
        
        potential_chunks = []
        for i, chunk in enumerate(chunks):
            score = 0
            for pattern in npc_patterns:
                if re.search(pattern, chunk):
                    score += 1
            
            if score >= 2:  # At least 2 pattern matches
                potential_chunks.append(i)
        
        # Group consecutive chunks
        if potential_chunks:
            current_group = [potential_chunks[0]]
            
            for i in potential_chunks[1:]:
                if i - current_group[-1] <= 1:  # Consecutive or one gap
                    current_group.append(i)
                else:
                    npc_chunk_groups.append(current_group)
                    current_group = [i]
            
            npc_chunk_groups.append(current_group)
        
        return npc_chunk_groups
    
    def _extract_npc_from_text(
        self,
        text: str,
        source_file: str
    ) -> List[NPCData]:
        """
        Extract NPC data from text using Azure OpenAI
        
        Args:
            text: Text potentially containing NPC data
            source_file: Source file path
            
        Returns:
            List of extracted NPCs
        """
        # Prepare the prompt for Azure OpenAI
        system_prompt = """You are an expert at extracting NPC (Non-Player Character) stat blocks from RPG rulebooks and adventures.
        Identify and extract structured NPC data from the provided text.
        
        Return a JSON array of NPCs found, with each NPC having these fields (use null for missing data):
        {
            "name": "NPC name",
            "description": "Brief description",
            "level": integer or null,
            "hit_points": "HP value or formula",
            "armor_class": "AC value",
            "strength": integer or null,
            "dexterity": integer or null,
            "constitution": integer or null,
            "intelligence": integer or null,
            "wisdom": integer or null,
            "charisma": integer or null,
            "skills": ["skill1", "skill2"],
            "abilities": ["ability1", "ability2"],
            "equipment": ["item1", "item2"],
            "attacks": ["attack description"],
            "challenge_rating": "CR value",
            "alignment": "alignment",
            "size": "size category",
            "creature_type": "type",
            "game_system": "D&D 5e/Pathfinder/Star Wars D6/etc",
            "confidence_score": 0.0 to 1.0
        }
        
        For Star Wars D6, also include:
        - force_sensitive: boolean
        - force_points: integer
        - dark_side_points: integer
        - character_points: integer
        
        Only extract clearly defined NPCs with stat blocks, not just mentioned characters.
        If no NPCs are found, return an empty array.
        """
        
        user_prompt = f"Extract all NPC stat blocks from this text:\n\n{text[:3000]}"  # Limit text size
        
        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,  # Low temperature for consistent extraction
                response_format={"type": "json_object"}
            )
            
            # Parse the response
            content = response.choices[0].message.content
            result = json.loads(content)
            
            # Handle both single NPC and array formats
            if isinstance(result, dict) and 'npcs' in result:
                npc_list = result['npcs']
            elif isinstance(result, list):
                npc_list = result
            elif isinstance(result, dict) and 'name' in result:
                npc_list = [result]
            else:
                npc_list = []
            
            # Convert to NPCData objects
            npcs = []
            for npc_dict in npc_list:
                # Check confidence score
                confidence = npc_dict.get('confidence_score', 0.8)
                if confidence < self.confidence_threshold:
                    continue
                
                # Create NPCData object
                npc = NPCData(
                    name=npc_dict.get('name', 'Unknown'),
                    description=npc_dict.get('description'),
                    level=npc_dict.get('level'),
                    hit_points=npc_dict.get('hit_points'),
                    armor_class=npc_dict.get('armor_class'),
                    strength=npc_dict.get('strength'),
                    dexterity=npc_dict.get('dexterity'),
                    constitution=npc_dict.get('constitution'),
                    intelligence=npc_dict.get('intelligence'),
                    wisdom=npc_dict.get('wisdom'),
                    charisma=npc_dict.get('charisma'),
                    skills=npc_dict.get('skills', []),
                    abilities=npc_dict.get('abilities', []),
                    equipment=npc_dict.get('equipment', []),
                    attacks=npc_dict.get('attacks', []),
                    challenge_rating=npc_dict.get('challenge_rating'),
                    alignment=npc_dict.get('alignment'),
                    size=npc_dict.get('size'),
                    creature_type=npc_dict.get('creature_type'),
                    force_sensitive=npc_dict.get('force_sensitive'),
                    force_points=npc_dict.get('force_points'),
                    dark_side_points=npc_dict.get('dark_side_points'),
                    character_points=npc_dict.get('character_points'),
                    source_file=source_file,
                    canonical=True,  # Assuming rulebook content
                    game_system=npc_dict.get('game_system'),
                    confidence_score=confidence,
                    raw_text=text[:500]  # Store first 500 chars for reference
                )
                
                npcs.append(npc)
            
            return npcs
            
        except Exception as e:
            print(f"Error extracting NPCs: {e}")
            return []
    
    def extract_npc_from_structured_text(self, text: str, source_file: str) -> Optional[NPCData]:
        """
        Extract NPC from well-structured stat block text
        
        Args:
            text: Structured stat block text
            source_file: Source file path
            
        Returns:
            NPCData or None
        """
        npc = NPCData(name="Unknown", source_file=source_file)
        
        # Extract name (usually first line or after "Name:")
        name_match = re.search(r'^([A-Z][^:\n]+)$', text, re.MULTILINE)
        if not name_match:
            name_match = re.search(r'(?i)name\s*:\s*(.+)', text)
        if name_match:
            npc.name = name_match.group(1).strip()
        
        # Extract attributes (D&D style)
        attr_patterns = {
            'strength': r'(?i)(?:str|strength)\s*:?\s*(\d+)',
            'dexterity': r'(?i)(?:dex|dexterity)\s*:?\s*(\d+)',
            'constitution': r'(?i)(?:con|constitution)\s*:?\s*(\d+)',
            'intelligence': r'(?i)(?:int|intelligence)\s*:?\s*(\d+)',
            'wisdom': r'(?i)(?:wis|wisdom)\s*:?\s*(\d+)',
            'charisma': r'(?i)(?:cha|charisma)\s*:?\s*(\d+)',
        }
        
        for attr, pattern in attr_patterns.items():
            match = re.search(pattern, text)
            if match:
                setattr(npc, attr, int(match.group(1)))
        
        # Extract HP and AC
        hp_match = re.search(r'(?i)hit\s*points?\s*:?\s*([\d\s+\-*/()d]+)', text)
        if hp_match:
            npc.hit_points = hp_match.group(1).strip()
        
        ac_match = re.search(r'(?i)(?:armor\s*class|ac)\s*:?\s*(\d+)', text)
        if ac_match:
            npc.armor_class = ac_match.group(1)
        
        # Extract CR
        cr_match = re.search(r'(?i)(?:challenge|cr)\s*(?:rating)?\s*:?\s*([\d/]+)', text)
        if cr_match:
            npc.challenge_rating = cr_match.group(1)
        
        # Extract alignment
        alignment_match = re.search(
            r'(?i)(lawful|neutral|chaotic)\s*(good|neutral|evil)',
            text
        )
        if alignment_match:
            npc.alignment = f"{alignment_match.group(1)} {alignment_match.group(2)}"
        
        # Extract skills (looking for comma-separated lists after "Skills:")
        skills_match = re.search(r'(?i)skills?\s*:?\s*([^\n]+)', text)
        if skills_match:
            skills_text = skills_match.group(1)
            npc.skills = [s.strip() for s in re.split(r'[,;]', skills_text)]
        
        # Validate that we found enough data to consider this an NPC
        if npc.name == "Unknown" and not any([
            npc.hit_points, npc.armor_class, npc.strength,
            npc.dexterity, npc.constitution
        ]):
            return None
        
        npc.raw_text = text[:500]
        return npc
    
    def detect_game_system(self, text: str) -> Optional[str]:
        """
        Detect which game system the content is for
        
        Args:
            text: Text to analyze
            
        Returns:
            Game system name or None
        """
        systems = {
            'D&D 5e': [
                r'(?i)proficiency\s+bonus', r'(?i)advantage', r'(?i)disadvantage',
                r'(?i)inspiration', r'(?i)death\s+saves?'
            ],
            'Pathfinder': [
                r'(?i)base\s+attack\s+bonus', r'(?i)cmb', r'(?i)cmd',
                r'(?i)fortitude', r'(?i)reflex', r'(?i)will'
            ],
            'Star Wars D6': [
                r'(?i)force\s+points?', r'(?i)dark\s+side\s+points?',
                r'(?i)character\s+points?', r'(?i)\d+D(?:\+\d+)?'
            ],
            'Starfinder': [
                r'(?i)stamina\s+points?', r'(?i)resolve\s+points?',
                r'(?i)eac', r'(?i)kac'
            ]
        }
        
        for system, patterns in systems.items():
            matches = sum(1 for p in patterns if re.search(p, text))
            if matches >= 2:
                return system
        
        return None
