#!/usr/bin/env python3
"""Temporarily disable CrewAI to get the backend running."""

import os
from pathlib import Path


def comment_out_nutrient_aware_imports():
    """Comment out the nutrient-aware service imports that use CrewAI."""

    files_to_modify = [
        {
            "path": "backend_gateway/routers/chat_router.py",
            "old": "from backend_gateway.services.nutrient_aware_crew_service import NutrientAwareCrewService",
            "new": "# from backend_gateway.services.nutrient_aware_crew_service import NutrientAwareCrewService  # Temporarily disabled",
        },
        {
            "path": "backend_gateway/routers/chat_router.py",
            "old": "def get_nutrient_aware_crew_service():",
            "new": "# def get_nutrient_aware_crew_service():",
        },
        {
            "path": "backend_gateway/routers/chat_router.py",
            "old": "    return NutrientAwareCrewService()",
            "new": "    # return NutrientAwareCrewService()",
        },
        {
            "path": "backend_gateway/routers/nutrition_router.py",
            "old": "from backend_gateway.services.nutrient_aware_crew_service import NutrientAwareCrewService",
            "new": "# from backend_gateway.services.nutrient_aware_crew_service import NutrientAwareCrewService  # Temporarily disabled",
        },
        {
            "path": "backend_gateway/routers/nutrition_router.py",
            "old": "nutrient_crew_service = NutrientAwareCrewService()",
            "new": "# nutrient_crew_service = NutrientAwareCrewService()  # Temporarily disabled",
        },
    ]

    for file_info in files_to_modify:
        file_path = Path(file_info["path"])
        if file_path.exists():
            with open(file_path, "r") as f:
                content = f.read()

            if file_info["old"] in content and not file_info["new"] in content:
                content = content.replace(file_info["old"], file_info["new"])
                with open(file_path, "w") as f:
                    f.write(content)
                print(f"✅ Modified {file_path}")
            else:
                print(f"⏭️  Skipped {file_path} (already modified or not found)")


def comment_out_nutrient_endpoints():
    """Comment out endpoints that depend on nutrient-aware service."""

    # Read chat_router.py
    chat_router_path = Path("backend_gateway/routers/chat_router.py")
    with open(chat_router_path, "r") as f:
        lines = f.readlines()

    # Find and comment out the nutrient endpoint
    in_nutrient_endpoint = False
    modified_lines = []

    for line in lines:
        if '@router.post("/message-with-nutrition"' in line:
            in_nutrient_endpoint = True
            modified_lines.append("# " + line)
        elif in_nutrient_endpoint:
            if line.strip() == "" or (line[0] not in [" ", "\t"] and line.strip() != ""):
                # End of function
                in_nutrient_endpoint = False
                modified_lines.append(line)
            else:
                modified_lines.append("# " + line)
        else:
            modified_lines.append(line)

    with open(chat_router_path, "w") as f:
        f.writelines(modified_lines)

    print("✅ Commented out nutrient-aware endpoints")


def main():
    """Main function."""
    print("🔧 Temporarily disabling CrewAI components...")

    comment_out_nutrient_aware_imports()
    comment_out_nutrient_endpoints()

    print("\n✅ Done! The backend should now start without CrewAI issues.")
    print("\n📋 Next steps:")
    print(
        "1. Start backend: source venv/bin/activate && python -m uvicorn backend_gateway.app:app --host 0.0.0.0 --port 8001"
    )
    print("2. Test: python test_chat_endpoint.py")
    print("\n⚠️  Note: Nutrient-aware features are temporarily disabled")


if __name__ == "__main__":
    main()
