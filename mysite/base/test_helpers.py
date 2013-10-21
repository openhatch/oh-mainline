from django.http import QueryDict


class QueryDictHelper():

    @classmethod
    def create_query_dict(cls, *args):
        queryDict = QueryDict('').copy()

        for arg in args:
            if isinstance(arg, tuple):
                if isinstance(arg[1], list):
                    # (k, [v1, v2, ..., vn])
                    queryDict.setlist(arg[0], arg[1])
                else:
                    # (k, v)
                    queryDict.update({arg[0]: arg[1]})
            else:
                # { k: v }
                queryDict.update(arg)

        return queryDict
