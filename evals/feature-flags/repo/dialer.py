from campaigns import finish


def next_calls(campaign, slots):
    if campaign.status != "running":
        return []
    pending = [n for n in campaign.contacts if n not in campaign.dialed]
    batch = pending[:slots]
    campaign.dialed.extend(batch)
    if not pending[slots:]:
        finish(campaign)
    return batch
