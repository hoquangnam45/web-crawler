from post import Post
from listing import Listing
from house import House

def semanticAnalysis(post: Post) -> Listing:
    house: House = House()
    return Listing(house)
     