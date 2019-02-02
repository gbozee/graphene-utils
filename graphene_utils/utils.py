import itertools

import graphene
from graphene.types.generic import GenericScalar

# from .. import services


def get_graphene_type(*args):
    options = {
        str: graphene.String,
        bool: graphene.Boolean,
        int: graphene.Int,
        float: graphene.Float,
        "json": GenericScalar,
        list: graphene.List,
        object: graphene.Field,
    }
    kwargs = {}
    if len(args) > 1:
        kwargs = args[1]
    try:
        if isinstance(kwargs, dict):
            result = options[args[0]](**kwargs)
        else:
            result = options[args[0]](kwargs)
    except KeyError:
        result = args[0]
    except TypeError:
        result = args[0]
    return result


def getFunc(key, name):
    def func(self, info, **kwargs):
        if hasattr(self, key):
            return getattr(self, key)
        return self.get(key)

    func.__name__ = name
    return func


def get_graphene_types(values):
    return {key[0]: get_graphene_type(*key[1:]) for key in values}


def createGrapheneClass(className, values):
    """This class helps in creating graphene models in which the
    keys are the fields and the values are what the resolve function
    returns
    """
    class_fields = {key[0]: get_graphene_type(*key[1:]) for key in values}
    cls = type(className, (graphene.ObjectType, ), class_fields)
    for key in values:
        if type(key) == tuple and len(key) > 2:
            name = f"resolve_{key[0]}"
            func = lambda self, info, **kwargs: key[-1](self)
            func.__name__ = name
        else:
            name = f"resolve_{key[0]}"
            func = getFunc(key[0], name)
        setattr(cls, name, func)
    return cls


def createGrapheneInputClass(className, values):
    class_fields = {key[0]: get_graphene_type(*key[1:]) for key in values}
    cls = type(className, (graphene.InputObjectType, ), class_fields)
    return cls


def dict_from_list(obj, _list):
    result = {}
    for key in _list:
        if isinstance(key, tuple):
            result[key[0]] = getattr(obj, key[1])
        else:
            if isinstance(key, dict):
                new_key = list(key.keys())[0]
                new_value = list(key.values())[0]
                result[new_key] = obj.get(new_key, new_value)
            else:
                if hasattr(obj, key):
                    result[key] = getattr(obj, key)
                else:
                    result[key] = obj.get(key)
    return result


class BaseMutation(object):
    fields = []
    form_fields = {}
    service_func_name = ""
    stop_point = ""

    def build_form_fields(self,
                          key,
                          fields=None,
                          name=None,
                          is_list=False,
                          **kwargs):
        for i in [fields]:
            if not i:
                raise NotImplementedError(f"Missing parameter for {key} ")
        if not name:
            return (key, get_graphene_type(*fields, kwargs))
        klass = type(name, (graphene.InputObjectType, ),
                     get_graphene_types(fields))
        if is_list:
            return (key, graphene.List(klass, **kwargs))
        return (key, klass(**kwargs))

    def get_form_fields(self):
        result = []
        for key, values in self.form_fields.items():
            if isinstance(values, dict) and values.get("fields"):
                result.append(self.build_form_fields(key, **values))
            else:
                result.append((key, values))
        return dict(result)

    def get_fields(self):
        return get_graphene_types(self.fields)

    def get_form(self):
        raise NotImplementedError

    def callback(self, *args, **kwargs):
        return self.form.save(*args, **kwargs)

    def mutate(self, *args, **kwargs):
        [klass, _, info] = args
        return authenticated_result(klass, info, self.callback, **kwargs)

    def service_action(self, user, param, fields=None, no_error=False):
        new_data = (param, )
        if isinstance(param, tuple):
            new_data = param
        ss = services.NewTutorApplicationService(user)
        func = getattr(ss, self.service_func_name)
        errors = None
        result = func(*new_data)

        self.update_stop_points(ss, user)

        data = {}
        if isinstance(result, tuple):
            user = result[0]
            errors = result[1]
        data = result
        if fields:
            data = UserToDict(user).to_dict()
            if isinstance(fields, list):
                data = dict_from_list(data, fields)
            if fields == "user":
                data = {"user": data}
        if no_error:
            return {**data}, result[1]
        return {**data, "errors": errors}

    @classmethod
    def Field(cls):
        m_instance = cls()
        klass = type(
            cls.__name__,
            (graphene.Mutation, ),
            {
                **m_instance.get_fields(),
                "Arguments":
                type("Arguments", (), m_instance.get_form_fields()),
                "mutate":
                m_instance.mutate,
            },
        )
        instance = klass.Field()
        instance.resolver = lambda *args, **kwargs: m_instance.mutate(
            klass, *args, **kwargs
        )
        return instance


def authenticated_result(cls, info, callback, **kwargs):
    result = callback(info, **kwargs)
    return cls(**result)
