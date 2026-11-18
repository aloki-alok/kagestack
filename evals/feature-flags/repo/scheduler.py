from campaigns import start, visible


def morning(campaigns):
    for campaign in visible(campaigns):
        if campaign.status != "done":
            start(campaign)
