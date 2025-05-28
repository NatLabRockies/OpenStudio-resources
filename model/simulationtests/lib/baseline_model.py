from pathlib import Path
from typing import Optional

import openstudio

VALID_ASHRAE_SYS_NUM_ARRAY = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10"]


class BaselineModel(openstudio.model.Model):
    def add_geometry(
        self,
        length: float,
        width: float,
        num_floors: int,
        floor_to_floor_height: float,
        plenum_height: float,
        perimeter_zone_depth: float,
    ):
        # input error checking
        if length <= 1e-4:
            raise ValueError("Length is too small")

        if width <= 1e-4:
            raise ValueError("Width is too small")

        if num_floors < 1:
            raise ValueError("num_floors must be >= 1")

        if floor_to_floor_height <= 1e-4:
            raise ValueError("floor_to_floor_height is too small")

        if plenum_height < 0:
            raise ValueError("plenum_height must be >= 0")

        if perimeter_zone_depth < 0:
            raise ValueError("perimeter_zone_depth must be >= 0")

        shortest_side = min(length, width)
        if (2 * perimeter_zone_depth) >= (shortest_side - 1e-4):
            raise ValueError("perimeter_zone_depth doesn't match the shortest side")

        # Loop through the number of floors
        for floor_idx in range(num_floors):
            z = floor_to_floor_height * floor_idx

            # Create a new story within the building
            story = openstudio.model.BuildingStory(self)
            story.setNominalFloortoFloorHeight(floor_to_floor_height)
            story.setName(f"Story {floor_idx + 1}")

            nw_point = openstudio.Point3d(0, width, z)
            ne_point = openstudio.Point3d(length, width, z)
            se_point = openstudio.Point3d(length, 0, z)
            sw_point = openstudio.Point3d(0, 0, z)
            # Identity matrix for setting space origins
            m = openstudio.Matrix(4, 4, 0)
            m[0, 0] = 1
            m[1, 1] = 1
            m[2, 2] = 1
            m[3, 3] = 1

            # Define polygons for a rectangular building
            if perimeter_zone_depth > 0:
                perimeter_nw_point = nw_point + openstudio.Vector3d(perimeter_zone_depth, -perimeter_zone_depth, 0)
                perimeter_ne_point = ne_point + openstudio.Vector3d(-perimeter_zone_depth, -perimeter_zone_depth, 0)
                perimeter_se_point = se_point + openstudio.Vector3d(-perimeter_zone_depth, perimeter_zone_depth, 0)
                perimeter_sw_point = sw_point + openstudio.Vector3d(perimeter_zone_depth, perimeter_zone_depth, 0)

                west_polygon = openstudio.Point3dVector()
                west_polygon.append(sw_point)
                west_polygon.append(nw_point)
                west_polygon.append(perimeter_nw_point)
                west_polygon.append(perimeter_sw_point)
                west_space = openstudio.model.Space.fromFloorPrint(west_polygon, floor_to_floor_height, self)
                west_space = west_space.get()
                # Note: could just use
                # openstudio.createTranslation(openstudio.Vector3d(sw_point.x(), sw_point.y(), sw_point.z()))
                m[0, 3] = sw_point.x()
                m[1, 3] = sw_point.y()
                m[2, 3] = sw_point.z()
                west_space.changeTransformation(openstudio.Transformation(m))
                west_space.setBuildingStory(story)
                west_space.setName(f"{story.nameString()} West Perimeter Space")

                north_polygon = openstudio.Point3dVector()
                north_polygon.append(nw_point)
                north_polygon.append(ne_point)
                north_polygon.append(perimeter_ne_point)
                north_polygon.append(perimeter_nw_point)
                north_space = openstudio.model.Space.fromFloorPrint(north_polygon, floor_to_floor_height, self)
                north_space = north_space.get()
                m[0, 3] = perimeter_nw_point.x()
                m[1, 3] = perimeter_nw_point.y()
                m[2, 3] = perimeter_nw_point.z()
                north_space.changeTransformation(openstudio.Transformation(m))
                north_space.setBuildingStory(story)
                north_space.setName(f"{story.nameString()} North Perimeter Space")

                east_polygon = openstudio.Point3dVector()
                east_polygon.append(ne_point)
                east_polygon.append(se_point)
                east_polygon.append(perimeter_se_point)
                east_polygon.append(perimeter_ne_point)
                east_space = openstudio.model.Space.fromFloorPrint(east_polygon, floor_to_floor_height, self)
                east_space = east_space.get()
                m[0, 3] = perimeter_se_point.x()
                m[1, 3] = perimeter_se_point.y()
                m[2, 3] = perimeter_se_point.z()
                east_space.changeTransformation(openstudio.Transformation(m))
                east_space.setBuildingStory(story)
                east_space.setName(f"{story.nameString()} East Perimeter Space")

                south_polygon = openstudio.Point3dVector()
                south_polygon.append(se_point)
                south_polygon.append(sw_point)
                south_polygon.append(perimeter_sw_point)
                south_polygon.append(perimeter_se_point)
                south_space = openstudio.model.Space.fromFloorPrint(south_polygon, floor_to_floor_height, self)
                south_space = south_space.get()
                m[0, 3] = sw_point.x()
                m[1, 3] = sw_point.y()
                m[2, 3] = sw_point.z()
                south_space.changeTransformation(openstudio.Transformation(m))
                south_space.setBuildingStory(story)
                south_space.setName(f"{story.nameString()} South Perimeter Space")

                core_polygon = openstudio.Point3dVector()
                core_polygon.append(perimeter_sw_point)
                core_polygon.append(perimeter_nw_point)
                core_polygon.append(perimeter_ne_point)
                core_polygon.append(perimeter_se_point)
                core_space = openstudio.model.Space.fromFloorPrint(core_polygon, floor_to_floor_height, self)
                core_space = core_space.get()
                m[0, 3] = perimeter_sw_point.x()
                m[1, 3] = perimeter_sw_point.y()
                m[2, 3] = perimeter_sw_point.z()
                core_space.changeTransformation(openstudio.Transformation(m))
                core_space.setBuildingStory(story)
                core_space.setName(f"{story.nameString()} Core Space")

            # Minimal zones
            else:
                core_polygon = openstudio.Point3dVector()
                core_polygon.append(sw_point)
                core_polygon.append(nw_point)
                core_polygon.append(ne_point)
                core_polygon.append(se_point)
                core_space = openstudio.model.Space.fromFloorPrint(core_polygon, floor_to_floor_height, self)
                core_space = core_space.get()
                m[0, 3] = sw_point.x()
                m[1, 3] = sw_point.y()
                m[2, 3] = sw_point.z()
                core_space.changeTransformation(openstudio.Transformation(m))
                core_space.setBuildingStory(story)
                core_space.setName(f"{story.nameString()} Core Space")

            # Set vertical story position
            story.setNominalZCoordinate(z)

        # We sort the spaces by name, so we add the thermalZones always in the same order in order
        # to try limiting differences in order of subsequent systems etc
        spaces = sorted(self.getSpaces(), key=lambda space: space.nameString())

        # Match surfaces for each space in the vector
        openstudio.model.matchSurfaces(openstudio.model.SpaceVector(spaces))

        renamed_surfaces = set()
        # Apply a thermal zone to each space in the model if that space has no thermal zone already
        for space in spaces:
            if not space.thermalZone().is_initialized():
                new_thermal_zone = openstudio.model.ThermalZone(self)
                space.setThermalZone(new_thermal_zone)
                new_thermal_zone.setName(space.nameString().replace("Space", "Thermal Zone"))

            # Rename all surfaces with a unique name for easy diffing
            for s in space.surfaces():
                fromSpaceName = space.nameString()
                surfaceType = s.surfaceType()
                boundaryCondition = s.outsideBoundaryCondition()
                if boundaryCondition.lower() == "ground":
                    s.setName(f"{fromSpaceName} Exterior Ground Floor")
                elif boundaryCondition.lower() == "outdoors":
                    if surfaceType.lower() == "wall":
                        s.setName(f"{fromSpaceName} Exterior Wall")
                    elif surfaceType.lower() == "roofceiling":
                        s.setName(f"{fromSpaceName} Exterior Roof")
                    elif surfaceType.lower() == "floor":
                        # This shouldn't happen in our code
                        s.setName(f"{fromSpaceName} Exterior Floor")
                    else:
                        raise ValueError(f"Unknown surfaceType {surfaceType} for {s.briefDescription()}")
                elif boundaryCondition.lower() == "surface":
                    if s.handle() in renamed_surfaces:
                        continue

                    adjacent_s_ = s.adjacentSurface()
                    if not adjacent_s_.is_initialized():
                        raise ValueError(
                            f"{s.briefDescription()} is listed as outside boundary condition = 'Surface' but it does not have an adjacent surface"
                        )

                    adjacent_s = adjacent_s_.get()
                    adjacent_space_ = adjacent_s.space()
                    if not adjacent_space_.is_initialized():
                        raise ValueError(f"Adjacent Surface {adjacent_s.nameString()} does not have a Space")

                    toSpaceName = adjacent_space_.get().nameString()

                    s.setName(f"{fromSpaceName} to {toSpaceName} Interior {surfaceType}")
                    adjacent_s.setName(f"{toSpaceName} to {fromSpaceName} Interior {surfaceType}")

                    renamed_surfaces.add(s.handle())
                    renamed_surfaces.add(adjacent_s.handle())

    def add_windows(self, wwr: float, offset: float, application_type: str):
        if wwr <= 0 or wwr >= 1:
            raise ValueError("wwr must be in the ]0, 1[ range")

        if offset <= 0:
            raise ValueError("offset must be > 0")

        heightOffsetFromFloor = application_type == "Above Floor"
        for s in self.getSurfaces():
            if s.outsideBoundaryCondition().lower() != "outdoors":
                continue

            new_window = s.setWindowToWallRatio(wwr, offset, heightOffsetFromFloor)
            # Name it like the wall (new_window will be initialized only for walls)
            if new_window.is_initialized():
                new_window.get().setName(f"{s.nameString()} Window")

    def set_constructions(self):
        construction_library_path = Path(__file__).parent / "baseline_model_constructions.osm"
        assert construction_library_path.is_file()

        vt = openstudio.osversion.VersionTranslator()
        construction_library = vt.loadModel(str(construction_library_path)).get()

        # Clone the default construction set from the construction library to the model
        default_construction_set = (
            construction_library.getDefaultConstructionSets()[0].clone(self).to_DefaultConstructionSet().get()
        )

        # Apply the newly-added construction set to the model
        building = self.getBuilding()
        building.setDefaultConstructionSet(default_construction_set)

        # get the air wall
        if openstudio.VersionString(openstudio.openStudioVersion()) > openstudio.VersionString("3.4.0"):
            construction_library.getConstructionAirBoundarys()[0].clone(self)
        else:
            for c in construction_library.getConstructions():
                if c.nameString().strip() == "Air_Wall":
                    c.clone(self)
                    break

    def add_daylighting(self, shades: bool):
        shading_control_hash = {}
        zones = sorted(self.getThermalZones(), key=lambda z: z.nameString())
        for zone in zones:
            biggestWindow = None
            for space in zone.spaces():
                for surface in space.surfaces():
                    if (surface.surfaceType() == "Wall") and (surface.outsideBoundaryCondition() == "Outdoors"):
                        for sub_surface in surface.subSurfaces():
                            ssfType = sub_surface.subSurfaceType()
                            if (ssfType == "FixedWindow") or (ssfType == "OperableWindow"):
                                if biggestWindow is None or (sub_surface.netArea() > biggestWindow.netArea()):
                                    biggestWindow = sub_surface

                                if shades:
                                    construction_ = sub_surface.construction()
                                    if not construction_.is_initialized():
                                        raise RuntimeError(
                                            "You must set constructions before you call `add_daylighting` with "
                                            f"`shades = True`! {sub_surface.briefDescription()} does not "
                                            "have a construction attached"
                                        )
                                    construction = construction_.get()
                                    construction_handle = construction.handle()
                                    if construction_handle in shading_control_hash:
                                        shading_control = shading_control_hash[construction_handle]
                                    else:
                                        material = openstudio.model.Blind(self)
                                        shading_control = openstudio.model.ShadingControl(material)
                                        shading_control_hash[construction_handle] = shading_control

                                    sub_surface.setShadingControl(shading_control)

            if biggestWindow:
                biggestWindowSpace = biggestWindow.surface().get().space().get()
                vertices = biggestWindow.vertices()
                centroid = openstudio.getCentroid(vertices).get()
                outwardNormal = biggestWindow.outwardNormal()
                outwardNormal.setLength(-2.0)
                position = centroid + outwardNormal
                offsetX = 0.0
                offsetY = 0.0
                offsetZ = -1.0

                dc = openstudio.model.DaylightingControl(self)
                dc.setSpace(biggestWindowSpace)
                dc.setPositionXCoordinate(position.x() + offsetX)
                dc.setPositionYCoordinate(position.y() + offsetY)
                dc.setPositionZCoordinate(position.z() + offsetZ)
                zone.setPrimaryDaylightingControl(dc)

                glr = openstudio.model.GlareSensor(self)
                glr.setSpace(biggestWindowSpace)
                glr.setPositionXCoordinate(position.x() + offsetX)
                glr.setPositionYCoordinate(position.y() + offsetY)
                glr.setPositionZCoordinate(position.z() + offsetZ)

                ill = openstudio.model.IlluminanceMap(self)
                ill.setSpace(biggestWindowSpace)
                ill.setOriginXCoordinate(position.x() + offsetX - 0.5)
                ill.setOriginYCoordinate(position.y() + offsetY - 0.5)
                ill.setOriginZCoordinate(position.z() + offsetZ)
                ill.setXLength(1)
                ill.setYLength(1)
                ill.setNumberofXGridPoints(5)
                ill.setNumberofYGridPoints(5)
                zone.setIlluminanceMap(ill)

    def add_hvac(self, ashrae_sys_num: str):
        if ashrae_sys_num not in VALID_ASHRAE_SYS_NUM_ARRAY:
            raise ValueError(f"System type: {ashrae_sys_num} is not a valid choice: {VALID_ASHRAE_SYS_NUM_ARRAY}")

        zones = sorted(self.getThermalZones(), key=lambda z: z.nameString())
        if ashrae_sys_num == "01":
            # 1: PTAC, Residential
            openstudio.model.addSystemType1(self, zones)
            return

        if ashrae_sys_num == "02":
            # 2: PTHP, Residential
            openstudio.model.addSystemType2(self, zones)
            return

        if ashrae_sys_num == "03":
            # 3: PSZ-AC
            for zone in zones:
                hvac = openstudio.model.addSystemType3(self)
                hvac = hvac.to_AirLoopHVAC().get()
                hvac.addBranchForZone(zone)
                outlet_node = hvac.supplyOutletNode()

                setpoint_manager = next(
                    spm
                    for spm in outlet_node.setpointManagers()
                    if spm.to_SetpointManagerSingleZoneReheat().is_initialized()
                )
                setpoint_manager = setpoint_manager.to_SetpointManagerSingleZoneReheat().get()

                # Set appropriate min/max temperatures (matches Zone Heat/Cool sizing parameters)
                setpoint_manager.setMinimumSupplyAirTemperature(14)
                setpoint_manager.setMaximumSupplyAirTemperature(40)

                setpoint_manager.setControlZone(zone)
            return

        if ashrae_sys_num == "04":
            # 4: PSZ-HP
            for zone in zones:
                hvac = openstudio.model.addSystemType4(self)
                hvac = hvac.to_AirLoopHVAC().get()
                hvac.addBranchForZone(zone)
                outlet_node = hvac.supplyOutletNode()

                setpoint_manager = next(
                    spm
                    for spm in outlet_node.setpointManagers()
                    if spm.to_SetpointManagerSingleZoneReheat().is_initialized()
                )
                setpoint_manager = setpoint_manager.to_SetpointManagerSingleZoneReheat().get()
                setpoint_manager.setControlZone(zone)
            return

        if ashrae_sys_num == "05":
            # 5: Packaged VAV w/ Reheat
            hvac = openstudio.model.addSystemType5(self)
            hvac = hvac.to_AirLoopHVAC().get()
            for zone in zones:
                hvac.addBranchForZone(zone)
            return

        if ashrae_sys_num == "06":
            # 6: Packaged VAV w/ PFP Boxes
            hvac = openstudio.model.addSystemType6(self)
            hvac = hvac.to_AirLoopHVAC().get()
            for zone in zones:
                hvac.addBranchForZone(zone)
            return

        if ashrae_sys_num == "07":
            # 7: VAV w/ Reheat
            hvac = openstudio.model.addSystemType7(self)
            hvac = hvac.to_AirLoopHVAC().get()
            for zone in zones:
                hvac.addBranchForZone(zone)
            return

        if ashrae_sys_num == "08":
            # 8: VAV w/ PFP Boxes
            hvac = openstudio.model.addSystemType8(self)
            hvac = hvac.to_AirLoopHVAC().get()
            for zone in zones:
                hvac.addBranchForZone(zone)
            return

        if ashrae_sys_num == "09":
            # 9: Warm air furnace, gas fired
            for zone in zones:
                hvac = openstudio.model.addSystemType9(self)
                hvac = hvac.to_AirLoopHVAC().get()
                hvac.addBranchForZone(zone)
                outlet_node = hvac.supplyOutletNode()

                setpoint_manager = next(
                    spm
                    for spm in outlet_node.setpointManagers()
                    if spm.to_SetpointManagerSingleZoneReheat().is_initialized()
                )
                setpoint_manager = setpoint_manager.to_SetpointManagerSingleZoneReheat().get()
                setpoint_manager.setControlZone(zone)
            return

        if ashrae_sys_num == "10":
            # 10: Warm air furnace, electric
            for zone in zones:
                hvac = openstudio.model.addSystemType10(self)
                hvac = hvac.to_AirLoopHVAC().get()
                hvac.addBranchForZone(zone)
                outlet_node = hvac.supplyOutletNode()

                setpoint_manager = next(
                    spm
                    for spm in outlet_node.setpointManagers()
                    if spm.to_SetpointManagerSingleZoneReheat().is_initialized()
                )
                setpoint_manager = setpoint_manager.to_SetpointManagerSingleZoneReheat().get()
                setpoint_manager.setControlZone(zone)
            return

        # if system number is not recognized
        raise ValueError(f"Cannot find system number {ashrae_sys_num}")

    def set_space_type(self):
        # baseline space type taken from 90.1-2004 Large Office, Whole Building on-demand space type generator
        space_type = openstudio.model.SpaceType(self)
        space_type.setName("Baseline Model Space Type")

        # create the schedule set for the space type
        default_sch_set = openstudio.model.DefaultScheduleSet(self)
        default_sch_set.setName("Baseline Model Schedule Set")
        space_type.setDefaultScheduleSet(default_sch_set)

        # schedule for infiltration
        sch_ruleset = openstudio.model.ScheduleRuleset(self)
        sch_ruleset.setName("Baseline Model Infiltration Schedule")
        # Winter Design Day
        winter_dsn_day = openstudio.model.ScheduleDay(self)
        sch_ruleset.setWinterDesignDaySchedule(winter_dsn_day)
        winter_dsn_day = sch_ruleset.winterDesignDaySchedule()
        winter_dsn_day.setName("Baseline Model Infiltration Schedule Winter Design Day")
        winter_dsn_day.addValue(openstudio.Time(0, 24, 0, 0), 1)
        # Summer Design Day
        summer_dsn_day = openstudio.model.ScheduleDay(self)
        sch_ruleset.setSummerDesignDaySchedule(summer_dsn_day)
        summer_dsn_day = sch_ruleset.summerDesignDaySchedule()
        summer_dsn_day.setName("Baseline Model Infiltration Schedule Summer Design Day")
        summer_dsn_day.addValue(openstudio.Time(0, 24, 0, 0), 1)
        # Weekdays
        week_day = sch_ruleset.defaultDaySchedule()
        week_day.setName("Baseline Model Infiltration Schedule Schedule All Days")
        week_day.addValue(openstudio.Time(0, 6, 0, 0), 1)
        week_day.addValue(openstudio.Time(0, 22, 0, 0), 0.25)
        week_day.addValue(openstudio.Time(0, 24, 0, 0), 1)
        # set the infiltration schedule
        infiltration_sch = default_sch_set.setInfiltrationSchedule(sch_ruleset)

        # schedule for occupancy, lights, electric equipment
        sch_ruleset = openstudio.model.ScheduleRuleset(self)
        sch_ruleset.setName("Baseline Model People Lights and Equipment Schedule")
        # Winter Design Day
        winter_dsn_day = openstudio.model.ScheduleDay(self)
        sch_ruleset.setWinterDesignDaySchedule(winter_dsn_day)
        winter_dsn_day = sch_ruleset.winterDesignDaySchedule()
        winter_dsn_day.setName("Baseline Model People Lights and Equipment Schedule Winter Design Day")
        winter_dsn_day.addValue(openstudio.Time(0, 24, 0, 0), 0)
        # Summer Design Day
        summer_dsn_day = openstudio.model.ScheduleDay(self)
        sch_ruleset.setSummerDesignDaySchedule(summer_dsn_day)
        summer_dsn_day = sch_ruleset.summerDesignDaySchedule()
        summer_dsn_day.setName("Baseline Model People Lights and Equipment Schedule Summer Design Day")
        summer_dsn_day.addValue(openstudio.Time(0, 24, 0, 0), 1)
        # Weekdays
        week_day = sch_ruleset.defaultDaySchedule()
        week_day.setName("Baseline Model People Lights and Equipment Schedule Schedule Week Day")
        week_day.addValue(openstudio.Time(0, 6, 0, 0), 0)
        week_day.addValue(openstudio.Time(0, 7, 0, 0), 0.1)
        week_day.addValue(openstudio.Time(0, 8, 0, 0), 0.2)
        week_day.addValue(openstudio.Time(0, 12, 0, 0), 0.95)
        week_day.addValue(openstudio.Time(0, 13, 0, 0), 0.5)
        week_day.addValue(openstudio.Time(0, 17, 0, 0), 0.95)
        week_day.addValue(openstudio.Time(0, 18, 0, 0), 0.7)
        week_day.addValue(openstudio.Time(0, 20, 0, 0), 0.4)
        week_day.addValue(openstudio.Time(0, 22, 0, 0), 0.1)
        week_day.addValue(openstudio.Time(0, 24, 0, 0), 0.05)
        # Saturdays
        saturday_rule = openstudio.model.ScheduleRule(sch_ruleset)
        saturday_rule.setName("Baseline Model People Lights and Equipment Schedule Saturday Rule")
        saturday_rule.setApplySaturday(True)
        saturday = saturday_rule.daySchedule()
        saturday.setName("Baseline Model People Lights and Equipment Schedule Saturday")
        saturday.addValue(openstudio.Time(0, 6, 0, 0), 0)
        saturday.addValue(openstudio.Time(0, 8, 0, 0), 0.1)
        saturday.addValue(openstudio.Time(0, 14, 0, 0), 0.5)
        saturday.addValue(openstudio.Time(0, 17, 0, 0), 0.1)
        saturday.addValue(openstudio.Time(0, 24, 0, 0), 0)
        # Sundays
        sunday_rule = openstudio.model.ScheduleRule(sch_ruleset)
        sunday_rule.setName("Baseline Model People Lights and Equipment Schedule Sunday Rule")
        sunday_rule.setApplySunday(True)
        sunday = sunday_rule.daySchedule()
        sunday.setName("Baseline Model People Lights and Equipment Schedule Schedule Sunday")
        sunday.addValue(openstudio.Time(0, 24, 0, 0), 0)
        # assign the schedule to the ruleset
        default_sch_set.setNumberofPeopleSchedule(sch_ruleset)
        default_sch_set.setLightingSchedule(sch_ruleset)
        default_sch_set.setElectricEquipmentSchedule(sch_ruleset)

        # schedule for occupant activity level = 120 W constant
        occ_activity_sch = openstudio.model.ScheduleRuleset(self)
        occ_activity_sch.setName("Baseline Model People Activity Schedule")
        occ_activity_sch.defaultDaySchedule().setName("Baseline Model People Activity Schedule Default")
        occ_activity_sch.defaultDaySchedule().addValue(openstudio.Time(0, 24, 0, 0), 120)
        default_sch_set.setPeopleActivityLevelSchedule(occ_activity_sch)

        # outdoor air = 0.0094 m^3/s*person (20 cfm/person)
        ventilation = openstudio.model.DesignSpecificationOutdoorAir(self)
        ventilation.setName("Baseline Model OA")
        space_type.setDesignSpecificationOutdoorAir(ventilation)
        ventilation.setOutdoorAirMethod("Sum")
        ventilation.setOutdoorAirFlowperPerson(openstudio.convert(20, "ft^3/min*person", "m^3/s*person").get())

        # infiltration = 0.00030226 m^3/s*m^2 exterior (0.06 cfm/ft^2 exterior)
        infiltration = openstudio.model.SpaceInfiltrationDesignFlowRate(self)
        infiltration.setName("Baseline Model Infiltration")
        infiltration.setSpaceType(space_type)
        infiltration.setFlowperExteriorSurfaceArea(openstudio.convert(0.06, "ft^3/min*ft^2", "m^3/s*m^2").get())

        # people = 0.053820 people/m^2 (0.005 people/ft^2)
        # create the people definition
        people_def = openstudio.model.PeopleDefinition(self)
        people_def.setName("Baseline Model People Definition")
        people_def.setPeopleperSpaceFloorArea(openstudio.convert(0.005, "people/ft^2", "people/m^2").get())
        # create the people instance and hook it up to the space type
        people = openstudio.model.People(people_def)
        people.setName("Baseline Model People")
        people.setSpaceType(space_type)

        # lights = 10.763910 W/m^2 (1 W/ft^2)
        # create the lighting definition
        lights_def = openstudio.model.LightsDefinition(self)
        lights_def.setName("Baseline Model Lights Definition")
        lights_def.setWattsperSpaceFloorArea(openstudio.convert(1, "W/ft^2", "W/m^2").get())
        # create the lighting instance and hook it up to the space type
        lights = openstudio.model.Lights(lights_def)
        lights.setName("Baseline Model Lights")
        lights.setSpaceType(space_type)

        # equipment = 10.763910 W/m^2 (1 W/ft^2)
        # create the electric equipment definition
        elec_equip_def = openstudio.model.ElectricEquipmentDefinition(self)
        elec_equip_def.setName("Baseline Model Electric Equipment Definition")
        elec_equip_def.setWattsperSpaceFloorArea(openstudio.convert(1, "W/ft^2", "W/m^2").get())
        # create the electric equipment instance and hook it up to the space type
        elec_equip = openstudio.model.ElectricEquipment(elec_equip_def)
        elec_equip.setName("Baseline Model Electric Equipment")
        elec_equip.setSpaceType(space_type)

        # set the space type of all spaces by setting it at the building level
        self.getBuilding().setSpaceType(space_type)

    def add_thermostats(self, heating_setpoint: float, cooling_setpoint: float):
        time_24hrs = openstudio.Time(0, 24, 0, 0)

        if heating_setpoint > cooling_setpoint:
            raise ValueError(f"{heating_setpoint=} cannot be greater than {cooling_setpoint=}")

        cooling_sch = openstudio.model.ScheduleRuleset(self)
        cooling_sch.setName("Cooling Sch")
        cooling_sch.defaultDaySchedule().setName("Cooling Sch Default")
        cooling_sch.defaultDaySchedule().addValue(time_24hrs, cooling_setpoint)

        heating_sch = openstudio.model.ScheduleRuleset(self)
        heating_sch.setName("Heating Sch")
        heating_sch.defaultDaySchedule().setName("Heating Sch Default")
        heating_sch.defaultDaySchedule().addValue(time_24hrs, heating_setpoint)

        zones = sorted(self.getThermalZones(), key=lambda z: z.nameString())

        for zone in zones:
            new_thermostat = openstudio.model.ThermostatSetpointDualSetpoint(self)
            new_thermostat.setHeatingSchedule(heating_sch)
            new_thermostat.setCoolingSchedule(cooling_sch)
            zone.setThermostatSetpointDualSetpoint(new_thermostat)

    def add_design_days(self):
        ddy_path = None
        if openstudio.VersionString(openstudio.openStudioVersion()) < openstudio.VersionString("3.7.0"):
            workflow = openstudio.openstudioutilitiesfiletypes.WorkflowJSON.load("in.osw")
        else:
            workflow = openstudio.WorkflowJSON.load("in.osw")
        if workflow.is_initialized():
            weather = workflow.get().weatherFile()
            if weather.is_initialized():
                weather_path = workflow.get().findFile(str(weather.get()))
                if weather_path.is_initialized():
                    weather_path = weather_path.get()
                    ddy_path = weather_path.replace_extension("ddy")
        # make sure the file exists on the filesystem; if it does, open it
        if not ddy_path:
            raise ValueError("Couldn't find DDY path")
        if not openstudio.exists(ddy_path):
            raise ValueError(f"Couldn't find DDY path at {ddy_path}")

        # TODO: I messed up the SWIG typemap for Path
        ddy_idf = openstudio.IdfFile.load(Path(str(ddy_path)), openstudio.IddFileType("EnergyPlus")).get()
        ddy_workspace = openstudio.Workspace(ddy_idf)
        reverse_translator = openstudio.energyplus.ReverseTranslator()
        ddy_model = reverse_translator.translateWorkspace(ddy_workspace)

        # Try to limit to the two main design days
        ddy_objects = [
            d
            for d in ddy_model.getDesignDays()
            if any([x in d.nameString() for x in [".4% Condns DB", "99.6% Condns DB"]])
        ]
        if not ddy_objects:
            raise ValueError("Couldn't load any Design Days")
        # Otherwise, get all .4% and 99.6%
        if len(ddy_objects) < 2:
            ddy_objects = [d for d in ddy_model.getDesignDays() if any([x in d.nameString() for x in [".4%", "99.6%"]])]

        # add the objects in the ddy file to the model
        self.addObjects(ddy_objects)

        # Do a couple more things
        sc = self.getSimulationControl()
        sc.setRunSimulationforSizingPeriods(False)
        sc.setRunSimulationforWeatherFileRunPeriods(True)

        timestep = self.getTimestep()
        timestep.setNumberOfTimestepsPerHour(4)

    def force_year_description(self):
        """Avoid a regression in UseWeatherFile handling.

        Historically, YearDescription had a default of 'UseWeatherFile' but that option was not supported until 3.3.0.
        So it would instead default to assumedBaseYear which is 2009, which starts on a Thursday.
        Except that 3.3.0 does take it into account and Chicago EPW has a start day of Sunday (and changes year to 2006).
        So to avoid problems, we force it to Thursday explicitly
        """
        yd = self.getYearDescription()
        yd.setDayofWeekforStartDay("Thursday")

    def save_openstudio_osm(self, osm_name: str, osm_save_directory: Optional[Path] = None):
        """Save an openstudio model.

        If osm_save_directory is None, Path.cwd() is used.
        """
        if osm_save_directory is None:
            osm_save_directory = Path.cwd()
        self.force_year_description()
        save_path = osm_save_directory / osm_name
        print(f"Saving to {save_path}")
        self.save(str(save_path), True)

    def add_standards(self, standards: dict):
        self.standards = {**standards}  # Explicit copy

    @staticmethod
    def _add_vals_to_sch(day_sch, sch_type, values):
        """Helper method to fill in hourly values."""
        if sch_type == "Constant":
            day_sch.addValue(openstudio.Time.new(0, 24, 0, 0), values[0])
        elif sch_type == "Hourly":
            for i in range(24):
                if i < 23 and values[i] == values[i + 1]:
                    continue
                day_sch.addValue(openstudio.Time(0, i + 1, 0, 0), values[i])

    def add_schedule(self, schedule_name):
        """
        Create a schedule from the openstudio standards dataset
        """
        for schedule in self.getSchedules():
            if schedule.nameString() == schedule_name:
                # openstudio.logFree(openstudio.Debug, 'openstudio.standards.Model', f"Already added schedule: {schedule_name}")
                return schedule

        if getattr(self, "standards", None) is None:
            raise ValueError("You must call add_standards first!")

        if "schedules" not in self.standards:
            raise ValueError("add_standards should have the 'schedules' key in the passed dict")

        rules = []
        for candidate_schedule in self.standards["schedules"]:
            if "name" not in candidate_schedule:
                openstudio.logFree(
                    openstudio.Debug, "openstudio.standards.Model", f"name is missing from {candidate_schedule}"
                )
                continue
            if candidate_schedule["name"] == schedule_name:
                rules.append(candidate_schedule)
        if not rules:
            raise ValueError(f"Schedule named ''{schedule_name}' not found in standards data")

        # Make a schedule ruleset
        sch_ruleset = openstudio.model.ScheduleRuleset(self)
        sch_ruleset.setName(schedule_name)

        # Lazy import
        from datetime import datetime

        for rule in rules:
            day_types = rule["day_types"].split("|")
            start_date = datetime.fromisoformat(rule["start_date"])
            end_date = datetime.fromisoformat(rule["end_date"])
            sch_type = rule["type"]
            values = rule["values"]

            # Day Type choices: Wkdy, Wknd, Mon, Tue, Wed, Thu, Fri, Sat, Sun, WntrDsn, SmrDsn, Hol

            # Default
            if "Default" in day_types:
                day_sch = sch_ruleset.defaultDaySchedule()
                day_sch.setName(f"{schedule_name} Default")
                BaselineModel._add_vals_to_sch(day_sch, sch_type, values)

            # Winter Design Day
            if "WntrDsn" in day_types:
                day_sch = openstudio.model.ScheduleDay(self)
                sch_ruleset.setWinterDesignDaySchedule(day_sch)
                day_sch = sch_ruleset.winterDesignDaySchedule()
                day_sch.setName(f"{schedule_name} Winter Design Day")
                BaselineModel._add_vals_to_sch(day_sch, sch_type, values)

            # Summer Design Day
            if "SmrDsn" in day_types:
                day_sch = openstudio.model.ScheduleDay(self)
                sch_ruleset.setSummerDesignDaySchedule(day_sch)
                day_sch = sch_ruleset.summerDesignDaySchedule()
                day_sch.setName(f"{schedule_name} Summer Design Day")
                BaselineModel._add_vals_to_sch(day_sch, sch_type, values)

            if any([x in ["Wkdy", "Wknd", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"] for x in day_types]):
                # Make the rule
                sch_rule = openstudio.model.ScheduleRule(sch_ruleset)
                day_sch = sch_rule.daySchedule()
                day_sch.setName(f"{schedule_name} Rule")
                BaselineModel._add_vals_to_sch(day_sch, sch_type, values)

                # Set the dates when the rule applies
                sch_rule.setStartDate(openstudio.Date(openstudio.MonthOfYear(start_date.month), start_date.day))
                sch_rule.setEndDate(openstudio.Date(openstudio.MonthOfYear(end_date.month), end_date.day))

                # Set the days when the rule applies
                # Weekends
                if "Wknd" in day_types:
                    sch_rule.setApplySaturday(True)
                    sch_rule.setApplySunday(True)
                # Weekdays
                if "Wkdy" in day_types:
                    sch_rule.setApplyMonday(True)
                    sch_rule.setApplyTuesday(True)
                    sch_rule.setApplyWednesday(True)
                    sch_rule.setApplyThursday(True)
                    sch_rule.setApplyFriday(True)

                # Individual Days
                if "Mon" in day_types:
                    sch_rule.setApplyMonday(True)
                if "Tue" in day_types:
                    sch_rule.setApplyTuesday(True)
                if "Wed" in day_types:
                    sch_rule.setApplyWednesday(True)
                if "Thu" in day_types:
                    sch_rule.setApplyThursday(True)
                if "Fri" in day_types:
                    sch_rule.setApplyFriday(True)
                if "Sat" in day_types:
                    sch_rule.setApplySaturday(True)
                if "Sun" in day_types:
                    sch_rule.setApplySunday(True)

        return sch_ruleset

    def add_water_heater(
        self,
        water_heater_type: str,
        water_heater_fuel: str,
        temp_sch_type_limits: Optional[openstudio.model.ScheduleTypeLimits] = None,
        swh_temp_sch: Optional[openstudio.model.Schedule] = None,
        ambient_temperature_thermal_zone: Optional[openstudio.model.ThermalZone] = None,
        service_water_flowrate_schedule: Optional[str] = None,
    ):
        assert water_heater_type in ["Mixed", "Stratified"]
        assert water_heater_fuel in ["Electricity", "Natural Gas"]

        # Water heater
        # TODO Standards - Change water heater methodology to follow 'Model Enhancements Appendix A.'
        water_heater_capacity_btu_per_hr = 2883000
        water_heater_capacity_kbtu_per_hr = openstudio.convert(
            water_heater_capacity_btu_per_hr, "Btu/hr", "kBtu/hr"
        ).get()
        water_heater_vol_gal = 100

        if temp_sch_type_limits is None:
            temp_sch_type_limits = openstudio.model.ScheduleTypeLimits(self)
            temp_sch_type_limits.setName("Temperature Schedule Type Limits")
            temp_sch_type_limits.setLowerLimitValue(0.0)
            temp_sch_type_limits.setUpperLimitValue(100.0)
            temp_sch_type_limits.setNumericType("Continuous")
            temp_sch_type_limits.setUnitType("Temperature")

        if swh_temp_sch is None:
            # Service water heating loop controls
            swh_temp_f = 140
            # swh_delta_t_r = 9  # 9F delta-T
            swh_temp_c = openstudio.convert(swh_temp_f, "F", "C").get()
            # swh_delta_t_k = openstudio.convert(swh_delta_t_r, "R", "K").get()
            swh_temp_sch = openstudio.model.ScheduleRuleset(self)
            swh_temp_sch.setName(f"Hot Water Loop Temp - {swh_temp_f}F")
            swh_temp_sch.defaultDaySchedule().setName(f"Hot Water Loop Temp - {swh_temp_f}F Default")
            swh_temp_sch.defaultDaySchedule().addValue(openstudio.Time(0, 24, 0, 0), swh_temp_c)
            swh_temp_sch.setScheduleTypeLimits(temp_sch_type_limits)

        # Water heater depends on the fuel type
        if water_heater_type == "Stratified":
            water_heater = openstudio.model.WaterHeaterStratified(self)
        else:
            water_heater = openstudio.model.WaterHeaterMixed(self)
            water_heater.setSetpointTemperatureSchedule(swh_temp_sch)
            water_heater.setHeaterMaximumCapacity(
                openstudio.convert(water_heater_capacity_btu_per_hr, "Btu/hr", "W").get()
            )
            water_heater.setDeadbandTemperatureDifference(openstudio.convert(3.6, "R", "K").get())
            water_heater.setHeaterControlType("Cycle")

        water_heater.setMaximumTemperatureLimit(openstudio.convert(180, "F", "C").get())
        water_heater.setOffCycleParasiticHeatFractiontoTank(0.8)
        water_heater.setIndirectWaterHeatingRecoveryTime(1.5)  # 1.5hrs

        if water_heater_fuel == "Electricity":
            water_heater.setHeaterFuelType("Electricity")
            water_heater.setHeaterThermalEfficiency(1.0)
            water_heater.setOffCycleParasiticFuelConsumptionRate(openstudio.convert(68.24, "Btu/hr", "W").get())
            water_heater.setOnCycleParasiticFuelConsumptionRate(openstudio.convert(68.24, "Btu/hr", "W").get())
            water_heater.setOffCycleParasiticFuelType("Electricity")
            water_heater.setOnCycleParasiticFuelType("Electricity")
            if water_heater_type == "Stratified":
                water_heater.setOffCycleFlueLossCoefficienttoAmbientTemperature(1.053)
            else:
                water_heater.setOffCycleLossCoefficienttoAmbientTemperature(1.053)
                water_heater.setOnCycleLossCoefficienttoAmbientTemperature(1.053)
        elif water_heater_fuel == "Natural Gas":
            water_heater.setHeaterFuelType("NaturalGas")
            water_heater.setHeaterThermalEfficiency(0.78)
            water_heater.setOffCycleParasiticFuelConsumptionRate(openstudio.convert(68.24, "Btu/hr", "W").get())
            water_heater.setOnCycleParasiticFuelConsumptionRate(openstudio.convert(68.24, "Btu/hr", "W").get())
            water_heater.setOffCycleParasiticFuelType("NaturalGas")
            water_heater.setOnCycleParasiticFuelType("NaturalGas")
            if water_heater_type == "Stratified":
                water_heater.setOffCycleFlueLossCoefficienttoAmbientTemperature(6.0)
            else:
                water_heater.setOffCycleLossCoefficienttoAmbientTemperature(6.0)
                water_heater.setOnCycleLossCoefficienttoAmbientTemperature(6.0)

        if service_water_flowrate_schedule is not None:
            rated_flow_rate_gal_per_min = 0.164843359974645
            rated_flow_rate_m3_per_s = openstudio.convert(rated_flow_rate_gal_per_min, "gal/min", "m^3/s").get()
            water_heater.setPeakUseFlowRate(rated_flow_rate_m3_per_s)

            schedule = self.add_schedule(service_water_flowrate_schedule)
            water_heater.setUseFlowRateFractionSchedule(schedule)

        return water_heater

    def add_swh_loop(
        self, water_heater_type: str, ambient_temperature_thermal_zone: Optional[openstudio.model.ThermalZone] = None
    ):
        # Service water heating loop
        service_water_loop = openstudio.model.PlantLoop(self)
        service_water_loop.setName("Service Water Loop")
        service_water_loop.setMaximumLoopTemperature(60)
        service_water_loop.setMinimumLoopTemperature(10)

        # Temperature schedule type limits
        temp_sch_type_limits = openstudio.model.ScheduleTypeLimits(self)
        temp_sch_type_limits.setName("Temperature Schedule Type Limits")
        temp_sch_type_limits.setLowerLimitValue(0.0)
        temp_sch_type_limits.setUpperLimitValue(100.0)
        temp_sch_type_limits.setNumericType("Continuous")
        temp_sch_type_limits.setUnitType("Temperature")

        # Service water heating loop controls
        swh_temp_f = 140
        swh_delta_t_r = 9  # 9F delta-T
        swh_temp_c = openstudio.convert(swh_temp_f, "F", "C").get()
        swh_delta_t_k = openstudio.convert(swh_delta_t_r, "R", "K").get()
        swh_temp_sch = openstudio.model.ScheduleRuleset(self)
        swh_temp_sch.setName(f"Hot Water Loop Temp - {swh_temp_f}F")
        swh_temp_sch.defaultDaySchedule().setName(f"Hot Water Loop Temp - {swh_temp_f}F Default")
        swh_temp_sch.defaultDaySchedule().addValue(openstudio.Time(0, 24, 0, 0), swh_temp_c)
        swh_temp_sch.setScheduleTypeLimits(temp_sch_type_limits)
        swh_stpt_manager = openstudio.model.SetpointManagerScheduled(self, swh_temp_sch)
        swh_stpt_manager.addToNode(service_water_loop.supplyOutletNode())
        sizing_plant = service_water_loop.sizingPlant()
        sizing_plant.setLoopType("Heating")
        sizing_plant.setDesignLoopExitTemperature(swh_temp_c)
        sizing_plant.setLoopDesignTemperatureDifference(swh_delta_t_k)

        # Service water heating pump
        swh_pump_head_press_pa = 0.001
        swh_pump_motor_efficiency = 1

        swh_pump = openstudio.model.PumpConstantSpeed(self)
        swh_pump.setName("Service Water Loop Pump")
        swh_pump.setRatedPumpHead(swh_pump_head_press_pa)
        swh_pump.setMotorEfficiency(swh_pump_motor_efficiency)
        swh_pump.setPumpControlType("Intermittent")
        swh_pump.addToNode(service_water_loop.supplyInletNode())

        water_heater = self.add_water_heater(
            water_heater_type=water_heater_type,
            water_heater_fuel="Natural Gas",
            temp_sch_type_limits=temp_sch_type_limits,
            swh_temp_sch=swh_temp_sch,
            ambient_temperature_thermal_zone=ambient_temperature_thermal_zone,
            service_water_flowrate_schedule=None,
        )
        service_water_loop.addSupplyBranchForComponent(water_heater)

        # Service water heating loop bypass pipes
        water_heater_bypass_pipe = openstudio.model.PipeAdiabatic(self)
        service_water_loop.addSupplyBranchForComponent(water_heater_bypass_pipe)
        coil_bypass_pipe = openstudio.model.PipeAdiabatic(self)
        service_water_loop.addDemandBranchForComponent(coil_bypass_pipe)
        supply_outlet_pipe = openstudio.model.PipeAdiabatic(self)
        supply_outlet_pipe.addToNode(service_water_loop.supplyOutletNode())
        demand_inlet_pipe = openstudio.model.PipeAdiabatic(self)
        demand_inlet_pipe.addToNode(service_water_loop.demandInletNode())
        demand_outlet_pipe = openstudio.model.PipeAdiabatic(self)
        demand_outlet_pipe.addToNode(service_water_loop.demandOutletNode())

        return service_water_loop

    def add_swh_end_uses(self, swh_loop: openstudio.model.PlantLoop, flow_rate_fraction_schedule: str):
        # Water use connection
        swh_connection = openstudio.model.WaterUseConnections(self)

        # Water fixture definition
        water_fixture_def = openstudio.model.WaterUseEquipmentDefinition(self)
        rated_flow_rate_gal_per_min = 1
        rated_flow_rate_m3_per_s = openstudio.convert(rated_flow_rate_gal_per_min, "gal/min", "m^3/s").get()
        water_fixture_def.setPeakFlowRate(rated_flow_rate_m3_per_s)
        water_fixture_def.setName(f"Service Water Use Def {rated_flow_rate_gal_per_min:.2f}gal/min")
        # Target mixed water temperature
        mixed_water_temp_f = 110
        mixed_water_temp_sch = openstudio.model.ScheduleRuleset(self)
        mixed_water_temp_sch.defaultDaySchedule().addValue(
            openstudio.Time(0, 24, 0, 0), openstudio.convert(mixed_water_temp_f, "F", "C").get()
        )
        water_fixture_def.setTargetTemperatureSchedule(mixed_water_temp_sch)

        # Water use equipment
        water_fixture = openstudio.model.WaterUseEquipment(water_fixture_def)
        schedule = self.add_schedule(schedule_name=flow_rate_fraction_schedule)
        water_fixture.setFlowRateFractionSchedule(schedule)
        water_fixture.setName(f"Service Water Use {rated_flow_rate_gal_per_min:.2f}gal/min")
        swh_connection.addWaterUseEquipment(water_fixture)

        # Connect the water use connection to the SWH loop
        swh_loop.addDemandBranchForComponent(swh_connection)

    # NOTE: a very rough way
    def rename_loop_nodes(self):
        for p in self.getPlantLoops():
            prefix = p.nameString()
            for c in reversed(list(p.supplyComponents())):
                if c.to_Node().is_initialized():
                    continue

                if c.to_ConnectorMixer().is_initialized():
                    c.setName(f"{prefix} Supply ConnectorMixer")
                    continue
                elif c.to_ConnectorSplitter().is_initialized():
                    c.setName(f"{prefix} Supply ConnectorSplitter")
                    continue

                obj_type = c.iddObjectType().valueName()
                obj_type_name = obj_type.replace("OS_", "").replace("_", "")

                if c.to_PumpVariableSpeed().is_initialized():
                    c.setName(f"{prefix} VSD Pump")
                elif c.to_PumpConstantSpeed().is_initialized():
                    c.setName(f"{prefix} CstSpeed Pump")
                elif c.to_HeaderedPumpsVariableSpeed().is_initialized():
                    c.setName(f"{prefix} Headered VSD Pump")
                elif c.to_HeaderedPumpsConstantSpeed().is_initialized():
                    c.setName(f"{prefix} Headered CstSpeed Pump")

                method_name = f"to_{obj_type_name}"
                if not hasattr(c, method_name):
                    continue

                actual_thing = getattr(c, method_name)()
                if not actual_thing.is_initialized():
                    continue

                actual_thing = actual_thing.get()
                if hasattr(actual_thing, "inletModelObject") and actual_thing.inletModelObject().is_initialized():
                    inlet_mo = actual_thing.inletModelObject().get()
                    inlet_mo.setName(f"{prefix} Supply Side {actual_thing.nameString()} Inlet Node")
                if hasattr(actual_thing, "outletModelObject") and actual_thing.outletModelObject().is_initialized():
                    outlet_mo = actual_thing.outletModelObject().get()
                    outlet_mo.setName(f"{prefix} Supply Side {actual_thing.nameString()} Outlet Node")

                # WaterToWaterComponent
                # Yep, that part is gross, but I don't care
                if (
                    hasattr(actual_thing, "supplyInletModelObject")
                    and actual_thing.supplyInletModelObject().is_initialized()
                ):
                    inlet_node = actual_thing.supplyInletModelObject().get().to_Node().get()
                    if inlet_node.plantLoop().is_initialized() and (inlet_node.plantLoop().get() == p):
                        inlet_node.setName(f"{prefix} Supply Side {actual_thing.nameString()} Inlet Node")

                if (
                    hasattr(actual_thing, "supplyOutletModelObject")
                    and actual_thing.supplyOutletModelObject().is_initialized()
                ):
                    outlet_node = actual_thing.supplyOutletModelObject().get().to_Node().get()
                    if outlet_node.plantLoop().is_initialized() and (outlet_node.plantLoop().get() == p):
                        outlet_node.setName(f"{prefix} Supply Side {actual_thing.nameString()} Outlet Node")

                if (
                    hasattr(actual_thing, "tertiaryInletModelObject")
                    and actual_thing.tertiaryInletModelObject().is_initialized()
                ):
                    inlet_node = actual_thing.tertiaryInletModelObject().get().to_Node().get()
                    if inlet_node.plantLoop().is_initialized() and (inlet_node.plantLoop().get() == p):
                        inlet_node.setName(f"{prefix} Tertiary Side {actual_thing.nameString()} Inlet Node")

                if (
                    hasattr(actual_thing, "tertiaryOutletModelObject")
                    and actual_thing.tertiaryOutletModelObject().is_initialized()
                ):
                    outlet_node = actual_thing.tertiaryOutletModelObject().get().to_Node().get()
                    if outlet_node.plantLoop().is_initialized() and (outlet_node.plantLoop().get() == p):
                        outlet_node.setName(f"{prefix} Tertiary Side {actual_thing.nameString()} Outlet Node")

            for c in reversed(list(p.demandComponents())):
                if c.to_Node().is_initialized():
                    continue

                if c.to_ConnectorMixer().is_initialized():
                    c.setName(f"{prefix} Demand ConnectorMixer")
                    continue
                elif c.to_ConnectorSplitter().is_initialized():
                    c.setName(f"{prefix} Demand ConnectorSplitter")
                    continue

                obj_type = c.iddObjectType().valueName()
                obj_type_name = obj_type.replace("OS_", "").replace("_", "")

                method_name = f"to_{obj_type_name}"
                if not hasattr(c, method_name):
                    continue

                actual_thing = getattr(c, method_name)()
                if not actual_thing.is_initialized():
                    continue

                actual_thing = actual_thing.get()
                if hasattr(actual_thing, "inletModelObject") and actual_thing.inletModelObject().is_initialized():
                    inlet_mo = actual_thing.inletModelObject().get()
                    inlet_mo.setName(f"{prefix} Demand Side {actual_thing.nameString()} Inlet Node")
                if hasattr(actual_thing, "outletModelObject") and actual_thing.outletModelObject().is_initialized():
                    outlet_mo = actual_thing.outletModelObject().get()
                    outlet_mo.setName(f"{prefix} Demand Side {actual_thing.nameString()} Outlet Node")

                # WaterToWaterComponent
                if (
                    hasattr(actual_thing, "waterInletModelObject")
                    and actual_thing.waterInletModelObject().is_initialized()
                ):
                    inlet_mo = actual_thing.waterInletModelObject().get()
                    inlet_mo.setName(f"{prefix} Demand Side {actual_thing.nameString()} Inlet Node")
                if (
                    hasattr(actual_thing, "waterOutletModelObject")
                    and actual_thing.waterOutletModelObject().is_initialized()
                ):
                    outlet_mo = actual_thing.waterOutletModelObject().get()
                    outlet_mo.setName(f"{prefix} Demand Side {actual_thing.nameString()} Outlet Node")

                if (
                    hasattr(actual_thing, "demandInletModelObject")
                    and actual_thing.demandInletModelObject().is_initialized()
                ):
                    inlet_node = actual_thing.demandInletModelObject().get().to_Node().get()
                    if inlet_node.plantLoop().is_initialized() and (inlet_node.plantLoop().get() == p):
                        inlet_node.setName(f"{prefix} Demand Side {actual_thing.nameString()} Inlet Node")

                if (
                    hasattr(actual_thing, "demandOutletModelObject")
                    and actual_thing.demandOutletModelObject().is_initialized()
                ):
                    outlet_node = actual_thing.demandOutletModelObject().get().to_Node().get()
                    if outlet_node.plantLoop().is_initialized() and (outlet_node.plantLoop().get() == p):
                        outlet_node.setName(f"{prefix} Demand Side {actual_thing.nameString()} Outlet Node")

            # Common nodes
            node = p.supplyInletNode()
            new_name = "Supply Inlet Node"
            new_name = f"{prefix} {new_name}"
            node.setName(new_name)

            node = p.supplyOutletNode()
            new_name = "Supply Outlet Node"
            new_name = f"{prefix} {new_name}"
            node.setName(new_name)

            # Demand Side
            node = p.demandInletNode()
            new_name = "Demand Inlet Node"
            new_name = f"{prefix} {new_name}"
            node.setName(new_name)

            node = p.demandOutletNode()
            new_name = "Demand Outlet Node"
            new_name = f"{prefix} {new_name}"
            node.setName(new_name)

    def rename_air_nodes(self):
        """Rename some nodes and such, for ease of debugging."""
        # NOTE: Not in the least complete, but I don't need it right now
        for a in self.getAirLoopHVACs():
            a.supplyInletNode().setName(f"{a.nameString()} Supply Inlet Node")
            a.supplyOutletNode().setName(f"{a.nameString()} Supply Outlet Node")
            a.mixedAirNode().get().setName(f"{a.nameString()} Mixed Air Node")

        # Rename Zone Air Nodes
        [z.zoneAirNode().setName(f"{z.nameString()} Zone Air Node") for z in self.getThermalZones()]

        # Rename thermostats
        [
            t.setName("{t.thermalZone().get().nameString()} ThermostatSetpointDualSetpoint")
            for t in self.getThermostatSetpointDualSetpoints()
        ]
