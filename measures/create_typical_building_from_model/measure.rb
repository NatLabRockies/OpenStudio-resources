# see the URL below for information on how to write OpenStudio measures
# http://nrel.github.io/OpenStudio-user-documentation/reference/measure_writing_guide/

# start the measure
class CreateTypicalBuildingFromModel < OpenStudio::Measure::ModelMeasure
  require 'openstudio-standards'

  # require all .rb files in resources folder
  Dir[File.dirname(__FILE__) + '/resources/*.rb'].each { |file| require file }

  # resource file modules
  include OsLib_HelperMethods
  include OsLib_ModelGeneration

  # human readable name
  def name
    return 'Create Typical Building from Model'
  end

  # human readable description
  def description
    return 'Takes a model with space and stub space types, and assigns constructions, schedules, internal loads, hvac, and other loads such as exterior lights and service water heating. The end result is somewhat like a custom protptye model with user geometry, but it may use different HVAC systems.'
  end

  # human readable description of modeling approach
  def modeler_description
    return 'Initially this was intended for stub space types, but it is possible that it will be run on models tha talready have internal loads, schedules, or constructions that should be preserved. Set it up to support addition at later date of bool args to skip specific types of model elements.'
  end

  # define the arguments that the user will input
  def arguments(model)
    args = OpenStudio::Measure::OSArgumentVector.new

    # see if building name contains any template values
    default_string = '90.1-2010'
    get_templates.each do |template_string|
      if model.getBuilding.name.to_s.include?(template_string)
        default_string = template_string
        next
      end
    end

    # Make argument for template
    template = OpenStudio::Measure::OSArgument.makeChoiceArgument('template', get_templates, true)
    template.setDisplayName('Target Standard')
    template.setDefaultValue(default_string)
    args << template

    # Make argument for system type
    hvac_chs = OpenStudio::StringVector.new
    hvac_chs << 'Inferred'
    hvac_chs << 'Ideal Air Loads'
    hvac_chs << 'PTAC with hot water heat'
    hvac_chs << 'PTAC with gas coil heat'
    hvac_chs << 'PTAC with electric baseboard heat'
    hvac_chs << 'PTAC with no heat'
    hvac_chs << 'PTAC with district hot water heat'
    hvac_chs << 'PTHP'
    hvac_chs << 'PSZ-AC with gas coil heat'
    hvac_chs << 'PSZ-AC with electric baseboard heat'
    hvac_chs << 'PSZ-AC with no heat'
    hvac_chs << 'PSZ-AC with district hot water heat'
    hvac_chs << 'PSZ-HP'
    hvac_chs << 'Fan coil district chilled water with no heat'
    hvac_chs << 'Fan coil district chilled water and boiler'
    hvac_chs << 'Fan coil district chilled water unit heaters'
    hvac_chs << 'Fan coil district chilled water electric baseboard heat'
    hvac_chs << 'Fan coil district hot and chilled water'
    hvac_chs << 'Fan coil district hot water and chiller'
    hvac_chs << 'Fan coil chiller with no heat'
    hvac_chs << 'Baseboard district hot water heat'
    hvac_chs << 'Baseboard district hot water heat with direct evap coolers'
    hvac_chs << 'Baseboard electric heat'
    hvac_chs << 'Baseboard electric heat with direct evap coolers'
    hvac_chs << 'Baseboard hot water heat'
    hvac_chs << 'Baseboard hot water heat with direct evap coolers'
    hvac_chs << 'Window AC with no heat'
    hvac_chs << 'Window AC with forced air furnace'
    hvac_chs << 'Window AC with district hot water baseboard heat'
    hvac_chs << 'Window AC with hot water baseboard heat'
    hvac_chs << 'Window AC with electric baseboard heat'
    hvac_chs << 'Window AC with unit heaters'
    hvac_chs << 'Direct evap coolers'
    hvac_chs << 'Direct evap coolers with unit heaters'
    hvac_chs << 'Unit heaters'
    hvac_chs << 'Heat pump heat with no cooling'
    hvac_chs << 'Heat pump heat with direct evap cooler'
    hvac_chs << 'VAV with reheat'
    hvac_chs << 'VAV with PFP boxes'
    hvac_chs << 'VAV with gas reheat'
    hvac_chs << 'VAV with zone unit heaters'
    hvac_chs << 'VAV with electric baseboard heat'
    hvac_chs << 'VAV cool with zone heat pump heat'
    hvac_chs << 'PVAV with reheat'
    hvac_chs << 'PVAV with PFP boxes'
    hvac_chs << 'Residential forced air'
    hvac_chs << 'Residential forced air cooling hot water baseboard heat'
    hvac_chs << 'Residential forced air with district hot water'
    hvac_chs << 'Residential heat pump'
    hvac_chs << 'Forced air furnace'
    hvac_chs << 'Forced air furnace district chilled water fan coil'
    hvac_chs << 'Forced air furnace direct evap cooler'
    hvac_chs << 'Residential AC with no heat'
    hvac_chs << 'Residential AC with electric baseboard heat'
    system_type = OpenStudio::Measure::OSArgument.makeChoiceArgument('system_type', hvac_chs, true)
    system_type.setDisplayName('HVAC System Type')
    system_type.setDefaultValue('Inferred')
    args << system_type

    # Make argument for HVAC delivery type
    hvac_type_chs = OpenStudio::StringVector.new
    hvac_type_chs << 'Forced Air'
    hvac_type_chs << 'Hydronic'
    hvac_delivery_type = OpenStudio::Measure::OSArgument.makeChoiceArgument('hvac_delivery_type', hvac_type_chs, true)
    hvac_delivery_type.setDisplayName('HVAC System Delivery Type')
    hvac_delivery_type.setDescription('How the HVAC system delivers heating or cooling to the zone.')
    hvac_delivery_type.setDefaultValue('Forced Air')
    args << hvac_delivery_type

    # Make argument for HVAC heating source
    htg_src_chs = OpenStudio::StringVector.new
    htg_src_chs << 'Electricity'
    htg_src_chs << 'NaturalGas'
    htg_src_chs << 'DistrictHeating'
    htg_src_chs << 'DistrictAmbient'
    htg_src = OpenStudio::Measure::OSArgument.makeChoiceArgument('htg_src', htg_src_chs, true)
    htg_src.setDisplayName('HVAC Heating Source')
    htg_src.setDescription('The primary source of heating used by HVAC systems in the model.')
    htg_src.setDefaultValue('NaturalGas')
    args << htg_src

    # Make argument for HVAC cooling source
    clg_src_chs = OpenStudio::StringVector.new
    clg_src_chs << 'Electricity'
    clg_src_chs << 'DistrictCooling'
    clg_src_chs << 'DistrictAmbient'
    clg_src = OpenStudio::Measure::OSArgument.makeChoiceArgument('clg_src', clg_src_chs, true)
    clg_src.setDisplayName('HVAC Cooling Source')
    clg_src.setDescription('The primary source of cooling used by HVAC systems in the model.')
    clg_src.setDefaultValue('Electricity')
    args << clg_src

    #     # fuel choices for multiple arguments
    #     fuel_choices = OpenStudio::StringVector.new
    #     fuel_choices << "Electric"
    #     fuel_choices << "Gas"
    #     fuel_choices << "Infer from HVAC System Type"
    #
    #     # make argument for fuel type (not used yet)
    #     fuel_type_swh = OpenStudio::Measure::OSArgument::makeChoiceArgument("fuel_type_swh", fuel_choices,true)
    #     fuel_type_swh.setDisplayName("Fuel Type for Service Water Heating Supply")
    #     fuel_type_swh.setDefaultValue("Infer from HVAC System Type")
    #     args << fuel_type_swh
    #
    #     # make argument for fuel type (not used yet)
    #     fuel_type_cooking = OpenStudio::Measure::OSArgument::makeChoiceArgument("fuel_type_cooking", fuel_choices,true)
    #     fuel_type_cooking.setDisplayName("Fuel Type for Cooking Loads")
    #     fuel_type_cooking.setDefaultValue("Gas")
    #     args << fuel_type_cooking
    #
    #     # make argument for fuel type (not used yet)
    #     fuel_type_laundry = OpenStudio::Measure::OSArgument::makeChoiceArgument("fuel_type_laundry", fuel_choices,true)
    #     fuel_type_laundry.setDisplayName("Fuel Type for Laundry Dryer Loads")
    #     fuel_type_laundry.setDefaultValue("Electric")
    #     args << fuel_type_laundry

    # make argument for kitchen makeup
    kitchen_makeup_choices = OpenStudio::StringVector.new
    kitchen_makeup_choices << 'None'
    kitchen_makeup_choices << 'Largest Zone'
    kitchen_makeup_choices << 'Adjacent'
    kitchen_makeup = OpenStudio::Measure::OSArgument.makeChoiceArgument('kitchen_makeup', kitchen_makeup_choices, true)
    kitchen_makeup.setDisplayName('Kitchen Exhaust MakeUp Air Calculation Method')
    kitchen_makeup.setDescription('Determine logic to identify dining or cafe zones to provide makeup air to kitchen exhaust.')
    kitchen_makeup.setDefaultValue('Adjacent')
    args << kitchen_makeup

    # make argument for exterior_lighting_zone
    exterior_lighting_zone_choices = OpenStudio::StringVector.new
    exterior_lighting_zone_choices << '0 - Undeveloped Areas Parks'
    exterior_lighting_zone_choices << '1 - Developed Areas Parks'
    exterior_lighting_zone_choices << '2 - Neighborhood'
    exterior_lighting_zone_choices << '3 - All Other Areas'
    exterior_lighting_zone_choices << '4 - High Activity'
    exterior_lighting_zone = OpenStudio::Measure::OSArgument.makeChoiceArgument('exterior_lighting_zone', exterior_lighting_zone_choices, true)
    exterior_lighting_zone.setDisplayName('Exterior Lighting Zone')
    exterior_lighting_zone.setDescription('Identify the Exterior Lighitng Zone for the Building Site.')
    exterior_lighting_zone.setDefaultValue('3 - All Other Areas')
    args << exterior_lighting_zone

    # make an argument for add_constructions
    add_constructions = OpenStudio::Measure::OSArgument.makeBoolArgument('add_constructions', true)
    add_constructions.setDisplayName('Add Constructions to Model')
    add_constructions.setDescription('Construction Set will be appied to entire building')
    add_constructions.setDefaultValue(true)
    args << add_constructions

    # make an argument for add_space_type_loads
    add_space_type_loads = OpenStudio::Measure::OSArgument.makeBoolArgument('add_space_type_loads', true)
    add_space_type_loads.setDisplayName('Add Space Type Loads to Model')
    add_space_type_loads.setDescription('Populate existing space types in model with internal loads.')
    add_space_type_loads.setDefaultValue(true)
    args << add_space_type_loads

    # make an argument for add_elevators
    add_elevators = OpenStudio::Measure::OSArgument.makeBoolArgument('add_elevators', true)
    add_elevators.setDisplayName('Add Elevators to Model')
    add_elevators.setDescription('Elevators will be add directly to space in model vs. being applied to a space type.')
    add_elevators.setDefaultValue(true)
    args << add_elevators

    # make an argument for add_exterior_lights
    add_exterior_lights = OpenStudio::Measure::OSArgument.makeBoolArgument('add_exterior_lights', true)
    add_exterior_lights.setDisplayName('Add Exterior Lights to Model')
    add_exterior_lights.setDescription('Multiple exterior lights objects will be added for different classes of lighting such as parking and facade.')
    add_exterior_lights.setDefaultValue(true)
    args << add_exterior_lights

    # make an argument for onsite_parking_fraction
    onsite_parking_fraction = OpenStudio::Measure::OSArgument.makeDoubleArgument('onsite_parking_fraction', true)
    onsite_parking_fraction.setDisplayName('Onsite Parking Fraction')
    onsite_parking_fraction.setDescription('If set to 0 no exterior lighting for parking will be added')
    onsite_parking_fraction.setDefaultValue(1.0)
    args << onsite_parking_fraction

    # make an argument for add_exhaust
    add_exhaust = OpenStudio::Measure::OSArgument.makeBoolArgument('add_exhaust', true)
    add_exhaust.setDisplayName('Add Exhaust Fans to Model')
    add_exhaust.setDescription('Depending upon building type exhaust fans can be in kitchens, restrooms or other space types')
    add_exhaust.setDefaultValue(true)
    args << add_exhaust

    # make an argument for add_swh
    add_swh = OpenStudio::Measure::OSArgument.makeBoolArgument('add_swh', true)
    add_swh.setDisplayName('Add Service Water Heating to Model')
    add_swh.setDescription('This will add both the supply and demand side of service water heating.')
    add_swh.setDefaultValue(true)
    args << add_swh

    # make an argument for add_thermostat
    add_thermostat = OpenStudio::Measure::OSArgument.makeBoolArgument('add_thermostat', true)
    add_thermostat.setDisplayName('Add Thermostats')
    add_thermostat.setDescription('Add Thermost to model based on Space Type Standards information of spaces assigned to thermal zones.')
    add_thermostat.setDefaultValue(true)
    args << add_thermostat

    # make an argument for add_hvac
    add_hvac = OpenStudio::Measure::OSArgument.makeBoolArgument('add_hvac', true)
    add_hvac.setDisplayName('Add HVAC System to Model')
    add_hvac.setDescription('Add HVAC System and thermostats to model')
    add_hvac.setDefaultValue(true)
    args << add_hvac

    # make an argument for remove_objects
    remove_objects = OpenStudio::Measure::OSArgument.makeBoolArgument('remove_objects', true)
    remove_objects.setDisplayName('Clean Model of non-gemoetry objects')
    remove_objects.setDescription('Only removes objects of type that are selected to be added.')
    remove_objects.setDefaultValue(true)
    args << remove_objects

    # make an argument for use_upstream_args
    use_upstream_args = OpenStudio::Measure::OSArgument.makeBoolArgument('use_upstream_args', true)
    use_upstream_args.setDisplayName('Use Upstream Argument Values')
    use_upstream_args.setDescription('When true this will look for arguments or registerValues in upstream measures that match arguments from this measure, and will use the value from the upstream measure in place of what is entered for this measure.')
    use_upstream_args.setDefaultValue(true)
    args << use_upstream_args

    return args
  end

  # define what happens when the measure is run
  def run(model, runner, user_arguments)
    super(model, runner, user_arguments)

    # assign the user inputs to variables
    args = OsLib_HelperMethods.createRunVariables(runner, model, user_arguments, arguments(model))
    if !args then return false end

    # lookup and replace argument values from upstream measures
    if args['use_upstream_args'] == true
      args.each do |arg,value|
        next if arg == 'use_upstream_args' # this argument should not be changed
        value_from_osw = OsLib_HelperMethods.check_upstream_measure_for_arg(runner, arg)
        if !value_from_osw.empty?
          runner.registerInfo("Replacing argument named #{arg} from current measure with a value of #{value_from_osw[:value]} from #{value_from_osw[:measure_name]}.")
          new_val = value_from_osw[:value]
          # todo - make code to handle non strings more robust. check_upstream_measure_for_arg coudl pass bakc the argument type
          if arg == 'total_bldg_floor_area'
            args[arg] = new_val.to_f
          elsif arg == 'num_stories_above_grade'
            args[arg] = new_val.to_f
          elsif arg == 'zipcode'
            args[arg] = new_val.to_i
          else
            args[arg] = new_val
          end
        end
      end
    end

    # validate fraction parking
    fraction = OsLib_HelperMethods.checkDoubleAndIntegerArguments(runner, user_arguments, 'min' => 0.0, 'max' => 1.0, 'min_eq_bool' => true, 'max_eq_bool' => true, 'arg_array' => ['onsite_parking_fraction'])
    if !fraction then return false end

    # report initial condition of model
    initial_objects = model.getModelObjects.size
    runner.registerInitialCondition("The building started with #{initial_objects} objects.")

    # open channel to log messages
    OsLib_HelperMethods.setup_log_msgs(runner)

    # Make the standard applier
    standard = Standard.build((args['template']).to_s)

    # add internal loads to space types
    if args['add_space_type_loads']

      # remove internal loads
      if args['remove_objects']
        model.getSpaceLoads.each do |instance|
          next if instance.name.to_s.include?('Elevator') # most prototype building types model exterior elevators with name Elevator
          next if instance.to_InternalMass.is_initialized
          next if instance.to_WaterUseEquipment.is_initialized
          instance.remove
        end
        model.getDesignSpecificationOutdoorAirs.each(&:remove)
        model.getDefaultScheduleSets.each(&:remove)
      end

      model.getSpaceTypes.each do |space_type|
        # Don't add infiltration here; will be added later in the script
        test = standard.space_type_apply_internal_loads(space_type, true, true, true, true, true, false)
        if test == false
          runner.registerWarning("Could not add loads for #{space_type.name}. Not expected for #{args['template']}")
          next
        end

        # apply internal load schedules
        # the last bool test it to make thermostat schedules. They are now added in HVAC section instead of here
        standard.space_type_apply_internal_load_schedules(space_type, true, true, true, true, true, true, false)

        # extend space type name to include the args['template']. Consider this as well for load defs
        space_type.setName("#{space_type.name} - #{args['template']}")
        runner.registerInfo("Adding loads to space type named #{space_type.name}")
      end

      # warn if spaces in model without space type
      spaces_without_space_types = []
      model.getSpaces.each do |space|
        next if space.spaceType.is_initialized
        spaces_without_space_types << space
      end
      if !spaces_without_space_types.empty?
        runner.registerWarning("#{spaces_without_space_types.size} spaces do not have space types assigned, and wont' receive internal loads from standards space type lookups.")
      end
    end

    # identify primary building type (used for construction, and ideally HVAC as well)
    building_types = {}
    model.getSpaceTypes.each do |space_type|
      # populate hash of building types
      if space_type.standardsBuildingType.is_initialized
        bldg_type = space_type.standardsBuildingType.get
        if !building_types.key?(bldg_type)
          building_types[bldg_type] = space_type.floorArea
        else
          building_types[bldg_type] += space_type.floorArea
        end
      else
        runner.registerWarning("Can't identify building type for #{space_type.name}")
      end
    end
    primary_bldg_type = building_types.key(building_types.values.max) # TODO: - this fails if no space types, or maybe just no space types with standards
    lookup_building_type = standard.model_get_lookup_name(primary_bldg_type) # Used for some lookups in the standards gem
    model.getBuilding.setStandardsBuildingType(primary_bldg_type)

    # make construction set and apply to building
    if args['add_constructions']

      # remove default construction sets
      if args['remove_objects']
        model.getDefaultConstructionSets.each(&:remove)
      end

      # TODO: - allow building type and space type specific constructions set selection.
      if ['SmallHotel', 'LargeHotel', 'MidriseApartment', 'HighriseApartment'].include?(primary_bldg_type)
        is_residential = 'Yes'
      else
        is_residential = 'No'
      end
      if standard.respond_to?('model_get_building_properties')
        climate_zone = standard.model_get_building_properties(model)['climate_zone']
      else
        climate_zone = standard.model_get_building_climate_zone_and_building_type(model)['climate_zone']
      end
      bldg_def_const_set = standard.model_add_construction_set(model, climate_zone, lookup_building_type, nil, is_residential)
      if bldg_def_const_set.is_initialized
        bldg_def_const_set = bldg_def_const_set.get
        if is_residential then bldg_def_const_set.setName("Res #{bldg_def_const_set.name}") end
        model.getBuilding.setDefaultConstructionSet(bldg_def_const_set)
        runner.registerInfo("Adding default construction set named #{bldg_def_const_set.name}")
      else
        runner.registerError("Could not create default construction set for the building type #{lookup_building_type} in climate zone #{climate_zone}.")
        return false
      end

      # address any adiabatic surfaces that don't have hard assigned constructions
      model.getSurfaces.each do |surface|
        next if surface.outsideBoundaryCondition != 'Adiabatic'
        next if surface.construction.is_initialized
        surface.setAdjacentSurface(surface)
        surface.setConstruction(surface.construction.get)
        surface.setOutsideBoundaryCondition('Adiabatic')
      end

      # Modify the infiltration rates
      if args['remove_objects']
        model.getSpaceInfiltrationDesignFlowRates.each(&:remove)
      end
      standard.model_apply_infiltration_standard(model)
      standard.model_modify_infiltration_coefficients(model, primary_bldg_type, climate_zone)

      # set ground temperatures from DOE prototype buildings
      if standard.respond_to?('model_add_ground_temperatures')
        standard.model_add_ground_temperatures(model, primary_bldg_type, climate_zone)
      else
        # 0.6.0+, model_set_ground_temperatures
        OpenstudioStandards::Weather.model_set_ground_temperatures(model, climate_zone: climate_zone)
      end
    end

    # add elevators (returns ElectricEquipment object)
    if args['add_elevators']

      # remove elevators as spaceLoads or exteriorLights
      model.getSpaceLoads.each do |instance|
        next if !instance.name.to_s.include?('Elevator') # most prototype building types model exterior elevators with name Elevator
        instance.remove
      end
      model.getExteriorLightss.each do |ext_light|
        next if !ext_light.name.to_s.include?('Fuel equipment') # some prototype building types model exterior elevators by this name
        ext_light.remove
      end

      elevators = standard.model_add_elevators(model)
      if elevators.nil?
        runner.registerInfo('No elevators added to the building.')
      else
        elevator_def = elevators.electricEquipmentDefinition
        design_level = elevator_def.designLevel.get
        runner.registerInfo("Adding #{elevators.multiplier.round(1)} elevators each with power of #{OpenStudio.toNeatString(design_level, 0, true)} (W), plus lights and fans.")
      end
    end

    # add exterior lights (returns a hash where key is lighting type and value is exteriorLights object)
    if args['add_exterior_lights']

      if args['remove_objects']
        model.getExteriorLightss.each do |ext_light|
          next if ext_light.name.to_s.include?('Fuel equipment') # some prototype building types model exterior elevators by this name
          ext_light.remove
        end
      end

      exterior_lights = standard.model_add_typical_exterior_lights(model, args['exterior_lighting_zone'].chars[0].to_i, args['onsite_parking_fraction'])
      exterior_lights.each do |k, v|
        runner.registerInfo("Adding Exterior Lights named #{v.exteriorLightsDefinition.name} with design level of #{v.exteriorLightsDefinition.designLevel} * #{OpenStudio.toNeatString(v.multiplier, 0, true)}.")
      end
    end

    # add_exhaust
    if args['add_exhaust']

      # remove exhaust objects
      if args['remove_objects']
        model.getFanZoneExhausts.each(&:remove)
      end

      zone_exhaust_fans = standard.model_add_exhaust(model, args['kitchen_makeup']) # second argument is strategy for finding makeup zones for exhaust zones
      zone_exhaust_fans.each do |k, v|
        max_flow_rate_ip = OpenStudio.convert(k.maximumFlowRate.get, 'm^3/s', 'cfm').get
        if v.key?(:zone_mixing)
          zone_mixing = v[:zone_mixing]
          mixing_source_zone_name = zone_mixing.sourceZone.get.name
          mixing_design_flow_rate_ip = OpenStudio.convert(zone_mixing.designFlowRate.get, 'm^3/s', 'cfm').get
          runner.registerInfo("Adding #{OpenStudio.toNeatString(max_flow_rate_ip, 0, true)} (cfm) of exhaust to #{k.thermalZone.get.name}, with #{OpenStudio.toNeatString(mixing_design_flow_rate_ip, 0, true)} (cfm) of makeup air from #{mixing_source_zone_name}")
        else
          runner.registerInfo("Adding #{OpenStudio.toNeatString(max_flow_rate_ip, 0, true)} (cfm) of exhaust to #{k.thermalZone.get.name}")
        end
      end
    end

    # add service water heating demand and supply
    if args['add_swh']

      # remove water use equipment and water use connections
      if args['remove_objects']
        # TODO: - remove plant loops used for service water heating
        model.getWaterUseEquipments.each(&:remove)
        model.getWaterUseConnectionss.each(&:remove)
      end

      typical_swh = standard.model_add_typical_swh(model)
      midrise_swh_loops = []
      stripmall_swh_loops = []
      typical_swh.each do |loop|
        if loop.name.get.include?('MidriseApartment')
          midrise_swh_loops << loop
        elsif loop.name.get.include?('RetailStripmall')
          stripmall_swh_loops << loop
        else
          water_use_connections = []
          loop.demandComponents.each do |component|
            next if !component.to_WaterUseConnections.is_initialized
            water_use_connections << component
          end
          runner.registerInfo("Adding #{loop.name} to the building. It has #{water_use_connections.size} water use connections.")
        end
      end
      if !midrise_swh_loops.empty?
        runner.registerInfo("Adding #{midrise_swh_loops.size} MidriseApartment service water heating loops.")
      end
      if !stripmall_swh_loops.empty?
        runner.registerInfo("Adding #{stripmall_swh_loops.size} RetailStripmall service water heating loops.")
      end
    end

    # TODO: - when add methods below add bool to enable/disable them with default value to true

    # add daylight controls, need to perform a sizing run for 2010
    if args['template'] == '90.1-2010'
      if standard.model_run_sizing_run(model, "#{Dir.pwd}/SRvt") == false
        return false
      end
    end
    standard.model_add_daylighting_controls(model)

    # TODO: - add refrigeration
    # remove refrigeration equipment
    if args['remove_objects']
      model.getRefrigerationSystems.each(&:remove)
    end

    # TODO: - add internal mass
    # remove internal mass
    # if args['remove_objects']
    #  model.getSpaceLoads.each do |instance|
    #    next if not instance.to_InternalMass.is_initialized
    #    instance.remove
    #  end
    # end

    # TODO: - add slab modeling and slab insulation

    # TODO: - fuel customization for cooking and laundry
    # works by switching some fraction of electric loads to gas if requested (assuming base load is electric)

    # add thermostats
    if args['add_thermostat']

      # remove thermostats
      if args['remove_objects']
        model.getThermostatSetpointDualSetpoints.each(&:remove)
      end

      model.getSpaceTypes.each do |space_type|
        # create thermostat schedules
        # apply internal load schedules
        # the last bool test it to make thermostat schedules. They are added to the model but not assigned
        standard.space_type_apply_internal_load_schedules(space_type, false, false, false, false, false, false, true)

        # identify thermal thermostat and apply to zones (apply_internal_load_schedules names )
        model.getThermostatSetpointDualSetpoints.each do |thermostat|
          next if !thermostat.name.to_s.include?(space_type.name.to_s)
          runner.registerInfo("Assigning #{thermostat.name} to thermal zones with #{space_type.name} assigned.")
          space_type.spaces.each do |space|
            next if !space.thermalZone.is_initialized
            space.thermalZone.get.setThermostatSetpointDualSetpoint(thermostat)
          end
          next
        end
      end
    end

    # add hvac system
    if args['add_hvac']

      # remove HVAC objects
      if args['remove_objects']
        standard.model_remove_prm_hvac(model)
      end

      case args['system_type']
        when 'Inferred'

          # Get the hvac delivery type enum
          hvac_delivery = case args['hvac_delivery_type']
                          when 'Forced Air'
                            'air'
                          when 'Hydronic'
                            'hydronic'
                          end

          # Group the zones by occupancy type.  Only split out
          # non-dominant groups if their total area exceeds the limit.
          sys_groups = standard.model_group_zones_by_type(model, OpenStudio.convert(20_000, 'ft^2', 'm^2').get)

          # For each group, infer the HVAC system type.
          sys_groups.each do |sys_group|
            # Infer the primary system type
            # runner.registerInfo("template = #{args['template']}, climate_zone = #{climate_zone}, occ_type = #{sys_group['type']}, hvac_delivery = #{hvac_delivery}, htg_src = #{args['htg_src']}, clg_src = #{args['clg_src']}, area_ft2 = #{sys_group['area_ft2']}, num_stories = #{sys_group['stories']}")
            sys_type, central_htg_fuel, zone_htg_fuel, clg_fuel = standard.model_typical_hvac_system_type(model,
                                                                                                          climate_zone,
                                                                                                          sys_group['type'],
                                                                                                          hvac_delivery,
                                                                                                          args['htg_src'],
                                                                                                          args['clg_src'],
                                                                                                          OpenStudio.convert(sys_group['area_ft2'], 'ft^2', 'm^2').get,
                                                                                                          sys_group['stories'])

            # Infer the secondary system type for multizone systems
            sec_sys_type = case sys_type
                           when 'PVAV Reheat', 'VAV Reheat'
                             'PSZ-AC'
                           when 'PVAV PFP Boxes', 'VAV PFP Boxes'
                             'PSZ-HP'
                           else
                             sys_type # same as primary system type
                           end

            # Group zones by story
            story_zone_lists = standard.model_group_zones_by_story(model, sys_group['zones'])

            # On each story, add the primary system to the primary zones
            # and add the secondary system to any zones that are different.
            story_zone_lists.each do |story_group|
              # Differentiate primary and secondary zones, based on
              # operating hours and internal loads (same as 90.1 PRM)
              pri_sec_zone_lists = standard.model_differentiate_primary_secondary_thermal_zones(model, story_group)
              # Add the primary system to the primary zones
              standard.model_add_hvac_system(model, sys_type, central_htg_fuel, zone_htg_fuel, clg_fuel, pri_sec_zone_lists['primary'])
              # Add the secondary system to the secondary zones (if any)
              if !pri_sec_zone_lists['secondary'].empty?
                standard.model_add_hvac_system(model, sec_sys_type, central_htg_fuel, zone_htg_fuel, clg_fuel, pri_sec_zone_lists['secondary'])
              end
            end
          end

        else

          # Group the zones by story
          if standard.respond_to?('model_group_zones_by_story')
            story_groups = standard.model_group_zones_by_story(model, model.getThermalZones)
          else
            # 0.6.0+
            story_groups = OpenstudioStandards::Geometry.model_group_thermal_zones_by_building_story(model, model.getThermalZones)
          end

          # Add the user specified HVAC system for each story.
          # Single-zone systems will get one per zone.
          story_groups.each do |zones|
            model.add_cbecs_hvac_system(standard, args['system_type'], zones)
          end

      end
    end

    # TODO: - hours of operation customization (initially using existing measure downstream of this one)
    # not clear yet if this is altering existing schedules, or additional inputs when schedules first requested

    # set hvac controls and efficiencies (this should be last model articulation element)
    if args['add_hvac']
      case args['system_type']
        when 'Ideal Air Loads'

        else
          # Set the heating and cooling sizing parameters
          standard.model_apply_prm_sizing_parameters(model)

          # Perform a sizing run
          if standard.model_run_sizing_run(model, "#{Dir.pwd}/SR1") == false
            return false
          end

          # If there are any multizone systems, reset damper positions
          # to achieve a 60% ventilation effectiveness minimum for the system
          # following the ventilation rate procedure from 62.1
          standard.model_apply_multizone_vav_outdoor_air_sizing(model)

          # Apply the prototype HVAC assumptions
          standard.model_apply_prototype_hvac_assumptions(model, primary_bldg_type, climate_zone)

          # Apply the HVAC efficiency standard
          standard.model_apply_hvac_efficiency_standard(model, climate_zone)
      end
    end

    # remove everything but spaces, zones, and stub space types (extend as needed for additional objects, may make bool arg for this)
    if args['remove_objects']
      model.purgeUnusedResourceObjects
      objects_after_cleanup = initial_objects - model.getModelObjects.size
      if objects_after_cleanup > 0
        runner.registerInfo("Removing #{objects_after_cleanup} objects from model")
      end
    end

    # report final condition of model
    runner.registerFinalCondition("The building finished with #{model.getModelObjects.size} objects.")

    # log messages to info messages
    OsLib_HelperMethods.log_msgs

    return true
  end
end

# register the measure to be used by the application
CreateTypicalBuildingFromModel.new.registerWithApplication
