

class Inventory:
    def __init__(self,size):
        self.inventory = {}
        self.size = size
        for i in range(size):
            self.inventory[i] = []

    def add_item(self,item,slot,should_be_empty=False):
        if should_be_empty == False:
            self.inventory[slot].append(item)
        else:
            if len(self.inventory[slot]) == 0:
                self.inventory[slot].append(item)
                return True
            else:
                return False

    def remove_item(self,slot,return_item=False):
        if return_item == False:
            del self.inventory[slot]
        else:
            item = self.inventory[slot]
            del self.inventory[slot]
            return item

    def get_item(self,slot):
        return self.inventory[slot]

    def free_slots(self):
        free_slots = []
        for slot in self.inventory:
            if len(self.inventory[slot]) == 0:
                free_slots.append(slot)

        return free_slots

    def get_all_items(self):
        return self.inventory           

    def clear(self):
        self.inventory = {}
