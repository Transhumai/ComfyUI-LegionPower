from .nodes.legion_config import LegionConfigNode
from .nodes.legion_master import LegionMasterNode, LegionMasterNode3, LegionMasterNode6
from .nodes.legion_warmup import LegionWarmupNode
from .nodes.legion_join import LegionJoinNode
from .nodes.legion_join_all import LegionJoinAllNode
from .nodes.legion_exporter import LegionExporterNode
from .nodes.legion_importer import LegionImporterNode

NODE_CLASS_MAPPINGS = {
    "LegionConfig": LegionConfigNode,
    "LegionWarmup": LegionWarmupNode,
    "LegionMaster3": LegionMasterNode3,
    "LegionMaster6": LegionMasterNode6,
    "LegionMaster": LegionMasterNode,
    "LegionJoin": LegionJoinNode,
    "LegionJoinAll": LegionJoinAllNode,
    "LegionExporter": LegionExporterNode,
    "LegionImporter": LegionImporterNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LegionConfig": "Legion: Configuration",
    "LegionWarmup": "Legion: Warmupper",
    "LegionMaster3": "Legion: Master (3 channels)",
    "LegionMaster6": "Legion: Master (6 channels)",
    "LegionMaster": "Legion: Master (12 channels)",
    "LegionJoin": "Legion: Join Campaign",
    "LegionJoinAll": "Legion: Join All Campaigns",
    "LegionExporter": "Legion: Exporter",
    "LegionImporter": "Legion: Importer",
}

# Messaggio di log aggiornato
#print("------------------------------------------")
#print("ComfyUI-LegionPower: Custom nodes loaded successfully.")
#print("  - Legion: Configuration")
#print("  - Legion: Warmupper")
#print("  - Legion: Master")
#print("  - Legion: Join Campaign")
#print("  - Legion: Join All Campaigns")
#print("  - Legion: Exporter")
#print("  - Legion: Importer")
#print("------------------------------------------")

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']