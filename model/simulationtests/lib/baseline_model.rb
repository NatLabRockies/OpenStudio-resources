# frozen_string_literal: true

# This allows importing this file into an irb session even if you don't have
# a global install of openstudio - useful for writing a test
require 'openstudio' unless defined?(OpenStudio)

class BaselineModel < OpenStudio::Model::Model
  def add_geometry(params)
    length = params['length']
    width = params['width']
    num_floors = params['num_floors']
    floor_to_floor_height = params['floor_to_floor_height']
    plenum_height = params['plenum_height']
    perimeter_zone_depth = params['perimeter_zone_depth']

    # input error checking
    if length <= 1e-4
      return false
    end

    if width <= 1e-4
      return false
    end

    if num_floors <= 1e-4
      return false
    end

    if floor_to_floor_height <= 1e-4
      return false
    end

    # TODO: plenum_height does not create a Plenum!
    if plenum_height < 0
      return false
    end

    shortest_side = [length, width].min
    if (perimeter_zone_depth < 0) || (2 * perimeter_zone_depth >= (shortest_side - 1e-4))
      return false
    end

    # Loop through the number of floors
    for floor in (0..num_floors - 1)

      z = floor_to_floor_height * floor

      # Create a new story within the building
      story = OpenStudio::Model::BuildingStory.new(self)
      story.setNominalFloortoFloorHeight(floor_to_floor_height)
      story.setName("Story #{floor + 1}")

      nw_point = OpenStudio::Point3d.new(0, width, z)
      ne_point = OpenStudio::Point3d.new(length, width, z)
      se_point = OpenStudio::Point3d.new(length, 0, z)
      sw_point = OpenStudio::Point3d.new(0, 0, z)

      # Identity matrix for setting space origins
      m = OpenStudio::Matrix.new(4, 4, 0)
      m[0, 0] = 1
      m[1, 1] = 1
      m[2, 2] = 1
      m[3, 3] = 1

      # Define polygons for a rectangular building
      if perimeter_zone_depth > 0
        perimeter_nw_point = nw_point + OpenStudio::Vector3d.new(perimeter_zone_depth, -perimeter_zone_depth, 0)
        perimeter_ne_point = ne_point + OpenStudio::Vector3d.new(-perimeter_zone_depth, -perimeter_zone_depth, 0)
        perimeter_se_point = se_point + OpenStudio::Vector3d.new(-perimeter_zone_depth, perimeter_zone_depth, 0)
        perimeter_sw_point = sw_point + OpenStudio::Vector3d.new(perimeter_zone_depth, perimeter_zone_depth, 0)

        west_polygon = OpenStudio::Point3dVector.new
        west_polygon << sw_point
        west_polygon << nw_point
        west_polygon << perimeter_nw_point
        west_polygon << perimeter_sw_point
        west_space = OpenStudio::Model::Space.fromFloorPrint(west_polygon, floor_to_floor_height, self)
        west_space = west_space.get
        m[0, 3] = sw_point.x
        m[1, 3] = sw_point.y
        m[2, 3] = sw_point.z
        west_space.changeTransformation(OpenStudio::Transformation.new(m))
        west_space.setBuildingStory(story)
        west_space.setName("Story #{floor + 1} West Perimeter Space")

        north_polygon = OpenStudio::Point3dVector.new
        north_polygon << nw_point
        north_polygon << ne_point
        north_polygon << perimeter_ne_point
        north_polygon << perimeter_nw_point
        north_space = OpenStudio::Model::Space.fromFloorPrint(north_polygon, floor_to_floor_height, self)
        north_space = north_space.get
        m[0, 3] = perimeter_nw_point.x
        m[1, 3] = perimeter_nw_point.y
        m[2, 3] = perimeter_nw_point.z
        north_space.changeTransformation(OpenStudio::Transformation.new(m))
        north_space.setBuildingStory(story)
        north_space.setName("Story #{floor + 1} North Perimeter Space")

        east_polygon = OpenStudio::Point3dVector.new
        east_polygon << ne_point
        east_polygon << se_point
        east_polygon << perimeter_se_point
        east_polygon << perimeter_ne_point
        east_space = OpenStudio::Model::Space.fromFloorPrint(east_polygon, floor_to_floor_height, self)
        east_space = east_space.get
        m[0, 3] = perimeter_se_point.x
        m[1, 3] = perimeter_se_point.y
        m[2, 3] = perimeter_se_point.z
        east_space.changeTransformation(OpenStudio::Transformation.new(m))
        east_space.setBuildingStory(story)
        east_space.setName("Story #{floor + 1} East Perimeter Space")

        south_polygon = OpenStudio::Point3dVector.new
        south_polygon << se_point
        south_polygon << sw_point
        south_polygon << perimeter_sw_point
        south_polygon << perimeter_se_point
        south_space = OpenStudio::Model::Space.fromFloorPrint(south_polygon, floor_to_floor_height, self)
        south_space = south_space.get
        m[0, 3] = sw_point.x
        m[1, 3] = sw_point.y
        m[2, 3] = sw_point.z
        south_space.changeTransformation(OpenStudio::Transformation.new(m))
        south_space.setBuildingStory(story)
        south_space.setName("Story #{floor + 1} South Perimeter Space")

        core_polygon = OpenStudio::Point3dVector.new
        core_polygon << perimeter_sw_point
        core_polygon << perimeter_nw_point
        core_polygon << perimeter_ne_point
        core_polygon << perimeter_se_point
        core_space = OpenStudio::Model::Space.fromFloorPrint(core_polygon, floor_to_floor_height, self)
        core_space = core_space.get
        m[0, 3] = perimeter_sw_point.x
        m[1, 3] = perimeter_sw_point.y
        m[2, 3] = perimeter_sw_point.z
        core_space.changeTransformation(OpenStudio::Transformation.new(m))
        core_space.setBuildingStory(story)
        core_space.setName("Story #{floor + 1} Core Space")

      # Minimal zones
      else
        core_polygon = OpenStudio::Point3dVector.new
        core_polygon << sw_point
        core_polygon << nw_point
        core_polygon << ne_point
        core_polygon << se_point
        core_space = OpenStudio::Model::Space.fromFloorPrint(core_polygon, floor_to_floor_height, self)
        core_space = core_space.get
        m[0, 3] = sw_point.x
        m[1, 3] = sw_point.y
        m[2, 3] = sw_point.z
        core_space.changeTransformation(OpenStudio::Transformation.new(m))
        core_space.setBuildingStory(story)
        core_space.setName("Story #{floor + 1} Core Space")

      end

      # Set vertical story position
      story.setNominalZCoordinate(z)

      # End of floor loop
    end

    # Put all of the spaces in the model into a vector
    # We sort the spaces by name, so we add the thermalZones always in the
    # same order in order to try limiting differences in order of subsequent
    # systems etc
    spaces = OpenStudio::Model::SpaceVector.new
    getSpaces.sort_by { |s| s.name.to_s }.each { |space| spaces << space }

    # Match surfaces for each space in the vector
    OpenStudio::Model.matchSurfaces(spaces)

    renamed_surfaces = Set.new
    # Apply a thermal zone to each space in the model if that space has no thermal zone already
    spaces.each do |space|
      if space.thermalZone.empty?
        new_thermal_zone = OpenStudio::Model::ThermalZone.new(self)
        space.setThermalZone(new_thermal_zone)
        new_thermal_zone.setName(space.name.get.sub('Space', 'Thermal Zone'))
      end

      # Rename all surfaces with a unique name for easy diffing
      space.surfaces.each do |s|
        fromSpaceName = space.nameString
        surfaceType = s.surfaceType()
        boundaryCondition = s.outsideBoundaryCondition
        if boundaryCondition.downcase == 'ground'
          s.setName("#{fromSpaceName} Exterior Ground Floor")
        elsif boundaryCondition.downcase == 'outdoors'
          if surfaceType.downcase == 'wall'
            s.setName("#{fromSpaceName} Exterior Wall")
          elsif surfaceType.downcase == 'roofceiling'
            s.setName("#{fromSpaceName} Exterior Roof")
          elsif surfaceType.downcase == 'floor'
            # This shouldn't happen in our code
            s.setName("#{fromSpaceName} Exterior Floor")
          else
            raise "Unknown surfaceType #{surfaceType} for #{s.briefDescription}"
          end
        elsif boundaryCondition.downcase == 'surface'

          next if renamed_surfaces.include?(s)

          adjacent_s_ = s.adjacentSurface
          raise "#{s.briefDescription} is listed as outside boundary condition = 'Surface' but it does not have an adjacent surface" if !adjacent_s_.is_initialized

          adjacent_s = adjacent_s_.get
          adjacent_space_ = adjacent_s.space
          raise "Adjacent Surface #{adjacent_s} does not have a Space" if !adjacent_space_.is_initialized

          toSpaceName = adjacent_space_.get.nameString

          s.setName("#{fromSpaceName} to #{toSpaceName} Interior #{s.surfaceType}")
          adjacent_s.setName("#{toSpaceName} to #{fromSpaceName} Interior #{s.surfaceType}")

          renamed_surfaces.add(s)
          renamed_surfaces.add(adjacent_s)
        end
        # End rename surfaces
      end
      # End loop on spaces to add thermal zone and rename surfaces
    end
  end

  def add_windows(params)
    wwr = params['wwr']
    offset = params['offset']
    application_type = params['application_type']

    # input checking
    if !wwr || !offset || !application_type
      return false
    end

    if (wwr <= 0) || (wwr >= 1)
      return false
    end

    if offset <= 0
      return false
    end

    heightOffsetFromFloor = nil
    if application_type == 'Above Floor'
      heightOffsetFromFloor = true
    else
      heightOffsetFromFloor = false
    end

    getSurfaces.each do |s|
      next if s.outsideBoundaryCondition != 'Outdoors'

      new_window = s.setWindowToWallRatio(wwr, offset, heightOffsetFromFloor)
      # Name it like the wall (new_window will be initialized only for walls)
      if new_window.is_initialized
        new_window.get.setName("#{s.nameString} Window")
      end
    end
  end

  def add_daylighting(params)
    shades = params['shades']

    shading_control_hash = {}

    zones = getThermalZones.sort_by { |z| z.name.to_s }
    zones.each do |zone|
      biggestWindow = nil
      zone.spaces.each do |space|
        space.surfaces.each do |surface|
          if (surface.surfaceType == 'Wall') && (surface.outsideBoundaryCondition == 'Outdoors')
            surface.subSurfaces.each do |sub_surface|
              if (sub_surface.subSurfaceType == 'FixedWindow') || (sub_surface.subSurfaceType == 'OperableWindow')
                if biggestWindow.nil? || (sub_surface.netArea > biggestWindow.netArea)
                  biggestWindow = sub_surface
                end

                if shades
                  construction = sub_surface.construction.get
                  shading_control = shading_control_hash[construction.handle.to_s]
                  if !shading_control
                    material = OpenStudio::Model::Blind.new(self)
                    shading_control = OpenStudio::Model::ShadingControl.new(material)
                    shading_control_hash[construction.handle.to_s] = shading_control
                  end
                  sub_surface.setShadingControl(shading_control)

                end
              end
            end
          end
        end
      end

      if biggestWindow
        vertices = biggestWindow.vertices
        centroid = OpenStudio.getCentroid(vertices).get
        outwardNormal = biggestWindow.outwardNormal
        outwardNormal.setLength(-2.0)
        position = centroid + outwardNormal
        offsetX = 0.0
        offsetY = 0.0
        offsetZ = -1.0

        dc = OpenStudio::Model::DaylightingControl.new(self)
        dc.setSpace(biggestWindow.surface.get.space.get)
        dc.setPositionXCoordinate(position.x + offsetX)
        dc.setPositionYCoordinate(position.y + offsetY)
        dc.setPositionZCoordinate(position.z + offsetZ)
        zone.setPrimaryDaylightingControl(dc)

        glr = OpenStudio::Model::GlareSensor.new(self)
        glr.setSpace(biggestWindow.surface.get.space.get)
        glr.setPositionXCoordinate(position.x + offsetX)
        glr.setPositionYCoordinate(position.y + offsetY)
        glr.setPositionZCoordinate(position.z + offsetZ)

        ill = OpenStudio::Model::IlluminanceMap.new(self)
        ill.setSpace(biggestWindow.surface.get.space.get)
        ill.setOriginXCoordinate(position.x + offsetX - 0.5)
        ill.setOriginYCoordinate(position.y + offsetY - 0.5)
        ill.setOriginZCoordinate(position.z + offsetZ)
        ill.setXLength(1)
        ill.setYLength(1)
        ill.setNumberofXGridPoints(5)
        ill.setNumberofYGridPoints(5)
        zone.setIlluminanceMap(ill)

      end
    end
  end

  def add_hvac(params)
    sys_num = params['ashrae_sys_num']

    sys_num_array = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10']

    # check the requested system number
    unless sys_num_array.include? sys_num
      puts "System type: #{sys_num} is not a valid choice"
      exit
    end

    # get the thermal zones in the self, and sort them by name to limit risks
    # of getting different results on subsequent runs
    zones = getThermalZones.sort_by { |z| z.name.to_s }

    # Add HVAC system type
    case sys_num
      # 1: PTAC, Residential
      when '01' then hvac = OpenStudio::Model.addSystemType1(self, zones)
      # 2: PTHP, Residential
      when '02'
        hvac = OpenStudio::Model.addSystemType2(self, zones)
      # 3: PSZ-AC
      when '03'
        zones.each do |zone|
          hvac = OpenStudio::Model.addSystemType3(self)
          hvac = hvac.to_AirLoopHVAC.get
          hvac.addBranchForZone(zone)
          outlet_node = hvac.supplyOutletNode
          setpoint_manager = outlet_node.setpointManagers.select { |spm| spm.to_SetpointManagerSingleZoneReheat.is_initialized }.first.to_SetpointManagerSingleZoneReheat.get
          # Set appropriate min/max temperatures (matches Zone Heat/Cool
          # sizing parameters)
          setpoint_manager.setMinimumSupplyAirTemperature(14)
          setpoint_manager.setMaximumSupplyAirTemperature(40)
          setpoint_manager.setControlZone(zone)
        end
      # 4: PSZ-HP
      when '04'
        zones.each do |zone|
          hvac = OpenStudio::Model.addSystemType4(self)
          hvac = hvac.to_AirLoopHVAC.get
          hvac.addBranchForZone(zone)
          outlet_node = hvac.supplyOutletNode
          setpoint_manager = outlet_node.setpointManagers.select { |spm| spm.to_SetpointManagerSingleZoneReheat.is_initialized }.first.to_SetpointManagerSingleZoneReheat.get
          setpoint_manager.setControlZone(zone)
        end
      # 5: Packaged VAV w/ Reheat
      when '05'
        hvac = OpenStudio::Model.addSystemType5(self)
        hvac = hvac.to_AirLoopHVAC.get
        zones.each do |zone|
          hvac.addBranchForZone(zone)
        end
      # 6: Packaged VAV w/ PFP Boxes
      when '06'
        hvac = OpenStudio::Model.addSystemType6(self)
        hvac = hvac.to_AirLoopHVAC.get
        zones.each do |zone|
          hvac.addBranchForZone(zone)
        end
      # 7: VAV w/ Reheat
      when '07'
        hvac = OpenStudio::Model.addSystemType7(self)
        hvac = hvac.to_AirLoopHVAC.get
        zones.each do |zone|
          hvac.addBranchForZone(zone)
        end
      # 8: VAV w/ PFP Boxes
      when '08'
        hvac = OpenStudio::Model.addSystemType8(self)
        hvac = hvac.to_AirLoopHVAC.get
        zones.each do |zone|
          hvac.addBranchForZone(zone)
        end
      # 9: Warm air furnace, gas fired
      when '09'
        zones.each do |zone|
          hvac = OpenStudio::Model.addSystemType9(self)
          hvac = hvac.to_AirLoopHVAC.get
          hvac.addBranchForZone(zone)
          outlet_node = hvac.supplyOutletNode
          setpoint_manager = outlet_node.setpointManagers.select { |spm| spm.to_SetpointManagerSingleZoneReheat.is_initialized }.first.to_SetpointManagerSingleZoneReheat.get
          setpoint_manager.setControlZone(zone)
        end
      # 10: Warm air furnace, electric
      when '10'
        zones.each do |zone|
          hvac = OpenStudio::Model.addSystemType10(self)
          hvac = hvac.to_AirLoopHVAC.get
          hvac.addBranchForZone(zone)
          outlet_node = hvac.supplyOutletNode
          setpoint_manager = outlet_node.setpointManagers.select { |spm| spm.to_SetpointManagerSingleZoneReheat.is_initialized }.first.to_SetpointManagerSingleZoneReheat.get
          setpoint_manager.setControlZone(zone)
        end
      # if system number is not recognized
      else puts "cannot find system number #{sys_num}"
    end
  end

  def set_constructions
    construction_library_path = "#{File.dirname(__FILE__)}/baseline_model_constructions.osm"

    # make sure the file exists on the filesystem; if it does, open it
    construction_library_path = OpenStudio::Path.new(construction_library_path)
    if OpenStudio.exists(construction_library_path)
      versionTranslator = OpenStudio::OSVersion::VersionTranslator.new
      construction_library = versionTranslator.loadModel(construction_library_path).get
    else
      puts "#{construction_library_path} couldn't be found"
    end

    # add the objects in the construction library to the model
    sets = construction_library.to_Model.getDefaultConstructionSets
    sets.first.clone(self)

    # apply the newly-added construction set to the model
    building = getBuilding
    default_construction_set = OpenStudio::Model.getDefaultConstructionSets(self)[0]
    building.setDefaultConstructionSet(default_construction_set)

    # get the air wall
    if Gem::Version.new(OpenStudio.openStudioVersion) > Gem::Version.new('3.4.0')
      construction_library.getConstructionAirBoundarys.first.clone(self)
    else
      construction_library.getConstructions.each do |c|
        if c.name.to_s.strip == 'Air_Wall'
          c.clone(self)
          break
        end
      end
    end
  end

  def set_space_type
    # method for converting from IP to SI if you know the strings of the input and the output
    ip_to_si = lambda { |number, ip_unit_string, si_unit_string|
      ip_unit = OpenStudio.createUnit(ip_unit_string, 'IP'.to_UnitSystem).get
      si_unit = OpenStudio.createUnit(si_unit_string, 'SI'.to_UnitSystem).get
      # puts "#{ip_unit} --> #{si_unit}"
      ip_quantity = OpenStudio::Quantity.new(number, ip_unit)
      si_quantity = OpenStudio.convert(ip_quantity, si_unit).get
      # puts "#{ip_quantity} = #{si_quantity}"
      return si_quantity.value
    }

    # baseline space type taken from 90.1-2004 Large Office, Whole Building on-demand space type generator
    space_type = OpenStudio::Model::SpaceType.new(self)
    space_type.setName('Baseline Model Space Type')

    # create the schedule set for the space type
    default_sch_set = OpenStudio::Model::DefaultScheduleSet.new(self)
    default_sch_set.setName('Baseline Model Schedule Set')
    space_type.setDefaultScheduleSet(default_sch_set)

    # schedule for infiltration
    sch_ruleset = OpenStudio::Model::ScheduleRuleset.new(self)
    sch_ruleset.setName('Baseline Model Infiltration Schedule')
    # Winter Design Day
    winter_dsn_day = OpenStudio::Model::ScheduleDay.new(self)
    sch_ruleset.setWinterDesignDaySchedule(winter_dsn_day)
    winter_dsn_day = sch_ruleset.winterDesignDaySchedule
    winter_dsn_day.setName('Baseline Model Infiltration Schedule Winter Design Day')
    winter_dsn_day.addValue(OpenStudio::Time.new(0, 24, 0, 0), 1)
    # Summer Design Day
    summer_dsn_day = OpenStudio::Model::ScheduleDay.new(self)
    sch_ruleset.setSummerDesignDaySchedule(summer_dsn_day)
    summer_dsn_day = sch_ruleset.summerDesignDaySchedule
    summer_dsn_day.setName('Baseline Model Infiltration Schedule Summer Design Day')
    summer_dsn_day.addValue(OpenStudio::Time.new(0, 24, 0, 0), 1)
    # Weekdays
    week_day = sch_ruleset.defaultDaySchedule
    week_day.setName('Baseline Model Infiltration Schedule Schedule All Days')
    week_day.addValue(OpenStudio::Time.new(0, 6, 0, 0), 1)
    week_day.addValue(OpenStudio::Time.new(0, 22, 0, 0), 0.25)
    week_day.addValue(OpenStudio::Time.new(0, 24, 0, 0), 1)
    # set the infiltration schedule
    infiltration_sch = default_sch_set.setInfiltrationSchedule(sch_ruleset)

    # schedule for occupancy, lights, electric equipment
    sch_ruleset = OpenStudio::Model::ScheduleRuleset.new(self)
    sch_ruleset.setName('Baseline Model People Lights and Equipment Schedule')
    # Winter Design Day
    winter_dsn_day = OpenStudio::Model::ScheduleDay.new(self)
    sch_ruleset.setWinterDesignDaySchedule(winter_dsn_day)
    winter_dsn_day = sch_ruleset.winterDesignDaySchedule
    winter_dsn_day.setName('Baseline Model People Lights and Equipment Schedule Winter Design Day')
    winter_dsn_day.addValue(OpenStudio::Time.new(0, 24, 0, 0), 0)
    # Summer Design Day
    summer_dsn_day = OpenStudio::Model::ScheduleDay.new(self)
    sch_ruleset.setSummerDesignDaySchedule(summer_dsn_day)
    summer_dsn_day = sch_ruleset.summerDesignDaySchedule
    summer_dsn_day.setName('Baseline Model People Lights and Equipment Schedule Summer Design Day')
    summer_dsn_day.addValue(OpenStudio::Time.new(0, 24, 0, 0), 1)
    # Weekdays
    week_day = sch_ruleset.defaultDaySchedule
    week_day.setName('Baseline Model People Lights and Equipment Schedule Schedule Week Day')
    week_day.addValue(OpenStudio::Time.new(0, 6, 0, 0), 0)
    week_day.addValue(OpenStudio::Time.new(0, 7, 0, 0), 0.1)
    week_day.addValue(OpenStudio::Time.new(0, 8, 0, 0), 0.2)
    week_day.addValue(OpenStudio::Time.new(0, 12, 0, 0), 0.95)
    week_day.addValue(OpenStudio::Time.new(0, 13, 0, 0), 0.5)
    week_day.addValue(OpenStudio::Time.new(0, 17, 0, 0), 0.95)
    week_day.addValue(OpenStudio::Time.new(0, 18, 0, 0), 0.7)
    week_day.addValue(OpenStudio::Time.new(0, 20, 0, 0), 0.4)
    week_day.addValue(OpenStudio::Time.new(0, 22, 0, 0), 0.1)
    week_day.addValue(OpenStudio::Time.new(0, 24, 0, 0), 0.05)
    # Saturdays
    saturday_rule = OpenStudio::Model::ScheduleRule.new(sch_ruleset)
    saturday_rule.setName('Baseline Model People Lights and Equipment Schedule Saturday Rule')
    saturday_rule.setApplySaturday(true)
    saturday = saturday_rule.daySchedule
    saturday.setName('Baseline Model People Lights and Equipment Schedule Saturday')
    saturday.addValue(OpenStudio::Time.new(0, 6, 0, 0), 0)
    saturday.addValue(OpenStudio::Time.new(0, 8, 0, 0), 0.1)
    saturday.addValue(OpenStudio::Time.new(0, 14, 0, 0), 0.5)
    saturday.addValue(OpenStudio::Time.new(0, 17, 0, 0), 0.1)
    saturday.addValue(OpenStudio::Time.new(0, 24, 0, 0), 0)
    # Sundays
    sunday_rule = OpenStudio::Model::ScheduleRule.new(sch_ruleset)
    sunday_rule.setName('Baseline Model People Lights and Equipment Schedule Sunday Rule')
    sunday_rule.setApplySunday(true)
    sunday = sunday_rule.daySchedule
    sunday.setName('Baseline Model People Lights and Equipment Schedule Schedule Sunday')
    sunday.addValue(OpenStudio::Time.new(0, 24, 0, 0), 0)
    # assign the schedule to the ruleset
    default_sch_set.setNumberofPeopleSchedule(sch_ruleset)
    default_sch_set.setLightingSchedule(sch_ruleset)
    default_sch_set.setElectricEquipmentSchedule(sch_ruleset)

    # schedule for occupant activity level = 120 W constant
    occ_activity_sch = OpenStudio::Model::ScheduleRuleset.new(self)
    occ_activity_sch.setName('Baseline Model People Activity Schedule')
    occ_activity_sch.defaultDaySchedule.setName('Baseline Model People Activity Schedule Default')
    occ_activity_sch.defaultDaySchedule.addValue(OpenStudio::Time.new(0, 24, 0, 0), 120)
    default_sch_set.setPeopleActivityLevelSchedule(occ_activity_sch)

    # outdoor air = 0.0094 m^3/s*person (20 cfm/person)
    ventilation = OpenStudio::Model::DesignSpecificationOutdoorAir.new(self)
    ventilation.setName('Baseline Model OA')
    space_type.setDesignSpecificationOutdoorAir(ventilation)
    ventilation.setOutdoorAirMethod('Sum')
    ventilation.setOutdoorAirFlowperPerson(ip_to_si.call(20, 'ft^3/min*person', 'm^3/s*person'))

    # infiltration = 0.00030226 m^3/s*m^2 exterior (0.06 cfm/ft^2 exterior)
    make_infiltration = false
    infiltration = OpenStudio::Model::SpaceInfiltrationDesignFlowRate.new(self)
    infiltration.setName('Baseline Model Infiltration')
    infiltration.setSpaceType(space_type)
    infiltration.setFlowperExteriorSurfaceArea(ip_to_si.call(0.06, 'ft^3/min*ft^2', 'm^3/s*m^2'))

    # people = 0.053820 people/m^2 (0.005 people/ft^2)
    # create the people definition
    people_def = OpenStudio::Model::PeopleDefinition.new(self)
    people_def.setName('Baseline Model People Definition')
    people_def.setPeopleperSpaceFloorArea(ip_to_si.call(0.005, 'people/ft^2', 'people/m^2'))
    # create the people instance and hook it up to the space type
    people = OpenStudio::Model::People.new(people_def)
    people.setName('Baseline Model People')
    people.setSpaceType(space_type)

    # lights = 10.763910 W/m^2 (1 W/ft^2)
    # create the lighting definition
    lights_def = OpenStudio::Model::LightsDefinition.new(self)
    lights_def.setName('Baseline Model Lights Definition')
    lights_def.setWattsperSpaceFloorArea(ip_to_si.call(1, 'W/ft^2', 'W/m^2'))
    # create the lighting instance and hook it up to the space type
    lights = OpenStudio::Model::Lights.new(lights_def)
    lights.setName('Baseline Model Lights')
    lights.setSpaceType(space_type)

    # equipment = 10.763910 W/m^2 (1 W/ft^2)
    # create the electric equipment definition
    elec_equip_def = OpenStudio::Model::ElectricEquipmentDefinition.new(self)
    elec_equip_def.setName('Baseline Model Electric Equipment Definition')
    elec_equip_def.setWattsperSpaceFloorArea(ip_to_si.call(1, 'W/ft^2', 'W/m^2'))
    # create the electric equipment instance and hook it up to the space type
    elec_equip = OpenStudio::Model::ElectricEquipment.new(elec_equip_def)
    elec_equip.setName('Baseline Model Electric Equipment')
    elec_equip.setSpaceType(space_type)

    # set the space type of all spaces by setting it at the building level
    getBuilding.setSpaceType(space_type)
  end

  def add_thermostats(params)
    heating_setpoint = params['heating_setpoint']
    cooling_setpoint = params['cooling_setpoint']

    time_24hrs = OpenStudio::Time.new(0, 24, 0, 0)

    cooling_sch = OpenStudio::Model::ScheduleRuleset.new(self)
    cooling_sch.setName('Cooling Sch')
    cooling_sch.defaultDaySchedule.setName('Cooling Sch Default')
    cooling_sch.defaultDaySchedule.addValue(time_24hrs, cooling_setpoint)

    heating_sch = OpenStudio::Model::ScheduleRuleset.new(self)
    heating_sch.setName('Heating Sch')
    heating_sch.defaultDaySchedule.setName('Heating Sch Default')
    heating_sch.defaultDaySchedule.addValue(time_24hrs, heating_setpoint)

    zones = getThermalZones.sort_by { |z| z.name.to_s }
    zones.each do |zone|
      new_thermostat = OpenStudio::Model::ThermostatSetpointDualSetpoint.new(self)

      new_thermostat.setHeatingSchedule(heating_sch)
      new_thermostat.setCoolingSchedule(cooling_sch)

      zone.setThermostatSetpointDualSetpoint(new_thermostat)
    end
  end

  # Historically, YearDescription had a default of 'UseWeatherFile' but that
  # option was not supported until 3.3.0. So it would instead default to
  # assumedBaseYear which is 2009, which starts on a Thursday.
  # Except that 3.3.0 does take it into account and Chicago EPW has a start day
  # of Sunday (and changes year to 2006). So to avoid problems, we force it to
  # Thursday explicitly
  def force_year_description
    yd = getYearDescription
    yd.setDayofWeekforStartDay('Thursday')
  end

  def save_openstudio_osm(params)
    osm_save_directory = params['osm_save_directory']
    osm_name = params['osm_name']

    force_year_description

    save_path = OpenStudio::Path.new("#{osm_save_directory}/#{osm_name}")
    # puts "Saving to #{save_path}"
    save(save_path, true)
  end

  def add_design_days
    ddy_path = nil

    workflow = OpenStudio::WorkflowJSON.load(OpenStudio::Path.new('in.osw'))
    if !workflow.empty?
      weather = workflow.get.weatherFile
      if !weather.empty?
        weather_path = workflow.get.findFile(weather.get)
        if !weather_path.empty?
          ddy_path = OpenStudio::Path.new(weather_path.get.to_s.gsub('.epw', '.ddy'))
        end
      end
    end

    # make sure the file exists on the filesystem; if it does, open it
    if ddy_path && OpenStudio.exists(ddy_path)
      ddy_idf = OpenStudio::IdfFile.load(ddy_path, 'EnergyPlus'.to_IddFileType).get
      ddy_workspace = OpenStudio::Workspace.new(ddy_idf)
      reverse_translator = OpenStudio::EnergyPlus::ReverseTranslator.new
      ddy_model = reverse_translator.translateWorkspace(ddy_workspace)

      # Try to limit to the two main design days
      ddy_objects = ddy_model.getDesignDays.select { |d| d.name.get.include?('.4% Condns DB') || d.name.get.include?('99.6% Condns DB') }
      # Otherwise, get all .4% and 99.6%
      if ddy_objects.size < 2
        ddy_objects = ddy_model.getDesignDays.select { |d| d.name.get.include?('.4%') || d.name.get.include?('99.6%') }
      end
      # add the objects in the ddy file to the model
      addObjects(ddy_objects)
    else
      puts "#{ddy_path} couldn't be found"
    end

    # Do a couple more things
    sc = getSimulationControl
    sc.setRunSimulationforSizingPeriods(false)
    sc.setRunSimulationforWeatherFileRunPeriods(true)

    timestep = getTimestep
    timestep.setNumberOfTimestepsPerHour(4)
  end

  attr_accessor :standards

  def add_standards(input_hash)
    standards_hash = {}
    standards_hash = standards_hash.merge(input_hash)
    self.standards = standards_hash
  end

  # Method to search through a hash for the objects that meets the
  # desired search criteria, as passed via a hash.  If capacity is supplied,
  # the objects will only be returned if the specified capacity is between
  # the minimum_capacity and maximum_capacity values.
  # Returns an Array (empty if nothing found) of matching objects.
  def find_objects(hash_of_objects, search_criteria, capacity = nil)
    desired_object = nil
    search_criteria_matching_objects = []
    matching_objects = []

    # Compare each of the objects against the search criteria
    hash_of_objects.each do |object|
      meets_all_search_criteria = true
      search_criteria.each do |key, value|
        # Don't check non-existent search criteria
        next unless object.key?(key)

        # Stop as soon as one of the search criteria is not met
        if object[key] != value
          meets_all_search_criteria = false
          break
        end
      end
      # Skip objects that don't meet all search criteria
      next if meets_all_search_criteria == false

      # If made it here, object matches all search criteria
      search_criteria_matching_objects << object
    end

    # If capacity was specified, narrow down the matching objects
    if capacity.nil?
      matching_objects = search_criteria_matching_objects
    else
      # Round up if capacity is an integer
      if capacity == capacity.round
        capacity += (capacity * 0.01)
      end
      search_criteria_matching_objects.each do |object|
        # Skip objects that don't have fields for minimum_capacity and maximum_capacity
        next if !object.key?('minimum_capacity') || !object.key?('maximum_capacity')
        # Skip objects that don't have values specified for minimum_capacity and maximum_capacity
        next if object['minimum_capacity'].nil? || object['maximum_capacity'].nil?
        # Skip objects whose the minimum capacity is below the specified capacity
        next if capacity <= object['minimum_capacity']
        # Skip objects whose max
        next if capacity > object['maximum_capacity']

        # Found a matching object
        matching_objects << object
      end
    end

    # Check the number of matching objects found
    if matching_objects.empty?
      desired_object = nil
      # OpenStudio::logFree(OpenStudio::Warn, 'openstudio.standards.Model', "Find objects search criteria returned no results. Search criteria: #{search_criteria}, capacity = #{capacity}.  Called from #{caller(0)[1]}.")
    end

    return matching_objects
  end

  # Create a schedule from the openstudio standards dataset.
  # TODO make return an OptionalScheduleRuleset
  def add_schedule(schedule_name)
    return nil if schedule_name.nil? || (schedule_name == '')

    # First check model and return schedule if it already exists
    getSchedules.each do |schedule|
      if schedule.name.get.to_s == schedule_name
        # OpenStudio::logFree(OpenStudio::Debug, 'openstudio.standards.Model', "Already added schedule: #{schedule_name}")
        return schedule
      end
    end

    require 'date'

    # OpenStudio::logFree(OpenStudio::Info, 'openstudio.standards.Model', "Adding schedule: #{schedule_name}")

    # Find all the schedule rules that match the name
    rules = find_objects(standards['schedules'], { 'name' => schedule_name })
    if rules.empty?
      # OpenStudio::logFree(OpenStudio::Warn, 'openstudio.standards.Model', "Cannot find data for schedule: #{schedule_name}, will not be created.")
      return false # TODO: change to return empty optional schedule:ruleset?
    end

    # Helper method to fill in hourly values
    add_vals_to_sch = lambda { |day_sch, sch_type, values|
      case sch_type
      when 'Constant'
        day_sch.addValue(OpenStudio::Time.new(0, 24, 0, 0), values[0])
      when 'Hourly'
        for i in 0..23
          next if values[i] == values[i + 1]

          day_sch.addValue(OpenStudio::Time.new(0, i + 1, 0, 0), values[i])
        end
      end
    }

    # Make a schedule ruleset
    sch_ruleset = OpenStudio::Model::ScheduleRuleset.new(self)
    sch_ruleset.setName(schedule_name.to_s)

    # Loop through the rules, making one for each row in the spreadsheet
    rules.each do |rule|
      day_types = rule['day_types']
      start_date = DateTime.parse(rule['start_date'])
      end_date = DateTime.parse(rule['end_date'])
      sch_type = rule['type']
      values = rule['values']

      # Day Type choices: Wkdy, Wknd, Mon, Tue, Wed, Thu, Fri, Sat, Sun, WntrDsn, SmrDsn, Hol

      # Default
      if day_types.include?('Default')
        day_sch = sch_ruleset.defaultDaySchedule
        day_sch.setName("#{schedule_name} Default")
        add_vals_to_sch.call(day_sch, sch_type, values)
      end

      # Winter Design Day
      if day_types.include?('WntrDsn')
        day_sch = OpenStudio::Model::ScheduleDay.new(self)
        sch_ruleset.setWinterDesignDaySchedule(day_sch)
        day_sch = sch_ruleset.winterDesignDaySchedule
        day_sch.setName("#{schedule_name} Winter Design Day")
        add_vals_to_sch.call(day_sch, sch_type, values)
      end

      # Summer Design Day
      if day_types.include?('SmrDsn')
        day_sch = OpenStudio::Model::ScheduleDay.new(self)
        sch_ruleset.setSummerDesignDaySchedule(day_sch)
        day_sch = sch_ruleset.summerDesignDaySchedule
        day_sch.setName("#{schedule_name} Summer Design Day")
        add_vals_to_sch.call(day_sch, sch_type, values)
      end

      # Other days (weekdays, weekends, etc)
      if day_types.include?('Wknd') ||
         day_types.include?('Wkdy') ||
         day_types.include?('Sat') ||
         day_types.include?('Sun') ||
         day_types.include?('Mon') ||
         day_types.include?('Tue') ||
         day_types.include?('Wed') ||
         day_types.include?('Thu') ||
         day_types.include?('Fri')

        # Make the Rule
        sch_rule = OpenStudio::Model::ScheduleRule.new(sch_ruleset)
        day_sch = sch_rule.daySchedule
        day_sch.setName("#{schedule_name} Summer Design Day")
        add_vals_to_sch.call(day_sch, sch_type, values)

        # Set the dates when the rule applies
        sch_rule.setStartDate(OpenStudio::Date.new(OpenStudio::MonthOfYear.new(start_date.month.to_i), start_date.day.to_i))
        sch_rule.setEndDate(OpenStudio::Date.new(OpenStudio::MonthOfYear.new(end_date.month.to_i), end_date.day.to_i))

        # Set the days when the rule applies
        # Weekends
        if day_types.include?('Wknd')
          sch_rule.setApplySaturday(true)
          sch_rule.setApplySunday(true)
        end
        # Weekdays
        if day_types.include?('Wkdy')
          sch_rule.setApplyMonday(true)
          sch_rule.setApplyTuesday(true)
          sch_rule.setApplyWednesday(true)
          sch_rule.setApplyThursday(true)
          sch_rule.setApplyFriday(true)
        end
        # Individual Days
        sch_rule.setApplyMonday(true) if day_types.include?('Mon')
        sch_rule.setApplyTuesday(true) if day_types.include?('Tue')
        sch_rule.setApplyWednesday(true) if day_types.include?('Wed')
        sch_rule.setApplyThursday(true) if day_types.include?('Thu')
        sch_rule.setApplyFriday(true) if day_types.include?('Fri')
        sch_rule.setApplySaturday(true) if day_types.include?('Sat')
        sch_rule.setApplySunday(true) if day_types.include?('Sun')

      end
      # Next rule
    end

    return sch_ruleset
  end

  def add_swh_end_uses(swh_loop, flow_rate_fraction_schedule)
    # Water use connection
    swh_connection = OpenStudio::Model::WaterUseConnections.new(self)

    # Water fixture definition
    water_fixture_def = OpenStudio::Model::WaterUseEquipmentDefinition.new(self)
    rated_flow_rate_gal_per_min = 1
    rated_flow_rate_m3_per_s = OpenStudio.convert(rated_flow_rate_gal_per_min, 'gal/min', 'm^3/s').get
    water_fixture_def.setPeakFlowRate(rated_flow_rate_m3_per_s)
    water_fixture_def.setName("Service Water Use Def #{rated_flow_rate_gal_per_min.round(2)}gal/min")
    # Target mixed water temperature
    mixed_water_temp_f = 110
    mixed_water_temp_sch = OpenStudio::Model::ScheduleRuleset.new(self)
    mixed_water_temp_sch.defaultDaySchedule.addValue(OpenStudio::Time.new(0, 24, 0, 0), OpenStudio.convert(mixed_water_temp_f, 'F', 'C').get)
    water_fixture_def.setTargetTemperatureSchedule(mixed_water_temp_sch)

    # Water use equipment
    water_fixture = OpenStudio::Model::WaterUseEquipment.new(water_fixture_def)
    schedule = add_schedule(flow_rate_fraction_schedule)
    water_fixture.setFlowRateFractionSchedule(schedule)
    water_fixture.setName("Service Water Use #{rated_flow_rate_gal_per_min.round(2)}gal/min")
    swh_connection.addWaterUseEquipment(water_fixture)

    # Connect the water use connection to the SWH loop
    swh_loop.addDemandBranchForComponent(swh_connection)
  end

  def add_swh_loop(water_heater_type, ambient_temperature_thermal_zone = nil)
    # Service water heating loop
    service_water_loop = OpenStudio::Model::PlantLoop.new(self)
    service_water_loop.setName('Service Water Loop')
    service_water_loop.setMaximumLoopTemperature(60)
    service_water_loop.setMinimumLoopTemperature(10)

    # Temperature schedule type limits
    temp_sch_type_limits = OpenStudio::Model::ScheduleTypeLimits.new(self)
    temp_sch_type_limits.setName('Temperature Schedule Type Limits')
    temp_sch_type_limits.setLowerLimitValue(0.0)
    temp_sch_type_limits.setUpperLimitValue(100.0)
    temp_sch_type_limits.setNumericType('Continuous')
    temp_sch_type_limits.setUnitType('Temperature')

    # Service water heating loop controls
    swh_temp_f = 140
    swh_delta_t_r = 9 # 9F delta-T
    swh_temp_c = OpenStudio.convert(swh_temp_f, 'F', 'C').get
    swh_delta_t_k = OpenStudio.convert(swh_delta_t_r, 'R', 'K').get
    swh_temp_sch = OpenStudio::Model::ScheduleRuleset.new(self)
    swh_temp_sch.setName("Hot Water Loop Temp - #{swh_temp_f}F")
    swh_temp_sch.defaultDaySchedule.setName("Hot Water Loop Temp - #{swh_temp_f}F Default")
    swh_temp_sch.defaultDaySchedule.addValue(OpenStudio::Time.new(0, 24, 0, 0), swh_temp_c)
    swh_temp_sch.setScheduleTypeLimits(temp_sch_type_limits)
    swh_stpt_manager = OpenStudio::Model::SetpointManagerScheduled.new(self, swh_temp_sch)
    swh_stpt_manager.addToNode(service_water_loop.supplyOutletNode)
    sizing_plant = service_water_loop.sizingPlant
    sizing_plant.setLoopType('Heating')
    sizing_plant.setDesignLoopExitTemperature(swh_temp_c)
    sizing_plant.setLoopDesignTemperatureDifference(swh_delta_t_k)

    # Service water heating pump
    swh_pump_head_press_pa = 0.001
    swh_pump_motor_efficiency = 1

    swh_pump = OpenStudio::Model::PumpConstantSpeed.new(self)
    swh_pump.setName('Service Water Loop Pump')
    swh_pump.setRatedPumpHead(swh_pump_head_press_pa.to_f)
    swh_pump.setMotorEfficiency(swh_pump_motor_efficiency)
    swh_pump.setPumpControlType('Intermittent')
    swh_pump.addToNode(service_water_loop.supplyInletNode)

    water_heater = add_water_heater(water_heater_type, 'Natural Gas', temp_sch_type_limits, swh_temp_sch, ambient_temperature_thermal_zone)
    service_water_loop.addSupplyBranchForComponent(water_heater)

    # Service water heating loop bypass pipes
    water_heater_bypass_pipe = OpenStudio::Model::PipeAdiabatic.new(self)
    service_water_loop.addSupplyBranchForComponent(water_heater_bypass_pipe)
    coil_bypass_pipe = OpenStudio::Model::PipeAdiabatic.new(self)
    service_water_loop.addDemandBranchForComponent(coil_bypass_pipe)
    supply_outlet_pipe = OpenStudio::Model::PipeAdiabatic.new(self)
    supply_outlet_pipe.addToNode(service_water_loop.supplyOutletNode)
    demand_inlet_pipe = OpenStudio::Model::PipeAdiabatic.new(self)
    demand_inlet_pipe.addToNode(service_water_loop.demandInletNode)
    demand_outlet_pipe = OpenStudio::Model::PipeAdiabatic.new(self)
    demand_outlet_pipe.addToNode(service_water_loop.demandOutletNode)

    return service_water_loop
  end

  def add_water_heater(water_heater_type, water_heater_fuel, temp_sch_type_limits = nil, swh_temp_sch = nil, ambient_temperature_thermal_zone = nil, service_water_flowrate_schedule = nil)
    # Water heater
    # TODO Standards - Change water heater methodology to follow
    # 'Model Enhancements Appendix A.'
    water_heater_capacity_btu_per_hr = 2883000
    water_heater_capacity_kbtu_per_hr = OpenStudio.convert(water_heater_capacity_btu_per_hr, 'Btu/hr', 'kBtu/hr').get
    water_heater_vol_gal = 100

    if temp_sch_type_limits.nil?
      # Temperature schedule type limits
      temp_sch_type_limits = OpenStudio::Model::ScheduleTypeLimits.new(self)
      temp_sch_type_limits.setName('Temperature Schedule Type Limits')
      temp_sch_type_limits.setLowerLimitValue(0.0)
      temp_sch_type_limits.setUpperLimitValue(100.0)
      temp_sch_type_limits.setNumericType('Continuous')
      temp_sch_type_limits.setUnitType('Temperature')
    end

    if swh_temp_sch.nil?
      # Service water heating loop controls
      swh_temp_f = 140
      swh_delta_t_r = 9 # 9F delta-T
      swh_temp_c = OpenStudio.convert(swh_temp_f, 'F', 'C').get
      swh_delta_t_k = OpenStudio.convert(swh_delta_t_r, 'R', 'K').get
      swh_temp_sch = OpenStudio::Model::ScheduleRuleset.new(self)
      swh_temp_sch.setName("Hot Water Loop Temp - #{swh_temp_f}F")
      swh_temp_sch.defaultDaySchedule.setName("Hot Water Loop Temp - #{swh_temp_f}F Default")
      swh_temp_sch.defaultDaySchedule.addValue(OpenStudio::Time.new(0, 24, 0, 0), swh_temp_c)
      swh_temp_sch.setScheduleTypeLimits(temp_sch_type_limits)
    end

    # Water heater depends on the fuel type
    if water_heater_type == 'Stratified'
      water_heater = OpenStudio::Model::WaterHeaterStratified.new(self)
    else
      water_heater = OpenStudio::Model::WaterHeaterMixed.new(self)
      water_heater.setSetpointTemperatureSchedule(swh_temp_sch)
      water_heater.setHeaterMaximumCapacity(OpenStudio.convert(water_heater_capacity_btu_per_hr, 'Btu/hr', 'W').get)
      water_heater.setDeadbandTemperatureDifference(OpenStudio.convert(3.6, 'R', 'K').get)
      water_heater.setHeaterControlType('Cycle')
    end

    water_heater.setName("#{water_heater_vol_gal}gal #{water_heater_fuel} Water Heater - #{water_heater_capacity_kbtu_per_hr.round}kBtu/hr")
    water_heater.setTankVolume(OpenStudio.convert(water_heater_vol_gal, 'gal', 'm^3').get)

    if ambient_temperature_thermal_zone.nil?
      # Assume the water heater is indoors at 70F for now
      default_water_heater_ambient_temp_sch = OpenStudio::Model::ScheduleRuleset.new(self)
      default_water_heater_ambient_temp_sch.setName('Water Heater Ambient Temp Schedule - 70F')
      default_water_heater_ambient_temp_sch.defaultDaySchedule.setName('Water Heater Ambient Temp Schedule - 70F Default')
      default_water_heater_ambient_temp_sch.defaultDaySchedule.addValue(OpenStudio::Time.new(0, 24, 0, 0), OpenStudio.convert(70, 'F', 'C').get)
      default_water_heater_ambient_temp_sch.setScheduleTypeLimits(temp_sch_type_limits)
      water_heater.setAmbientTemperatureIndicator('Schedule')
      water_heater.setAmbientTemperatureSchedule(default_water_heater_ambient_temp_sch)
    else
      water_heater.setAmbientTemperatureIndicator('ThermalZone')
      water_heater.setAmbientTemperatureThermalZone ambient_temperature_thermal_zone
    end

    water_heater.setMaximumTemperatureLimit(OpenStudio.convert(180, 'F', 'C').get)
    water_heater.setOffCycleParasiticHeatFractiontoTank(0.8)
    water_heater.setIndirectWaterHeatingRecoveryTime(1.5) # 1.5hrs
    case water_heater_fuel
    when 'Electricity'
      water_heater.setHeaterFuelType('Electricity')
      water_heater.setHeaterThermalEfficiency(1.0)
      water_heater.setOffCycleParasiticFuelConsumptionRate(OpenStudio.convert(68.24, 'Btu/hr', 'W').get)
      water_heater.setOnCycleParasiticFuelConsumptionRate(OpenStudio.convert(68.24, 'Btu/hr', 'W').get)
      water_heater.setOffCycleParasiticFuelType('Electricity')
      water_heater.setOnCycleParasiticFuelType('Electricity')
      if water_heater_type == 'Stratified'
        water_heater.setOffCycleFlueLossCoefficienttoAmbientTemperature(1.053)
      else
        water_heater.setOffCycleLossCoefficienttoAmbientTemperature(1.053)
        water_heater.setOnCycleLossCoefficienttoAmbientTemperature(1.053)
      end
    when 'Natural Gas'
      water_heater.setHeaterFuelType('NaturalGas')
      water_heater.setHeaterThermalEfficiency(0.78)
      water_heater.setOffCycleParasiticFuelConsumptionRate(OpenStudio.convert(68.24, 'Btu/hr', 'W').get)
      water_heater.setOnCycleParasiticFuelConsumptionRate(OpenStudio.convert(68.24, 'Btu/hr', 'W').get)
      water_heater.setOffCycleParasiticFuelType('NaturalGas')
      water_heater.setOnCycleParasiticFuelType('NaturalGas')
      if water_heater_type == 'Stratified'
        water_heater.setOffCycleFlueLossCoefficienttoAmbientTemperature(6.0)
      else
        water_heater.setOffCycleLossCoefficienttoAmbientTemperature(6.0)
        water_heater.setOnCycleLossCoefficienttoAmbientTemperature(6.0)
      end
    end

    if !service_water_flowrate_schedule.nil?
      rated_flow_rate_gal_per_min = 0.164843359974645
      rated_flow_rate_m3_per_s = OpenStudio.convert(rated_flow_rate_gal_per_min, 'gal/min', 'm^3/s').get
      water_heater.setPeakUseFlowRate(rated_flow_rate_m3_per_s)

      schedule = add_schedule(service_water_flowrate_schedule)
      water_heater.setUseFlowRateFractionSchedule(schedule)
    end

    return water_heater
  end

  # NOTE: a very rough way
  def rename_loop_nodes
    getPlantLoops.each do |p|
      prefix = p.name.to_s

      p.supplyComponents.reverse.each do |c|
        next if c.to_Node.is_initialized

        if c.to_ConnectorMixer.is_initialized
          c.setName("#{prefix} Supply ConnectorMixer")
        elsif c.to_ConnectorSplitter.is_initialized
          c.setName("#{prefix} Supply ConnectorSplitter")
        else

          obj_type = c.iddObjectType.valueName
          obj_type_name = obj_type.gsub('OS_', '').gsub('_', '')

          if c.to_PumpVariableSpeed.is_initialized
            c.setName("#{prefix} VSD Pump")
          elsif c.to_PumpConstantSpeed.is_initialized
            c.setName("#{prefix} CstSpeed Pump")
          elsif c.to_HeaderedPumpsVariableSpeed.is_initialized
            c.setName("#{prefix} Headered VSD Pump")
          elsif c.to_HeaderedPumpsConstantSpeed.is_initialized
            c.setName("#{prefix} Headered CstSpeed Pump")
          end

          method_name = "to_#{obj_type_name}"
          next if !c.respond_to?(method_name)

          actual_thing = c.method(method_name).call
          next if actual_thing.empty?

          actual_thing = actual_thing.get
          if actual_thing.respond_to?('inletModelObject') && actual_thing.inletModelObject.is_initialized
            inlet_mo = actual_thing.inletModelObject.get
            inlet_mo.setName("#{prefix} Supply Side #{actual_thing.name} Inlet Node")
          end
          if actual_thing.respond_to?('outletModelObject') && actual_thing.outletModelObject.is_initialized
            outlet_mo = actual_thing.outletModelObject.get
            outlet_mo.setName("#{prefix} Supply Side #{actual_thing.name} Outlet Node")
          end

          # WaterToWaterComponent
          # Yep, that part is gross, but I don't care
          if actual_thing.respond_to?('supplyInletModelObject') && actual_thing.supplyInletModelObject.is_initialized
            inlet_node = actual_thing.supplyInletModelObject.get.to_Node.get
            if inlet_node.plantLoop.is_initialized && (inlet_node.plantLoop.get == p)
              inlet_node.setName("#{prefix} Supply Side #{actual_thing.name} Inlet Node")
            end
          end
          if actual_thing.respond_to?('supplyOutletModelObject') && actual_thing.supplyOutletModelObject.is_initialized
            outlet_node = actual_thing.supplyOutletModelObject.get.to_Node.get
            if outlet_node.plantLoop.is_initialized && (outlet_node.plantLoop.get == p)
              outlet_node.setName("#{prefix} Supply Side #{actual_thing.name} Outlet Node")
            end
          end

          if actual_thing.respond_to?('tertiaryInletModelObject') && actual_thing.tertiaryInletModelObject.is_initialized
            inlet_node = actual_thing.tertiaryInletModelObject.get.to_Node.get
            if inlet_node.plantLoop.is_initialized && (inlet_node.plantLoop.get == p)
              inlet_node.setName("#{prefix} Tertiary Side #{actual_thing.name} Inlet Node")
            end
          end
          if actual_thing.respond_to?('tertiaryOutletModelObject') && actual_thing.tertiaryOutletModelObject.is_initialized
            outlet_node = actual_thing.tertiaryOutletModelObject.get.to_Node.get
            if outlet_node.plantLoop.is_initialized && (outlet_node.plantLoop.get == p)
              outlet_node.setName("#{prefix} Tertiary Side #{actual_thing.name} Outlet Node")
            end
          end

        end
      end

      p.demandComponents.reverse.each do |c|
        next if c.to_Node.is_initialized

        if c.to_ConnectorMixer.is_initialized
          c.setName("#{prefix} Demand ConnectorMixer")
        elsif c.to_ConnectorSplitter.is_initialized
          c.setName("#{prefix} Demand ConnectorSplitter")
        else
          obj_type = c.iddObjectType.valueName
          obj_type_name = obj_type.gsub('OS_', '').gsub('_', '')
          method_name = "to_#{obj_type_name}"
          next if !c.respond_to?(method_name)

          actual_thing = c.method(method_name).call
          next if actual_thing.empty?

          actual_thing = actual_thing.get
          if actual_thing.respond_to?('inletModelObject') && actual_thing.inletModelObject.is_initialized
            inlet_mo = actual_thing.inletModelObject.get
            inlet_mo.setName("#{prefix} Demand Side #{actual_thing.name} Inlet Node")
          end
          if actual_thing.respond_to?('outletModelObject') && actual_thing.outletModelObject.is_initialized
            outlet_mo = actual_thing.outletModelObject.get
            outlet_mo.setName("#{prefix} Demand Side #{actual_thing.name} Outlet Node")
          end

          # WaterToAirComponent
          if actual_thing.respond_to?('waterInletModelObject') && actual_thing.waterInletModelObject.is_initialized
            inlet_mo = actual_thing.waterInletModelObject.get
            inlet_mo.setName("#{prefix} Demand Side #{actual_thing.name} Inlet Node")
          end
          if actual_thing.respond_to?('waterOutletModelObject') && actual_thing.waterOutletModelObject.is_initialized
            outlet_mo = actual_thing.waterOutletModelObject.get
            outlet_mo.setName("#{prefix} Demand Side #{actual_thing.name} Outlet Node")
          end

          if actual_thing.respond_to?('demandInletModelObject') && actual_thing.demandInletModelObject.is_initialized
            inlet_node = actual_thing.demandInletModelObject.get.to_Node.get
            if inlet_node.plantLoop.is_initialized && (inlet_node.plantLoop.get == p)
              inlet_node.setName("#{prefix} Demand Side #{actual_thing.name} Inlet Node")
            end
          end
          if actual_thing.respond_to?('demandOutletModelObject') && actual_thing.demandOutletModelObject.is_initialized
            outlet_node = actual_thing.demandOutletModelObject.get.to_Node.get
            if outlet_node.plantLoop.is_initialized && (outlet_node.plantLoop.get == p)
              outlet_node.setName("#{prefix} Demand Side #{actual_thing.name} Outlet Node")
            end
          end

        end
      end

      node = p.supplyInletNode
      new_name = 'Supply Inlet Node'
      new_name = "#{prefix} #{new_name}"
      node.setName(new_name)

      node = p.supplyOutletNode
      new_name = 'Supply Outlet Node'
      new_name = "#{prefix} #{new_name}"
      node.setName(new_name)

      # Demand Side
      node = p.demandInletNode
      new_name = 'Demand Inlet Node'
      new_name = "#{prefix} #{new_name}"
      node.setName(new_name)

      node = p.demandOutletNode
      new_name = 'Demand Outlet Node'
      new_name = "#{prefix} #{new_name}"
      node.setName(new_name)
    end
  end

  # NOTE: Not in the least complete, but I don't need it right now
  def rename_air_nodes
    # Rename some nodes and such, for ease of debugging
    getAirLoopHVACs.each do |a|
      a.supplyInletNode.setName("#{a.name} Supply Inlet Node")
      a.supplyOutletNode.setName("#{a.name} Supply Outlet Node")
      a.mixedAirNode.get.setName("#{a.name} Mixed Air Node")
    end

    # Rename Zone Air Nodes
    getThermalZones.each { |z| z.zoneAirNode.setName("#{z.name} Zone Air Node") }

    # Rename thermostats
    getThermostatSetpointDualSetpoints.each { |t| t.setName("#{t.thermalZone.get.name} ThermostatSetpointDualSetpoint") }
  end
end
