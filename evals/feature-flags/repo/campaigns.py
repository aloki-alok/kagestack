from dataclasses import dataclass, field


@dataclass
class Campaign:
    id: int
    name: str
    status: str = "draft"
    is_archived: bool = False
    contacts: list = field(default_factory=list)
    dialed: list = field(default_factory=list)


def start(campaign):
    campaign.status = "running"


def finish(campaign):
    campaign.status = "done"


def archive(campaign):
    campaign.is_archived = True


def visible(campaigns):
    return [c for c in campaigns if not c.is_archived]
