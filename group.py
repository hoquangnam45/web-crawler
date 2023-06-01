class Group:    
    def __init__(self, id: str, linkedPageIds: list[str], linkGroupIds: list[str]):
        self.id = id
        self.linkedPageIds = linkedPageIds
        self.linkedGroupIds = linkGroupIds