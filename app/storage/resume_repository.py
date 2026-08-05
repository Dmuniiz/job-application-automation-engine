import json
import logging
from typing import Dict, Optional, List
from pathlib import Path
from app.models.resume import ResumeProfile

logger = logging.getLogger(__name__)

class ResumeRepository:
    """
    Manages loading, storing, and retrieving multiple canonical resume profiles.
    """

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self._profiles: Dict[str, ResumeProfile] = {}

    def register_profile(self, profile: ResumeProfile) -> None:
        """Register or update an in-memory profile."""
        self._profiles[profile.profile_id] = profile
        logger.info(f"Registered resume profile: '{profile.profile_id}' ({profile.target_role_category})")

    def get_profile(self, profile_id: str) -> Optional[ResumeProfile]:
        """Fetch a specific resume profile by ID."""
        return self._profiles.get(profile_id)

    def list_profile_ids(self) -> List[str]:
        """Returns all available profile IDs."""
        return list(self._profiles.keys())

    def save_to_disk(self, profile_id: str) -> None:
        """Persists profile to JSON disk storage."""
        profile = self.get_profile(profile_id)
        if not profile:
            raise ValueError(f"Profile {profile_id} not found.")
        
        self.data_dir.mkdir(parents=True, exist_ok=True)
        file_path = self.data_dir / f"resume_{profile_id}.json"
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(profile.model_dump_json(indent=2))
        logger.info(f"Saved profile '{profile_id}' to {file_path}")

    def load_from_disk(self, profile_id: str) -> Optional[ResumeProfile]:
        """Loads profile from JSON file."""
        file_path = self.data_dir / f"resume_{profile_id}.json"
        if not file_path.exists():
            return None
        
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            profile = ResumeProfile(**data)
            self.register_profile(profile)
            return profile