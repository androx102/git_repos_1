import random
from collections import defaultdict

class karakan():
    def __init__(self):
        self.id = random.random()
    
    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, __value: object) -> bool:
        return self.id == __value.id




my_dict = defaultdict(list)    



karakan_1 = karakan()
karakan_2 = karakan()



my_dict[karakan_1].append(5)     #.append(5)
my_dict[karakan_1].append(6)

print()
