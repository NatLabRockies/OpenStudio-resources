
class AddHVACSystem < OpenStudio::Ruleset::ModelUserScript

  # override name to return the name of your script
  def name
    return "Add HVAC System Appropriate to give building type"
  end

  # return a vector of arguments
  def arguments(model)
    result = OpenStudio::Ruleset::UserScriptArgumentVector.new

    hvac_sys_num = OpenStudio::Ruleset::UserScriptArgument::makeIntegerArgument("hvac_sys_num")
    hvac_sys_num.setDisplayName("ASHRAE HVAC System Type Number")
    result << hvac_sys_num

    return result
  end

  def getDefaultArgumentsForNationalGrid(model,building_sector,sqft,number_of_non_plenum_stories)

    sys_num = -9999
    args = arguments(model)

    #get the input from the input hash
    building_sector = building_sector
    sqft = sqft
    num_floors = number_of_non_plenum_stories

    #infer number of floors if not specified directly
    unless num_floors
      length = input["building"]["geometry"]["length"]
      width = input["building"]["geometry"]["width"]
      num_floors = sqft / (length * width)
      num_floors = num_floors.round
    end

    #heating_fuel_type = input.input_hash[:heating_fuel_type]
    heating_fuel_type = "natural gas"

    #pick the hvac system based on ASHRAE 90.1-2004 Appendix G
    case building_sector
    #residential
    when "residential" :
      if heating_fuel_type == "electricity"
        sys_num = 2 #PTHP
      else
        sys_num = 1 #PTAC
      end
    #nonresidential
    when "commercial" :
      #nonresidential and 3 floors or less and <75,000 ft2
      if (num_floors <= 3 and sqft < 75000)
        if heating_fuel_type == "electricity"
          sys_num = 4 #PSZ-HP
        else
          sys_num = 3 #PSZ-AC
        end
      #nonresidential and 4 or 5 floors or 5 floors or less and 75,000 ft2 to 150,000 ft2
      elsif ( ((num_floors == 4 or num_floors == 5) and sqft < 75000) or (num_floors <= 5 and (sqft >= 75000 and sqft <= 150000)) )
        if heating_fuel_type == "electricity"
          sys_num = 6 #Packaged VAV w/ PFP Boxes
        else
          sys_num = 5 #Packaged VAV w/ Reheat
        end
      #nonresidential and more than 5 floors or >150,000 ft2
      elsif (num_floors >= 5 or sqft > 150000)
        if heating_fuel_type == "electricity"
          sys_num = 8 #VAV w/ PFP Boxes
        else
          sys_num = 7 #VAV w/ Reheat
        end
      end
    #heated only storage
    when "heated only storage" :
      if heating_fuel_type == "electricity"
        sys_num = 10 #Warm air furnace, electric
      else
        sys_num = 9 #Warm air furnace, gas fired
      end
    end

    if sys_num == -9999
      puts "#{sys_num} is not a valid system type."
      exit
    end

    result = OpenStudio::Ruleset::UserScriptArgumentMap.new
    arg = args[0].clone
    arg.setValue(sys_num)
    # arg.setDefaultValue(sys_num)
    # arg.setRangeType("Enumerated")
    # arg.setRange([1,2,3,4,5,6,7,8,9,10])
    result["hvac_sys_num"] = arg

    return result

  end

  def run(model, runner, arguments)

    # puts "Adding HVAC system."
    hvac_sys_num = arguments["hvac_sys_num"].valueAsInteger
    puts "hvac_sys_num = #{hvac_sys_num}"

    #get the thermal zones in the model
    zones = model.getThermalZones

    #get thermal zones that have a dual setpoint thermostat
    conditioned_zones = []
    zones.each do |zone|
      zone_thermostat = zone.thermostatSetpointDualSetpoint
      if not zone_thermostat.empty?
        conditioned_zones << zone
      else
        puts "> #{zone.name.to_s} is not conditioned"
      end
    end

    #Add HVAC system type
    case hvac_sys_num
    #1: PTAC, Residential
    when 1 :
      #add a system type 1 - PTAC to each zone
      hvac = OpenStudio::Model::addSystemType1(model, conditioned_zones)

    #2: PTHP, Residential
    when 2 :
      #add a system type 2 - PTHP to each zone
      hvac = OpenStudio::Model::addSystemType2(model, conditioned_zones)

    #3: PSZ-AC
    when 3 :
      #add a system type 3 - PSZ-AC to each zone and set this zone to be the controlling zone
      conditioned_zones.each do|zone|
        hvac = OpenStudio::Model::addSystemType3(model)
        hvac = hvac.to_AirLoopHVAC.get
        hvac.addBranchForZone(zone)
        outlet_node = hvac.supplyOutletNode
        setpoint_manager = outlet_node.setpointManagers.select { |spm| spm.to_SetpointManagerSingleZoneReheat.is_initialized }.first.to_SetpointManagerSingleZoneReheat.get
        setpoint_manager.setControlZone(zone)
      end

    #4: PSZ-HP
    when 4 :
      #add a system type 4 - PSZ-HP to each zone and set this zone to be the controlling zone
      conditioned_zones.each do|zone|
        hvac = OpenStudio::Model::addSystemType4(model)
        hvac = hvac.to_AirLoopHVAC.get
        hvac.addBranchForZone(zone)
        heat_pump = hvac.supplyComponents("OS:AirLoopHVAC:UnitaryHeatPump:AirToAir".to_IddObjectType)[0]
        heat_pump = heat_pump.to_AirLoopHVACUnitaryHeatPumpAirToAir.get
        heat_pump.setControllingZone(zone)
      end

    #5: Packaged VAV w/ Reheat
    when 5 :
      #add a system type 5 - Packaged VAV with Reheat to the model and hook up
      #each zone to this system
      hvac = OpenStudio::Model::addSystemType5(model)
      hvac = hvac.to_AirLoopHVAC.get
      conditioned_zones.each do|zone|
        hvac.addBranchForZone(zone)
      end

    #6: Packaged VAV w/ PFP Boxes
    when 6 :
      #add a system type 6 - Packaged VAV with PFP Boxes to the model and hook up
      #each zone to this system
      hvac = OpenStudio::Model::addSystemType6(model)
      hvac = hvac.to_AirLoopHVAC.get
      conditioned_zones.each do|zone|
        hvac.addBranchForZone(zone)
      end

    #7: VAV w/ Reheat
    when 7 :
      #add a system type 7 - VAV with Reheat to the model and hook up
      #each zone to this system
      hvac = OpenStudio::Model::addSystemType7(model)
      hvac = hvac.to_AirLoopHVAC.get
      conditioned_zones.each do|zone|
        hvac.addBranchForZone(zone)
      end
    #8: VAV w/ PFP Boxes
    when 8 :
      #add a system type 8 - VAV with PFP Boxes to the model and hook up
      #each zone to this system
      hvac = OpenStudio::Model::addSystemType8(model)
      hvac = hvac.to_AirLoopHVAC.get
      conditioned_zones.each do|zone|
        hvac.addBranchForZone(zone)
      end

    #9: Warm air furnace, gas fired
    when 9 :
      #add a system type 9 - Gas Fired Furnace to each zone and set this zone to be the controlling zone
      conditioned_zones.each do|zone|
        hvac = OpenStudio::Model::addSystemType9(model)
        hvac = hvac.to_AirLoopHVAC.get
        hvac.addBranchForZone(zone)
        outlet_node = hvac.supplyOutletNode
        setpoint_manager = outlet_node.setpointManagers.select { |spm| spm.to_SetpointManagerSingleZoneReheat.is_initialized }.first.to_SetpointManagerSingleZoneReheat.get
        setpoint_manager.setControlZone(zone)
      end

    #10: Warm air furnace, electric
    when 10 :
      #add a system type 10 - Electric Furnace to each zone and set this zone to be the controlling zone
      conditioned_zones.each do|zone|
        hvac = OpenStudio::Model::addSystemType10(model)
        hvac = hvac.to_AirLoopHVAC.get
        hvac.addBranchForZone(zone)
        outlet_node = hvac.supplyOutletNode
        setpoint_manager = outlet_node.setpointManagers.select { |spm| spm.to_SetpointManagerSingleZoneReheat.is_initialized }.first.to_SetpointManagerSingleZoneReheat.get
        setpoint_manager.setControlZone(zone)
      end
    #if system number is not recognized
    else puts "AddHVACSystem - cannot find system number #{hvac_sys_num}"
      exit
    end

    # puts "HVAC system added."

  end

end

AddHVACSystem.new













