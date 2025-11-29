# src/comfyui_legion_power/nodes/legion_join_all.py

from ..core.legion_datatypes import LEGION_CAMPAIGN


class LegionJoinAllNode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {"campaign_1": (LEGION_CAMPAIGN,)},
            "optional": {
                "campaign_2": (LEGION_CAMPAIGN,),
                "campaign_3": (LEGION_CAMPAIGN,),
                "campaign_4": (LEGION_CAMPAIGN,),
            }
        }

    RETURN_TYPES = (LEGION_CAMPAIGN, LEGION_CAMPAIGN, LEGION_CAMPAIGN, LEGION_CAMPAIGN)
    RETURN_NAMES = ("campaign_1", "campaign_2", "campaign_3", "campaign_4")
    FUNCTION = "join_all_campaigns"
    CATEGORY = "Legion"
    OUTPUT_NODE = True

    def join_all_campaigns(self, **kwargs):
        campaigns = [c for c in kwargs.values() if c is not None]
        print(f"[Legion Join All] Joining all {len(campaigns)} campaigns...")

        # Wait for all async execution threads
        for i, campaign in enumerate(campaigns, 1):
            if hasattr(campaign, 'execution_thread') and campaign.execution_thread:
                print(f"[Legion Join All] Waiting for campaign {i}/{len(campaigns)} (ID: {campaign.campaign_id})...")
                campaign.execution_thread.join()  # Block until this thread completes
                print(f"[Legion Join All] Campaign {i}/{len(campaigns)} completed")

        # Check all campaigns succeeded
        for campaign in campaigns:
            if campaign.status == "FAILED":
                raise RuntimeError(f"Campaign {campaign.campaign_id} failed during execution")
            if campaign.status not in ["COMPLETED", "DRY_RUN_COMPLETE"]:
                raise RuntimeError(f"Campaign {campaign.campaign_id} has unexpected status: {campaign.status}")

        print(f"[Legion Join All] All {len(campaigns)} campaigns completed successfully")

        # Return the campaign handles in the same order they came in
        return (
            kwargs.get("campaign_1"),
            kwargs.get("campaign_2"),
            kwargs.get("campaign_3"),
            kwargs.get("campaign_4"),
        )
