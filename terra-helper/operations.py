class Lists:
    @staticmethod
    def difference(list1, list2):
        return list(set(list1) - set(list2))

    @staticmethod
    def intersection(list1, list2):
        return list(set(list1).intersection(set(list2)))

    @classmethod
    def unpack(cls, list_of_lists):
        new_list = []
        for item in list_of_lists:
            if isinstance(item, list):
                new_list.extend(cls.unpack_while_loop(item))
            else:
                new_list.extend([item])
        return new_list

    @classmethod
    def unpack_while_loop(cls, list_of_lists):
        unpacked_list = cls.unpack(list_of_lists)
        list_elements = [item for item in unpacked_list if isinstance(item, list)]
        while list_elements:
            unpacked_list = cls.unpack(unpacked_list)
            list_elements = [item for item in unpacked_list if isinstance(item, list)]
        return unpacked_list
