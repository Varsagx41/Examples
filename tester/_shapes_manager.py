import _shapes
import inspect
from _generators import ChoiceGenerator


class ShapesTree(object):
    edges = {}
    redges = {}
    counters = {}
    enabled = []
    settings = {}
    generated = {}
    _objects = {}

    def __init__(self):
        shapes = []
        for key, value in _shapes.__dict__.iteritems():
            if type(value) == type:
                if _shapes.Shape in inspect.getmro(value)[1:]:
                    shapes.append(value)

        bonds = {}
        for shape in shapes:
            sobj = shape()
            bonds[shape] = sobj._meta['bonds']

        for vertex, bond in bonds.iteritems():
            if bond:
                for fieldname, value in bond.iteritems():
                    if value[0] in self.edges:
                        self.edges[value[0]].append((value[1], fieldname,
                                                     vertex))
                    else:
                        self.edges[value[0]] = [(value[1], fieldname, vertex)]

                    if vertex in self.redges:
                        self.redges[vertex].append((fieldname, value[1],
                                                    value[0]))
                    else:
                        self.redges[vertex] = [(fieldname, value[1], value[0])]

                    if value[0] in self.counters:
                        self.counters[value[0]][0] += 1
                    else:
                        self.counters[value[0]] = [1, 0]

                    if vertex in self.counters:
                        self.counters[vertex][1] += 1
                    else:
                        self.counters[vertex] = [0, 1]

    def get_object(self, shape):
        if shape not in self._objects:
            self._objects[shape] = shape()
        return self._objects[shape]

    def get_root(self):
        counters = tuple(self.counters.items())
        counters = sorted(counters, key=lambda x: (x[1][1], x[1][0]))
        return counters[0][0]

    def get_childs(self, vertex):
        if type(vertex) == list or type(vertex) == tuple:
            childs = set(map(lambda x: x[2], self.edges.get(vertex[0], set())))
            for i in range(1, len(vertex)):
                childs &= set(map(lambda x: x[2], self.edges.get(vertex[i], set())))
            return list(childs)
        else:
            return list(set(map(lambda x: x[2], self.edges.get(vertex, []))))

    def get_parents(self, vertex):
        return list(set(map(lambda x: x[2], self.redges.get(vertex, []))))

    def get_all(self):
        return list(set(self.edges.keys() + self.redges.keys()))

    def get_edges(self, parent, child):
        edges = filter(lambda x: x[2] == child, self.edges.get(parent, []))
        return map(lambda x: (x[0], x[1], parent in self.enabled and child in self.enabled), edges)

    def enable_all(self):
        self.enabled = self.get_all()

    def disable_all(self):
        self.enabled = []

    def enable(self, shape):
        if shape not in self.enabled:
            if shape in self.edges or shape in self.redges:
                self.enabled.append(shape)

    def disable(self, shape):
        if shape in self.enabled:
            self.enabled.remove(shape)

    def is_enabled(self, shape):
        return shape in self.enabled

    def set_amount(self, shape, amount):
        if shape in self.settings:
            self.settings[shape]['amount'] = amount
        else:
            self.settings[shape] = {'amount': amount}

    def del_amount(self, shape):
        if shape in self.settings:
            self.settings[shape].pop('amount', None)

    def get_amount(self, shape, multi=1):
        amount = -1
        if shape in self.settings:
            if 'amount' in self.settings[shape]:
                am = self.settings[shape]['amount']
                if type(am) == int:
                    return am
                else:
                    multi *= int(am[1:])

        for parent in self.get_parents(shape):
            amount = max(amount, self.get_amount(parent))
        return amount * multi if amount != -1 else -1

    def set_statics(self, shape, statics):
        if shape in self.settings:
            self.settings[shape]['statics'] = statics
        else:
            self.settings[shape] = {'statics': statics}

    def del_statics(self, shape):
        if shape in self.settings:
            self.settings[shape].pop('statics', None)

    def set_defaults(self):
        changes = {}
        shapes = self.get_all()
        for shape in shapes:
            if shape in self.enabled:
                if shape not in self.settings:
                    self.settings[shape] = {}
                if 'amount' not in self.settings[shape]:
                    amount = 'x1'
                    if len(self.get_parents(shape)) == 0:
                        amount = 1000
                    self.settings[shape]['amount'] = amount
                    if shape not in changes:
                        changes[shape] = {}
                    changes[shape]['amount'] = amount
        return changes if len(changes) else None

    def _can_be_generated(self, shape):
        edges = []
        fields = {}
        for parent in self.get_parents(shape):
            buf = self.get_edges(parent, shape)
            for b in buf:
                edges.append((b[1], b[0], parent, b[2]))

        statics = None
        if 'statics' in self.settings[shape]:
            statics = self.settings[shape]['statics']
        if statics:
            for static in statics:
                for edge in list(edges):
                    if static[:3] == edge[:3]:
                        edges.remove(edge)
                        fields[edge[0]] = static[3].split(',')
                        break

        edges = filter(lambda x: x[3], edges)
        for edge in list(edges):
            if edge[2] in self.generated:
                if edge[1] in self.generated[edge[2]]:
                    edges.remove(edge)
                    fields[edge[0]] = self.generated[edge[2]][edge[1]]

        return not bool(edges), fields

    def _save_generated(self, shape, generated):
        result = {}
        edges = []
        for child in self.get_childs(shape):
            edges += self.get_edges(shape, child)
        fields = set(map(lambda x: x[0], edges))
        for field in fields:
            result[field] = [getattr(gen, field, None) for gen in generated]
        self.generated[shape] = result

    def delete(self, last=True, all=False):
        results = {}
        for Shape in self.enabled:
            results[Shape] = {}
            shape = self.get_object(Shape)
            if all:
                amount = shape.delete_all()
            else:
                amount = shape.delete_last()
            if amount:
                results[Shape]['status'] = 'success'
            else:
                results[Shape]['status'] = 'warning'
            results[Shape]['amount'] = amount
        return results

    def purge(self):
        results = {}
        for Shape in self.get_all():
            results[Shape] = {}
            shape = self.get_object(Shape)
            amount = shape.delete_all()
            if amount:
                results[Shape]['status'] = 'success'
            else:
                results[Shape]['status'] = 'warning'
            results[Shape]['amount'] = amount
        return results

    def generate(self):
        self.generated = {}
        self.set_defaults()
        results = {}
        pending = list(self.enabled)
        while len(pending):
            Shape = pending[0]
            status, fields = self._can_be_generated(Shape)
            if status:
                shape = self.get_object(Shape)
                for name, value in fields.iteritems():
                    shape[name] = ChoiceGenerator(choices=value)
                if Shape not in results:
                    results[Shape] = {}
                amount = self.get_amount(Shape)
                try:
                    generated = shape.create(amount)
                except:
                    results[Shape]['status'] = 'error'
                    return results
                else:
                    if amount == len(generated):
                        results[Shape]['status'] = 'success'
                    else:
                        results[Shape]['status'] = 'warning'
                    results[Shape]['amount'] = len(generated)
                    self._save_generated(Shape, generated)
                    pending.pop(0)
            else:
                pending.append(pending.pop(0))
        return results
