from crewai import Crew
import logging
import os
from src.agents.bite_cam import BiteCam
from src.agents.food_categorizer import FoodCategorizer
from src.agents.unit_canon import UnitCanon
from src.agents.fresh_filter import FreshFilter

logger = logging.getLogger(__name__)

class PantryNormalizationCrew(Crew):
    """
    Pantry Normalization Crew: Processes raw food items into normalized, categorized inventory.
    
    Flow: BiteCam -> FoodCategorizer -> UnitCanon -> FreshFilter
    """
    
    def __init__(self):
        super().__init__()
        self.bite_cam = BiteCam()
        self.food_categorizer = FoodCategorizer()
        self.unit_canon = UnitCanon()
        self.fresh_filter = FreshFilter()
        
        # Environment flags
        self.enable_bite_cam = os.getenv("ENABLE_BITE_CAM", "true").lower() == "true"
        self.enable_fresh_filter = os.getenv("ENABLE_FRESH_FILTER_AGENT", "true").lower() == "true"
        
        logger.info(f"PantryNormalizationCrew initialized - BiteCam: {self.enable_bite_cam}, FreshFilter: {self.enable_fresh_filter}")

    async def run(self, input_data: dict):
        """
        Run the pantry normalization crew.
        
        Args:
            input_data: {
                "image_b64": str (optional) - Base64 encoded image for BiteCam
                "raw_items": list[dict] (optional) - Pre-extracted raw items [{"raw_line": "2 lb chicken"}]
                "user_id": str (optional) - User ID for personalization
                "freshness_days": int (optional) - Days threshold for freshness filter
            }
            
        Returns:
            list[dict]: Normalized pantry items with canonical units and freshness data
        """
        try:
            logger.info("Starting pantry normalization workflow")
            
            # Step 1: Extract items from image (if BiteCam enabled and image provided)
            if self.enable_bite_cam and input_data.get("image_b64"):
                logger.info("Running BiteCam for image processing")
                bite_cam_result = await self.bite_cam.run(input_data["image_b64"])
                raw_items = [{"raw_line": line} for line in bite_cam_result.get("raw_lines", [])]
            elif input_data.get("raw_items"):
                logger.info("Using provided raw items")
                raw_items = input_data["raw_items"]
            else:
                logger.warning("No image or raw items provided for pantry normalization")
                return []

            if not raw_items:
                logger.warning("No raw items to process")
                return []

            logger.info(f"Processing {len(raw_items)} raw items")

            # Step 2: Categorize foods using USDA database
            logger.info("Running FoodCategorizer")
            categorized_items = await self.food_categorizer.run(raw_items)
            
            if not categorized_items:
                logger.warning("No items were successfully categorized")
                return []

            logger.info(f"Categorized {len(categorized_items)} items")

            # Step 3: Canonicalize units
            logger.info("Running UnitCanon for unit standardization")
            canonicalized_items = await self.unit_canon.run(categorized_items)
            
            if not canonicalized_items:
                logger.warning("No items survived unit canonicalization")
                return []

            logger.info(f"Canonicalized {len(canonicalized_items)} items")

            # Step 4: Apply freshness filter (if enabled)
            if self.enable_fresh_filter:
                logger.info("Running FreshFilter")
                user_id = input_data.get("user_id")
                freshness_days = input_data.get("freshness_days", 7)
                final_items = await self.fresh_filter.run(canonicalized_items, user_id, freshness_days)
            else:
                logger.info("FreshFilter disabled, skipping")
                final_items = canonicalized_items

            logger.info(f"Pantry normalization completed: {len(final_items)} final items")
            
            # Add crew metadata
            for item in final_items:
                item["processed_by"] = "pantry_normalization_crew"
                item["processing_timestamp"] = self._get_timestamp()

            return final_items

        except Exception as e:
            logger.error(f"Pantry normalization crew failed: {e}")
            raise

    def _get_timestamp(self) -> str:
        """Get current timestamp for processing metadata"""
        from datetime import datetime
        return datetime.now().isoformat()

    async def health_check(self) -> dict:
        """Check the health of all crew agents"""
        health_status = {
            "crew": "pantry_normalization",
            "status": "healthy",
            "agents": {},
            "enabled_agents": []
        }
        
        try:
            # Check agent availability
            agents_to_check = [
                ("food_categorizer", self.food_categorizer, True),
                ("unit_canon", self.unit_canon, True),
                ("bite_cam", self.bite_cam, self.enable_bite_cam),
                ("fresh_filter", self.fresh_filter, self.enable_fresh_filter)
            ]
            
            for agent_name, agent_instance, is_enabled in agents_to_check:
                if is_enabled:
                    health_status["enabled_agents"].append(agent_name)
                    # Basic health check - ensure agent has required methods
                    if hasattr(agent_instance, 'run'):
                        health_status["agents"][agent_name] = "healthy"
                    else:
                        health_status["agents"][agent_name] = "unhealthy - missing run method"
                        health_status["status"] = "degraded"
                else:
                    health_status["agents"][agent_name] = "disabled"

            return health_status

        except Exception as e:
            health_status["status"] = "unhealthy"
            health_status["error"] = str(e)
            return health_status

    def get_workflow_description(self) -> dict:
        """Get description of the workflow"""
        return {
            "name": "Pantry Normalization Crew",
            "description": "Processes raw food items into normalized, categorized inventory",
            "workflow": [
                {
                    "step": 1,
                    "agent": "BiteCam",
                    "description": "Extract food items from images using GPT-4 vision",
                    "enabled": self.enable_bite_cam,
                    "input": "Base64 encoded image",
                    "output": "List of raw text lines describing food items"
                },
                {
                    "step": 2,
                    "agent": "FoodCategorizer", 
                    "description": "Match items to USDA food database for categorization",
                    "enabled": True,
                    "input": "Raw text lines",
                    "output": "Categorized items with USDA food data"
                },
                {
                    "step": 3,
                    "agent": "UnitCanon",
                    "description": "Standardize quantities and units using Pint library",
                    "enabled": True,
                    "input": "Categorized items with raw quantities",
                    "output": "Items with canonical units and quantities"
                },
                {
                    "step": 4,
                    "agent": "FreshFilter",
                    "description": "Filter items by freshness and add expiration estimates",
                    "enabled": self.enable_fresh_filter,
                    "input": "Canonicalized items",
                    "output": "Fresh items with expiration data"
                }
            ],
            "environment_flags": {
                "ENABLE_BITE_CAM": self.enable_bite_cam,
                "ENABLE_FRESH_FILTER_AGENT": self.enable_fresh_filter
            }
        }