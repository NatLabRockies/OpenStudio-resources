import openstudio


class SurfaceVisitor:
    def __init__(self, model: openstudio.model.Model):
        self.surfs = []
        self.summary = ""
        self.setup(model)
        self.run(model)
        self.shutdown(model)

    def setup(self, model):
        pass

    def run(self, model):
        allsurfs = model.getSurfaces()
        for surf in allsurfs:
            if surf in self.surfs:
                continue

            other = surf.adjacentSurface()
            if not other.is_initialized():
                self.surfs.append(surf)
                self.exteriorSurface(model, surf)
                continue

            if other.get() in self.surfs:
                continue

            # This is an interior surface
            stype = surf.surfaceType().lower()
            self.surfs.append(surf)

            if stype == "floor":
                self.interiorFloor(model, surf, other.get())
            elif stype == "roofceiling":
                self.interiorRoofCeiling(model, surf, other.get())
            else:  # Wall
                self.interiorWall(model, surf, other.get())

    def interiorFloor(self, model, surface, adjacentSurface):
        pass

    def interiorWall(self, model, surface, adjacentSurface):
        pass

    def interiorRoofCeiling(self, model, surface, adjacentSurface):
        pass

    def exteriorSurface(self, model, surface):
        pass

    def shutdown(self, model):
        self.summary = f"Visited {len(self.surfs)} surfaces"
