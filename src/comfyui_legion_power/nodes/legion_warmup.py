from ..nodes.legion_master import LegionMasterNode
from ..core.legion_datatypes import LEGION_CONFIG, LEGION_CAMPAIGN


class LegionWarmupNode(LegionMasterNode):
    """
    A simplified version of the Master node that only performs a warmup.
    It ensures a worker is running for the given config and passes on a live campaign handle.
    """
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "legion_config": (LEGION_CONFIG,),
            }
        }

    RETURN_TYPES = (LEGION_CAMPAIGN,)
    RETURN_NAMES = ("legion_campaign",)
    FUNCTION = "warmup" # Use a different function name for clarity

    def warmup(self, legion_config):
        # Call the parent (Master) execute function with fixed parameters
        # and return only the first value (the campaign).
        campaign, *_ = self.execute(legion_config=legion_config, just_warmup = True)
        return (campaign,)


